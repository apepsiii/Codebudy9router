"""
V2Fun.ai SSE Monitor
Real-time generation status monitoring via Server-Sent Events

Usage:
    from v2fun_scripts.sse_monitor import SSEMonitor
    
    monitor = SSEMonitor(token)
    monitor.watch(task_uuid, on_update=callback, on_done=done_callback)
"""

import json
import threading
import requests
from typing import Callable, Optional


class SSEMonitor:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.prod.v2fun.ai"
        self.sse_url = f"{self.base_url}/ums/external/sse?token={token}"
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._watchers: dict = {}

    def watch(
        self,
        task_uuid: str,
        on_update: Optional[Callable] = None,
        on_done: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ):
        """Register a task to watch"""
        self._watchers[task_uuid] = {
            "on_update": on_update,
            "on_done": on_done,
            "on_error": on_error,
            "done": False
        }
        
        if self._thread is None or not self._thread.is_alive():
            self._start()

    def _start(self):
        """Start SSE listener thread"""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop SSE listener"""
        self._stop_event.set()

    def _listen(self):
        """Listen to SSE stream"""
        try:
            response = requests.get(
                self.sse_url,
                stream=True,
                timeout=300,
                headers={
                    "Accept": "text/event-stream",
                    "Cache-Control": "no-cache"
                }
            )
            response.raise_for_status()

            buffer = ""
            for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                if self._stop_event.is_set():
                    break

                buffer += chunk
                while "\n\n" in buffer:
                    event_str, buffer = buffer.split("\n\n", 1)
                    self._parse_event(event_str)

                # Stop if all watchers are done
                if self._watchers and all(w["done"] for w in self._watchers.values()):
                    break

        except Exception as e:
            for task_uuid, watcher in self._watchers.items():
                if not watcher["done"] and watcher.get("on_error"):
                    watcher["on_error"](task_uuid, str(e))

    def _parse_event(self, event_str: str):
        """Parse SSE event and dispatch to watchers"""
        data = None
        for line in event_str.strip().splitlines():
            if line.startswith("data:"):
                raw = line[5:].strip()
                if raw and raw != ":heartbeat":
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        pass

        if not data:
            return

        # Try to match event to a watcher by taskId
        task_id = (
            data.get("taskId") or
            data.get("task_id") or
            data.get("taskUuid") or
            data.get("taskuuid")
        )

        for task_uuid, watcher in self._watchers.items():
            if watcher["done"]:
                continue

            # Match by taskId or broadcast to all
            if task_id and str(task_id) != str(task_uuid):
                continue

            status = data.get("status", "").upper()
            progress = data.get("progress", 0)
            work_url = data.get("workUrl") or data.get("work_url")
            thumb = data.get("thumb") or data.get("thumbnail")

            if watcher.get("on_update"):
                watcher["on_update"](task_uuid, {
                    "status": status,
                    "progress": progress,
                    "work_url": work_url,
                    "thumb": thumb,
                    "raw": data
                })

            if status in ("C", "COMPLETED", "DONE", "SUCCESS", "F", "FAILED", "ERROR"):
                watcher["done"] = True
                if watcher.get("on_done"):
                    watcher["on_done"](task_uuid, {
                        "status": status,
                        "work_url": work_url,
                        "thumb": thumb,
                        "raw": data
                    })
