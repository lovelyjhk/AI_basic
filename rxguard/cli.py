from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List, Optional

from .config import AppConfig
from .repo import Repo
from .canary import CanaryManager
from .logging_utils import get_logger


logger = get_logger("rxguard")


def load_or_init_config(args: argparse.Namespace) -> AppConfig:
    if args.command == "init":
        repo_dir = os.path.abspath(args.repo)
        data_dirs = [os.path.abspath(d) for d in args.data]
        config = AppConfig.default(repo_dir, data_dirs)
        # create structure and key
        repo = Repo.init_repo(config)
        # deploy canaries
        canary = CanaryManager(config)
        canary.deploy(per_dir=args.canaries)
        # save config
        config_path = os.path.join(repo_dir, "config.yml")
        config.save(config_path)
        print(f"Initialized repository at {repo_dir}. Config: {config_path}")
        return config

    # other commands load config from path
    config_path = os.path.abspath(args.config)
    config = AppConfig.load(config_path)
    return config


def cmd_snapshot(config: AppConfig, label: Optional[str]) -> None:
    repo = Repo(config)
    repo.load()
    snap = repo.create_snapshot(label=label)
    print(f"Snapshot {snap.id} created with {len(snap.files)} files")


def cmd_restore(config: AppConfig, snapshot_id: str, dest: str, paths: Optional[List[str]]) -> None:
    repo = Repo(config)
    repo.load()
    repo.restore(snapshot_id, dest, include_prefixes=paths)
    print(f"Restored snapshot {snapshot_id} to {dest}")


def cmd_list(config: AppConfig, files: bool) -> None:
    repo = Repo(config)
    snaps = repo.list_snapshots()
    if not files:
        for s in snaps:
            print(s)
    else:
        for s in snaps:
            snap = repo.load_snapshot(s)
            print(f"{s} ({len(snap.files)} files)")
            for fe in snap.files[:50]:
                print("  ", fe.path, "chunks=", len(fe.chunks))
            if len(snap.files) > 50:
                print("  ...")


def cmd_verify(config: AppConfig, snapshot_id: Optional[str]) -> None:
    repo = Repo(config)
    files, missing = repo.verify(snapshot_id)
    if missing == 0:
        print(f"OK: {files} files, no missing chunks")
    else:
        print(f"WARN: {files} files, missing chunks: {missing}")


def cmd_protect(config: AppConfig) -> None:
    from .watcher import RansomwareWatcher

    repo = Repo(config)
    repo.load()
    canary = CanaryManager(config)
    watcher = RansomwareWatcher(config, repo, canary)
    watcher.run()


def cmd_simulate(config: AppConfig, target: Optional[str], count: int) -> None:
    import random
    import time

    victim_dirs = [target] if target else config.data_dirs
    files: List[str] = []
    for d in victim_dirs:
        for root, _, names in os.walk(d):
            for n in names:
                files.append(os.path.join(root, n))
    random.shuffle(files)
    modified = 0
    for p in files[:count]:
        try:
            with open(p, "rb") as f:
                data = f.read()
            # simple xor mutate to increase entropy but keep recoverability for demo
            mutated = bytes(b ^ 0x5A for b in data)
            with open(p + ".locked", "wb") as f:
                f.write(mutated)
            modified += 1
            time.sleep(0.01)
        except Exception:
            continue
    print(f"Simulated modification of {modified} files (non-destructive copies with .locked)")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="rxguard", description="Ransomware defense MVP for healthcare")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("init", help="Initialize repository and deploy canaries")
    sp.add_argument("--repo", required=True, help="Repository directory")
    sp.add_argument("--data", required=True, nargs="+", help="One or more data directories to protect")
    sp.add_argument("--canaries", type=int, default=3, help="Number of canaries per data directory")
    sp.set_defaults(func=lambda a: load_or_init_config(a))

    sp = sub.add_parser("snapshot", help="Create snapshot")
    sp.add_argument("--config", required=True, help="Path to config.yml")
    sp.add_argument("--label", help="Optional snapshot label")
    sp.set_defaults(func=lambda a: cmd_snapshot(AppConfig.load(os.path.abspath(a.config)), a.label))

    sp = sub.add_parser("restore", help="Restore snapshot to destination")
    sp.add_argument("--config", required=True, help="Path to config.yml")
    sp.add_argument("--snapshot", required=True, help="Snapshot ID")
    sp.add_argument("--dest", required=True, help="Destination directory")
    sp.add_argument("--paths", nargs="*", help="Optional path prefixes to include")
    sp.set_defaults(func=lambda a: cmd_restore(AppConfig.load(os.path.abspath(a.config)), a.snapshot, a.dest, a.paths))

    sp = sub.add_parser("list", help="List snapshots")
    sp.add_argument("--config", required=True, help="Path to config.yml")
    sp.add_argument("--files", action="store_true", help="Show files in each snapshot")
    sp.set_defaults(func=lambda a: cmd_list(AppConfig.load(os.path.abspath(a.config)), a.files))

    sp = sub.add_parser("verify", help="Verify manifests and chunk presence")
    sp.add_argument("--config", required=True, help="Path to config.yml")
    sp.add_argument("--snapshot", help="Specific snapshot ID to verify")
    sp.set_defaults(func=lambda a: cmd_verify(AppConfig.load(os.path.abspath(a.config)), a.snapshot))

    sp = sub.add_parser("protect", help="Run realtime watcher and create auto snapshots on alerts")
    sp.add_argument("--config", required=True, help="Path to config.yml")
    sp.set_defaults(func=lambda a: cmd_protect(AppConfig.load(os.path.abspath(a.config))))

    sp = sub.add_parser("simulate", help="Simulate suspicious activity (non-destructive)")
    sp.add_argument("--config", required=True, help="Path to config.yml")
    sp.add_argument("--target", help="Optional specific directory to simulate in")
    sp.add_argument("--count", type=int, default=200, help="Number of files to affect")
    sp.set_defaults(func=lambda a: cmd_simulate(AppConfig.load(os.path.abspath(a.config)), a.target, a.count))

    return p


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = args.func(args)
    if result is not None:
        # some subcommands return the config
        pass

