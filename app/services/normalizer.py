from app.models.events import ParsedEvent, RawEvent


class EventNormalizer:

    def normalize(self, event: RawEvent) -> ParsedEvent:
        data = event.data

        return ParsedEvent(
            timestamp=event.timestamp,
            event_name=str(
                data.get("Event-Name", "")
            ),

            uuid=self._text(
                data.get("Unique-ID")
            ),

            call_direction=self._text(
                data.get("Call-Direction")
            ),

            caller_number=self._normalize_number(
                data.get("Caller-Caller-ID-Number")
            ),

            destination_number=self._normalize_number(
                data.get("Caller-Destination-Number")
            ),

            event_timestamp=self._integer(
                data.get("Event-Date-Timestamp")
            ),

            event_subclass=self._text(
                data.get("Event-Subclass")
            ),

            cc_action=self._text(
                data.get("CC-Action")
            ),

            cc_queue=self._text(
                data.get("CC-Queue")
                or data.get("variable_cc_queue")
            ),

            cc_agent=self._text(
                data.get("CC-Agent")
                or data.get("variable_cc_agent")
            ),

            cc_member_uuid=self._text(
                data.get("CC-Member-UUID")
                or data.get("variable_cc_member_uuid")
                or data.get("variable_cc_member_pre_answer_uuid")
            ),

            cc_member_session_uuid=self._text(
                data.get("CC-Member-Session-UUID")
                or data.get("variable_cc_member_session_uuid")
            ),

            dtmf_digit=self._text(
                data.get("DTMF-Digit")
            ),

            hangup_cause=self._text(
                data.get("Hangup-Cause")
            ),

            data=data,
        )

    @staticmethod
    def _text(value) -> str | None:
        if value is None:
            return None

        value = str(value).strip()

        return value if value else None

    @staticmethod
    def _integer(value) -> int | None:
        if value is None:
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_number(value) -> str | None:
        if value is None:
            return None

        value = str(value).strip()

        if not value:
            return None

        # Remove URL encoding sometimes found in the logs.
        value = value.replace("%2B", "+")

        # Remove surrounding spaces.
        value = value.strip()

        # Convert Saudi international format:
        # 00966XXXXXXXXX -> +966XXXXXXXXX
        if value.startswith("00"):
            value = "+" + value[2:]

        # Keep + and digits only.
        if value.startswith("+"):
            return "+" + "".join(
                character
                for character in value[1:]
                if character.isdigit()
            )

        return "".join(
            character
            for character in value
            if character.isdigit()
        )