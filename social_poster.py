"""
BroadFSC Social Media Cross-Platform Auto-Poster
Posts daily market insights to LinkedIn, X (Twitter), and Telegram simultaneously.
Uses Groq AI to generate platform-appropriate content.

Requirements:
    LINKEDIN_ACCESS_TOKEN  - LinkedIn OAuth token (optional)
    X_API_KEY              - X/Twitter API key (optional)
    X_API_SECRET          - X/Twitter API secret (optional)
    X_ACCESS_TOKEN        - X/Twitter access token (optional)
    X_ACCESS_TOKEN_SECRET - X/Twitter access token secret (optional)
    GROQ_API_KEY          - For AI content generation
    TELEGRAM_BOT_TOKEN    - For notifications
    TELEGRAM_CHANNEL_ID   - Notification channel
"""

import os
import sys
import datetime
import requests
import json

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Config
# ============================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

LINKEDIN_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
X_API_KEY = os.environ.get("X_API_KEY", "")
X_API_SECRET = os.environ.get("X_API_SECRET", "")
X_ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN", "")
X_ACCESS_TOKEN_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET", "")

TELEGRAM_LINK = "https://t.me/BroadFSC"
WEBSITE_LINK = "https://www.broadfsc.com/different"

# Platform character limits
PLATFORM_LIMITS = {
    "x": 280,
    "linkedin": 3000,
    "telegram_group": 4096,
}


# ============================================================
# AI Content Generation
# ============================================================

def generate_all_platform_content():
    """Generate content for all platforms using AI."""
    if not GROQ_API_KEY:
        return get_fallback_all_content()

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        now = datetime.datetime.utcnow()

        # Step 1: Generate main analysis
        analysis_prompt = (
            "You are a senior market analyst at Broad Investment Securities. "
            "Write today's global market summary ({date}).\n\n"
            "Provide 3-4 key observations about current global markets. "
            "Include specific data points where possible (indices, yields, commodities).\n\n"
            "Requirements:\n"
            "- Professional tone\n"
            "- 200-300 words\n"
            "- NO guaranteed returns or specific buy/sell recommendations\n"
            "- Format as plain text, no markdown"
        ).format(date=now.strftime("%B %d, %Y"))

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": analysis_prompt}],
            max_tokens=500,
            temperature=0.7
        )
        analysis = response.choices[0].message.content.strip()

        # Step 2: Generate platform-specific versions
        x_prompt = (
            "Convert this market analysis into a single X/Twitter post (max 280 chars). "
            "Include 2-3 relevant hashtags and the link {link}. "
            "No guaranteed returns.\n\n"
            "Analysis: {analysis}"
        ).format(link=TELEGRAM_LINK, analysis=analysis[:500])

        li_prompt = (
            "Convert this market analysis into a LinkedIn post (max 3000 chars). "
            "Use a professional networking tone. Add a question at the end to drive engagement. "
            "Include a subtle mention: 'Follow BroadFSC for daily global market briefings.'\n\n"
            "Analysis: {analysis}"
        ).format(analysis=analysis)

        # Generate X post
        x_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": x_prompt}],
            max_tokens=150,
            temperature=0.8
        )
        x_post = x_response.choices[0].message.content.strip()

        # Generate LinkedIn post
        li_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": li_prompt}],
            max_tokens=600,
            temperature=0.7
        )
        li_post = li_response.choices[0].message.content.strip()

        return {
            "analysis": analysis,
            "x": x_post[:280] if len(x_post) > 280 else x_post,
            "linkedin": li_post[:3000] if len(li_post) > 3000 else li_post,
        }
    except Exception as e:
        print("  AI content generation failed: " + str(e))
        return get_fallback_all_content()


def get_fallback_all_content():
    """Fallback content when AI is unavailable."""
    now = datetime.datetime.utcnow()
    date_str = now.strftime("%B %d, %Y")
    weekday = now.strftime("%A")

    return {
        "analysis": (
            "Global Market Snapshot - " + date_str + " (" + weekday + ")\n\n"
            "Key themes in today's markets:\n\n"
            "1. Central Bank Policy - Major central banks continue to navigate "
            "the balance between inflation control and economic growth support. "
            "Market participants are closely watching for policy signals.\n\n"
            "2. Global Equity Rotation - Sector rotation patterns persist as investors "
            "reassess growth vs. value allocations across major indices.\n\n"
            "3. Commodity Markets - Energy and commodity prices remain influenced "
            "by geopolitical developments and supply-demand dynamics.\n\n"
            "4. Currency Markets - FX volatility reflects diverging monetary policy "
            "paths among major economies.\n\n"
            "Stay informed with daily briefings from BroadFSC."
        ),
        "x": (
            "Global Markets Update: Key themes to watch this week - "
            "Central bank policy signals, sector rotation, commodity flows. "
            "Stay informed: " + TELEGRAM_LINK + " "
            "#Investing #Markets #Trading"
        ),
        "linkedin": (
            "Global Market Update - " + date_str + "\n\n"
            "Here are the key themes I'm watching across global markets today:\n\n"
            "Central Bank Policy: Major central banks are navigating the balance between "
            "inflation control and growth support. Policy divergence among Fed, ECB, and BOJ "
            "continues to create cross-border capital flow opportunities.\n\n"
            "Equity Sector Rotation: The ongoing rotation between growth and value sectors "
            "reflects changing expectations about the rate environment and earnings quality.\n\n"
            "What's your outlook for global markets this week?\n\n"
            "Follow BroadFSC for daily global market briefings and professional investment insights."
        ),
    }


# ============================================================
# Platform Posting Functions
# ============================================================

def post_to_x(content):
    """Post to X/Twitter."""
    if not X_API_KEY or not X_ACCESS_TOKEN:
        print("  X: Skipped (no API credentials)")
        return False

    try:
        # Using X API v2
        headers = {"Authorization": "Bearer " + X_ACCESS_TOKEN}

        payload = {"text": content}

        # Need to generate OAuth 1.0a signature for posting
        # For simplicity, using a helper approach
        import hashlib
        import hmac
        import base64
        import urllib.parse

        oauth_consumer_key = X_API_KEY
        oauth_nonce = os.urandom(16).hex()
        oauth_timestamp = str(int(datetime.datetime.utcnow().timestamp()))
        oauth_signature_method = "HMAC-SHA1"
        oauth_version = "1.0"
        oauth_token = X_ACCESS_TOKEN

        params = {
            "oauth_consumer_key": oauth_consumer_key,
            "oauth_nonce": oauth_nonce,
            "oauth_signature_method": oauth_signature_method,
            "oauth_timestamp": oauth_timestamp,
            "oauth_token": oauth_token,
            "oauth_version": oauth_version,
        }

        base_url = "https://api.twitter.com/2/tweets"

        # Create signature base string
        param_str = "&".join([k + "=" + urllib.parse.quote(v, safe="") for k, v in sorted(params.items())])
        base_string = "POST&" + urllib.parse.quote(base_url, safe="") + "&" + urllib.parse.quote(param_str, safe="")

        # Create signing key
        signing_key = urllib.parse.quote(X_API_SECRET, safe="") + "&" + urllib.parse.quote(X_ACCESS_TOKEN_SECRET, safe="")

        # Generate signature
        signature = base64.b64encode(
            hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
        ).decode()

        params["oauth_signature"] = signature

        oauth_header = "OAuth " + ", ".join([
            k + '="' + urllib.parse.quote(v, safe="") + '"' for k, v in sorted(params.items())
        ])

        headers = {
            "Authorization": oauth_header,
            "Content-Type": "application/json",
        }

        r = requests.post(base_url, headers=headers, json=payload, timeout=15)
        if r.status_code == 201:
            print("  X: Posted successfully!")
            return True
        else:
            print("  X: FAIL HTTP " + str(r.status_code) + " - " + r.text[:200])
            return False
    except Exception as e:
        print("  X: FAIL - " + str(e))
        return False


def post_to_linkedin(content):
    """Post to LinkedIn."""
    if not LINKEDIN_TOKEN:
        print("  LinkedIn: Skipped (no access token)")
        return False

    try:
        headers = {"Authorization": "Bearer " + LINKEDIN_TOKEN, "Content-Type": "application/json"}

        # Get user profile URN
        profile_r = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers, timeout=10)
        if profile_r.status_code != 200:
            print("  LinkedIn: Profile fetch FAIL HTTP " + str(profile_r.status_code))
            return False

        profile_data = profile_r.json()
        person_urn = "urn:li:person:" + profile_data["sub"]

        # Create post
        post_data = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content,
                    },
                    "shareMediaCategory": "ARTICLE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        post_r = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=headers,
            json=post_data,
            timeout=15
        )
        if post_r.status_code in (200, 201):
            print("  LinkedIn: Posted successfully!")
            return True
        else:
            print("  LinkedIn: FAIL HTTP " + str(post_r.status_code) + " - " + post_r.text[:200])
            return False
    except Exception as e:
        print("  LinkedIn: FAIL - " + str(e))
        return False


def notify_telegram(message):
    """Send notification to Telegram channel."""
    if not BOT_TOKEN or not CHANNEL_ID:
        return
    url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception:
        pass


# ============================================================
# Main
# ============================================================
def main():
    print("=" * 50)
    print("BroadFSC Social Media Cross-Platform Auto-Poster")
    print("=" * 50)

    now = datetime.datetime.utcnow()
    print("Current UTC: " + now.strftime("%Y-%m-%d %H:%M"))
    print()

    # Check platform availability
    platforms = []
    if X_API_KEY and X_ACCESS_TOKEN:
        platforms.append("x")
    if LINKEDIN_TOKEN:
        platforms.append("linkedin")

    if not platforms:
        print("No social media platforms configured.")
        print("To enable, add these GitHub Secrets:")
        print("  - X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET (for X/Twitter)")
        print("  - LINKEDIN_ACCESS_TOKEN (for LinkedIn)")
        print()
        print("Telegram notification will still work as fallback.")
        # Still notify about what would have been posted
        content = generate_all_platform_content()
        print()
        print("Generated content preview (not posted):")
        print("--- X Preview ---")
        print(content["x"])
        print()
        print("--- LinkedIn Preview ---")
        print(content["linkedin"][:200] + "...")
        print()
        print("No platforms configured. Exiting.")
        return

    print("Platforms configured: " + ", ".join(platforms))
    print()

    # Step 1: Generate content
    print("Step 1: Generating content via AI...")
    content = generate_all_platform_content()
    print("  Analysis: " + str(len(content["analysis"])) + " chars")
    print("  X post: " + str(len(content["x"])) + " chars")
    print("  LinkedIn: " + str(len(content["linkedin"])) + " chars")
    print()

    # Step 2: Post to each platform
    results = {}
    print("Step 2: Posting to platforms...")
    if "x" in platforms:
        results["X"] = post_to_x(content["x"])
    if "linkedin" in platforms:
        results["LinkedIn"] = post_to_linkedin(content["linkedin"])
    print()

    # Step 3: Notify
    success_list = [k for k, v in results.items() if v]
    fail_list = [k for k, v in results.items() if not v]

    if success_list:
        notify_telegram(
            "Social Media Update\n\n"
            "Posted to: " + ", ".join(success_list) + "\n"
            + (content["x"] if "X" in success_list else "")
        )

    print("Results:")
    for platform, success in results.items():
        print("  " + platform + ": " + ("SUCCESS" if success else "FAILED"))

    print()
    print("=" * 50)


if __name__ == "__main__":
    main()
