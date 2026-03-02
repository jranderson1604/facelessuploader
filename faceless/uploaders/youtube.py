"""YouTube Shorts uploader via YouTube Data API v3 (OAuth2)."""

import logging
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from faceless.config import YOUTUBE_CLIENT_SECRETS_FILE

log = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "youtube_token.json"


def _get_authenticated_service():
    """Authenticate and return a YouTube API service object."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(YOUTUBE_CLIENT_SECRETS_FILE):
                raise FileNotFoundError(
                    f"YouTube client secrets file not found: {YOUTUBE_CLIENT_SECRETS_FILE}\n"
                    "Download it from https://console.cloud.google.com/apis/credentials"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                YOUTUBE_CLIENT_SECRETS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def upload(
    video_path: str | Path,
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    category_id: str = "22",  # People & Blogs
    privacy: str = "public",
) -> str:
    """Upload a video to YouTube as a Short.

    Returns the video ID on success.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    youtube = _get_authenticated_service()

    # Add #Shorts to description to signal YouTube this is a Short
    if "#Shorts" not in description:
        description = f"{description}\n\n#Shorts".strip()

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags or ["shorts", "reddit", "storytime"],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=10 * 1024 * 1024,
    )

    log.info("Uploading to YouTube: %s", title[:60])
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            log.info("Upload progress: %d%%", int(status.progress() * 100))

    video_id = response["id"]
    log.info("YouTube upload complete: https://youtube.com/shorts/%s", video_id)
    return video_id
