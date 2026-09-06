from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .config import Config
from .video import find_slides, create_reel
from .cloudinary_uploader import CloudinaryUploader
from .meta_api import MetaAPI
from .ledger import PublicationLedger


class ReelPublisher:
    def __init__(self, config: Config):
        self.config = config
        self.meta = MetaAPI(config.meta_api_version)
        self.ledger = PublicationLedger(
            config.data_dir / "publications.json"
        )

    def _job_paths(self, job_id: str):
        carousel_dir = Path("/data/jobs") / job_id / "carousel"
        reel_dir = Path("/data/jobs") / job_id / "reel"
        reel_path = reel_dir / "reel.mp4"
        return carousel_dir, reel_dir, reel_path

    def create(self, job_id: str):
        carousel_dir, reel_dir, reel_path = self._job_paths(job_id)
        slides = find_slides(carousel_dir)

        print("Slides:")
        for i, slide in enumerate(slides, 1):
            print(f"  {i}. {slide.name}")

        create_reel(slides, reel_path)

        return {
            "job_id": job_id,
            "video": str(reel_path),
            "slides": [str(p) for p in slides],
            "seconds_per_slide": 4,
            "duration_seconds": 24,
            "resolution": "1080x1920",
        }

    def publish(self, job_id: str, caption: str):
        self.config.validate()

        existing = self.ledger.get(job_id)
        if existing and existing.get("reel_media_id"):
            raise RuntimeError(
                "This job already has a published Reel: "
                + str(existing["reel_media_id"])
            )

        carousel_dir, reel_dir, reel_path = self._job_paths(job_id)
        slides = find_slides(carousel_dir)

        if not reel_path.exists():
            print("Reel MP4 does not exist. Creating it...")
            create_reel(slides, reel_path)
        else:
            print(f"Using existing Reel video: {reel_path}")

        account = self.meta.choose_account(
            self.config.meta_user_access_token,
            self.config.meta_page_name,
            self.config.meta_page_id,
        )

        uploader = CloudinaryUploader(
            self.config.cloudinary_cloud_name,
            self.config.cloudinary_api_key,
            self.config.cloudinary_api_secret,
            self.config.cloudinary_folder,
        )

        print("Uploading Reel video to Cloudinary...")
        uploaded = uploader.upload_video(
            reel_path,
            public_id=job_id,
        )

        video_url = uploaded["secure_url"]
        print("Cloudinary upload complete.")

        print("Creating Instagram Reel container...")
        container = self.meta.create_reel_container(
            account.ig_user_id,
            account.page_access_token,
            video_url,
            caption,
        )

        container_id = container.get("id")
        if not container_id:
            raise RuntimeError(
                f"Meta did not return Reel container ID: {container}"
            )

        print(f"Reel container: {container_id}")
        print("Waiting for Reel processing...")

        status = self.meta.wait_until_ready(
            container_id,
            account.page_access_token,
        )

        print("Reel is ready. Publishing...")

        published = self.meta.publish(
            account.ig_user_id,
            account.page_access_token,
            container_id,
        )

        media_id = published.get("id")
        if not media_id:
            raise RuntimeError(
                f"Meta did not return published Reel media ID: {published}"
            )

        record = {
            "job_id": job_id,
            "published_at_utc": datetime.now(
                timezone.utc
            ).isoformat(),
            "page_name": account.page_name,
            "page_id": account.page_id,
            "ig_user_id": account.ig_user_id,
            "reel_container_id": container_id,
            "reel_media_id": media_id,
            "reel_video": str(reel_path),
            "cloudinary_url": video_url,
            "caption": caption,
            "status": status,
        }

        self.ledger.record(job_id, record)

        return record
