from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .cloudinary_uploader import CloudinaryUploader
from .config import Config
from .ledger import PublicationLedger
from .meta_api import MetaAPI
from .video import choose_random_music, create_reel, find_slides


MUSIC_DIR = Path(__file__).resolve().parents[2] / "data" / "music"


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

    def _load_json_file(self, file_path: Path):
        if not file_path.exists():
            return {}

        try:
            return json.loads(
                file_path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Failed to parse JSON file: {file_path}"
            ) from exc

    def _lookup_card_value(
        self,
        slides: list[dict],
        label_contains: str,
    ):
        normalized_label = label_contains.lower()

        for slide in slides:
            for card in slide.get("cards", []):
                label = str(card.get("label", "")).lower()
                if normalized_label in label:
                    value = card.get("value")
                    if value:
                        return str(value)

            for bullet in slide.get("bullets", []):
                if normalized_label in str(bullet).lower():
                    return str(bullet)

        return None

    def _collect_urls(self, facts: dict):
        urls = []

        if facts.get("source_url"):
            urls.append(str(facts["source_url"]))

        for item in facts.get("links", []) or []:
            if isinstance(item, dict):
                url = (
                    item.get("url")
                    or item.get("href")
                    or item.get("link")
                )
                if url:
                    urls.append(str(url))
            else:
                urls.append(str(item))

        unique_urls = []
        seen = set()

        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls

    def _to_hashtag(self, value: str):
        cleaned = re.sub(r"[^A-Za-z0-9]+", "", value)
        if not cleaned:
            return None

        return f"#{cleaned}"

    def _build_hashtags(
        self,
        topic: str,
        organisation: str,
    ):
        hashtags = []
        seen = set()

        def add(tag: str | None):
            if tag and tag not in seen:
                hashtags.append(tag)
                seen.add(tag)

        if organisation:
            add(self._to_hashtag(organisation))
            if "SBI" in organisation.upper():
                add("#SBI")
            if "Bank" in organisation:
                add("#BankJobs")

        if topic:
            if "Recruitment" in topic:
                add("#Recruitment")

        for tag in [
            "#GovernmentJobs",
            "#JobAlert",
            "#CareerOpportunity",
        ]:
            add(tag)

        if len(hashtags) < 6:
            add("#Jobs")
            add("#Vacancy")

        return hashtags[:8]

    def _build_reel_details_text(
        self,
        input_dir: Path,
        reel_path: Path,
    ):
        carousel = self._load_json_file(
            input_dir / "carousel.json"
        )
        facts = self._load_json_file(
            input_dir / "facts.json"
        )

        topic = (
            carousel.get("topic")
            or facts.get("recruitment_name")
            or input_dir.name
        )
        organisation = (
            carousel.get("organisation")
            or facts.get("organisation")
            or "Unknown organisation"
        )

        vacancies = facts.get("total_vacancies")
        if vacancies is None:
            vacancies = self._lookup_card_value(
                carousel.get("slides", []),
                "Vacancies",
            )

        deadline = facts.get("application_end")
        if deadline is None:
            deadline = self._lookup_card_value(
                carousel.get("slides", []),
                "deadline",
            )

        relevant_urls = self._collect_urls(facts)

        hashtags = self._build_hashtags(
            topic,
            organisation,
        )

        lines = [
            f"Job title: {topic}",
            f"Organisation: {organisation}",
            f"Vacancies: {vacancies if vacancies is not None else 'Not provided'}",
            f"Application deadline: {deadline if deadline is not None else 'Not provided'}",
            "",
            "Relevant URLs:",
        ]

        if relevant_urls:
            lines.extend(f"- {url}" for url in relevant_urls)
        else:
            lines.append("- No URLs were found in carousel.json or facts.json.")

        lines.extend(
            [
                "",
                "Relevant hashtags:",
                ", ".join(hashtags),
            ]
        )

        text_path = reel_path.parent / "reel_details.txt"
        text_path.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )

        return text_path

    def create(
        self,
        input_dir_string: str,
        music_path_string: str | None = None,
    ):
        input_dir = Path(
            input_dir_string
        ).expanduser().resolve()

        music_path = (
            Path(music_path_string).expanduser().resolve()
            if music_path_string
            else choose_random_music(MUSIC_DIR)
        )

        print(f"Selected background music: {music_path}")

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
            music_path,
        )

        details_path = self._build_reel_details_text(
            input_dir,
            reel_path,
        )

        return {
            "input_dir": str(input_dir),
            "slides": [
                str(p) for p in slides
            ],
            "reel": str(reel_path),
            "reel_details_file": str(details_path),
            "seconds_per_slide": 4,
            "duration_seconds": 24,
            "resolution": "1080x1920",
            "fps": 30,
            "music": str(music_path) if music_path else None,
        }

    def publish(
        self,
        input_dir_string: str,
        caption: str,
        music_path_string: str | None = None,
    ):
        self.config.validate()

        input_dir = Path(
            input_dir_string
        ).expanduser().resolve()

        music_path = (
            Path(music_path_string).expanduser().resolve()
            if music_path_string
            else choose_random_music(MUSIC_DIR)
        )

        print(f"Selected background music: {music_path}")

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
                music_path,
            )
        else:
            print(
                f"Using existing Reel video: "
                f"{reel_path}"
            )

        details_path = self._build_reel_details_text(
            input_dir,
            reel_path,
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
            "reel_details_file": str(details_path),
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
