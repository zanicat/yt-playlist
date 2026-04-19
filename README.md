# YouTube Channel Watcher

Automatically saves videos to a YouTube playlist when a channel uploads a video whose title contains a keyword. Runs on a schedule using GitHub Actions — no servers, no cost.

## How it works

1. GitHub Actions runs once daily at noon UTC (configurable)
2. The script fetches the channel's public RSS feed — no API key needed for this step
3. Each new video title is checked against your keyword
4. If it matches, the YouTube Data API adds it to your playlist
5. Processed video IDs are committed back to the repo so nothing is added twice

---

## Prerequisites

- A GitHub account with a repository for this automation
- A Google account that owns the target playlist
- Python 3 (only needed locally for the one-time OAuth setup step)

> **Using WSL (Windows Subsystem for Linux)?** The OAuth token setup requires a couple of extra steps since WSL can't open a browser automatically. Follow the WSL-specific instructions in step 5.

---

## Setup

### 1. Copy the files into your repo

Create this structure:

```
your-repo/
├── .github/
│   └── workflows/
│       └── youtube-watcher.yml
├── watcher.py
└── seen_videos.txt        ← create this as an empty file
```

Paste the contents of `watcher.py` and `youtube-watcher.yml` from the project source.

---

### 2. Find your channel ID, keyword, and playlist ID

**Channel ID**

The channel ID looks like `UCxxxxxxxxxxxxxxxxxxxxxx`. Find it at:

- The channel's URL if it uses the old format: `youtube.com/channel/UCxxxxxx`
- Or via the channel's About page → Share → Copy channel ID

If the channel uses a custom handle (e.g. `youtube.com/@channelname`), open the page source and search for `"channelId"` — it appears near the top. If CTRL+F looks funky on browser like it did for me, CTRL+A and copy paste entire thing into notepad and then look for `"channelId":"UC`_______

**Keyword**

The phrase to match against video titles. Matching is case-insensitive and checks whether the title *contains* the keyword — e.g. `"weekly recap"` would match `"My Weekly Recap - April 2026"`.

**Playlist ID**

Open your playlist on YouTube. The URL will look like:

```
https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxxxxxxxxxx
```

The playlist ID is the `PLxxxxxxxxxxxxxxxxxxxxxx` part.

---

### 3. Edit the placeholders in `watcher.py`

Open `watcher.py` and update these three lines near the top:

```python
CHANNEL_ID   = "UC_REPLACE_WITH_CHANNEL_ID"
KEYWORD      = "REPLACE_WITH_YOUR_KEYWORD"
PLAYLIST_ID  = "PL_REPLACE_WITH_PLAYLIST_ID"
```

---

### 4. Get a YouTube Data API key

The API key is used to authenticate calls to the YouTube Data API.

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or select an existing one)
3. Navigate to **APIs & Services → Library**
4. Search for **YouTube Data API v3** and click **Enable**
5. Go to **APIs & Services → Credentials**
6. Click **Create Credentials → API key**
7. Copy the key — you'll add it as a GitHub secret in step 6

---

### 5. Get an OAuth refresh token

The API key alone only allows reading public data. Writing to a playlist requires OAuth. You need to do this once on your local machine to generate a long-lived refresh token.

**Create an OAuth client:**

1. Still in **APIs & Services → Credentials**, click **Create Credentials → OAuth 2.0 Client ID**
2. Choose **Desktop app** as the application type, give it any name
3. Click **Download JSON** — this is your `client_secrets.json`

**Add yourself as a test user:**

Before running the script, add your Google account as an authorised test user, otherwise Google will block the OAuth flow with an `access_denied` error.

1. Go to **APIs & Services → OAuth consent screen**
2. Scroll down to **Test users**
3. Click **Add users** and enter the Gmail address you will authorise with
4. Click **Save**

**Copy `client_secrets.json` to your working directory:**

Install the required library:

```bash
pip install google-auth-oauthlib
```

Make sure `client_secrets.json` is in the directory where you are running the commands. If you downloaded it on Windows, copy it into your working directory first or cd into downloads directory. Rename the file to client_secrets.json if needed (example below - find ur own path):

```bash
cp /mnt/c/Users/<your-windows-username>/Downloads/client_secret_*.json ~/client_secrets.json
```

If that path doesn't work (OneDrive or permissions), copy the file manually in Windows Explorer by pasting this into the Explorer address bar and dragging the file in:

```
\\wsl$\Ubuntu\home\<your-wsl-username>\
```

**Generate the refresh token:**

> **WSL users:** WSL cannot open a browser automatically, so use the script below instead of the standard `run_local_server` approach. It prints a URL for you to open manually in your Windows browser.

```bash
python -c "
from google_auth_oauthlib.flow import InstalledAppFlow
flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json',
    scopes=['https://www.googleapis.com/auth/youtube'])
flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
print('Open this URL in your browser:')
print(auth_url)
code = input('Paste the authorisation code here: ')
flow.fetch_token(code=code)
creds = flow.credentials
print('CLIENT_ID:    ', creds.client_id)
print('CLIENT_SECRET:', creds.client_secret)
print('REFRESH_TOKEN:', creds.refresh_token)
"
```

1. The script prints a long URL — copy it and open it in your Windows browser
2. Sign in with the Google account that owns the playlist
3. If you see a warning that the app is unverified, click **Advanced** → **Go to [app name] (unsafe)** — this is expected for personal OAuth apps
4. After authorising, Google displays a code on screen — copy it
5. Paste the code back into the terminal when prompted
6. The three values (`CLIENT_ID`, `CLIENT_SECRET`, `REFRESH_TOKEN`) will be printed — copy all three

---

### 6. Add GitHub Secrets

In your GitHub repository, go to **Settings → Secrets and variables → Actions → Repository secrets → New repository secret** and add all four secrets:

> Use **Repository secrets**, not Environment secrets. Environment secrets are for multi-environment setups and are not needed here.

| Secret name | Where to get it |
|---|---|
| `YOUTUBE_API_KEY` | Step 4 |
| `YOUTUBE_CLIENT_ID` | Printed in step 5 |
| `YOUTUBE_CLIENT_SECRET` | Printed in step 5 |
| `YOUTUBE_REFRESH_TOKEN` | Printed in step 5 |

---

### 7. Commit and push

Add all files to your repository and push:

```bash
git add .
git commit -m "Add YouTube watcher"
git push
```

GitHub Actions will pick up the workflow automatically. You can verify it's recognised under the **Actions** tab in your repo.

---

## Running manually

To trigger a run without waiting for the schedule, go to the **Actions** tab in your repo, select the **YouTube watcher** workflow, and click **Run workflow**.

This is useful for testing your setup immediately after configuration.

---

## Adjusting the schedule

The workflow runs once daily at noon UTC by default. To change this, edit the `cron` line in `youtube-watcher.yml`:

```yaml
- cron: "0 12 * * *"   # once daily at noon UTC (default)
- cron: "0 * * * *"    # every hour
- cron: "0 */6 * * *"  # every 6 hours
- cron: "0 9 * * *"    # once daily at 9:00 UTC
- cron: "0 9 * * 1"    # every Monday at 9:00 UTC
```

Cron syntax is `minute hour day month weekday`. Times are in UTC. [crontab.guru](https://crontab.guru) is a helpful reference.

> GitHub Actions free tier provides 2,000 minutes per month. Hourly checks on a single workflow use roughly 60–120 minutes per month depending on runtime.

---

## Changing the keyword

Update `KEYWORD` in `watcher.py` and push the change. The new keyword applies to all videos checked from that point forward. Previously seen videos (logged in `seen_videos.txt`) will not be re-evaluated.

To re-check all videos from scratch, delete the contents of `seen_videos.txt`, commit, and push.

---

## Watching multiple channels or keywords

Duplicate the relevant section in `watcher.py` or run the script in a loop with different configs. Alternatively, copy the workflow file and point it at a second script with different values. Each combination of channel + keyword + playlist should have its own set of variables.

---

## Troubleshooting

**The workflow doesn't appear in the Actions tab**

Make sure the workflow file is at exactly `.github/workflows/youtube-watcher.yml` and that the `on:` block is valid YAML (indentation matters).

**`quotaExceeded` error in the logs**

The YouTube Data API has a free quota of 10,000 units per day. Adding a video to a playlist costs 50 units, so you would need to add 200 videos in a single day to hit the limit. If this happens, the quota resets at midnight Pacific Time.

**`invalid_grant` error**

The refresh token has expired or been revoked. Re-run the local OAuth script from step 5 to generate a new one, then update the `YOUTUBE_REFRESH_TOKEN` secret in GitHub.

**Videos are being skipped that should match**

Check the capitalisation of your keyword — matching is case-insensitive, but extra spaces or punctuation in the title could prevent a match. Review the workflow logs under the Actions tab to see the exact titles being evaluated.

**`seen_videos.txt` keeps growing**

This is expected — it stores every video ID the script has ever seen from the feed. The YouTube RSS feed returns the 15 most recent videos, so the file typically grows by at most 15 entries per new upload cycle. It will not cause any issues at normal scale.

---

## File reference

| File | Purpose |
|---|---|
| `watcher.py` | Main script — fetches feed, checks titles, calls API |
| `.github/workflows/youtube-watcher.yml` | Defines the scheduled GitHub Actions job |
| `seen_videos.txt` | Tracks processed video IDs to prevent duplicates |
