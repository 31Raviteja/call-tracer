import ast
from datetime import datetime

from app.models.events import RawEvent


class EventParser:

    def parse(self, line: str) -> RawEvent | None:
        line = line.strip()

        if "#:EVENT[" not in line:
            return None

        try:
            timestamp_text, event_text = line.split(
                "#:EVENT['freeswitch']:",
                1,
            )
        except ValueError:
            return None

        timestamp_text = timestamp_text.strip()
        event_text = event_text.strip()

        try:
            timestamp = datetime.fromisoformat(timestamp_text)
        except ValueError:
            return None

        try:
            data = ast.literal_eval(event_text)
        except (ValueError, SyntaxError):
            return None

        if not isinstance(data, dict):
            return None

        return RawEvent(
            timestamp=timestamp,
            data=data,
        )