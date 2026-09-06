from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Config:
    meta_api_version: str = os.getenv("META_API_VERSION", "v26.0")
    meta_user_access_token: str = os.getenv("META_USER_ACCESS_TOKEN", "")
    meta_page_id: str = os.getenv("META_PAGE_ID", "")
    meta_page_name: str = os.getenv("META_PAGE_NAME", "")

    cloudinary_cloud_name: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    cloudinary_api_key: str = os.getenv("CLOUDINARY_API_KEY", "")
    cloudinary_api_secret: str = os.getenv("CLOUDINARY_API_SECRET", "")
    cloudinary_folder: str = os.getenv(
        "CLOUDINARY_FOLDER",
        "shaktidootam/instagram_reels",
    )

    data_dir: Path = ROOT / "data"

    def validate_meta(self):
        missing = []

        if not self.meta_user_access_token:
            missing.append("META_USER_ACCESS_TOKEN")

        if not self.meta_page_id:
            missing.append("META_PAGE_ID")

        if missing:
            raise RuntimeError(
                "Missing Meta settings in .env: "
                + ", ".join(missing)
            )

    def validate_cloudinary(self):
        missing = []

        for name, value in [
            ("CLOUDINARY_CLOUD_NAME", self.cloudinary_cloud_name),
            ("CLOUDINARY_API_KEY", self.cloudinary_api_key),
            ("CLOUDINARY_API_SECRET", self.cloudinary_api_secret),
        ]:
            if not value:
                missing.append(name)

        if missing:
            raise RuntimeError(
                "Missing Cloudinary settings in .env: "
                + ", ".join(missing)
            )

    def validate(self):
        self.validate_meta()
        self.validate_cloudinary()

    @property
    def graph_base(self):
        version = self.meta_api_version
        if not version.startswith("v"):
            version = "v" + version
        return f"https://graph.facebook.com/{version}"
