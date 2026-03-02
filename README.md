# Faceless Shorts

Paste a Reddit link, get a vertical short video with TTS narration and subtitles. You upload it yourself.

## How It Works

1. Scrapes the Reddit post text
2. Generates TTS narration (Microsoft Edge voices — free, sounds natural)
3. Renders a 1080x1920 vertical video with background footage and animated subtitles
4. Saves the `.mp4` to `output/` — you upload it wherever you want

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Reddit API (required)

1. Go to https://www.reddit.com/prefs/apps
2. Create a "script" app
3. Copy the client ID and secret

```bash
cp .env.example .env
# Fill in REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET
```

### Background Videos

Drop any `.mp4` files into the `backgrounds/` folder. Minecraft parkour, Subway Surfers, satisfying clips — whatever you want. Landscape gets auto-cropped to vertical.

If you don't add any, it'll use a plain dark background.

## Usage

```bash
# From a Reddit URL
faceless url https://reddit.com/r/tifu/comments/abc123/...

# Auto-grab top stories
faceless auto -n 5
```

Videos land in `output/`. Upload them to YouTube Shorts, TikTok, Instagram Reels yourself.

## Config

Edit `.env`:

| Variable | Default | What it does |
|----------|---------|-------------|
| `REDDIT_CLIENT_ID` | — | Reddit API client ID |
| `REDDIT_CLIENT_SECRET` | — | Reddit API client secret |
| `TTS_VOICE` | `en-US-ChristopherNeural` | Voice for narration |

Run `edge-tts --list-voices` for all available voices. Good ones:
- `en-US-ChristopherNeural` — deep male voice
- `en-US-JennyNeural` — female voice
- `en-US-GuyNeural` — casual male voice
