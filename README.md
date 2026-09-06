# ig_reel_publisher

Standalone local Python application for creating and optionally publishing a 24-second Instagram Reel from an existing six-slide job-post carousel.

This version does NOT use Docker.

## Reel format

- Exactly 6 slides
- 4 seconds per slide
- 24 seconds total
- 1080x1920 (9:16)
- 30 FPS
- H.264 MP4
- No audio
- Original slide files are never modified

## Input

The application accepts the same job folder used by the carousel publisher:

```text
../output_carousel/JOB_ID/
    slide_1.png
    slide_2.png
    slide_3.png
    slide_4.png
    slide_5.png
    slide_6.png
```

PNG/JPG/JPEG/WEBP are accepted. Exactly six image files must be present.

## 1. Install

From macOS:

```bash
brew install ffmpeg
```

Create the virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Configure

```bash
cp .env.example .env
```

Set your Meta and Cloudinary credentials.

Use a fresh Meta User Access Token. Do not paste tokens into source code or commit `.env`.

## 3. Create Reel only

This is the recommended first test:

```bash
./run.sh create \
  --input-dir "../output_carousel/25_Indian_Overseas_Bank_IOB_Security_Guard_Recruitment_2026_Apply_Online_2026-08-29"
```

The output will be:

```text
../output_carousel/25_Indian_Overseas_Bank_IOB_Security_Guard_Recruitment_2026_Apply_Online_2026-08-29/reel/reel.mp4
```

## 4. Publish Reel

After inspecting the MP4:

```bash
./run.sh publish \
  --input-dir "../output_carousel/25_Indian_Overseas_Bank_IOB_Security_Guard_Recruitment_2026_Apply_Online_2026-08-29" \
  --caption "Latest government job notification. Check the slides for eligibility, dates, fees and application details." \
  --publish
```

The application will:

1. Validate exactly six slides
2. Create/reuse the 24-second MP4
3. Get the Page Access Token through the configured Page ID
4. Upload the MP4 to Cloudinary
5. Create an Instagram REELS container
6. Wait for `FINISHED`
7. Publish the Reel
8. Record the result in `data/publications.json`

The `--publish` flag is required for an actual Instagram publication.

Without `--publish`, `publish` is rejected; use `create` when you only want the MP4.

## 5. Status

```bash
./run.sh status --job-id 25_Indian_Overseas_Bank_IOB_Security_Guard_Recruitment_2026_Apply_Online_2026-08-29
```

## Separate service

This project intentionally does not import or modify `ig_carousel_publisher`.

The two applications share only the six slide files:

```text
Carousel publisher → slide_1 ... slide_6
                              ↓
                       Reel publisher
```

## Expected commands

Carousel service:

```bash
cd ../ig_carousel_publisher
./run.sh publish ...
```

Reel service:

```bash
cd ../ig_reel_publisher
./run.sh create ...
./run.sh publish ...
```
