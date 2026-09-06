from __future__ import annotations

import json
from pathlib import Path


class PublicationLedger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _load(self):
        if not self.path.exists():
            return {}

        return json.loads(
            self.path.read_text(
                encoding="utf-8"
            )
        )

    def get(self, job_id: str):
        return self._load().get(job_id)

    def record(
        self,
        job_id: str,
        record: dict,
    ):
        data = self._load()
        data[job_id] = record

        self.path.write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
