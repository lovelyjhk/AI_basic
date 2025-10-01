import argparse
import os
import signal
import socket
import sys
import threading
import time
from typing import Optional

import requests
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent, FileMovedEvent, FileDeletedEvent
from watchdog.observers import Observer


class AgentConfig:
    def __init__(self, server_url: str, watch_path: str, agent_id: str) -> None:
        self.server_url = server_url.rstrip('/')
        self.watch_path = watch_path
        self.agent_id = agent_id
        self.host = socket.gethostname()


class AgentEventHandler(FileSystemEventHandler):
    def __init__(self, config: AgentConfig) -> None:
        super().__init__()
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _post(self, event_type: str, path: str) -> None:
        try:
            payload = {
                "event_type": event_type,
                "path": path,
                "host": self.config.host,
                "agent_id": self.config.agent_id,
                # server supplies ts if missing; send for demo ordering
                "ts": time.time(),
            }
            url = f"{self.config.server_url}/api/events"
            self.session.post(url, json=payload, timeout=2)
        except Exception:
            # Best-effort for demo; avoid crashing on transient errors
            pass

    def on_created(self, event: FileCreatedEvent) -> None:
        if not event.is_directory:
            self._post("created", event.src_path)

    def on_modified(self, event: FileModifiedEvent) -> None:
        if not event.is_directory:
            self._post("modified", event.src_path)

    def on_moved(self, event: FileMovedEvent) -> None:
        if not event.is_directory:
            self._post("moved", f"{event.src_path} -> {event.dest_path}")

    def on_deleted(self, event: FileDeletedEvent) -> None:
        if not event.is_directory:
            self._post("deleted", event.src_path)


def run_agent(config: AgentConfig) -> None:
    os.makedirs(config.watch_path, exist_ok=True)
    handler = AgentEventHandler(config)
    observer = Observer()
    observer.schedule(handler, path=config.watch_path, recursive=True)
    observer.start()

    stop_event = threading.Event()

    def handle_signal(signum: int, frame: Optional[object]) -> None:
        stop_event.set()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    print(f"[agent] watching: {config.watch_path} -> {config.server_url}")
    try:
        while not stop_event.is_set():
            time.sleep(0.2)
    finally:
        observer.stop()
        observer.join(timeout=5)
        print("[agent] stopped")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RansomShield demo agent")
    parser.add_argument("--server", default="http://127.0.0.1:8000", help="Server base URL")
    parser.add_argument("--path", default="/workspace/demo_dir", help="Directory to watch")
    parser.add_argument("--agent-id", default="agent-1", help="Agent identifier")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    cfg = AgentConfig(server_url=args.server, watch_path=args.path, agent_id=args.agent_id)
    run_agent(cfg)

