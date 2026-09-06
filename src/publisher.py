from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .cloudinary_uploader import CloudinaryUploader
from .config import Config
from .ledger import PublicationLedger
from .meta_api import MetaAPI
from .video import create_reel, find_slides


class ReelPublisher:
    def __init__(self, config: Config):
        self.config = config
        self.meta = MetaAPI(
            config.meta_api_version
        )
        self.ledger = PublicationLedger(
            config.data_dir / "publications.json"
        )

    def _paths(self, input_dir: Path):
        reel_dir = input_dir / "reel"
        reel_path = reel_dir / "reel.mp4"
        return reel_dir, reel_path

    def create(self, input_dir_string: str):
        input_dir = Path(
            input_dir_string
        ).expanduser().resolve()

        slides = find_slides(input_dir)

        print("\nSlides selected:")
        for index, slide in enumerate(
            slides, 1
        ):
            print(f"  {index}. {slide.name}")

        _, reel_path = self._paths(
            input_dir
        )

        create_reel(
            slides,
            reel_path,
        )

        return {
            "input_dir": str(input_dir),
            "slides": [
                str(p) for p in slides
            ],
            "reel": str(reel_path),
            "seconds_per_slide": 4,
            "duration_seconds": 24,
            "resolution": "1080x1920",
            "fps": 30,
        }

    def publish(
        self,
        input_dir_string: str,
        caption: str,
    ):
        self.config.validate()

        input_dir = Path(
            input_dir_string
        ).expanduser().resolve()

        job_id = input_dir.name

        existing = self.ledger.get(job_id)

        if existing and existing.get(
            "reel_media_id"
        ):
            raise RuntimeError(
                "This job already has a published Reel. "
                f"Instagram media ID: "
                f"{existing['reel_media_id']}"
            )

        slides = find_slides(input_dir)

        _, reel_path = self._paths(
            input_dir
        )

        if not reel_path.exists():
            print(
                "Reel video does not exist. "
                "Creating it now..."
            )
            create_reel(
                slides,
                reel_path,
            )
        else:
            print(
                f"Using existing Reel video: "
                f"{reel_path}"
            )

        print("Discovering Instagram account...")
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

        video_url = uploaded.get(
            "secure_url"
        )

        if not video_url:
            raise RuntimeError(
                f"Cloudinary did not return secure_url: "
                f"{uploaded}"
            )

        print("Cloudinary upload complete.")

        print(
            "Creating Instagram Reel container..."
        )

        container = (
            self.meta.create_reel_container(
                account.ig_user_id,
                account.page_access_token,
                video_url,
                caption,
            )
        )

        container_id = container.get("id")

        if not container_id:
            raise RuntimeError(
                "Meta did not return Reel container ID: "
                f"{container}"
            )

        print(
            f"Reel container created: "
            f"{container_id}"
        )

        print(
            "Waiting for Instagram Reel "
            "processing..."
        )

        status = self.meta.wait_until_ready(
            container_id,
            account.page_access_token,
        )

        print(
            "Reel processing finished. "
            "Publishing..."
        )

        published = self.meta.publish(
            account.ig_user_id,
            account.page_access_token,
            container_id,
        )

        media_id = published.get("id")

        if not media_id:
            raise RuntimeError(
                "Meta did not return published Reel "
                f"media ID: {published}"
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

        self.ledger.record(
            job_id,
            record,
        )

        print(
            "\nSUCCESS — one Instagram Reel "
            "was published."
        )

        return record

    def status(self, job_id: str):
        record = self.ledger.get(job_id)

        if record is None:
            return {
                "job_id": job_id,
                "status": "not_found",
            }

        return record
