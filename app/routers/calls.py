from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.models.call_history import CallHistory
from app.services.call_finder import CallFinder
from app.services.log_reader import LogReader
from app.services.normalizer import EventNormalizer
from app.services.parser import EventParser
from app.services.tracer import CallTracer


router = APIRouter(
    prefix="/calls",
    tags=["Calls"],
)


def load_events():
    reader = LogReader(settings.log_dir)
    parser = EventParser()
    normalizer = EventNormalizer()

    events = []

    for line in reader.iter_event_lines():
        raw_event = parser.parse(line)

        if raw_event is None:
            continue

        events.append(
            normalizer.normalize(raw_event)
        )

    return events


@router.get("/search")
def search_calls(
    number: str | None = None,
    direction: str | None = None,
    tenant: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    events = load_events()

    finder = CallFinder(events)

    calls = finder.search(
        number=number,
        direction=direction,
        tenant=tenant,
    )

    total = len(calls)

    start = (page - 1) * page_size
    end = start + page_size

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "results": calls[start:end],
    }


@router.get("/count")
def count_calls():
    events = load_events()

    finder = CallFinder(events)

    calls = finder.search()

    return {
        "count": len(calls),
    }


@router.get(
    "/history",
    response_model=list[CallHistory],
)
def get_call_history(
    number: str,
):
    events = load_events()

    finder = CallFinder(events)

    calls = finder.search(
        number=number,
    )

    if not calls:
        raise HTTPException(
            status_code=404,
            detail="No calls found for this number",
        )

    tracer = CallTracer(events)

    histories = []

    for call in calls:
        history = tracer.trace(
            call["call_id"]
        )

        if history is not None:
            histories.append(history)

    if not histories:
        raise HTTPException(
            status_code=404,
            detail="Call history could not be reconstructed",
        )

    return histories


@router.get(
    "/{call_id}",
    response_model=CallHistory,
)
def get_call(call_id: str):
    events = load_events()

    tracer = CallTracer(events)

    history = tracer.trace(call_id)

    if history is None:
        raise HTTPException(
            status_code=404,
            detail="Call not found",
        )

    return history