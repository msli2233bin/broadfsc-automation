"""
Threads Token: Generate + Exchange to Long-Lived in ONE step.
Paste the fresh token when prompted, it will be exchanged immediately.
"""
import requests
import sys
import os

APP_SECRET = "9857adbca8c910959a78e14d813c0e53"

token = input("Paste fresh Access Token here and press Enter: ").strip()

if not token:
    print("No token!")
    sys.exit(1)

# Step 1: Verify token
print("\n[1/3] Verifying token...")
r = requests.get("https://graph.threads.net/v1.0/me", params={"access_token": token})
print(f"  Status: {r.status_code}")
if r.status_code != 200:
    print(f"  Error: {r.text}")
    print("\n  Token is INVALID. Make sure you copy it IMMEDIATELY after generating.")
    sys.exit(1)
user_id = r.json().get("id")
print(f"  User ID: {user_id}")
print(f"  Token is VALID!")

# Step 2: Exchange for long-lived token
print("\n[2/3] Exchanging for long-lived token (60 days)...")
r = requests.get("https://graph.threads.net/v1.0/access_token", params={
    "grant_type": "th_exchange_token",
    "client_secret": APP_SECRET,
    "access_token": token,
})
print(f"  Status: {r.status_code}")
if r.status_code != 200:
    print(f"  Error: {r.text}")
    sys.exit(1)
data = r.json()
long_token = data.get("access_token")
expires = data.get("expires_in", 0)
print(f"  Long-lived token received!")
print(f"  Expires in: {expires}s (~{expires//86400} days)")

# Step 3: Save to .env
print(f"\n[3/3] Saving to .env...")
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
with open(env_path, "a") as f:
    f.write(f"\nTHREADS_ACCESS_TOKEN={long_token}\n")
    f.write(f"THREADS_USER_ID={user_id}\n")
    f.write(f"THREADS_APP_SECRET={APP_SECRET}\n")
print(f"  Saved to: {env_path}")

# Also set system environment variables
os.environ["THREADS_ACCESS_TOKEN"] = long_token
os.environ["THREADS_USER_ID"] = user_id

print(f"\n{'='*50}")
print(f"SUCCESS!")
print(f"{'='*50}")
print(f"Long-lived Token: {long_token[:30]}...")
print(f"User ID: {user_id}")
print(f"Expires: ~{expires//86400} days")
print(f"\nNext step: Add THREADS_ACCESS_TOKEN to GitHub Secrets")
print(f"  gh secret set THREADS_ACCESS_TOKEN --body \"{long_token}\"")
