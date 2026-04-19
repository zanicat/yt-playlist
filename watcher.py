import os
import sys
import xml.etree.ElementTree as ET
import urllib.request
import json

CHANNEL_ID   = "UCkERe-GrNHU_DkHZ2PmiqgQ"   # test
KEYWORD      = "california"     # placeholder
PLAYLIST_ID  = "PL4mkSuVGr_mvBkA74oL-S4pobBiTV-Etx"  # test
SEEN_FILE    = "seen_videos.txt"
RSS_URL      = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"

API_KEY           = os.environ["YOUTUBE_API_KEY"]
CLIENT_ID         = os.environ["YOUTUBE_CLIENT_ID"]
CLIENT_SECRET     = os.environ["YOUTUBE_CLIENT_SECRET"]
REFRESH_TOKEN     = os.environ["YOUTUBE_REFRESH_TOKEN"]


def get_access_token():
    data = json.dumps({
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["access_token"]


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE) as f:
        return set(line.strip() for line in f if line.strip())


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        f.write("\n".join(sorted(seen)))


def fetch_feed():
    with urllib.request.urlopen(RSS_URL) as r:
        return r.read()


def add_to_playlist(video_id, access_token):
    data = json.dumps({
        "snippet": {
            "playlistId": PLAYLIST_ID,
            "resourceId": {"kind": "youtube#video", "videoId": video_id}
        }
    }).encode()
    req = urllib.request.Request(
        f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet",
        data=data,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read())
    print(f"  Added: {result['snippet']['title']}")


def main():
    seen = load_seen()
    feed_xml = fetch_feed()
    ns = {"yt": "http://www.youtube.com/xml/schemas/2015",
          "atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(feed_xml)
    entries = root.findall("atom:entry", ns)

    matched = []
    for entry in entries:
        video_id = entry.find("yt:videoId", ns).text
        title    = entry.find("atom:title", ns).text
        if video_id in seen:
            continue
        seen.add(video_id)
        if KEYWORD.lower() in title.lower():
            print(f"Match: '{title}' ({video_id})")
            matched.append(video_id)
        else:
            print(f"Skip:  '{title}'")

    if matched:
        token = get_access_token()
        for vid in matched:
            add_to_playlist(vid, token)

    save_seen(seen)
    print(f"Done. {len(matched)} video(s) added.")


if __name__ == "__main__":
    main()
