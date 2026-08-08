from collections.abc import Iterator
from pathlib import Path


class LogReader:
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir

    def iter_event_lines(self) -> Iterator[str]:
        if not self.log_dir.exists():
            return

        for log_file in sorted(self.log_dir.glob("*.log")):
            if not log_file.is_file():
                continue

            try:
                with log_file.open(
                    "r",
                    encoding="utf-8",
                    errors="replace",
                ) as file:

                    for line in file:
                        line = line.strip()

                        if not line:
                            continue

                        if "#:EVENT" not in line:
                            continue

                        yield line

            except OSError:
                continue