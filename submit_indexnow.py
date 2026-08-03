# -*- coding: utf-8 -*-
"""Submit all SEO site URLs to Bing IndexNow for fast indexing."""
import re, json, urllib.request, urllib.error

SITEMAP = r"c:\Users\Administrator\Documents\WorkBuddyProjects\20260414140743\broadfsc-automation\docs\peptide-seo\sitemap.xml"
KEY = "a8f5f167f44f4964e6c998dee827110c"
HOST = "msli2233bin.github.io"
KEY_LOC = f"https://{HOST}/broadfsc-automation/peptide-seo/{KEY}.txt"

xml = open(SITEMAP, encoding="utf-8").read()
urls = re.findall(r"<loc>(.*?)</loc>", xml)
print(f"found {len(urls)} urls")

payload = json.dumps({
    "host": HOST,
    "key": KEY,
    "keyLocation": KEY_LOC,
    "urlList": urls,
}).encode()
req = urllib.request.Request(
    "https://api.indexnow.org/indexnow",
    data=payload,
    headers={"Content-Type": "application/json", "User-Agent": "RTPeptideBot/1.0"},
    method="POST",
)
try:
    r = urllib.request.urlopen(req, timeout=30)
    print("IndexNow status", r.status, r.read().decode()[:200])
except urllib.error.HTTPError as e:
    print("IndexNow HTTP", e.code, e.fp.read().decode()[:300] if e.fp else "")
