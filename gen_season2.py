"""
BroadFSC TikTok Season 2 — Technical Indicators Series (EP5-EP8)

EP5: Moving Average Crossovers (Golden Cross & Death Cross)
EP6: RSI Overbought/Oversold Strategy
EP7: Stop Loss & Take Profit Like a Pro
EP8: Trend Lines Trading Guide

Uses v5 video engine from tiktok_poster.py — just generates 4 videos locally.
"""

import os
import sys
import asyncio
import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Import video engine
from tiktok_poster import (
    _script_to_spoken_format, build_spoken_lines, generate_all_audio,
    create_video_v5, C, _render_scene_v5, _font, _wrap,
    W, H, FPS, TTS_VOICE, TTS_RATE
)

# Set API key
# GROQ_API_KEY should be set via environment variable

# ============================================================
# Season 2 Scripts (EP5-EP8)
# ============================================================
SEASON2_SCRIPTS = [
    # ── EP5: MOVING AVERAGE CROSSOVERS ──────────────────────
    {
        "type": "signal",
        "hook": "Two lines crossing on a chart just told you what to do next.",
        "promise": "Moving average crossovers explained in sixty seconds.",
        "body": [
            "When the fifty day crosses above the two hundred day, that's a GOLDEN CROSS. The uptrend is strengthening. This is your buy signal.",
            "When the fifty day crosses below the two hundred day, that's a DEATH CROSS. The downtrend is accelerating. Time to protect your portfolio.",
        ],
        "midpoint": "But here's what most beginners get wrong.",
        "midpoint_detail": "These crossovers work best on daily or weekly charts. On lower timeframes you'll get whipsawed with fake signals constantly.",
        "cta": "Save this. Next time you see a cross, you'll know exactly what it means. Follow for more.",
        "hashtags": "#movingaverage #goldencross #tradingstrategy #investing #technicalanalysis",
    },
    # ── EP6: RSI OVERBOUGHT/OVERSOLD ────────────────────────
    {
        "type": "signal",
        "hook": "RSI just flashed a signal. Do you know how to read it?",
        "promise": "The two numbers that predict reversals.",
        "body": [
            "When RSI drops below thirty, the asset is OVERSOLD. Selling pressure is exhausted. A bounce could be coming. Smart traders look for buy setups here.",
            "When RSI rises above seventy, the asset is OVERBOUGHT. Buying momentum is fading. A pullback could be near. This is where you consider taking profits.",
        ],
        "midpoint": "But here's what most beginners miss.",
        "midpoint_detail": "RSI can stay overbought or oversold for extended periods during strong trends. Never trade RSI alone. Always combine it with price action at support and resistance.",
        "cta": "Screenshot this for your next trade setup. Follow for more.",
        "hashtags": "#RSI #trading #technicalanalysis #overbought #investing",
    },
    # ── EP7: STOP LOSS & TAKE PROFIT ───────────────────────
    {
        "type": "mistake",
        "hook": "Most traders lose money not because they're wrong about direction.",
        "promise": "They don't manage risk properly. Here's how the pros do it.",
        "body": [
            "Rule one: ALWAYS set your stop loss BEFORE you enter a trade. Not after. This removes emotion from the decision completely.",
            "The key ratio is one to three. Risk three dollars on your stop loss, aim for nine dollars on your take profit. Even if you're only right forty percent of the time, you'll still be profitable.",
        ],
        "midpoint": "But here's the mistake almost everyone makes.",
        "midpoint_detail": "They move their stop loss when the trade goes against them. Hope is not a strategy. Set it and forget it. A small loss is just the cost of doing business.",
        "cta": "Share this with someone who keeps moving their stop loss. Follow.",
        "hashtags": "#stoploss #riskmanagement #trading #investing #takeprofit",
    },
    # ── EP8: TREND LINES ───────────────────────────────────
    {
        "type": "beginner",
        "hook": "If you can draw a straight line, you can trade trends.",
        "promise": "Trend lines are the most visual tool in all of technical analysis.",
        "body": [
            "For an uptrend line, connect at least two higher lows. The more times price bounces off this line, the more valid it becomes.",
            "The real trading opportunity comes when a trend line BREAKS. But wait for a confirmed break. Price must close beyond the line, not just poke through temporarily.",
        ],
        "midpoint": "And here's the most reliable setup you'll find.",
        "midpoint_detail": "After a trend line breaks, the old line often flips from support to resistance, or vice versa. This role reversal is one of the most consistent patterns in trading.",
        "cta": "Draw your first trend line today. Follow for more trading education.",
        "hashtags": "#trendlines #technicalanalysis #trading #investing #chartpatterns",
    },
]


async def generate_episode(ep_num, script_dict, output_dir):
    """Generate a single episode video."""
    print(f"\n{'='*58}")
    print(f" EP.{ep_num} — {script_dict['hook'][:50]}...")
    print(f"{'='*58}")

    # Convert to spoken format
    script = _script_to_spoken_format(script_dict)
    script["type"] = script_dict.get("type", "general")
    script["hashtags"] = script_dict.get("hashtags", "#investing #finance")

    # Generate TTS audio
    print("--- Generating Voice Over ---")
    spoken_lines = build_spoken_lines(script)
    audio_info = await generate_all_audio(spoken_lines, output_dir)
    print(f"  Generated {len(audio_info)} audio clips")

    # Create video
    print("--- Creating Video ---")
    video_path = os.path.join(output_dir, f"tiktok_ep{ep_num}.mp4")
    success = create_video_v5(script, audio_info, video_path)

    if success:
        size_kb = os.path.getsize(video_path) // 1024
        print(f"  EP.{ep_num} SUCCESS: {video_path} ({size_kb}KB)")
    else:
        print(f"  EP.{ep_num} FAILED!")

    # Cleanup TTS cache
    for _, ap, _ in audio_info:
        try:
            if os.path.exists(ap):
                os.remove(ap)
        except:
            pass

    return video_path if success else None


async def main():
    print("=" * 58)
    print(" BroadFSC TikTok Season 2 — EP5-EP8")
    print(" Technical Indicators Series")
    print("=" * 58)
    print(f" Time: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_s2_cache")
    os.makedirs(output_dir, exist_ok=True)

    results = {}
    for i, script_dict in enumerate(SEASON2_SCRIPTS):
        ep_num = 5 + i
        path = await generate_episode(ep_num, script_dict, output_dir)
        results[ep_num] = path

    # Copy final videos to project root
    print("\n" + "=" * 58)
    print(" RESULTS")
    print("=" * 58)
    for ep_num, path in sorted(results.items()):
        if path and os.path.exists(path):
            final_name = f"tiktok_ep{ep_num}_final.mp4"
            final_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), final_name)
            import shutil
            shutil.copy2(path, final_path)
            size_kb = os.path.getsize(final_path) // 1024
            print(f"  EP.{ep_num}: {final_name} ({size_kb}KB) ✅")
        else:
            print(f"  EP.{ep_num}: FAILED ❌")

    # Cleanup temp dir
    try:
        import shutil
        shutil.rmtree(output_dir, ignore_errors=True)
    except:
        pass

    print("\nDone! Videos ready for upload.")


if __name__ == "__main__":
    asyncio.run(main())
