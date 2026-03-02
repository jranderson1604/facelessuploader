"""Scrape Reddit stories — supports direct URLs, subreddit hot/top, and search."""

import json
import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path

import praw

from faceless.config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT

log = logging.getLogger(__name__)


@dataclass
class RedditStory:
    title: str
    body: str
    author: str
    subreddit: str
    url: str
    score: int
    post_id: str

    @property
    def full_text(self) -> str:
        return f"{self.title}\n\n{self.body}" if self.body else self.title

    def to_dict(self) -> dict:
        return asdict(self)


def _get_client() -> praw.Reddit:
    return praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )


def _submission_to_story(submission) -> RedditStory:
    return RedditStory(
        title=submission.title,
        body=submission.selftext or "",
        author=str(submission.author) if submission.author else "[deleted]",
        subreddit=str(submission.subreddit),
        url=f"https://reddit.com{submission.permalink}",
        score=submission.score,
        post_id=submission.id,
    )


def scrape_url(url: str) -> RedditStory:
    """Fetch a single Reddit post by URL."""
    reddit = _get_client()
    submission = reddit.submission(url=url)
    story = _submission_to_story(submission)
    log.info("Scraped story: %s (score %d)", story.title[:60], story.score)
    return story


def scrape_subreddit(
    subreddit: str = "askreddit",
    sort: str = "hot",
    limit: int = 10,
    time_filter: str = "day",
    min_body_length: int = 200,
) -> list[RedditStory]:
    """Fetch stories from a subreddit with optional filtering."""
    reddit = _get_client()
    sub = reddit.subreddit(subreddit)

    if sort == "hot":
        posts = sub.hot(limit=limit * 3)
    elif sort == "top":
        posts = sub.top(time_filter=time_filter, limit=limit * 3)
    elif sort == "new":
        posts = sub.new(limit=limit * 3)
    else:
        posts = sub.hot(limit=limit * 3)

    stories = []
    for submission in posts:
        if submission.is_self and len(submission.selftext) >= min_body_length:
            stories.append(_submission_to_story(submission))
            if len(stories) >= limit:
                break

    log.info("Found %d stories from r/%s", len(stories), subreddit)
    return stories


# Default subreddits that tend to have good story content
STORY_SUBREDDITS = [
    "askreddit",
    "tifu",
    "AmItheAsshole",
    "TrueOffMyChest",
    "confession",
    "relationships",
    "MaliciousCompliance",
    "pettyrevenge",
    "ProRevenge",
    "entitledparents",
    "nosleep",
    "letsnotmeet",
]


def scrape_best_stories(limit: int = 10) -> list[RedditStory]:
    """Pull the best stories across multiple subreddits."""
    all_stories: list[RedditStory] = []
    per_sub = max(2, limit // len(STORY_SUBREDDITS) + 1)

    for sub_name in STORY_SUBREDDITS:
        try:
            stories = scrape_subreddit(sub_name, sort="hot", limit=per_sub)
            all_stories.extend(stories)
        except Exception as exc:
            log.warning("Failed to scrape r/%s: %s", sub_name, exc)

    # Deduplicate and sort by score
    seen_ids: set[str] = set()
    unique: list[RedditStory] = []
    for s in all_stories:
        if s.post_id not in seen_ids:
            seen_ids.add(s.post_id)
            unique.append(s)
    unique.sort(key=lambda s: s.score, reverse=True)
    return unique[:limit]
