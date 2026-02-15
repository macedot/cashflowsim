"""API client for CashflowSim simulation service.

This module provides a client to communicate with the Go-based simulation API.
"""

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

import requests
import streamlit as st
from pandas import isna

# API Configuration
API_URL = os.getenv("SIMULATION_API_URL", "http://simulation:8080")
API_TIMEOUT = int(os.getenv("SIMULATION_API_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("SIMULATION_MAX_RETRIES", "3"))
BACKOFF_FACTOR = float(os.getenv("SIMULATION_BACKOFF_FACTOR", "1.0"))

# Reusable session for connection pooling
_session: requests.Session | None = None


def _get_session() -> requests.Session:
    """Get or create a reusable requests session for connection pooling."""
    global _session
    if _session is None:
        _session = requests.Session()
    return _session


class CashflowItem(TypedDict):
    """A single cashflow item."""

    name: str
    value: float


class Cashflow(TypedDict):
    """Cashflow data for a specific date."""

    date: str
    cashflow: float
    balance: float
    items: List[CashflowItem]


class SimulationEvent(TypedDict):
    """Input event for simulation."""

    name: str
    start_date: str
    end_date: Optional[str]
    frequency: Optional[str]
    value: float
    obs: Optional[str]


def _format_date(dt: datetime) -> str:
    """Format datetime to ISO 8601 string.

    Args:
        dt: Datetime to format

    Returns:
        ISO 8601 formatted string
    """
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _make_request_with_retry(
    method: str,
    url: str,
    json_data: Optional[Dict[str, Any]] = None,
    retries: int = MAX_RETRIES,
) -> requests.Response:
    """Make HTTP request with exponential backoff retry logic.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        json_data: Optional JSON payload
        retries: Number of retry attempts

    Returns:
        Response object

    Raises:
        requests.RequestException: If all retries fail
    """
    last_exception = None

    session = _get_session()
    for attempt in range(retries):
        try:
            response = session.request(
                method=method,
                url=url,
                json=json_data,
                timeout=API_TIMEOUT,
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            last_exception = e
            if attempt < retries - 1:
                sleep_time = BACKOFF_FACTOR * (2**attempt)
                time.sleep(sleep_time)
            continue

    raise last_exception


def check_health() -> bool:
    """Check if the simulation API is healthy.

    Returns:
        True if API is healthy, False otherwise
    """
    try:
        response = _make_request_with_retry("GET", f"{API_URL}/health", retries=1)
        data = response.json()
        return data.get("status") == "ok"
    except BaseException:
        return False


def run_simulation(
    events: List[Dict[str, Any]],
    initial_balance: float,
    sim_start: datetime,
    sim_end: datetime,
) -> Optional[List[Cashflow]]:
    """Run cashflow simulation via API.

    Args:
        events: List of financial events
        initial_balance: Starting balance amount
        sim_start: Simulation start date
        sim_end: Simulation end date

    Returns:
        List of cashflow data or None if simulation failed

    Example:
        >>> events = [{
        ...     "name": "Salary",
        ...     "start_date": datetime(2025, 1, 1),
        ...     "frequency": "monthly",
        ...     "value": 5000
        ... }]
        >>> result = run_simulation(events, 1000, datetime(2025, 1, 1), datetime(2025, 12, 31))
    """
    # Convert events to API format using list comprehension
    def convert_event(event: Dict[str, Any]) -> SimulationEvent:
        end_date = event.get("end_date")
        return {
            "name": event.get("name", ""),
            "start_date": _format_date(event["start_date"]),
            "end_date": _format_date(end_date) if end_date and not isna(end_date) else None,
            "frequency": event.get("frequency") or None,
            "value": float(event.get("value", 0)),
            "obs": event.get("obs") or None,
        }

    api_events: List[SimulationEvent] = [convert_event(e) for e in events]

    # Prepare request payload
    payload = {
        "events": api_events,
        "initial_balance": initial_balance,
        "sim_start": _format_date(sim_start),
        "sim_end": _format_date(sim_end),
    }

    try:
        response = _make_request_with_retry(
            "POST",
            f"{API_URL}/api/v1/simulate",
            json_data=payload,
        )
        data = response.json()
        return data.get("cashflows", [])
    except requests.exceptions.ConnectionError as e:
        st.error(f"⚠️ Cannot connect to simulation service: {e}")
        return None
    except requests.exceptions.Timeout:
        st.error("⚠️ Simulation request timed out. Please try again.")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"⚠️ Simulation failed: {e.response.text if e.response else str(e)}")
        return None
    except Exception as e:
        st.error(f"⚠️ Unexpected error: {e}")
        return None
