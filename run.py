from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.config import Config
from src.publisher import ReelPublisher


def main():
    parser = argparse.ArgumentParser(
        description="Standalone Instagram Reel publisher"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    for command in ("create", "publish"):
        p = sub.add_parser(command)
        p.add_argument("--job-id", required=True)
        p.add_argument("--caption", default="")

    status = sub.add_parser("status")
    status.add_argument("--job-id", required=True)

    args = parser.parse_args()

    if args.command == "status":
        path = Path("/app/data/publications.json")
        if not path.exists():
            print("No publication ledger yet.")
            return
        data = json.loads(path.read_text())
        record = data.get(args.job_id)
        print(json.dumps(record, indent=2) if record else f"No record for {args.job_id}")
        return

    config = Config()
    publisher = ReelPublisher(config)

    try:
        if args.command == "create":
            result = publisher.create(args.job_id)
        else:
            result = publisher.publish(args.job_id, args.caption)

        print(json.dumps(result, indent=2))
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
