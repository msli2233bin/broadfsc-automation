"""
BroadFSC Email Campaign System
Brevo API integration for automated email outreach.

Free Tier Limits:
- 300 emails/day (transactional)
- 9,000 emails/month
- Unlimited contacts

Strategy:
- Warm-up: 30-day gradual ramp-up
- 4 personality system (Alex/Thomas/Michael/Iron Bull)
- Anti-spam: domain rotation, daily limits, bounce tracking
- 3 platforms ready: Brevo (active), Sender/Kit (pending eu.org domain)

Usage:
  python email_campaign.py --send          # Send today's email batch
  python email_campaign.py --warmup        # Show warm-up schedule
  python email_campaign.py --stats         # Show send statistics
  python email_campaign.py --test          # Send test email
  python email_campaign.py --add-contact   # Add a contact
  python email_campaign.py --import-csv    # Import contacts from CSV
  python email_campaign.py --templates     # List available templates
"""

import os
import sys
import json
import datetime
import random
import time
import csv
import re
import argparse
from pathlib import Path
from email.utils import formataddr

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# Config
# ============================================================
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_API_URL = "https://api.brevo.com/v3"

# Sender config
SENDER_NAME = "BroadFSC"
SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", "msli2233bin+brevo@gmail.com")
REPLY_TO_EMAIL = os.environ.get("BREVO_REPLY_TO", "msli2233bin@gmail.com")

# When eu.org domain is approved, switch to:
# SENDER_EMAIL = "insights@broadfsc.eu.org"
# REPLY_TO_EMAIL = "contact@broadfsc.eu.org"

# Data directories
DATA_DIR = Path(__file__).parent / "email_data"
CONTACTS_FILE = DATA_DIR / "contacts.json"
SEND_LOG_FILE = DATA_DIR / "send_log.json"
BOUNCE_FILE = DATA_DIR / "bounces.json"
WARMUP_FILE = DATA_DIR / "warmup_state.json"
TEMPLATES_DIR = DATA_DIR / "templates"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

# Analytics tracking
try:
    from analytics_logger import log_post
    HAS_ANALYTICS = True
except ImportError:
    HAS_ANALYTICS = False

# ============================================================
# 4 Personality System
# ============================================================
PERSONALITIES = {
    "alex": {
        "name": "Alex Chen",
        "title": "Chief Technical Analyst",
        "tone": "sharp, data-driven, contrarian",
        "sign_off": "Trade smart,\nAlex Chen\nChief Technical Analyst, BroadFSC",
        "emoji": "🐊",
        "focus": "technical analysis, chart patterns, entry/exit signals"
    },
    "thomas": {
        "name": "Thomas Yang",
        "title": "Senior Value Analyst",
        "tone": "patient, fundamental, long-term focused",
        "sign_off": "Invest wisely,\nThomas Yang\nSenior Value Analyst, BroadFSC",
        "emoji": "📘",
        "focus": "value investing, fundamentals, dividend yields"
    },
    "michael": {
        "name": "Michael Hong",
        "title": "Macro Strategist",
        "tone": "big picture, geopolitical, macro trends",
        "sign_off": "Stay ahead of the curve,\nMichael Hong\nMacro Strategist, BroadFSC",
        "emoji": "🔭",
        "focus": "macro trends, central banks, geopolitical analysis"
    },
    "iron_bull": {
        "name": "Iron Bull",
        "title": "Retail Momentum Trader",
        "tone": "aggressive, meme-aware, high-energy",
        "sign_off": "Bullish & Bearish,\nIron Bull\nRetail Momentum Desk, BroadFSC",
        "emoji": "⚔️",
        "focus": "momentum plays, retail sentiment, breakout alerts"
    }
}

def get_personality_for_date(date=None):
    """Rotate personalities by date, same as social media system."""
    if date is None:
        date = datetime.date.today()
    personalities = list(PERSONALITIES.keys())
    index = date.timetuple().tm_yday % len(personalities)
    return personalities[index], PERSONALITIES[personalities[index]]

# ============================================================
# 30-Day Warm-Up Schedule
# ============================================================
WARMUP_SCHEDULE = [
    # (day_range, max_daily_sends, description)
    ((1, 3),   5,   "Ultra conservative - just getting started"),
    ((4, 7),   10,  "Very slow - building reputation"),
    ((8, 14),  20,  "Moderate - steady growth"),
    ((15, 21), 30,  "Growing - good reputation building"),
    ((22, 30), 50,  "Ramping up - almost at full capacity"),
    ((31, 999), 100, "Full capacity - Brevo free limit is 300/day"),
]

def get_warmup_state():
    """Load or initialize warm-up state."""
    if WARMUP_FILE.exists():
        return json.loads(WARMUP_FILE.read_text(encoding='utf-8'))
    return {
        "start_date": datetime.date.today().isoformat(),
        "current_day": 1,
        "daily_sends_today": 0,
        "last_send_date": None,
        "total_sends": 0,
        "total_bounces": 0,
        "total_opens": 0,
        "total_clicks": 0
    }

def save_warmup_state(state):
    """Save warm-up state."""
    WARMUP_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding='utf-8')

def get_daily_limit(state=None):
    """Get today's maximum send count based on warm-up schedule."""
    if state is None:
        state = get_warmup_state()
    start = datetime.date.fromisoformat(state["start_date"])
    today = datetime.date.today()
    day_num = (today - start).days + 1

    for (start_day, end_day), limit, desc in WARMUP_SCHEDULE:
        if start_day <= day_num <= end_day:
            return limit, day_num, desc

    # Fallback to max
    return 300, day_num, "Full capacity"

def advance_warmup_day(state=None):
    """Check if it's a new day and reset daily counter."""
    if state is None:
        state = get_warmup_state()
    today = datetime.date.today().isoformat()
    if state["last_send_date"] != today:
        start = datetime.date.fromisoformat(state["start_date"])
        state["current_day"] = (datetime.date.today() - start).days + 1
        state["daily_sends_today"] = 0
        state["last_send_date"] = today
        save_warmup_state(state)
    return state

# ============================================================
# Brevo API Client
# ============================================================
class BrevoClient:
    """Simple Brevo API wrapper."""

    def __init__(self, api_key=None):
        self.api_key = api_key or BREVO_API_KEY
        self.base_url = BREVO_API_URL
        self.session = requests.Session()
        self.session.headers.update({
            "api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def _request(self, method, endpoint, data=None, params=None):
        """Make API request with error handling."""
        url = f"{self.base_url}{endpoint}"
        try:
            resp = self.session.request(method, url, json=data, params=params, timeout=30)
            if resp.status_code == 401:
                return {"error": "Invalid API key", "status": 401}
            if resp.status_code == 429:
                return {"error": "Rate limited - too many requests", "status": 429}
            if resp.status_code in (200, 201, 204):
                try:
                    return resp.json() if resp.text.strip() else {"status": "success"}
                except json.JSONDecodeError:
                    return {"status": "success", "raw": resp.text}
            return {"error": f"HTTP {resp.status_code}", "status": resp.status_code, "detail": resp.text[:500]}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {e}"}

    # --- Account ---
    def get_account(self):
        return self._request("GET", "/account")

    # --- Contacts ---
    def create_contact(self, email, attributes=None, list_ids=None):
        """Create or update a contact."""
        data = {
            "email": email,
            "updateEnabled": True,
            "emailBlacklisted": False,
            "smsBlacklisted": False
        }
        if attributes:
            data["attributes"] = attributes
        if list_ids:
            data["listIds"] = list_ids
        return self._request("POST", "/contacts", data=data)

    def get_contact(self, email):
        return self._request("GET", f"/contacts/{email}")

    def get_contacts(self, limit=50, offset=0):
        return self._request("GET", "/contacts", params={"limit": limit, "offset": offset})

    def delete_contact(self, email):
        return self._request("DELETE", f"/contacts/{email}")

    # --- Lists ---
    def get_lists(self):
        return self._request("GET", "/contacts/lists")

    def create_list(self, name, folder_id=None):
        data = {"name": name, "folderId": folder_id or 1}
        return self._request("POST", "/contacts/lists", data=data)

    # --- Send Email ---
    def send_transactional_email(self, to_email, to_name, subject, html_content,
                                  text_content=None, tags=None, template_id=None,
                                  params=None):
        """Send a transactional email."""
        data = {
            "sender": {
                "name": SENDER_NAME,
                "email": SENDER_EMAIL
            },
            "to": [{
                "email": to_email,
                "name": to_name or to_email.split("@")[0]
            }],
            "subject": subject,
            "replyTo": {
                "email": REPLY_TO_EMAIL,
                "name": SENDER_NAME
            }
        }

        if template_id:
            data["templateId"] = template_id
        elif html_content:
            data["htmlContent"] = html_content
        elif text_content:
            data["textContent"] = text_content
        else:
            return {"error": "Must provide html_content, text_content, or template_id"}

        if tags:
            data["tags"] = tags
        if params:
            data["params"] = params

        return self._request("POST", "/smtp/email", data=data)

    # --- Email Campaigns ---
    def create_campaign(self, name, subject, html_content, list_ids, sender_name=None,
                        sender_email=None, reply_to=None):
        """Create an email campaign (marketing email)."""
        data = {
            "name": name,
            "subject": subject,
            "sender": {
                "name": sender_name or SENDER_NAME,
                "email": sender_email or SENDER_EMAIL
            },
            "htmlContent": html_content,
            "replyTo": reply_to or REPLY_TO_EMAIL,
        }
        if list_ids:
            data["recipients"] = {"listIds": list_ids}
        return self._request("POST", "/emailCampaigns", data=data)

    def send_campaign(self, campaign_id):
        """Send a campaign immediately."""
        return self._request("POST", f"/emailCampaigns/{campaign_id}/sendNow")

    # --- Statistics ---
    def get_email_stats(self, days=7):
        """Get email statistics for the last N days."""
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=days)
        params = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat()
        }
        return self._request("GET", "/smtp/statistics/reports", params=params)

# ============================================================
# Email Templates
# ============================================================
def get_default_templates():
    """Professional email templates — designed to look like personal analyst notes, NOT marketing."""

    templates = {}

    # Template 1: Professional Market Note — reads like a personal note from an analyst
    templates["market_insights_intro"] = {
        "name": "Professional Market Note",
        "subject": "{{subject}}",
        "category": "cold_outreach",
        "html": """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0; padding:20px; background-color:#f4f5f7; font-family:Georgia,'Times New Roman',serif;">

<table width="100%" cellpadding="0" cellspacing="0" style="max-width:580px; margin:0 auto; background-color:#ffffff;">
<!-- SIMPLE HEADER — just a thin accent line, no big colored box -->
<tr><td style="background-color:#1a1a2e; height:4px; font-size:1px; line-height:1px;">&nbsp;</td></tr>

<!-- BODY — clean, text-forward, no boxes no buttons -->
<tr><td style="padding:32px 36px 20px;">
  <p style="font-family:Georgia,serif; font-size:14px; color:#888; margin:0 0 20px; letter-spacing:0.5px; text-transform:uppercase;">{{headline}}</p>

  <p style="font-family:Georgia,serif; font-size:17px; line-height:1.65; color:#1a1a1a; margin:0 0 18px;">{{hook_sentence}}</p>

  <p style="font-family:Georgia,serif; font-size:15px; line-height:1.7; color:#333; margin:0 0 18px;">{{insight_paragraph}}</p>

  <p style="font-family:Georgia,serif; font-size:15px; line-height:1.7; color:#333; margin:0 0 24px;"><strong style="color:#1a1a1a;">Why it matters:</strong> {{so_what}}</p>

  <p style="font-family:Georgia,serif; font-size:14px; line-height:1.7; color:#555; margin:0 0 28px; border-top:1px solid #eee; padding-top:16px;">{{natural_reference}}</p>

  <!-- PS: Free value hook — highest recall position -->
  <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
  <tr><td style="background-color:#f9f9f9; border-left:3px solid #1a1a2e; padding:14px 18px;">
    <p style="font-family:Georgia,serif; font-size:14px; color:#333; margin:0; line-height:1.6;"><strong style="color:#1a1a2e;">PS</strong> — {{ps_note}}</p>
  </td></tr>
  </table>

  <!-- SIGNATURE — professional, includes contact naturally -->
  <table width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid #ddd; padding-top:16px;">
  <tr>
    <td style="padding-top:12px;">
      <p style="font-family:Arial,sans-serif; font-size:14px; color:#1a1a1a; margin:0;"><strong>{{personality_name}}</strong></p>
      <p style="font-family:Arial,sans-serif; font-size:13px; color:#666; margin:2px 0 0;">{{personality_title}}, BroadFSC</p>
      <p style="font-family:Arial,sans-serif; font-size:13px; margin:6px 0 0;"><a href="mailto:msli2233bin@gmail.com" style="color:#1a1a2e; text-decoration:none;">msli2233bin@gmail.com</a></p>
      <p style="font-family:Arial,sans-serif; font-size:13px; margin:2px 0 0;"><a href="https://www.broadfsc.com/different" style="color:#1a1a2e; text-decoration:none;">broadfsc.com</a></p>
    </td>
  </tr>
  </table>
</td></tr>

<!-- FOOTER — minimal -->
<tr><td style="background-color:#f8f8f8; padding:14px 36px; text-align:center;">
  <p style="font-family:Arial,sans-serif; color:#999; font-size:11px; margin:0;">Broad Investment Securities &bull; Licensed &amp; Regulated</p>
</td></tr>
</table>

</body>
</html>"""
    }

    # Template 2: Weekly Market Note — same clean style, more data points
    templates["weekly_digest"] = {
        "name": "Weekly Market Note",
        "subject": "{{subject}}",
        "category": "newsletter",
        "html": """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0; padding:20px; background-color:#f4f5f7; font-family:Georgia,'Times New Roman',serif;">

<table width="100%" cellpadding="0" cellspacing="0" style="max-width:580px; margin:0 auto; background-color:#ffffff;">
<tr><td style="background-color:#1a1a2e; height:4px; font-size:1px; line-height:1px;">&nbsp;</td></tr>

<tr><td style="padding:32px 36px 20px;">
  <p style="font-family:Georgia,serif; font-size:14px; color:#888; margin:0 0 20px; letter-spacing:0.5px; text-transform:uppercase;">{{headline}}</p>

  <p style="font-family:Georgia,serif; font-size:17px; line-height:1.65; color:#1a1a1a; margin:0 0 18px;">{{hook_sentence}}</p>

  <p style="font-family:Georgia,serif; font-size:15px; line-height:1.7; color:#333; margin:0 0 18px;">{{insight_paragraph}}</p>

  <p style="font-family:Georgia,serif; font-size:15px; line-height:1.7; color:#333; margin:0 0 24px;"><strong style="color:#1a1a1a;">Why it matters:</strong> {{so_what}}</p>

  <p style="font-family:Georgia,serif; font-size:14px; line-height:1.7; color:#555; margin:0 0 28px; border-top:1px solid #eee; padding-top:16px;">{{natural_reference}}</p>

  <!-- PS: Free value hook — highest recall position -->
  <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
  <tr><td style="background-color:#f9f9f9; border-left:3px solid #1a1a2e; padding:14px 18px;">
    <p style="font-family:Georgia,serif; font-size:14px; color:#333; margin:0; line-height:1.6;"><strong style="color:#1a1a2e;">PS</strong> — {{ps_note}}</p>
  </td></tr>
  </table>

  <!-- SIGNATURE -->
  <table width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid #ddd; padding-top:16px;">
  <tr>
    <td style="padding-top:12px;">
      <p style="font-family:Arial,sans-serif; font-size:14px; color:#1a1a1a; margin:0;"><strong>{{personality_name}}</strong></p>
      <p style="font-family:Arial,sans-serif; font-size:13px; color:#666; margin:2px 0 0;">{{personality_title}}, BroadFSC</p>
      <p style="font-family:Arial,sans-serif; font-size:13px; margin:6px 0 0;"><a href="mailto:msli2233bin@gmail.com" style="color:#1a1a2e; text-decoration:none;">msli2233bin@gmail.com</a></p>
      <p style="font-family:Arial,sans-serif; font-size:13px; margin:2px 0 0;"><a href="https://www.broadfsc.com/different" style="color:#1a1a2e; text-decoration:none;">broadfsc.com</a></p>
    </td>
  </tr>
  </table>
</td></tr>

<tr><td style="background-color:#f8f8f8; padding:14px 36px; text-align:center;">
  <p style="font-family:Arial,sans-serif; color:#999; font-size:11px; margin:0;">Broad Investment Securities &bull; Licensed &amp; Regulated</p>
</td></tr>
</table>

</body>
</html>"""
    }

    # Template 3: Re-engagement — short, personal, no pressure
    templates["re_engage"] = {
        "name": "Quick Check-in",
        "subject": "{{subject}}",
        "category": "re_engagement",
        "html": """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0; padding:20px; background-color:#f4f5f7; font-family:Georgia,'Times New Roman',serif;">

<table width="100%" cellpadding="0" cellspacing="0" style="max-width:580px; margin:0 auto; background-color:#ffffff;">
<tr><td style="background-color:#1a1a2e; height:4px; font-size:1px; line-height:1px;">&nbsp;</td></tr>

<tr><td style="padding:32px 36px 20px;">
  <p style="font-family:Georgia,serif; font-size:14px; color:#888; margin:0 0 20px; letter-spacing:0.5px; text-transform:uppercase;">Quick note</p>

  <p style="font-family:Georgia,serif; font-size:17px; line-height:1.65; color:#1a1a1a; margin:0 0 18px;">{{hook_sentence}}</p>

  <p style="font-family:Georgia,serif; font-size:15px; line-height:1.7; color:#333; margin:0 0 18px;">{{insight_paragraph}}</p>

  <p style="font-family:Georgia,serif; font-size:15px; line-height:1.7; color:#333; margin:0 0 24px;"><strong style="color:#1a1a1a;">Why it matters:</strong> {{so_what}}</p>

  <p style="font-family:Georgia,serif; font-size:14px; line-height:1.7; color:#555; margin:0 0 28px; border-top:1px solid #eee; padding-top:16px;">{{natural_reference}}</p>

  <!-- PS: Free value hook -- highest recall position -->
  <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
  <tr><td style="background-color:#f9f9f9; border-left:3px solid #1a1a2e; padding:14px 18px;">
    <p style="font-family:Georgia,serif; font-size:14px; color:#333; margin:0; line-height:1.6;"><strong style="color:#1a1a2e;">PS</strong> — {{ps_note}}</p>
  </td></tr>
  </table>

  <!-- SIGNATURE -->
  <table width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid #ddd; padding-top:16px;">
  <tr>
    <td style="padding-top:12px;">
      <p style="font-family:Arial,sans-serif; font-size:14px; color:#1a1a1a; margin:0;"><strong>{{personality_name}}</strong></p>
      <p style="font-family:Arial,sans-serif; font-size:13px; color:#666; margin:2px 0 0;">{{personality_title}}, BroadFSC</p>
      <p style="font-family:Arial,sans-serif; font-size:13px; margin:6px 0 0;"><a href="mailto:msli2233bin@gmail.com" style="color:#1a1a2e; text-decoration:none;">msli2233bin@gmail.com</a></p>
      <p style="font-family:Arial,sans-serif; font-size:13px; margin:2px 0 0;"><a href="https://www.broadfsc.com/different" style="color:#1a1a2e; text-decoration:none;">broadfsc.com</a></p>
    </td>
  </tr>
  </table>
</td></tr>

<tr><td style="background-color:#f8f8f8; padding:14px 36px; text-align:center;">
  <p style="font-family:Arial,sans-serif; color:#999; font-size:11px; margin:0;">Broad Investment Securities &bull; Licensed &amp; Regulated</p>
</td></tr>
</table>

</body>
</html>"""
    }

    return templates

def save_default_templates():
    """Save default templates to disk (always overwrite to keep in sync)."""
    templates = get_default_templates()
    for key, tmpl in templates.items():
        filepath = TEMPLATES_DIR / f"{key}.json"
        filepath.write_text(json.dumps(tmpl, indent=2, ensure_ascii=False), encoding='utf-8')
    return templates

# ============================================================
# Contact Management
# ============================================================
def load_contacts():
    """Load contacts from local JSON file."""
    if CONTACTS_FILE.exists():
        return json.loads(CONTACTS_FILE.read_text(encoding='utf-8'))
    return []

def save_contacts(contacts):
    """Save contacts to local JSON file."""
    CONTACTS_FILE.write_text(json.dumps(contacts, indent=2, ensure_ascii=False), encoding='utf-8')

def add_contact(email, name="", source="manual", tags=None, attributes=None):
    """Add a contact locally and to Brevo."""
    contacts = load_contacts()

    # Check for duplicate
    for c in contacts:
        if c["email"].lower() == email.lower():
            print(f"Contact already exists: {email}")
            return False

    contact = {
        "email": email.lower().strip(),
        "name": name or email.split("@")[0],
        "first_name": (name or email.split("@")[0]).split()[0] if name else email.split("@")[0],
        "source": source,
        "tags": tags or [],
        "attributes": attributes or {},
        "added_date": datetime.date.today().isoformat(),
        "status": "active",
        "emails_sent": 0,
        "last_email_date": None,
        "opens": 0,
        "clicks": 0,
        "bounced": False
    }

    contacts.append(contact)
    save_contacts(contacts)

    # Also add to Brevo
    if BREVO_API_KEY:
        client = BrevoClient()
        brevo_attrs = {
            "FNAME": contact["first_name"],
            "LNAME": " ".join(name.split()[1:]) if name and len(name.split()) > 1 else ""
        }
        if attributes:
            brevo_attrs.update(attributes)
        result = client.create_contact(email, attributes=brevo_attrs)
        if "error" in result:
            print(f"Brevo contact creation: {result.get('error', result)}")
        else:
            print(f"Contact added to Brevo: {email}")

    print(f"Contact added: {email} ({name})")
    return True

def import_contacts_from_csv(csv_path, source="csv_import"):
    """Import contacts from CSV file. Expected columns: email, name, tags"""
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return 0

    added = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get("email", "").strip()
            name = row.get("name", "").strip()
            tags = [t.strip() for t in row.get("tags", "").split(",") if t.strip()]

            if not email or "@" not in email:
                continue

            if add_contact(email, name=name, source=source, tags=tags):
                added += 1
            time.sleep(0.5)  # Rate limit

    print(f"Imported {added} contacts from {csv_path}")
    return added

# ============================================================
# Send Log & Anti-Spam
# ============================================================
def load_send_log():
    """Load send log."""
    if SEND_LOG_FILE.exists():
        return json.loads(SEND_LOG_FILE.read_text(encoding='utf-8'))
    return []

def save_send_log(log):
    """Save send log."""
    # Keep only last 10000 entries
    if len(log) > 10000:
        log = log[-10000:]
    SEND_LOG_FILE.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding='utf-8')

def load_bounces():
    """Load bounce list."""
    if BOUNCE_FILE.exists():
        return json.loads(BOUNCE_FILE.read_text(encoding='utf-8'))
    return []

def add_bounce(email, reason="unknown"):
    """Add email to bounce list."""
    bounces = load_bounces()
    bounces.append({
        "email": email,
        "reason": reason,
        "date": datetime.date.today().isoformat()
    })
    BOUNCE_FILE.write_text(json.dumps(bounces, indent=2, ensure_ascii=False), encoding='utf-8')

    # Mark contact as bounced
    contacts = load_contacts()
    for c in contacts:
        if c["email"].lower() == email.lower():
            c["bounced"] = True
            c["status"] = "bounced"
    save_contacts(contacts)

def is_bounced(email):
    """Check if email has previously bounced."""
    bounces = load_bounces()
    return any(b["email"].lower() == email.lower() for b in bounces)

def can_send_to(email, min_gap_days=3):
    """Check if we can send to this email (anti-spam)."""
    if is_bounced(email):
        return False, "Previously bounced"

    log = load_send_log()
    recent_sends = [e for e in log
                    if e["to"].lower() == email.lower()
                    and e.get("date")]

    if recent_sends:
        last_send = max(recent_sends, key=lambda x: x.get("date", ""))
        last_date = datetime.date.fromisoformat(last_send["date"])
        days_since = (datetime.date.today() - last_date).days
        if days_since < min_gap_days:
            return False, f"Last sent {days_since} days ago (min gap: {min_gap_days})"

    # Check contact status
    contacts = load_contacts()
    for c in contacts:
        if c["email"].lower() == email.lower():
            if c.get("status") == "unsubscribed":
                return False, "Unsubscribed"
            if c.get("emails_sent", 0) >= 10 and c.get("opens", 0) == 0:
                return False, "Zero opens after 10 sends — cold lead"
            break

    return True, "OK"

# ============================================================
# AI Content Generation (via Groq)
# ============================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def generate_email_content(personality_key, contact, market_data=None):
    """Generate professional insight email content using Groq AI.

    Design philosophy: This should read like a professional investor sharing
    a genuine market observation with a colleague — NOT a marketing email.
    The reader should think "this person knows what they're talking about"
    before they ever see a company name.
    """
    pers_key, pers = get_personality_for_date()

    prompt = f"""You are {pers['name']}, a real person who happens to work at BroadFSC.
Your writing style: {pers['tone']}
Your expertise: {pers['focus']}

You're writing a brief personal note to a fellow investor you haven't met yet.
This is NOT a marketing email. This is NOT a sales pitch. This is a professional
sharing a genuine, timely market observation.

REAL-TIME MARKET DATA (as of today — USE THESE EXACT NUMBERS, do NOT fabricate any price or index level):
{market_data if market_data else "Market data unavailable — write a general market observation without specific numbers."}

CRITICAL RULES:
1. ONLY use the market data provided above. Do NOT make up, guess, or fabricate any index levels, stock prices, or percentages.
2. If market data shows S&P 500 at 7000+, do NOT write about 5000-level support. Use the ACTUAL numbers provided.

CONTENT RULES (these make or break whether the email gets read):
3. Start with a SURPRISING or COUNTER-INTUITIVE observation about the market data — something that would make an experienced investor stop scrolling.
4. Write like you're talking to one smart person, not an audience. No "Dear Investor", no "I wanted to reach out".
5. Be SPECIFIC with numbers and levels. Vague = spam. "S&P 500 just tested 7,174 resistance for the 3rd time" > "Markets are volatile".
6. Share one genuine CONTRARIAN or NON-OBVIOUS insight that most retail investors would miss. This is the hook.
7. NO marketing language: no "opportunity", "unlock", "leverage", "empower", "comprehensive", "cutting-edge", "world-class".
8. NO call-to-action phrases: no "sign up", "subscribe", "learn more", "discover", "get started", "don't miss out".
9. Mention BroadFSC ONLY in the "natural_reference" and "ps_note" fields — nowhere else in the email body.
10. The website link (broadfsc.com/different) should appear naturally in "natural_reference", not as a button or promotion.
11. Your email contact (msli2233bin@gmail.com) goes in the signature, like a normal person's email footer.
12. Keep it SHORT: 120-200 words total. Busy people delete long emails from strangers.
13. Subject line: specific + curiosity gap, under 50 chars, no emoji. Like a Bloomberg headline, not a newsletter.
14. PS NOTE (critical for conversion): End with a PS that offers genuine FREE value — a specific stock research report, a trade idea, or a market brief. This is the #1 thing recipients remember. Make it sound like an afterthought, not a sales pitch. Examples:
    - "PS — If you're looking at energy names, we just finished a 12-page deep-dive on XLE's top 3 holdings. No cost, just reply."
    - "PS — Attached is the trade plan we're running for clients this week (entry, stop, target). Happy to share."
    - "PS — Our recent report on why small-caps are setting up (with specific ticker list) is here: broadfsc.com/different — no paywall."

BAD subject examples (too marketing): "Your Market Edge Awaits", "Weekly Insights Inside", "Don't Miss This Opportunity"
GOOD subject examples: "S&P testing 7,174 for 3rd time", "Why the VIX says otherwise", "Gold broke something important"

Return as JSON:
{{
  "subject": "...",
  "hook_sentence": "The surprising opening line that makes them keep reading",
  "insight_paragraph": "Your specific, data-backed contrarian observation (the meat of the email)",
  "so_what": "One sentence on why this matters for their portfolio",
  "natural_reference": "One sentence naturally mentioning BroadFSC, like you'd mention your firm in a real email",
  "ps_note": "The PS line that offers genuine free value (research report, trade idea, or brief). Make it specific and low-pressure.",
  "headline": "Short label for the email header (3-5 words, like 'Market Note' or 'Quick Take')"
}}"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 800
    }

    try:
        resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            # Strip code fences if present
            content = re.sub(r'^```(?:json)?\s*', '', content.strip())
            content = re.sub(r'\s*```$', '', content.strip())

            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Try regex extraction
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        pass

                # Fallback: construct from raw text
                return {
                    "subject": f"Quick market note",
                    "hook_sentence": content[:200],
                    "insight_paragraph": content[200:500] if len(content) > 200 else "",
                    "so_what": "Worth watching closely this week.",
                    "natural_reference": "I shared more context on broadfsc.com/different if you're curious.",
                    "headline": "Market Note"
                }
        else:
            print(f"Groq API error: {resp.status_code}")
            return None
    except Exception as e:
        print(f"AI generation failed: {e}")
        return None

def get_market_snapshot():
    """Get quick market data for email personalization.
    Uses actual index tickers (not ETFs) so AI gets real index levels.
    Includes explicit price levels in the output to prevent AI from fabricating numbers.
    """
    try:
        import yfinance as yf
        # Use actual indices, not ETFs — AI needs real index levels
        tickers = {
            "^GSPC": "S&P 500",
            "^DJI": "Dow Jones",
            "^IXIC": "Nasdaq Composite",
            "GC=F": "Gold",
            "CL=F": "Crude Oil",
            "DX-Y.NYB": "US Dollar Index",
            "BTC-USD": "Bitcoin"
        }
        snapshot = []
        for ticker, name in tickers.items():
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period="5d")
                if len(hist) >= 2:
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2]
                    close = latest["Close"]
                    change_pct = ((close - prev["Close"]) / prev["Close"]) * 100
                    week_ago = hist.iloc[0]["Close"]
                    week_chg = ((close - week_ago) / week_ago) * 100
                    direction = "▲" if change_pct > 0 else "▼"
                    snapshot.append(
                        f"{name}: {close:,.2f} ({direction} {abs(change_pct):.2f}% today, "
                        f"week: {week_chg:+.2f}%)"
                    )
                elif len(hist) == 1:
                    close = hist.iloc[-1]["Close"]
                    snapshot.append(f"{name}: {close:,.2f}")
            except Exception:
                continue
        return "; ".join(snapshot) if snapshot else "Market data unavailable"
    except Exception:
        return "Market data unavailable"

# ============================================================
# Email Sending Engine
# ============================================================
def send_email_batch(max_sends=None, dry_run=False):
    """Send a batch of emails based on warm-up schedule."""
    if not BREVO_API_KEY:
        print("ERROR: BREVO_API_KEY not set. Get it from https://app.brevo.com/settings/keys/api")
        return 0

    # Check warm-up state
    state = advance_warmup_day()
    daily_limit, day_num, desc = get_daily_limit(state)
    remaining = daily_limit - state["daily_sends_today"]

    if max_sends:
        remaining = min(remaining, max_sends)

    if remaining <= 0:
        print(f"Daily limit reached: {state['daily_sends_today']}/{daily_limit} ({desc})")
        return 0

    print(f"Day {day_num} of warm-up | Daily limit: {daily_limit} | Remaining: {remaining} | {desc}")

    # Get personality for today
    pers_key, pers = get_personality_for_date()
    print(f"Today's personality: {pers['emoji']} {pers['name']} ({pers['title']})")

    # Load contacts and filter
    contacts = load_contacts()
    eligible = []
    for c in contacts:
        if c.get("bounced") or c.get("status") in ("unsubscribed", "bounced"):
            continue
        can_send, reason = can_send_to(c["email"])
        if can_send:
            eligible.append(c)
        else:
            print(f"  Skipping {c['email']}: {reason}")

    if not eligible:
        print("No eligible contacts to send to.")
        return 0

    # Prioritize: new contacts first, then by engagement
    eligible.sort(key=lambda c: (c.get("opens", 0), c.get("emails_sent", 0)))

    # Limit batch size
    to_send = eligible[:remaining]
    print(f"Sending to {len(to_send)} contacts...")

    # Get market data
    market_data = get_market_snapshot()

    # Initialize Brevo client
    client = BrevoClient()

    # Load template
    templates = save_default_templates()
    template = templates.get("market_insights_intro", {})

    sent_count = 0
    errors = 0
    log = load_send_log()

    for contact in to_send:
        if dry_run:
            print(f"  [DRY RUN] Would send to: {contact['email']} ({contact.get('name', '')})")
            sent_count += 1
            continue

        # Generate AI content
        ai_content = generate_email_content(pers_key, contact, market_data)

        if not ai_content:
            print(f"  Skipping {contact['email']}: AI content generation failed")
            errors += 1
            continue

        # Build HTML from template — new professional style
        html = template.get("html", "")
        html = html.replace("{{headline}}", ai_content.get("headline", "Market Note"))
        html = html.replace("{{hook_sentence}}", ai_content.get("hook_sentence", ""))
        html = html.replace("{{insight_paragraph}}", ai_content.get("insight_paragraph", ""))
        html = html.replace("{{so_what}}", ai_content.get("so_what", ""))
        html = html.replace("{{natural_reference}}", ai_content.get("natural_reference", ""))
        html = html.replace("{{ps_note}}", ai_content.get("ps_note", ""))
        html = html.replace("{{personality_name}}", pers["name"])
        html = html.replace("{{personality_title}}", pers["title"])

        subject = ai_content.get("subject", "Quick market note")

        # Send email
        result = client.send_transactional_email(
            to_email=contact["email"],
            to_name=contact.get("name", contact["email"].split("@")[0]),
            subject=subject,
            html_content=html,
            tags=[pers_key, "cold_outreach", f"day{day_num}"]
        )

        if "error" in result:
            print(f"  ERROR sending to {contact['email']}: {result['error']}")
            errors += 1

            # Check for bounce indicators
            if "bounce" in str(result).lower() or "invalid" in str(result).lower():
                add_bounce(contact["email"], str(result))
        else:
            sent_count += 1
            message_id = result.get("messageId", "")
            print(f"  Sent to {contact['email']} | ID: {message_id}")

            # Log the send
            log.append({
                "to": contact["email"],
                "subject": subject,
                "personality": pers_key,
                "date": datetime.date.today().isoformat(),
                "time": datetime.datetime.now().isoformat(),
                "message_id": message_id,
                "status": "sent"
            })

            # Update contact stats
            contact["emails_sent"] = contact.get("emails_sent", 0) + 1
            contact["last_email_date"] = datetime.date.today().isoformat()

        # Rate limiting: wait between sends
        delay = random.uniform(3, 8)  # 3-8 seconds between emails
        time.sleep(delay)

    # Save updated state
    save_send_log(log)
    save_contacts(contacts)

    state["daily_sends_today"] += sent_count
    state["total_sends"] += sent_count
    save_warmup_state(state)

    # Analytics
    if HAS_ANALYTICS and sent_count > 0:
        log_post("email_brevo", f"sent_{sent_count}", content_preview=f"{pers_key} day{day_num} sent:{sent_count} err:{errors}")

    print(f"\n{'='*50}")
    print(f"Batch complete: {sent_count} sent, {errors} errors")
    print(f"Daily progress: {state['daily_sends_today']}/{daily_limit}")
    print(f"Warm-up day: {day_num} | {desc}")

    return sent_count

def send_test_email(test_email=None):
    """Send a test email to verify Brevo setup."""
    if not BREVO_API_KEY:
        print("ERROR: BREVO_API_KEY not set!")
        print("Get it from: https://app.brevo.com/settings/keys/api")
        return False

    if not test_email:
        test_email = REPLY_TO_EMAIL

    client = BrevoClient()
    pers_key, pers = get_personality_for_date()

    result = client.send_transactional_email(
        to_email=test_email,
        to_name="Test Recipient",
        subject=f"🧪 BroadFSC Email Test — {pers['name']}",
        html_content=f"""<html><body style="font-family: Arial; padding: 20px;">
<h2>Email System Test</h2>
<p>This is a test email from the BroadFSC Email Campaign System.</p>
<p>Today's personality: {pers['emoji']} {pers['name']} ({pers['title']})</p>
<p>Timestamp: {datetime.datetime.now().isoformat()}</p>
<p>Sender: {SENDER_EMAIL}</p>
<hr>
<p style="color: #999; font-size: 12px;">Broad Investment Securities | Test Email</p>
</body></html>""",
        tags=["test"]
    )

    if "error" in result:
        print(f"Test email FAILED: {result['error']}")
        return False
    else:
        print(f"Test email sent to {test_email}! Message ID: {result.get('messageId', 'N/A')}")
        return True

# ============================================================
# CLI Interface
# ============================================================
def show_warmup_schedule():
    """Display the 30-day warm-up schedule."""
    state = get_warmup_state()
    start_date = datetime.date.fromisoformat(state["start_date"])
    today = datetime.date.today()
    current_day = (today - start_date).days + 1

    print("=" * 60)
    print("📧 BroadFSC Email Warm-Up Schedule")
    print("=" * 60)
    print(f"Start date: {state['start_date']}")
    print(f"Today: Day {current_day}")
    print(f"Total sends so far: {state.get('total_sends', 0)}")
    print("-" * 60)

    for (start_day, end_day), limit, desc in WARMUP_SCHEDULE:
        marker = " ◄ CURRENT" if start_day <= current_day <= end_day else ""
        status = "✅" if current_day > end_day else ("🔄" if start_day <= current_day <= end_day else "⏳")
        print(f"  {status} Day {start_day:3d}-{end_day:3d}: {limit:3d} emails/day | {desc}{marker}")

    daily_limit, day_num, desc = get_daily_limit(state)
    print("-" * 60)
    print(f"  Today's limit: {daily_limit} emails | Already sent: {state.get('daily_sends_today', 0)}")
    print("=" * 60)

def show_stats():
    """Show email campaign statistics."""
    state = get_warmup_state()
    contacts = load_contacts()
    log = load_send_log()
    bounces = load_bounces()

    print("=" * 60)
    print("📊 BroadFSC Email Campaign Statistics")
    print("=" * 60)

    # Contacts
    active = [c for c in contacts if c.get("status") == "active"]
    print(f"\n👥 Contacts: {len(contacts)} total | {len(active)} active | {len(bounces)} bounced")

    # Sends
    today_sends = [e for e in log if e.get("date") == datetime.date.today().isoformat()]
    print(f"\n📧 Sends today: {len(today_sends)}")
    print(f"   Total sends: {state.get('total_sends', 0)}")
    print(f"   Total bounces: {state.get('total_bounces', 0)}")

    # Personality breakdown
    pers_counts = {}
    for e in log:
        p = e.get("personality", "unknown")
        pers_counts[p] = pers_counts.get(p, 0) + 1

    print(f"\n🎭 By Personality:")
    for p, count in sorted(pers_counts.items(), key=lambda x: -x[1]):
        pers = PERSONALITIES.get(p, {})
        print(f"   {pers.get('emoji', '?')} {pers.get('name', p)}: {count}")

    # Warm-up status
    daily_limit, day_num, desc = get_daily_limit(state)
    print(f"\n📈 Warm-up: Day {day_num} | {daily_limit}/day | {desc}")

    # Brevo account
    if BREVO_API_KEY:
        client = BrevoClient()
        account = client.get_account()
        if "error" not in account:
            print(f"\n🏢 Brevo Account: {account.get('email', 'N/A')}")
            print(f"   Plan: {account.get('plan', 'N/A')}")

    print("=" * 60)

def list_templates():
    """List available email templates."""
    templates = save_default_templates()
    print("=" * 60)
    print("📝 Available Email Templates")
    print("=" * 60)
    for key, tmpl in templates.items():
        print(f"\n  📄 {key}")
        print(f"     Name: {tmpl['name']}")
        print(f"     Category: {tmpl.get('category', 'N/A')}")
        print(f"     Subject: {tmpl.get('subject', 'N/A')}")

def main():
    parser = argparse.ArgumentParser(description="BroadFSC Email Campaign System")
    parser.add_argument("--send", action="store_true", help="Send today's email batch")
    parser.add_argument("--test", nargs="?", const=True, default=False,
                        help="Send test email (optionally specify recipient)")
    parser.add_argument("--warmup", action="store_true", help="Show warm-up schedule")
    parser.add_argument("--stats", action="store_true", help="Show send statistics")
    parser.add_argument("--templates", action="store_true", help="List email templates")
    parser.add_argument("--add-contact", nargs=2, metavar=("EMAIL", "NAME"),
                        help="Add a contact")
    parser.add_argument("--import-csv", metavar="CSV_PATH",
                        help="Import contacts from CSV")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulate sending without actually sending")
    parser.add_argument("--max", type=int, help="Maximum emails to send")
    parser.add_argument("--init", action="store_true",
                        help="Initialize: save templates + create directories")

    args = parser.parse_args()

    if args.init:
        save_default_templates()
        state = get_warmup_state()
        save_warmup_state(state)
        print("✅ Email campaign system initialized!")
        print(f"   Data dir: {DATA_DIR}")
        print(f"   Templates: {len(list(TEMPLATES_DIR.glob('*.json')))} saved")
        return

    if args.warmup:
        show_warmup_schedule()
        return

    if args.stats:
        show_stats()
        return

    if args.templates:
        list_templates()
        return

    if args.add_contact:
        email, name = args.add_contact
        add_contact(email, name=name)
        return

    if args.import_csv:
        import_contacts_from_csv(args.import_csv)
        return

    if args.test is not False:
        test_email = args.test if isinstance(args.test, str) else None
        send_test_email(test_email)
        return

    if args.send:
        send_email_batch(max_sends=args.max, dry_run=args.dry_run)
        return

    # Default: show help
    parser.print_help()

if __name__ == "__main__":
    main()
