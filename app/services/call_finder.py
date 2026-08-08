from app.models.events import ParsedEvent
from app.services.normalizer import EventNormalizer


class CallFinder:

    def __init__(self, events: list[ParsedEvent]):
        self.events = events

    def search(
        self,
        number: str | None = None,
        direction: str | None = None,
        tenant: str | None = None,
    ) -> list[dict]:

        normalized_number = (
            EventNormalizer._normalize_number(number)
            if number
            else None
        )

        calls: dict[str, dict] = {}

        for event in self.events:

            # A call starts from the customer's inbound channel.
            if event.event_name != "CHANNEL_CREATE":
                continue

            if event.call_direction != "inbound":
                continue

            if not event.uuid:
                continue

            if normalized_number:
                if event.caller_number != normalized_number:
                    continue

            if direction:
                if event.call_direction != direction:
                    continue

            event_tenant = self._get_tenant(event)

            if tenant and event_tenant != tenant:
                continue

            if event.uuid in calls:
                continue

            calls[event.uuid] = {
                "call_id": event.uuid,
                "uuid": event.uuid,
                "timestamp": event.timestamp,
                "caller_number": event.caller_number,
                "destination_number": event.destination_number,
                "direction": event.call_direction,
                "tenant": event_tenant,
            }

        return sorted(
            calls.values(),
            key=lambda call: call["timestamp"],
        )

    @staticmethod
    def _get_tenant(
        event: ParsedEvent,
    ) -> str | None:

        possible_fields = (
            "variable_sip_h_X-SCUD-TENANT",
            "variable_tenant",
            "Tenant",
            "tenant",
        )

        for field in possible_fields:

            value = event.data.get(field)

            if value:
                return str(value).strip()

        return None