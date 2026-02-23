# The Larry Seyer Show - Podcast Automation

This system automatically converts YouTube videos into an Apple Podcasts-compatible feed.

## How It Works

```
YouTube RSS → GitHub Actions (Saturday 10am) → Internet Archive (audio storage)
                      ↓
              GitHub Pages (RSS feed) → Apple Podcasts
```

- **Weekly automation**: Runs every Saturday at 10 AM Central
- **Free hosting**: Audio files stored on Internet Archive (unlimited, free)
- **Apple-compliant**: RSS feed follows Apple Podcasts specifications

## Setup Tasks (One-Time)

### 1. Create Internet Archive Account

1. Go to [archive.org](https://archive.org) and create a free account
2. Verify your email address

### 2. Get S3 API Keys

1. Go to [archive.org/account/s3.php](https://archive.org/account/s3.php)
2. You'll see your **Access Key** and **Secret Key**
3. Copy both keys - you'll need them in the next step

### 3. Add GitHub Secrets

1. Go to your repository: `github.com/larryseyer/larryseyer.github.io`
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add:
   - Name: `IA_ACCESS_KEY` | Value: Your Internet Archive access key
   - Name: `IA_SECRET_KEY` | Value: Your Internet Archive secret key

### 4. Create Podcast Artwork

Apple Podcasts requires square artwork, minimum 1400x1400 pixels.

1. Create or resize an image to at least 1400x1400 (3000x3000 recommended)
2. Save as JPEG or PNG
3. Place the file at: `podcast/artwork.png` (or `.jpg`) in this repository
4. Commit and push the change

### 5. Run Initial Sync

1. Go to: **Actions** tab in GitHub
2. Select **Podcast Sync** workflow
3. Click **Run workflow**
4. Enable **Process all videos from 2024 onward** for backfill
5. Click **Run workflow**

This will process all your YouTube videos from 2024 onwards.

### 6. Submit to Apple Podcasts

1. Go to [podcastsconnect.apple.com](https://podcastsconnect.apple.com)
2. Sign in with your Apple ID
3. Click **+** to add a new show
4. Enter your feed URL: `https://larryseyer.com/podcast/feed.xml`
5. Follow the prompts to complete submission
6. Wait for Apple's review (usually 1-5 days)

## Files

| File | Purpose |
|------|---------|
| `feed.xml` | RSS feed served to podcast apps |
| `episodes.json` | Tracks processed episodes (prevents duplicates) |
| `artwork.jpg` | Podcast cover art (you provide this) |
| `README.md` | This documentation |

## Manual Operations

### Process a Single Video

Run the workflow with a specific video ID:
1. Actions → Podcast Sync → Run workflow
2. Enter the YouTube video ID in the **video_id** field
3. Run workflow

### Check Sync Status

- View recent runs: **Actions** → **Podcast Sync**
- Check feed: [larryseyer.com/podcast/feed.xml](https://larryseyer.com/podcast/feed.xml)

## Troubleshooting

**Workflow fails with "Missing credentials"**
- Ensure `IA_ACCESS_KEY` and `IA_SECRET_KEY` secrets are set correctly

**No new episodes appearing**
- Check that new videos exist on YouTube
- Verify the workflow ran successfully in Actions tab

**Apple Podcasts not updating**
- Apple polls feeds every few hours; updates aren't instant
- Validate feed at [podcastsconnect.apple.com](https://podcastsconnect.apple.com)

## Feed URL

```
https://larryseyer.com/podcast/feed.xml
```
