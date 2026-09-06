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
        "CLOUDINARY_FOLDER", "shaktidootam/instagram_reels"
    )

    data_dir: Path = ROOT / "data"

    def validate(self):
        missing = []
        for name, value in [
            ("META_USER_ACCESS_TOKEN", self.meta_user_access_token),
            ("META_PAGE_ID", self.meta_page_id),
            ("CLOUDINARY_CLOUD_NAME", self.cloudinary_cloud_name),
            ("CLOUDINARY_API_KEY", self.cloudinary_api_key),
            ("CLOUDINARY_API_SECRET", self.cloudinary_api_secret),
        ]:
            if not value:
                missing.append(name)

        if missing:
            raise RuntimeError(
                "Missing settings in .env: " + ", ".join(missing)
            )

    @property
    def graph_base(self):
        version = self.meta_api_version
        if not version.startswith("v"):
            version = "v" + version
        return f"https://graph.facebook.com/{version}"
