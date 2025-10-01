import argparse
import os
import random
import shutil
import string
import time
from pathlib import Path


def random_text(size: int) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choice(alphabet) for _ in range(size))


def write_file(path: Path, size: int = 2048) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        f.write(random_text(size))


def simulate_activity(root: Path, files: int, pace: float) -> None:
    print(f"[sim] generating activity in {root} ({files} files, pace={pace}s)")
    root.mkdir(parents=True, exist_ok=True)
    created = []

    # Phase 1: create files
    for i in range(files):
        p = root / f"doc_{i:03d}.txt"
        write_file(p, size=1024 + (i % 5) * 512)
        created.append(p)
        time.sleep(pace)

    # Phase 2: modify and rename some files rapidly (emulate encryption)
    for i, p in enumerate(created):
        if not p.exists():
            continue
        # Overwrite with high-entropy-like content
        with p.open('wb') as f:
            f.write(os.urandom(4096))
        enc = p.with_suffix(p.suffix + ".encrypted")
        try:
            p.rename(enc)
        except Exception:
            # If rename fails on some FS, copy instead
            shutil.copy2(p, enc)
        time.sleep(max(0.01, pace / 4))

    # Phase 3: delete a subset
    for i, p in enumerate(list(root.glob("*.encrypted"))[: max(1, files // 10) ]):
        try:
            p.unlink()
        except Exception:
            pass
        time.sleep(max(0.01, pace / 6))

    print("[sim] done")


def main() -> None:
    parser = argparse.ArgumentParser(description="RansomShield demo simulator")
    parser.add_argument("--path", default="/workspace/demo_dir", help="Directory to manipulate")
    parser.add_argument("--files", type=int, default=40, help="Number of files to create/modify")
    parser.add_argument("--pace", type=float, default=0.02, help="Seconds between operations during creation")
    args = parser.parse_args()

    simulate_activity(Path(args.path), files=args.files, pace=args.pace)


if __name__ == "__main__":
    main()

