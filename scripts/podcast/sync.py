#!/usr/bin/env python3
"""
YouTube to Apple Podcasts Sync Script

Automates converting Larry Seyer's YouTube show into an Apple Podcasts-compatible feed.
- Fetches YouTube RSS feed for new videos
- Extracts audio using yt-dlp
- Uploads to Internet Archive for free hosting
- Generates Apple Podcasts-compliant RSS feed

Usage:
    python sync.py                    # Process new episodes only
    python sync.py --backfill         # Process all episodes from 2024 onward
    python sync.py --video-id=ABC123  # Process a single video
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

import boto3
import requests
from botocore.config import Config
from feedgen.feed import FeedGenerator

# Configuration
YOUTUBE_CHANNEL_ID = "UCTjKRQNMHOdeHrJNqrhj5rA"
YOUTUBE_RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
BACKFILL_START_DATE = datetime(2024, 1, 1, tzinfo=timezone.utc)

# Internet Archive settings
IA_S3_ENDPOINT = "https://s3.us.archive.org"
IA_ITEM_ID = "larry-seyer-show-podcast"  # Will be created on first upload

# Podcast metadata
PODCAST_TITLE = "The Larry Seyer Show"
PODCAST_DESCRIPTION = (
    "Grammy-winning recording engineer Larry Seyer discusses music production, "
    "recording techniques, and shares stories from his legendary career working with "
    "artists like George Strait, Lyle Lovett, and many more."
)
PODCAST_AUTHOR = "Larry Seyer"
PODCAST_EMAIL = "larry@larryseyer.com"
PODCAST_WEBSITE = "https://larryseyer.com"
PODCAST_IMAGE_URL = "https://larryseyer.com/podcast/artwork.png"
PODCAST_CATEGORY = "Music"
PODCAST_SUBCATEGORY = "Music Commentary"
PODCAST_LANGUAGE = "en-us"
PODCAST_EXPLICIT = "no"

# Paths
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.parent
PODCAST_DIR = REPO_ROOT / "podcast"
EPISODES_FILE = PODCAST_DIR / "episodes.json"
FEED_FILE = PODCAST_DIR / "feed.xml"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def get_ia_credentials() -> tuple[str, str]:
    """Get Internet Archive S3 credentials from environment."""
    access_key = os.environ.get("IA_ACCESS_KEY")
    secret_key = os.environ.get("IA_SECRET_KEY")

    if not access_key or not secret_key:
        raise ValueError(
            "Missing Internet Archive credentials. "
            "Set IA_ACCESS_KEY and IA_SECRET_KEY environment variables."
        )

    return access_key, secret_key


def get_ia_client():
    """Create boto3 client for Internet Archive S3 API."""
    access_key, secret_key = get_ia_credentials()

    return boto3.client(
        "s3",
        endpoint_url=IA_S3_ENDPOINT,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4")
    )


def load_episodes() -> list[dict]:
    """Load processed episodes from JSON file."""
    if not EPISODES_FILE.exists():
        return []

    with open(EPISODES_FILE, "r") as f:
        return json.load(f)


def save_episodes(episodes: list[dict]) -> None:
    """Save processed episodes to JSON file."""
    PODCAST_DIR.mkdir(parents=True, exist_ok=True)

    with open(EPISODES_FILE, "w") as f:
        json.dump(episodes, f, indent=2, default=str)


def fetch_youtube_feed() -> list[dict]:
    """Fetch and parse YouTube RSS feed."""
    logger.info(f"Fetching YouTube feed: {YOUTUBE_RSS_URL}")

    response = requests.get(YOUTUBE_RSS_URL, timeout=30)
    response.raise_for_status()

    # Parse XML
    root = ET.fromstring(response.content)

    # YouTube Atom feed namespaces
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "media": "http://search.yahoo.com/mrss/"
    }

    videos = []
    for entry in root.findall("atom:entry", ns):
        video_id = entry.find("yt:videoId", ns).text
        title = entry.find("atom:title", ns).text
        published = entry.find("atom:published", ns).text

        # Parse media group for description and thumbnail
        media_group = entry.find("media:group", ns)
        description = ""
        thumbnail = ""
        if media_group is not None:
            desc_elem = media_group.find("media:description", ns)
            if desc_elem is not None and desc_elem.text:
                description = desc_elem.text
            thumb_elem = media_group.find("media:thumbnail", ns)
            if thumb_elem is not None:
                thumbnail = thumb_elem.get("url", "")

        # Parse published date
        pub_date = datetime.fromisoformat(published.replace("Z", "+00:00"))

        videos.append({
            "video_id": video_id,
            "title": title,
            "description": description,
            "thumbnail": thumbnail,
            "published": pub_date,
            "url": f"https://www.youtube.com/watch?v={video_id}"
        })

    logger.info(f"Found {len(videos)} videos in feed")
    return videos


def extract_audio(video_id: str, output_dir: Path) -> tuple[Path, dict]:
    """Extract audio from YouTube video using yt-dlp."""
    logger.info(f"Extracting audio from video: {video_id}")

    output_template = str(output_dir / f"{video_id}.%(ext)s")
    url = f"https://www.youtube.com/watch?v={video_id}"

    # yt-dlp command for 128kbps MP3
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "128K",
        "--output", output_template,
        "--print-json",
        "--no-playlist",
        url
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    # Parse JSON output for metadata
    metadata = json.loads(result.stdout.strip().split("\n")[-1])

    audio_file = output_dir / f"{video_id}.mp3"
    if not audio_file.exists():
        raise FileNotFoundError(f"Expected audio file not found: {audio_file}")

    return audio_file, metadata


def upload_to_internet_archive(
    audio_file: Path,
    video_id: str,
    title: str,
    description: str,
    pub_date: datetime
) -> str:
    """Upload audio file to Internet Archive and return URL."""
    logger.info(f"Uploading to Internet Archive: {audio_file.name}")

    client = get_ia_client()

    # File key within the item
    file_key = f"{video_id}.mp3"

    # Metadata headers for Internet Archive
    metadata = {
        "x-archive-meta-mediatype": "audio",
        "x-archive-meta-collection": "opensource_audio",
        "x-archive-meta-title": title,
        "x-archive-meta-creator": PODCAST_AUTHOR,
        "x-archive-meta-date": pub_date.strftime("%Y-%m-%d"),
        "x-archive-meta-description": description[:1000] if description else "",
        "x-archive-meta-subject": "podcast;music;recording;larry seyer",
        "x-archive-meta-licenseurl": "https://creativecommons.org/licenses/by-nc/4.0/",
    }

    # Read file and upload
    with open(audio_file, "rb") as f:
        file_content = f.read()

    # Upload with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            client.put_object(
                Bucket=IA_ITEM_ID,
                Key=file_key,
                Body=file_content,
                ContentType="audio/mpeg",
                Metadata={k.replace("x-archive-meta-", ""): v for k, v in metadata.items()}
            )
            break
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Upload attempt {attempt + 1} failed: {e}. Retrying...")
            else:
                raise

    # Construct public URL
    audio_url = f"https://archive.org/download/{IA_ITEM_ID}/{file_key}"
    logger.info(f"Upload complete: {audio_url}")

    return audio_url


def generate_rss_feed(episodes: list[dict]) -> None:
    """Generate Apple Podcasts-compliant RSS feed."""
    logger.info("Generating RSS feed")

    fg = FeedGenerator()
    fg.load_extension("podcast")

    # Channel metadata
    fg.title(PODCAST_TITLE)
    fg.description(PODCAST_DESCRIPTION)
    fg.author({"name": PODCAST_AUTHOR, "email": PODCAST_EMAIL})
    fg.link(href=PODCAST_WEBSITE, rel="alternate")
    fg.link(href=f"{PODCAST_WEBSITE}/podcast/feed.xml", rel="self")
    fg.language(PODCAST_LANGUAGE)
    fg.image(PODCAST_IMAGE_URL)
    fg.copyright(f"Copyright {datetime.now().year} {PODCAST_AUTHOR}")

    # iTunes/Apple Podcasts specific
    fg.podcast.itunes_author(PODCAST_AUTHOR)
    fg.podcast.itunes_category(PODCAST_CATEGORY, PODCAST_SUBCATEGORY)
    fg.podcast.itunes_explicit(PODCAST_EXPLICIT)
    fg.podcast.itunes_image(PODCAST_IMAGE_URL)
    fg.podcast.itunes_owner(name=PODCAST_AUTHOR, email=PODCAST_EMAIL)
    fg.podcast.itunes_summary(PODCAST_DESCRIPTION)
    fg.podcast.itunes_type("episodic")

    # Sort episodes by date (newest first)
    sorted_episodes = sorted(
        episodes,
        key=lambda e: e.get("published", ""),
        reverse=True
    )

    # Add episodes
    for ep in sorted_episodes:
        if not ep.get("audio_url"):
            continue  # Skip episodes without audio

        fe = fg.add_entry()
        fe.id(ep["video_id"])
        fe.title(ep["title"])
        fe.description(ep.get("description", ""))
        fe.link(href=ep.get("youtube_url", ""))

        # Parse published date if it's a string
        pub_date = ep["published"]
        if isinstance(pub_date, str):
            pub_date = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
        fe.published(pub_date)

        # Audio enclosure
        fe.enclosure(
            ep["audio_url"],
            str(ep.get("file_size", 0)),
            "audio/mpeg"
        )

        # iTunes episode metadata
        fe.podcast.itunes_author(PODCAST_AUTHOR)
        fe.podcast.itunes_duration(ep.get("duration", 0))
        fe.podcast.itunes_explicit(PODCAST_EXPLICIT)
        fe.podcast.itunes_summary(ep.get("description", "")[:4000])

        if ep.get("thumbnail"):
            fe.podcast.itunes_image(ep["thumbnail"])

    # Write feed
    PODCAST_DIR.mkdir(parents=True, exist_ok=True)
    fg.rss_file(str(FEED_FILE), pretty=True)
    logger.info(f"RSS feed written to: {FEED_FILE}")


def process_video(video: dict, episodes: list[dict]) -> Optional[dict]:
    """Process a single video: extract audio, upload, return episode data."""
    video_id = video["video_id"]

    # Check if already processed
    if any(ep["video_id"] == video_id for ep in episodes):
        logger.info(f"Skipping already processed video: {video_id}")
        return None

    logger.info(f"Processing video: {video['title']}")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        try:
            # Extract audio
            audio_file, metadata = extract_audio(video_id, temp_path)
            file_size = audio_file.stat().st_size
            duration = metadata.get("duration", 0)

            # Upload to Internet Archive
            audio_url = upload_to_internet_archive(
                audio_file,
                video_id,
                video["title"],
                video["description"],
                video["published"]
            )

            # Create episode entry
            episode = {
                "video_id": video_id,
                "title": video["title"],
                "description": video["description"],
                "thumbnail": video.get("thumbnail", ""),
                "published": video["published"].isoformat(),
                "youtube_url": video["url"],
                "audio_url": audio_url,
                "file_size": file_size,
                "duration": int(duration),
                "processed_at": datetime.now(timezone.utc).isoformat()
            }

            return episode

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to extract audio from {video_id}: {e}")
            logger.error(f"stderr: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Failed to process video {video_id}: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(description="Sync YouTube videos to podcast feed")
    parser.add_argument(
        "--backfill",
        action="store_true",
        help="Process all videos from 2024 onward"
    )
    parser.add_argument(
        "--video-id",
        type=str,
        help="Process a single video by ID"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without actually doing it"
    )
    args = parser.parse_args()

    # Load existing episodes
    episodes = load_episodes()
    logger.info(f"Loaded {len(episodes)} existing episodes")

    # Fetch YouTube feed
    videos = fetch_youtube_feed()

    # Filter videos based on mode
    if args.video_id:
        videos = [v for v in videos if v["video_id"] == args.video_id]
        if not videos:
            logger.error(f"Video not found in feed: {args.video_id}")
            sys.exit(1)
    elif args.backfill:
        videos = [v for v in videos if v["published"] >= BACKFILL_START_DATE]
        logger.info(f"Backfill mode: {len(videos)} videos from 2024 onward")
    else:
        # Only process videos not already in episodes
        processed_ids = {ep["video_id"] for ep in episodes}
        videos = [v for v in videos if v["video_id"] not in processed_ids]
        logger.info(f"Found {len(videos)} new videos to process")

    if args.dry_run:
        logger.info("Dry run - would process these videos:")
        for v in videos:
            logger.info(f"  - {v['title']} ({v['video_id']})")
        return

    # Process videos
    new_episodes = []
    for video in videos:
        episode = process_video(video, episodes)
        if episode:
            new_episodes.append(episode)
            episodes.append(episode)
            # Save after each successful processing
            save_episodes(episodes)

    logger.info(f"Processed {len(new_episodes)} new episodes")

    # Regenerate RSS feed
    generate_rss_feed(episodes)

    logger.info("Sync complete!")


if __name__ == "__main__":
    main()
