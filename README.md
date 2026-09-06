# Reel Publisher

Standalone Docker-ready service for creating and publishing a 24-second Instagram Reel from exactly six existing carousel slides.

## Workflow

Input:
`/data/jobs/<job_id>/carousel/slide_1.png ... slide_6.png`

Output:
`/data/jobs/<job_id>/reel/reel.mp4`

The Reel is:
- 6 slides
- 4 seconds per slide
- 24 seconds total
- 1080x1920
- 30 FPS
- H.264 MP4
- no audio

Publishing:
1. Validate six slides
2. Create MP4 with FFmpeg
3. Upload MP4 to Cloudinary
4. Create Instagram REELS container
5. Wait until Instagram reports FINISHED
6. Publish Reel
7. Record result in `data/publications.json`

## Setup

Copy `.env.example` to `.env` and fill in credentials.

Install Docker Desktop and build:

```bash
docker compose build
```

## Dry run

This creates the Reel video but does not publish:

```bash
./run.sh create \
  --job-id 25_Indian_Overseas_Bank_IOB_Security_Guard_Recruitment_2026_Apply_Online_2026-08-29
```

## Publish

```bash
./run.sh publish \
  --job-id 25_Indian_Overseas_Bank_IOB_Security_Guard_Recruitment_2026_Apply_Online_2026-08-29 \
  --caption "Latest government job notification. Check the slides for eligibility, dates, fees and application details."
```

## Expected shared storage

The service expects the six carousel images at:

```text
/data/jobs/<job_id>/carousel/
  slide_1.png
  slide_2.png
  slide_3.png
  slide_4.png
  slide_5.png
  slide_6.png
```

For your existing project, mount `../output_carousel` as `/data/jobs`.

## Environment

Required:

```text
META_API_VERSION=v26.0
META_USER_ACCESS_TOKEN=...
META_PAGE_ID=1283817824820147
META_PAGE_NAME=Shaktidootam

CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
CLOUDINARY_FOLDER=shaktidootam/instagram_reels
```

Do not commit `.env`.

## Duplicate protection

The local ledger stores the job ID and Reel media/container IDs. A successfully published job is not published again by default.

Use:

```bash
./run.sh status --job-id <job_id>
```

to inspect the local publication record.
