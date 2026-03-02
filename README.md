# Faceless Shorts

Automated faceless short-form video generator and multi-platform uploader. Scrapes Reddit stories, generates TTS narration with animated subtitles over gameplay footage, and uploads to YouTube Shorts, TikTok, and Instagram Reels — up to 10+ times per day on autopilot.

## How It Works

1. **Scrape** — Pulls stories from Reddit (direct URL or auto-discovers top posts from story subreddits)
2. **Narrate** — Converts text to speech using Edge TTS (Microsoft's free, high-quality voices)
3. **Render** — Composites vertical video: background footage + animated subtitles + TTS audio
4. **Upload** — Pushes to YouTube Shorts, TikTok, and Instagram Reels
5. **Schedule** — Built-in scheduler runs the full pipeline automatically throughout the day

## Quick Start

### 1. Install

```bash
# Clone the repo
git clone <this-repo>
cd facelessuploader

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### 2. Configure

```bash
# Copy the example env file
cp .env.example .env

# Edit with your credentials
nano .env
```

You need to set up at minimum:
- **Reddit API** credentials ([create an app here](https://www.reddit.com/prefs/apps))
- At least one upload platform (YouTube, TikTok, or Instagram)

### 3. Download Background Videos

```bash
# Downloads Minecraft parkour gameplay for backgrounds
faceless download-backgrounds -q "minecraft parkour gameplay" -n 3
```

Or manually drop any vertical `.mp4` files into the `backgrounds/` folder.

### 4. Generate Your First Video

```bash
# From a specific Reddit URL
faceless url https://reddit.com/r/tifu/comments/abc123/...

# Auto-find top stories and generate
faceless auto -n 3

# Generate without uploading (test mode)
faceless url https://reddit.com/r/... --no-upload
```

### 5. Run on Autopilot

```bash
# Start the scheduler — 10 uploads/day between 8am-10pm
faceless schedule

# Customize
faceless schedule -n 15 --start-hour 6 --end-hour 23

# Only upload to YouTube
faceless schedule -p youtube
```

### 6. Web Dashboard

```bash
faceless web
# Opens at http://127.0.0.1:5000
```

The dashboard lets you:
- Paste a Reddit URL and generate/upload with one click
- Auto-generate from top stories
- View upload history across all platforms

## Platform Setup

### YouTube Shorts

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable the YouTube Data API v3
3. Create OAuth 2.0 credentials (Desktop app)
4. Download `client_secrets.json` to the project root
5. Run `faceless auth youtube` to authenticate (opens browser)

### TikTok

1. Log in to TikTok in your browser
2. Open DevTools > Application > Cookies
3. Copy the `sessionid` cookie value
4. Set `TIKTOK_SESSION_ID` in `.env`

### Instagram Reels

1. Set `INSTAGRAM_USERNAME` and `INSTAGRAM_PASSWORD` in `.env`
2. That's it — uses the instagrapi library for direct API access

## CLI Reference

```
faceless url <URL>              Generate from a Reddit post URL
  --no-upload                   Skip uploading, just render the video
  -p youtube/tiktok/instagram   Upload to specific platform(s)

faceless auto                   Auto-scrape and generate
  -n COUNT                      Number of videos (default: 1)
  -p PLATFORM                   Target platform

faceless schedule               Start autopilot scheduler
  -n UPLOADS_PER_DAY            How many per day (default: 10)
  --start-hour / --end-hour     Active hours

faceless download-backgrounds   Fetch background gameplay clips
  -q QUERY                      Search query
  -n COUNT                      Number of clips

faceless history                Show upload history
  --json-output                 Output as JSON

faceless auth youtube           Authenticate with YouTube
faceless web                    Start web dashboard
```

## Project Structure

```
facelessuploader/
├── faceless/
│   ├── cli.py              # CLI commands
│   ├── config.py           # Configuration from .env
│   ├── pipeline.py         # End-to-end orchestration
│   ├── scrapers/
│   │   └── reddit.py       # Reddit story scraper
│   ├── tts/
│   │   └── engine.py       # Text-to-speech (Edge/gTTS/pyttsx3)
│   ├── video/
│   │   └── generator.py    # Video rendering engine
│   ├── uploaders/
│   │   ├── manager.py      # Multi-platform upload orchestrator
│   │   ├── youtube.py      # YouTube Shorts uploader
│   │   ├── tiktok.py       # TikTok uploader
│   │   └── instagram.py    # Instagram Reels uploader
│   └── scheduler/
│       └── scheduler.py    # APScheduler-based autopilot
├── web/
│   ├── app.py              # Flask web dashboard
│   ├── templates/
│   │   └── index.html      # Dashboard UI
│   └── static/
│       ├── style.css        # Dark theme styles
│       └── app.js           # Frontend JS
├── backgrounds/             # Background video clips (add your own)
├── output/                  # Generated videos land here
├── .env.example             # Config template
├── requirements.txt
└── pyproject.toml
```

## Configuration

All settings are in `.env`. Key options:

| Variable | Default | Description |
|----------|---------|-------------|
| `TTS_ENGINE` | `edge` | TTS engine: `edge`, `gtts`, or `pyttsx3` |
| `TTS_VOICE` | `en-US-ChristopherNeural` | Edge TTS voice |
| `UPLOADS_PER_DAY` | `10` | Auto-scheduler target |
| `SCHEDULE_START_HOUR` | `8` | Scheduler start time |
| `SCHEDULE_END_HOUR` | `22` | Scheduler end time |
| `FONT_SIZE` | `60` | Subtitle font size |
| `SUBTITLE_STYLE` | `word_highlight` | Subtitle animation style |

## Tips

- **Best voices**: Try `en-US-ChristopherNeural` (male) or `en-US-JennyNeural` (female). Run `edge-tts --list-voices` for all options.
- **Background videos**: Minecraft parkour, Subway Surfers, and satisfying clips work best. Vertical (9:16) is ideal but landscape gets auto-cropped.
- **Story length**: Videos are best at 30-90 seconds. The scraper filters for stories with at least 200 characters by default.
- **Avoid bans**: The scheduler adds random jitter between uploads. Don't set `UPLOADS_PER_DAY` too high on new accounts.
