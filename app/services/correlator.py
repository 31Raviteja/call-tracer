from collections import defaultdict

from app.models.events import ParsedEvent


class CallCorrelator:

    def __init__(self, events: list[ParsedEvent]):
        self.events = events
        self.graph = self._build_graph()

    def _build_graph(self) -> dict[str, set[str]]:
        graph: dict[str, set[str]] = defaultdict(set)

        for event in self.events:

            if not event.uuid:
                continue

            related_uuids = {
                event.cc_member_session_uuid,
                event.cc_member_uuid,
            }

            for related_uuid in related_uuids:

                if not related_uuid:
                    continue

                if related_uuid == event.uuid:
                    continue

                graph[event.uuid].add(related_uuid)
                graph[related_uuid].add(event.uuid)

        return graph

    def correlate(self, root_uuid: str) -> set[str]:

        if not root_uuid:
            return set()

        visited: set[str] = set()
        stack: list[str] = [root_uuid]

        while stack:

            current_uuid = stack.pop()

            if current_uuid in visited:
                continue

            visited.add(current_uuid)

            for related_uuid in self.graph.get(
                current_uuid,
                set(),
            ):
                if related_uuid not in visited:
                    stack.append(related_uuid)

        return visited