"""Enable or fix GitHub Pages for broadfsc-automation repo."""
import subprocess, json, urllib.request, sys

# Get token from git credential
result = subprocess.run(
    ['C:/Program Files/Git/bin/git.exe', 'credential', 'fill'],
    input='protocol=https\nhost=github.com\n\n',
    capture_output=True, text=True, timeout=15
)
token = ''
for line in result.stdout.strip().split('\n'):
    if line.startswith('password='):
        token = line.split('=', 1)[1]
        break

if not token:
    print("NO_TOKEN - cannot proceed")
    sys.exit(1)

print(f"Got token: {token[:8]}...")

headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github+json',
    'Content-Type': 'application/json'
}

# Check current pages config
try:
    req = urllib.request.Request(
        'https://api.github.com/repos/msli2233bin/broadfsc-automation/pages',
        headers=headers
    )
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    source = data.get('source', {})
    print(f"Current Pages: branch={source.get('branch','?')}, path={source.get('path','/')}")
    print(f"URL: {data.get('html_url','?')}")
    print(f"Status: {data.get('status','?')}")
    
    # If not serving from root, update it
    if source.get('path', '/') != '/' or source.get('branch', '') != 'main':
        print("Updating Pages to serve from root of main...")
        req2 = urllib.request.Request(
            'https://api.github.com/repos/msli2233bin/broadfsc-automation/pages',
            data=json.dumps({'source': {'branch': 'main', 'path': '/'}}).encode(),
            headers=headers,
            method='PUT'
        )
        resp2 = urllib.request.urlopen(req2)
        print("Updated!")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP {e.code}: {body[:200]}")
    if e.code == 404:
        print("Pages not enabled. Creating...")
        req3 = urllib.request.Request(
            'https://api.github.com/repos/msli2233bin/broadfsc-automation/pages',
            data=json.dumps({'source': {'branch': 'main', 'path': '/'}}).encode(),
            headers=headers,
            method='POST'
        )
        try:
            resp3 = urllib.request.urlopen(req3)
            print("Pages ENABLED with root directory on main branch!")
        except urllib.error.HTTPError as e3:
            print(f"Enable failed: {e3.code} - {e3.read().decode()[:200]}")
except Exception as e:
    print(f"Error: {e}")
