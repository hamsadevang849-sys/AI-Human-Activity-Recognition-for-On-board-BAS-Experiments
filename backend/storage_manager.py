"""
Local Storage and Structured Text Log Manager for BAS HAR.
"""
import os
from datetime import datetime
from typing import List
from .models import LogEntry, StorageInfo, StorageFile

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage")

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(STORAGE_DIR, exist_ok=True)

AUDIT_LOG_FILE = os.path.join(LOGS_DIR, "bas_exp_audit.txt")

DEFAULT_LOGS = [
    LogEntry(timestamp="10:42:13", step="STEP 01", activity="Astronaut entered experiment zone. Suction seal confirmed nominal.", status="VALIDATED", outcome="NOMINAL_AUDIT"),
    LogEntry(timestamp="10:42:27", step="STEP 02", activity="Sample container retrieved from cryo-bay.", status="VALIDATED", outcome="NOMINAL_AUDIT")
]

class StorageManager:
    def __init__(self):
        self.logs: List[LogEntry] = list(DEFAULT_LOGS)
        self.recording_active = True
        self.total_capacity_gb = 4000.0
        self.used_capacity_gb = 1640.0
        self.files = [
            StorageFile(filename="EXPERIMENT_001.mp4", duration="01:24:32", size_mb=412, recorded_at="2026-09-25 09:15"),
            StorageFile(filename="EXPERIMENT_002.mp4", duration="00:48:21", size_mb=248, recorded_at="2026-09-25 10:30")
        ]
        self._sync_log_file()

    def add_log(self, step: str, activity: str, status: str, outcome: str = "NOMINAL_AUDIT") -> LogEntry:
        now_time = datetime.now().strftime("%H:%M:%S")
        entry = LogEntry(
            timestamp=now_time,
            step=step,
            activity=activity,
            status=status,
            outcome=outcome
        )
        self.logs.append(entry)
        self._sync_log_file()
        return entry

    def get_logs(self) -> List[LogEntry]:
        return self.logs

    def export_structured_text(self) -> str:
        header = (
            "============================================================\n"
            "AI HUMAN ACTIVITY RECOGNITION — EXPERIMENT AUDIT LOG\n"
            "MISSION: BAS-EXP-001 | SYSTEM: ON-BOARD STANDALONE EDGE AI\n"
            "FORMAT: timestamp | step | activity | status | outcome\n"
            "============================================================\n\n"
        )
        lines = [header]
        for l in self.logs:
            lines.append(f"[{l.timestamp}] | {l.step} | {l.activity} | {l.status} | {l.outcome}\n")
        return "".join(lines)

    def _sync_log_file(self):
        try:
            with open(AUDIT_LOG_FILE, "w", encoding="utf-8") as f:
                f.write(self.export_structured_text())
        except Exception:
            pass

    def get_storage_info(self) -> StorageInfo:
        free_gb = self.total_capacity_gb - self.used_capacity_gb
        pct_free = round((free_gb / self.total_capacity_gb) * 100, 1)
        return StorageInfo(
            total_capacity_gb=self.total_capacity_gb,
            used_capacity_gb=self.used_capacity_gb,
            free_capacity_gb=free_gb,
            percent_free=pct_free,
            recording_active=self.recording_active,
            files=self.files
        )

    def toggle_recording(self) -> bool:
        self.recording_active = not self.recording_active
        return self.recording_active

storage_manager = StorageManager()
