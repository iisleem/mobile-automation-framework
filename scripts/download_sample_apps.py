from __future__ import annotations

import argparse
from pathlib import Path
import sys
from urllib.request import urlretrieve


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.config_reader import ConfigReader


def main() -> int:
    parser = argparse.ArgumentParser(description="Download sample apps used by runnable examples.")
    parser.add_argument("--android", action="store_true", help="Download Android TheApp APK.")
    parser.add_argument("--ios", action="store_true", help="Download iOS TheApp simulator app zip.")
    parser.add_argument("--all", action="store_true", help="Download Android and iOS sample apps.")
    args = parser.parse_args()

    if not args.android and not args.ios and not args.all:
        parser.print_help()
        return 0

    settings = ConfigReader(PROJECT_ROOT).read_settings()
    if args.android or args.all:
        _download(settings["sample_apps"]["the_app_android_url"], PROJECT_ROOT / "apps" / "TheApp.apk")
    if args.ios or args.all:
        _download(settings["sample_apps"]["the_app_ios_url"], PROJECT_ROOT / "apps" / "TheApp.app.zip")
    return 0


def _download(url: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url}")
    urlretrieve(url, output)
    print(f"Saved {output}")


if __name__ == "__main__":
    raise SystemExit(main())
