"""Scrape Reddit stories by URL or from top subreddits."""

import logging
from dataclasses import dataclass, asdict

import praw

from faceless.config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET

log = logging.getLogger(__name__)


@dataclass
class RedditStory:
    title: str
    body: str
    subreddit: str
    score: int
    post_id: str

    @property
    def full_text(self) -> str:
        return f"{self.title}\n\n{self.body}" if self.body else self.title


def _get_client() -> praw.Reddit:
    return praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent="faceless-shorts/1.0",
    )


def _to_story(submission) -> RedditStory:
    return RedditStory(
        title=submission.title,
        body=submission.selftext or "",
        subreddit=str(submission.subreddit),
        score=submission.score,
        post_id=submission.id,
    )


def scrape_url(url: str) -> RedditStory:
    """Fetch a single Reddit post by URL."""
    submission = _get_client().submission(url=url)
    story = _to_story(submission)
    log.info("Scraped: %s (r/%s, score %d)", story.title[:60], story.subreddit, story.score)
    return story


STORY_SUBREDDITS = [
    "askreddit", "tifu", "AmItheAsshole", "TrueOffMyChest",
    "confession", "MaliciousCompliance", "pettyrevenge", "ProRevenge",
    "entitledparents", "nosleep",
]


def scrape_top(limit: int = 10, min_length: int = 200) -> list[RedditStory]:
    """Pull top stories across story subreddits."""
    reddit = _get_client()
    stories: list[RedditStory] = []
    seen: set[str] = set()

    for sub_name in STORY_SUBREDDITS:
        try:
            for post in reddit.subreddit(sub_name).hot(limit=limit):
                if post.is_self and len(post.selftext) >= min_length and post.id not in seen:
                    seen.add(post.id)
                    stories.append(_to_story(post))
        except Exception as exc:
            log.warning("Failed r/%s: %s", sub_name, exc)

    stories.sort(key=lambda s: s.score, reverse=True)
    return stories[:limit]
