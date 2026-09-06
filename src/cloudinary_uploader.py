from pathlib import Path
import cloudinary
import cloudinary.uploader


class CloudinaryUploader:
    def __init__(
        self,
        cloud_name: str,
        api_key: str,
        api_secret: str,
        folder: str,
    ):
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )
        self.folder = folder

    def upload_video(self, path: Path, public_id: str):
        return cloudinary.uploader.upload(
            str(path),
            resource_type="video",
            folder=self.folder,
            public_id=public_id,
        )
