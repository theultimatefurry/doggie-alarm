import json, os, smtplib, time, urllib.request, xml.etree.ElementTree as ET
from email.message import EmailMessage

HANDLE = "doggiedasher"
API_KEY = os.environ["YT_API_KEY"]
GMAIL = os.environ["GMAIL_ADDRESS"]
GMAIL_PASS = os.environ["GMAIL_APP_PASSWORD"]
SEND_TO = os.environ["ICLOUD_ADDRESS"]
STATE_FILE = "last_alert.txt"


def fetch(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                return r.read()
        except Exception as e:
            print(f"Connection problem (try {attempt + 1}/3): {e}")
            time.sleep(5)
    print("YouTube couldn't be reached. Will try again next check.")
    raise SystemExit(0)


# 1. Find the channel ID from the @handle
ch = json.loads(fetch(f"https://www.googleapis.com/youtube/v3/channels?part=id&forHandle={HANDLE}&key={API_KEY}"))
channel_id = ch["items"][0]["id"]

# 2. Get recent video IDs from the channel's RSS feed
feed = ET.fromstring(fetch(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"))
ns = {"yt": "http://www.youtube.com/xml/schemas/2015"}
ids = [e.text for e in feed.findall(".//yt:videoId", ns)][:15]

# 3. Check which of them (if any) is live right now
vids = json.loads(fetch(f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={','.join(ids)}&key={API_KEY}"))
live = [v for v in vids["items"] if v["snippet"]["liveBroadcastContent"] == "live"]

if not live:
    print("Doggie is not live.")
    raise SystemExit

video_id = live[0]["id"]
title = live[0]["snippet"]["title"]

# 4. Don't alarm twice for the same stream
last = open(STATE_FILE).read().strip() if os.path.exists(STATE_FILE) else ""
if last == video_id:
    print("Already alerted for this stream.")
    raise SystemExit

# 5. Send the trigger email
msg = EmailMessage()
msg["Subject"] = "DOGGIE LIVE"
msg["From"] = GMAIL
msg["To"] = SEND_TO
msg.set_content(f"{title}\nhttps://youtube.com/watch?v={video_id}")
with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
    s.login(GMAIL, GMAIL_PASS)
    s.send_message(msg)

open(STATE_FILE, "w").write(video_id)
print("Alert sent!")
