"""
NV Optimizer 2.0 - Logger estruturado
Registra todas as operações em formato estruturado.
"""

import csv
import json
import os
import threading
from datetime import datetime
from collections import deque


class StructuredLogger:
    """Logger estruturado que registra operações em JSON + CSV."""

    def __init__(self, log_dir: str = None):
        if log_dir is None:
            appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
            log_dir = os.path.join(appdata, "NVOptimizer", "logs")
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

        self._lock = threading.Lock()
        self._session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        self._json_path = os.path.join(self.log_dir, f"nv-optimizer-{self._session_id}.json")
        self._csv_path = os.path.join(self.log_dir, f"nv-optimizer-{self._session_id}.csv")
        self._recent = deque(maxlen=200)

        self._init_csv()

    def _init_csv(self):
        with open(self._csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "operation", "module", "command",
                "previous_state", "new_state", "status", "error",
            ])

    def log(
        self,
        operation: str,
        module: str = "",
        command: str = "",
        previous_state: str = "",
        new_state: str = "",
        status: str = "info",
        error: str = "",
        details: dict = None,
    ):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "module": module,
            "command": command,
            "previous_state": previous_state,
            "new_state": new_state,
            "status": status,
            "error": error,
            "session_id": self._session_id,
        }
        if details:
            entry["details"] = details

        with self._lock:
            with open(self._json_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
            with open(self._csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    entry["timestamp"],
                    operation,
                    module,
                    command,
                    previous_state,
                    new_state,
                    status,
                    error,
                ])
            self._recent.append(entry)

    def success(self, operation: str, module: str = "general",
                command: str = "", previous_state: str = "",
                new_state: str = "", details: dict = None):
        self.log(operation, module, command, previous_state, new_state,
                 "success", details=details)

    def error(self, operation: str, error: str, module: str = "general",
              command: str = ""):
        self.log(operation, module, command, error=error, status="error")

    def warning(self, operation: str, message: str, module: str = "general",
                command: str = ""):
        self.log(operation, module, command, new_state=message, status="warning")

    def info(self, operation: str, message: str, module: str = "general",
             command: str = "", previous_state: str = "", new_state: str = ""):
        self.log(operation, module, command, previous_state, new_state,
                 "info", error=message if message else "")

    def get_logs(self, limit: int = 200) -> list:
        with self._lock:
            logs = list(self._recent)[-limit:]
            return logs

    def get_log_paths(self) -> dict:
        return {"json": self._json_path, "csv": self._csv_path}


logger = StructuredLogger()