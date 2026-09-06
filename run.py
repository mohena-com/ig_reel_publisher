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

    create = sub.add_parser(
        "create",
        help="Create the 24-second Reel MP4 only; do not publish.",
    )
    create.add_argument("--input-dir", required=True)

    publish = sub.add_parser(
        "publish",
        help="Create/upload/publish the Reel.",
    )
    publish.add_argument("--input-dir", required=True)
    publish.add_argument("--caption", required=True)
    publish.add_argument(
        "--publish",
        action="store_true",
        help="Required confirmation that the Reel may be published.",
    )

    status = sub.add_parser("status", help="Show local publication status.")
    status.add_argument("--job-id", required=True)

    args = parser.parse_args()

    config = Config()
    publisher = ReelPublisher(config)

    try:
        if args.command == "create":
            result = publisher.create(args.input_dir)

        elif args.command == "publish":
            if not args.publish:
                raise RuntimeError(
                    "Publishing requires the --publish flag."
                )
            result = publisher.publish(
                args.input_dir,
                args.caption,
            )

        else:
            result = publisher.status(args.job_id)

        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
