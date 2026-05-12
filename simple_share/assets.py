import shutil
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
STATIC_DIR = PACKAGE_DIR / "static"


def publish_static_assets(output_dir: Path) -> None:
    target_dir = output_dir / "static"
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(STATIC_DIR, target_dir)
