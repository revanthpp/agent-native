from __future__ import annotations

from datetime import datetime, timezone


class ReplayStore:
    def __init__(self, window_seconds: int = 300, max_entries: int = 10000): self.window_seconds, self.max_entries, self._seen = window_seconds, max_entries, {}
    def check_and_record(self, *, context: str, nonce: str, created: int, now: int | None = None):
        current=now or int(datetime.now(timezone.utc).timestamp())
        if abs(current-created)>self.window_seconds: return False, "timestamp_outside_window"
        key=(context, nonce)
        if key in self._seen: return False, "replay_detected"
        self._seen[key]=created
        if len(self._seen)>self.max_entries: self._seen={k:v for k,v in self._seen.items() if v >= current-self.window_seconds}
        return True, "fresh"
