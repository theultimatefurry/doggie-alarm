import json, os, smtplib, urllib.request, xml.etree.ElementTree as ET
from email.message import EmailMessage

HANDLE = "LofiGirl"
API_KEY = os.environ["YT_API_KEY"]
GMAIL = os.environ["GMAIL_ADDRESS"]
GMAIL_PASS = os.environ["GMAIL_APP_PASSWORD"]
SEND_TO = os.environ["ICLOUD_ADDRESS"]
STATE_FILE = "last_alert.txt"


def get_json(url):
    with urllib.request.urlopen(url) as r:
        return json.load(r)


# 1. Find the channel ID from the @handle
ch = get_json(f"https://www.googleapis.com/youtube/v3/channels?part=id&forHandle={HANDLE}&key={API_KEY}")
channel_id = ch["items"][0]["id"]

# 2. Get recent video IDs from the channel's free RSS feed
with urllib.request.urlopen(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}") as r:
    feed = ET.fromstring(r.read())
ns = {"yt": "http://www.youtube.com/xml/schemas/2015"}
ids = [e.text for e in feed.findall(".//yt:videoId", ns)][:15]

# 3. Ask YouTube which of them (if any) is live right now
vids = get_json(f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={','.join(ids)}&key={API_KEY}")
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
