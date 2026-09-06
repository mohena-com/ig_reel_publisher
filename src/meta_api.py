from __future__ import annotations

import time
from dataclasses import dataclass

import requests


@dataclass
class InstagramAccount:
    page_id: str
    page_name: str
    page_access_token: str
    ig_user_id: str


class MetaAPI:
    def __init__(self, api_version: str):
        version = api_version
        if not version.startswith("v"):
            version = "v" + version

        self.base = f"https://graph.facebook.com/{version}"

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "ig-reel-publisher/1.0",
            }
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        params=None,
        data=None,
    ):
        response = self.session.request(
            method,
            self.base + path,
            params=params,
            data=data,
            timeout=60,
        )

        try:
            payload = response.json()
        except Exception:
            payload = {"raw": response.text}

        if not response.ok:
            raise RuntimeError(
                f"Meta API error {response.status_code}: {payload}"
            )

        return payload

    def discover_page(
        self,
        user_access_token: str,
        page_id: str,
    ):
        return self._request(
            "GET",
            f"/{page_id}",
            params={
                "fields": (
                    "id,name,access_token,"
                    "instagram_business_account"
                ),
                "access_token": user_access_token,
            },
        )

    def choose_account(
        self,
        user_access_token: str,
        page_name: str,
        page_id: str,
    ) -> InstagramAccount:

        page = self.discover_page(
            user_access_token,
            page_id,
        )

        if page.get("id") != page_id:
            raise RuntimeError(
                f"Meta returned unexpected Page ID: "
                f"{page.get('id')}"
            )

        actual_name = page.get("name", "")

        if (
            page_name
            and actual_name.strip().lower()
            != page_name.strip().lower()
        ):
            raise RuntimeError(
                f"Configured Page name '{page_name}' does not "
                f"match Meta Page name '{actual_name}'."
            )

        page_access_token = page.get("access_token")

        if not page_access_token:
            raise RuntimeError(
                "Meta did not return a Page Access Token."
            )

        instagram = page.get(
            "instagram_business_account"
        ) or {}

        ig_user_id = instagram.get("id")

        if not ig_user_id:
            raise RuntimeError(
                "The configured Facebook Page has no linked "
                "Instagram Professional account."
            )

        return InstagramAccount(
            page_id=page["id"],
            page_name=actual_name,
            page_access_token=page_access_token,
            ig_user_id=ig_user_id,
        )

    def create_reel_container(
        self,
        ig_user_id: str,
        page_access_token: str,
        video_url: str,
        caption: str,
    ):
        return self._request(
            "POST",
            f"/{ig_user_id}/media",
            data={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "access_token": page_access_token,
            },
        )

    def container_status(
        self,
        container_id: str,
        page_access_token: str,
    ):
        return self._request(
            "GET",
            f"/{container_id}",
            params={
                "fields": "status_code,status",
                "access_token": page_access_token,
            },
        )

    def wait_until_ready(
        self,
        container_id: str,
        page_access_token: str,
        timeout_seconds: int = 600,
        poll_seconds: int = 10,
    ):
        deadline = time.time() + timeout_seconds
        last = None

        while time.time() < deadline:
            last = self.container_status(
                container_id,
                page_access_token,
            )

            code = str(
                last.get("status_code", "")
            ).upper()

            if code in {"FINISHED", "PUBLISHED"}:
                return last

            if code == "ERROR":
                raise RuntimeError(
                    f"Instagram Reel container failed: {last}"
                )

            time.sleep(poll_seconds)

        raise TimeoutError(
            "Instagram Reel did not become ready within "
            f"{timeout_seconds}s. Last status: {last}"
        )

    def publish(
        self,
        ig_user_id: str,
        page_access_token: str,
        creation_id: str,
    ):
        return self._request(
            "POST",
            f"/{ig_user_id}/media_publish",
            data={
                "creation_id": creation_id,
                "access_token": page_access_token,
            },
        )
