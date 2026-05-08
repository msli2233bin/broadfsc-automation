"""
统一社区评论调度器
=================
不定时到各大社区去评论。

每次运行：
1. 随机选1-2个平台（权重不同）
2. 每个平台随机延迟 60-180秒
3. 调用对应engager（每次只回复2-4条，模拟真人）
4. 记录到 analytics_db

这样即使定时触发，实际评论行为也是随机分散的。

运行：
    python community_commenter.py              # 正常运行
    python community_commenter.py --dry-run    # 只模拟
    python community_commenter.py --platforms bluesky,mastodon  # 指定平台
"""
import os
import sys
import time
import random
import subprocess
from pathlib import Path
from datetime import datetime

# 平台注册表（权重=活跃度，越高越常被选中）
ENGAGERS = {
    "bluesky": {
        "script": "bluesky_engager.py",
        "weight": 3,
        "enabled": True,
    },
    "mastodon": {
        "script": "mastodon_engager.py",
        "weight": 2,
        "enabled": True,
    },
    "threads": {
        "script": "threads_engager.py",
        "weight": 2,
        "enabled": True,
    },
}


def pick_platforms():
    """随机选1-2个平台"""
    enabled = [p for p, cfg in ENGAGERS.items() if cfg["enabled"]]
    if not enabled:
        return []
    weights = [ENGAGERS[p]["weight"] for p in enabled]
    # 75%概率选1个，25%选2个
    n = random.choices([1, 2], weights=[3, 1])[0]
    n = min(n, len(enabled))
    return random.choices(enabled, weights=weights, k=n)


def run_engager(platform, dry_run=False):
    """运行某个平台的engager（subprocess调用）"""
    cfg = ENGAGERS[platform]
    script = Path(__file__).parent / cfg["script"]

    if not script.exists():
        print(f"  [WARN] {script.name} not found, skipping {platform}")
        return False

    limit = random.randint(2, 4)  # 每次少量，模拟真人
    cmd = [sys.executable, str(script), "--limit", str(limit)]
    if dry_run:
        cmd.append("--dry-run")

    print(f"  [RUN] {platform}: {script.name} --limit {limit}")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=180,
        cwd=str(script.parent),
    )
    # 打印最后几行输出
    out = result.stdout.strip()
    if out:
        for line in out.splitlines()[-8:]:
            print(f"    {line}")
    if result.stderr:
        err = result.stderr.strip()
        for line in err.splitlines()[-4:]:
            print(f"    [ERR] {line}")
    return result.returncode == 0


def log_to_db(platform, results):
    """记录到 analytics_db"""
    try:
        from analytics_db import get_db
        conn = get_db()
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for r in results:
            cursor.execute(
                "INSERT OR IGNORE INTO engagements (ts, platform, action, target, success) VALUES (?, ?, ?, ?, ?)",
                (now, platform, "comment", r.get("target", ""), r.get("success", 0)),
            )
        conn.commit()
    except Exception as e:
        print(f"  [DB] Log failed: {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Community Commenter - Unified Scheduler")
    parser.add_argument("--dry-run", action="store_true", help="Simulate only")
    parser.add_argument("--platforms", type=str, default=None, help="Comma-separated, e.g. bluesky,mastodon")
    args = parser.parse_args()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"[{now_str}] Community Commenter starting...")

    if args.platforms:
        platforms = [p.strip() for p in args.platforms.split(",")]
    else:
        platforms = pick_platforms()

    if not platforms:
        print("  No platforms selected. Exiting.")
        return

    print(f"  Selected: {', '.join(platforms)}")
    print(f"  Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()

    for i, platform in enumerate(platforms):
        if i > 0:
            delay = random.uniform(60, 180)
            print(f"  [DELAY] Waiting {delay:.0f}s before next platform...")
            if not args.dry_run:
                time.sleep(delay)

        run_engager(platform, dry_run=args.dry_run)

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] All done.")


if __name__ == "__main__":
    main()
