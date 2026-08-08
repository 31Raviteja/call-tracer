from datetime import datetime

from app.models.call_history import (
    CallHistory,
    CallLeg,
    CallStep,
    CallSummary,
)
from app.models.events import ParsedEvent
from app.services.correlator import CallCorrelator


class CallTracer:

    def __init__(self, events: list[ParsedEvent]):
        self.events = events
        self.correlator = CallCorrelator(events)

    def trace(self, root_uuid: str) -> CallHistory | None:
        related_uuids = self.correlator.correlate(root_uuid)

        if not related_uuids:
            return None

        call_events = [
            event
            for event in self.events
            if (
                event.uuid in related_uuids
                or event.cc_member_session_uuid == root_uuid
            )
        ]

        if not call_events:
            return None

        call_events.sort(
            key=lambda event: event.timestamp
        )

        root_events = [
            event
            for event in call_events
            if event.uuid == root_uuid
        ]

        if not root_events:
            return None

        started_at = self._first_event_time(
            root_events,
            "CHANNEL_CREATE",
        )

        ended_at = self._first_event_time(
            root_events,
            "CHANNEL_HANGUP",
        )

        answered_at = self._find_agent_answer_time(
            call_events=call_events,
            root_uuid=root_uuid,
        )

        customer_number = self._first_value(
            root_events,
            "caller_number",
        )

        did = self._first_value(
            root_events,
            "destination_number",
        )

        direction = self._first_value(
            root_events,
            "call_direction",
        )

        hangup_cause = self._first_hangup_cause(
            root_events
        )

        tenant = self._find_tenant(call_events)

        legs = self._build_legs(call_events)

        timeline = self._build_timeline(call_events)

        recordings = self._find_recordings(call_events)

        durations = self._calculate_durations(
            call_events=call_events,
            started_at=started_at,
            answered_at=answered_at,
            ended_at=ended_at,
        )

        return CallHistory(
            call_id=root_uuid,
            tenant=tenant,
            customer_number=customer_number,
            did=did,
            direction=direction,
            started_at=started_at,
            ended_at=ended_at,
            answered=answered_at is not None,
            hangup_cause=hangup_cause,
            legs=legs,
            timeline=timeline,
            recordings=recordings,
            durations_sec=durations,
        )

    @staticmethod
    def _first_value(
        events: list[ParsedEvent],
        attribute: str,
    ) -> str | None:

        for event in events:
            value = getattr(event, attribute, None)

            if value:
                return value

        return None

    @staticmethod
    def _first_event_time(
        events: list[ParsedEvent],
        event_name: str,
    ) -> datetime | None:

        for event in events:
            if event.event_name == event_name:
                return event.timestamp

        return None

    @staticmethod
    def _find_agent_answer_time(
        call_events: list[ParsedEvent],
        root_uuid: str,
    ) -> datetime | None:

        for event in call_events:
            if event.event_name != "CHANNEL_ANSWER":
                continue

            if event.uuid == root_uuid:
                continue

            if event.cc_agent:
                return event.timestamp

        return None

    @staticmethod
    def _first_hangup_cause(
        events: list[ParsedEvent],
    ) -> str | None:

        for event in events:
            if event.event_name == "CHANNEL_HANGUP":
                if event.hangup_cause:
                    return event.hangup_cause

        return None

    @staticmethod
    def _find_tenant(
        events: list[ParsedEvent],
    ) -> str | None:

        for event in events:
            tenant = event.data.get(
                "variable_sip_h_X-SCUD-TENANT"
            )

            if tenant:
                return str(tenant)

        return None

    @staticmethod
    def _build_legs(
        events: list[ParsedEvent],
    ) -> list[CallLeg]:

        legs: dict[str, CallLeg] = {}

        for event in events:
            if not event.uuid:
                continue

            if event.uuid in legs:
                continue

            role = "channel"

            if event.cc_agent:
                role = "agent"

            elif event.cc_member_session_uuid:
                role = "queue_member"

            elif event.call_direction == "inbound":
                role = "customer"

            legs[event.uuid] = CallLeg(
                uuid=event.uuid,
                role=role,
                direction=event.call_direction,
                destination=event.destination_number,
            )

        return list(legs.values())

    @staticmethod
    def _build_timeline(
        events: list[ParsedEvent],
    ) -> list[CallStep]:

        timeline: list[CallStep] = []

        for event in events:

            step = CallTracer._event_to_step(event)

            if step is not None:
                timeline.append(step)

        timeline.sort(
            key=lambda item: item.at
        )

        return timeline

    @staticmethod
    def _event_to_step(
        event: ParsedEvent,
    ) -> CallStep | None:

        if event.event_name == "CHANNEL_CREATE":
            return CallStep(
                at=event.timestamp,
                step="channel_create",
                detail={
                    "uuid": event.uuid,
                    "direction": event.call_direction,
                    "destination": event.destination_number,
                },
            )

        if event.event_name == "CHANNEL_ANSWER":
            return CallStep(
                at=event.timestamp,
                step="channel_answer",
                detail={
                    "uuid": event.uuid,
                },
            )

        if event.event_name == "CHANNEL_ORIGINATE":
            return CallStep(
                at=event.timestamp,
                step="channel_originate",
                detail={
                    "uuid": event.uuid,
                    "destination": event.destination_number,
                },
            )

        if event.event_name == "RECORD_START":
            return CallStep(
                at=event.timestamp,
                step="record_start",
                detail={
                    "uuid": event.uuid,
                },
            )

        if event.event_name == "CHANNEL_HANGUP":
            detail = {
                "uuid": event.uuid,
                "cause": event.hangup_cause,
            }

            if event.cc_agent:
                detail["agent"] = event.cc_agent

            return CallStep(
                at=event.timestamp,
                step="channel_hangup",
                detail=detail,
            )

        if event.event_name == "DTMF":
            return CallStep(
                at=event.timestamp,
                step="dtmf",
                detail={
                    "digit": event.dtmf_digit,
                },
            )

        if event.event_name == "CUSTOM":
            return CallTracer._custom_event_to_step(event)

        return None

    @staticmethod
    def _custom_event_to_step(
        event: ParsedEvent,
    ) -> CallStep:

        detail = {
            "action": event.cc_action,
            "queue": event.cc_queue,
            "agent": event.cc_agent,
            "member_uuid": event.cc_member_uuid,
            "member_session_uuid": event.cc_member_session_uuid,
        }

        action = event.cc_action

        if action == "member-queue-start":
            step = "queue_join"

        elif action == "member-queue-end":
            step = "queue_leave"

        elif action == "agent-offering":
            step = "agent_offered"

        elif action == "bridge-agent-fail":
            step = "agent_failed"

        else:
            step = "custom"

        return CallStep(
            at=event.timestamp,
            step=step,
            detail=detail,
        )

    @staticmethod
    def _find_recordings(
        events: list[ParsedEvent],
    ) -> list[str]:

        recordings: list[str] = []

        for event in events:

            if event.event_name != "RECORD_START":
                continue

            recording = (
                event.data.get("Recording-File-Path")
                or event.data.get("variable_recording_file")
                or event.data.get("variable_recording_file_path")
            )

            if recording:
                recording = str(recording)

                if recording not in recordings:
                    recordings.append(recording)

        return recordings

    @staticmethod
    def _calculate_durations(
        call_events: list[ParsedEvent],
        started_at: datetime | None,
        answered_at: datetime | None,
        ended_at: datetime | None,
    ) -> CallSummary:

        total = CallTracer._seconds(
            started_at,
            ended_at,
        )

        ring = CallTracer._seconds(
            started_at,
            answered_at,
        )

        talk = CallTracer._seconds(
            answered_at,
            ended_at,
        )

        ivr_start = CallTracer._find_step_time(
            call_events,
            "CHANNEL_ANSWER",
        )

        queue_start = CallTracer._find_custom_time(
            call_events,
            "member-queue-start",
        )

        queue_end = CallTracer._find_custom_time(
            call_events,
            "member-queue-end",
        )

        ivr = CallTracer._seconds(
            ivr_start,
            queue_start,
        )

        queue_wait = CallTracer._seconds(
            queue_start,
            queue_end,
        )

        return CallSummary(
            ring=ring,
            ivr=ivr,
            queue_wait=queue_wait,
            talk=talk,
            total=total,
        )

    @staticmethod
    def _find_step_time(
        events: list[ParsedEvent],
        event_name: str,
    ) -> datetime | None:

        for event in events:
            if event.event_name == event_name:
                return event.timestamp

        return None

    @staticmethod
    def _find_custom_time(
        events: list[ParsedEvent],
        action: str,
    ) -> datetime | None:

        for event in events:
            if (
                event.event_name == "CUSTOM"
                and event.cc_action == action
            ):
                return event.timestamp

        return None

    @staticmethod
    def _seconds(
        start: datetime | None,
        end: datetime | None,
    ) -> float | None:

        if start is None or end is None:
            return None

        value = (end - start).total_seconds()

        if value < 0:
            return None

        return value