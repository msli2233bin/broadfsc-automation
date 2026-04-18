"""
BroadFSC Bluesky Auto-Poster
Posts market insights to Bluesky using AT Protocol API.

Setup:
1. Register at bsky.app
2. Go to Settings > App Passwords > Generate new password
3. Set environment variables:
   - BLUESKY_HANDLE: your handle (e.g., broadfsc.bsky.social)
   - BLUESKY_APP_PASSWORD: the generated app password (xxxx-xxxx-xxxx-xxxx)
   - GROQ_API_KEY: for AI content generation (optional, has fallback)
"""

import os
import sys
import datetime
import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Config
BLUESKY_HANDLE = os.environ.get("BLUESKY_HANDLE", "")
BLUESKY_APP_PASSWORD = os.environ.get("BLUESKY_APP_PASSWORD", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

PDS_URL = "https://bsky.social/xrpc"
TELEGRAM_LINK = "https://t.me/BroadFSC"
HUB_LINK = "https://msli2233bin.github.io/broadfsc-automation/"
HASHTAGS = ["#Investing", "#Trading", "#MarketAnalysis"]


def create_session():
    """Authenticate with Bluesky and return session tokens."""
    resp = requests.post(
        f"{PDS_URL}/com.atproto.server.createSession",
        json={"identifier": BLUESKY_HANDLE, "password": BLUESKY_APP_PASSWORD},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def post_bluesky(text):
    """Create a post on Bluesky."""
    if not BLUESKY_HANDLE or not BLUESKY_APP_PASSWORD:
        print("Bluesky: Missing BLUESKY_HANDLE or BLUESKY_APP_PASSWORD")
        return False

    try:
        session = create_session()
        access_jwt = session["accessJwt"]
        did = session["did"]
        print(f"Authenticated: {session['handle']} (DID: {did})")
    except Exception as e:
        print(f"Bluesky auth failed: {e}")
        return False

    # Trim to 300 graphemes
    if len(text) > 290:
        text = text[:287] + "..."

    record = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    try:
        r = requests.post(
            f"{PDS_URL}/com.atproto.repo.createRecord",
            headers={"Authorization": f"Bearer {access_jwt}"},
            json={"repo": did, "collection": "app.bsky.feed.post", "record": record},
            timeout=15,
        )
        if r.status_code in [200, 201]:
            uri = r.json().get("uri", "")
            print(f"Bluesky: Posted! URI: {uri}")
            return True
        else:
            print(f"Bluesky: FAIL HTTP {r.status_code} - {r.text[:300]}")
            return False
    except Exception as e:
        print(f"Bluesky: FAIL - {e}")
        return False


def generate_content():
    """Generate a Bluesky post using AI or fallback."""
    if not GROQ_API_KEY:
        return get_fallback()

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        now = datetime.datetime.utcnow()
        day = now.strftime("%A")
        tags = " ".join(HASHTAGS)

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": (
                    "You are a professional market analyst at BroadFSC. "
                    "Write ONE short market insight post for Bluesky.\n"
                    f"Today is {day}.\n\n"
                    "Requirements:\n"
                    "- Maximum 280 characters\n"
                    "- Include 1 specific market observation\n"
                    f"- End with: {tags}\n"
                    "- Do NOT include any links\n"
                    "- Do NOT promise returns"
                )
            }],
            max_tokens=100,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI generation failed: {e}")
        return get_fallback()


def get_fallback():
    """Fallback content when AI is unavailable."""
    posts = [
        f"Global markets update: Central bank policy divergence drives cross-currency flows. Daily briefings at {TELEGRAM_LINK} {' '.join(HASHTAGS)}",
        f"Key themes: Fed signals, earnings season, geopolitical risk premiums shaping commodity markets. {' '.join(HASHTAGS)}",
        f"Markets move fast. BroadFSC delivers AI-powered daily market briefings in English, Spanish & Arabic. {TELEGRAM_LINK} {' '.join(HASHTAGS)}",
    ]
    idx = datetime.datetime.utcnow().timetuple().tm_yday % len(posts)
    return posts[idx]


def main():
    print("=" * 40)
    print("BroadFSC Bluesky Auto-Poster")
    print("=" * 40)
    print(f"UTC: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")
    print()

    content = generate_content()
    print(f"Content: {content[:100]}...")
    success = post_bluesky(content)

    if success:
        print("\nDone! Post published to Bluesky.")
    else:
        print("\nFailed to post to Bluesky.")


if __name__ == "__main__":
    main()
