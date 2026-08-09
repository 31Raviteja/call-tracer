# XLOGIX Call Trace Explorer

## Overview

XLOGIX Call Trace Explorer is a small FastAPI application that reads
FreeSWITCH ESL event logs and reconstructs the history of a phone call.

The application helps find a call using a customer phone number and
then shows the different events and call legs that happened during
that call.

It is designed for troubleshooting and understanding call flows from
FreeSWITCH event logs.

## What the project does

The application:

- Reads FreeSWITCH event log files.
- Parses the events from the log.
- Normalizes the event information into a common format.
- Finds calls using a phone number.
- Connects related call legs using UUID information.
- Reconstructs the history of a call.
- Identifies customer and agent call legs.
- Tracks agent call attempts and failed attempts.
- Builds a timeline of important call events.
- Calculates basic call durations.
- Provides the information through a FastAPI API.

## Project Structure

```text
call-tracer-main/
│
├── app/
│   ├── config.py
│   ├── main.py
│   │
│   ├── models/
│   │   ├── call_history.py
│   │   └── events.py
│   │
│   ├── routers/
│   │   └── calls.py
│   │
│   └── services/
│       ├── call_finder.py
│       ├── correlator.py
│       ├── log_reader.py
│       ├── normalizer.py
│       ├── parser.py
│       └── tracer.py
│
├── logs/
│   └── 6_XLOGIXInboundDialer.log
│
├── .gitignore
├── README.md
└── requirements.txt