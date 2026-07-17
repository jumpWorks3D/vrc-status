#!/usr/bin/env python3
"""Generate a validated VRChat status file for GitHub Pages."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_URL = "https://status.vrchat.com/api/v2/summary.json"

USER_AGENT = (
    "jumpWorks3D-vrc-status/1.0 "
    "(+https://github.com/jumpWorks3D/vrc-status)"
)

REQUEST_TIMEOUT_SECONDS = 20
MAX_RESPONSE_BYTES = 2 * 1024 * 1024

EXPECTED_PAGE_ID = "gw6db8tk47y2"
EXPECTED_PAGE_NAME = "VRChat"
EXPECTED_PAGE_URL = "https://status.vrchat.com"

TARGET_COMPONENTS = {
    "api_website": {
        "id": "64b3rr3cxgk5",
        "name": "API / Website",
    },
    "realtime_networking": {
        "id": "t1jm7fqqq43h",
        "name": "Realtime Networking",
    },
}

OVERALL_STATUS_MAP = {
    "none": "operational",
    "minor": "degraded",
    "major": "partial_outage",
    "critical": "major_outage",
    "maintenance": "maintenance",
}

COMPONENT_STATUS_MAP = {
    "operational": "operational",
    "degraded_performance": "degraded",
    "partial_outage": "partial_outage",
    "major_outage": "major_outage",
    "under_maintenance": "maintenance",
}


class StatusGenerationError(RuntimeError):
    """Raised when the source data cannot be trusted or normalized."""


def require_object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise StatusGenerationError(f"{path} must be an object.")

    return value


def require_array(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise StatusGenerationError(f"{path} must be an array.")

    return value


def require_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise StatusGenerationError(
            f"{path} must be a non-empty string."
        )

    if "\r" in value or "\n" in value or "=" in value:
        raise StatusGenerationError(
            f"{path} contains a forbidden character."
        )

    return value


def require_boolean(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise StatusGenerationError(f"{path} must be a boolean.")

    return value


def reject_duplicate_json_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise StatusGenerationError(
                f"JSON contains a duplicate key: {key!r}."
            )

        result[key] = value

    return result


def parse_json(payload: bytes) -> dict[str, Any]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exception:
        raise StatusGenerationError(
            "The response is not valid UTF-8."
        ) from exception

    try:
        data = json.loads(
            text,
            object_pairs_hook=reject_duplicate_json_keys,
        )
    except json.JSONDecodeError as exception:
        raise StatusGenerationError(
            "The response is not valid JSON at "
            f"line {exception.lineno}, "
            f"column {exception.colno}."
        ) from exception

    return require_object(data, "root")


def fetch_summary() -> dict[str, Any]:
    request = urllib.request.Request(
        SOURCE_URL,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "User-Agent": USER_AGENT,
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=REQUEST_TIMEOUT_SECONDS,
        ) as response:
            if response.status != 200:
                raise StatusGenerationError(
                    f"Unexpected HTTP status: {response.status}."
                )

            final_url = response.geturl()

            if final_url != SOURCE_URL:
                raise StatusGenerationError(
                    f"Unexpected redirect target: {final_url!r}."
                )

            content_type = response.headers.get_content_type()

            if content_type != "application/json":
                raise StatusGenerationError(
                    f"Unexpected Content-Type: {content_type!r}."
                )

            payload = response.read(MAX_RESPONSE_BYTES + 1)

    except urllib.error.HTTPError as exception:
        raise StatusGenerationError(
            f"HTTP request failed with status {exception.code}."
        ) from exception

    except urllib.error.URLError as exception:
        raise StatusGenerationError(
            f"HTTP request failed: {exception.reason}."
        ) from exception

    if not payload:
        raise StatusGenerationError("The response body is empty.")

    if len(payload) > MAX_RESPONSE_BYTES:
        raise StatusGenerationError(
            f"The response exceeds {MAX_RESPONSE_BYTES} bytes."
        )

    return parse_json(payload)


def parse_utc_timestamp(value: Any, path: str) -> str:
    raw_value = require_string(value, path)

    try:
        parsed_value = datetime.fromisoformat(
            raw_value.replace("Z", "+00:00")
        )
    except ValueError as exception:
        raise StatusGenerationError(
            f"{path} is not a valid ISO 8601 timestamp."
        ) from exception

    if parsed_value.tzinfo is None:
        raise StatusGenerationError(
            f"{path} must include a timezone."
        )

    normalized_value = (
        parsed_value
        .astimezone(timezone.utc)
        .replace(microsecond=0)
    )

    return normalized_value.isoformat().replace("+00:00", "Z")


def normalize_status(
    raw_value: Any,
    mapping: dict[str, str],
    path: str,
) -> str:
    source_value = require_string(raw_value, path)
    normalized_value = mapping.get(source_value)

    if normalized_value is None:
        raise StatusGenerationError(
            f"{path} has an unknown value: {source_value!r}."
        )

    return normalized_value


def validate_page(root: dict[str, Any]) -> str:
    page = require_object(root.get("page"), "page")

    page_id = require_string(page.get("id"), "page.id")
    page_name = require_string(page.get("name"), "page.name")
    page_url = require_string(page.get("url"), "page.url")

    if page_id != EXPECTED_PAGE_ID:
        raise StatusGenerationError(
            f"Unexpected page.id: {page_id!r}."
        )

    if page_name != EXPECTED_PAGE_NAME:
        raise StatusGenerationError(
            f"Unexpected page.name: {page_name!r}."
        )

    if page_url.rstrip("/") != EXPECTED_PAGE_URL:
        raise StatusGenerationError(
            f"Unexpected page.url: {page_url!r}."
        )

    return parse_utc_timestamp(
        page.get("updated_at"),
        "page.updated_at",
    )


def validate_overall(root: dict[str, Any]) -> str:
    status = require_object(root.get("status"), "status")

    return normalize_status(
        status.get("indicator"),
        OVERALL_STATUS_MAP,
        "status.indicator",
    )


def find_component(
    components: list[Any],
    component_id: str,
    expected_name: str,
) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []

    for index, item in enumerate(components):
        component = require_object(
            item,
            f"components[{index}]",
        )

        current_id = require_string(
            component.get("id"),
            f"components[{index}].id",
        )

        if current_id == component_id:
            matches.append(component)

    if not matches:
        raise StatusGenerationError(
            "Required component "
            f"{expected_name!r} ({component_id}) was not found."
        )

    if len(matches) != 1:
        raise StatusGenerationError(
            f"Component ID {component_id!r} appears more than once."
        )

    component = matches[0]

    actual_name = require_string(
        component.get("name"),
        f"component[{component_id}].name",
    )

    if actual_name != expected_name:
        raise StatusGenerationError(
            f"Component {component_id!r} has name "
            f"{actual_name!r}; expected {expected_name!r}."
        )

    is_group = require_boolean(
        component.get("group"),
        f"component[{component_id}].group",
    )

    if not is_group:
        raise StatusGenerationError(
            f"Component {component_id!r} is no longer a group."
        )

    page_id = require_string(
        component.get("page_id"),
        f"component[{component_id}].page_id",
    )

    if page_id != EXPECTED_PAGE_ID:
        raise StatusGenerationError(
            f"Component {component_id!r} belongs to "
            f"unexpected page {page_id!r}."
        )

    return component


def build_output(root: dict[str, Any]) -> str:
    source_updated_at = validate_page(root)
    overall = validate_overall(root)

    components = require_array(
        root.get("components"),
        "components",
    )

    normalized_components: dict[str, str] = {}

    for output_key, expected in TARGET_COMPONENTS.items():
        component = find_component(
            components,
            expected["id"],
            expected["name"],
        )

        normalized_components[output_key] = normalize_status(
            component.get("status"),
            COMPONENT_STATUS_MAP,
            f"component[{expected['id']}].status",
        )

    generated_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

    lines = [
        "version=1",
        f"generated_at={generated_at}",
        f"source_updated_at={source_updated_at}",
        f"overall={overall}",
        f"api_website={normalized_components['api_website']}",
        (
            "realtime_networking="
            f"{normalized_components['realtime_networking']}"
        ),
    ]

    for line in lines:
        if line.count("=") != 1:
            raise StatusGenerationError(
                f"Generated an invalid output line: {line!r}."
            )

        if "\r" in line or "\n" in line:
            raise StatusGenerationError(
                f"Generated an invalid output line: {line!r}."
            )

    return "\n".join(lines) + "\n"


def write_output(content: str) -> Path:
    repository_root = Path(__file__).resolve().parents[1]
    output_path = repository_root / "public" / "vrc-status.txt"

    temporary_path = output_path.with_suffix(
        output_path.suffix + ".tmp"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        with temporary_path.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as stream:
            stream.write(content)

        os.replace(temporary_path, output_path)

    finally:
        if temporary_path.exists():
            temporary_path.unlink()

    if output_path.stat().st_size == 0:
        raise StatusGenerationError(
            "The generated output file is empty."
        )

    return output_path


def main() -> int:
    try:
        summary = fetch_summary()
        content = build_output(summary)
        output_path = write_output(content)

    except StatusGenerationError as exception:
        print(
            f"ERROR: {exception}",
            file=sys.stderr,
        )
        return 1

    except OSError as exception:
        print(
            f"ERROR: File operation failed: {exception}",
            file=sys.stderr,
        )
        return 1

    print(f"Generated {output_path}")
    print(content, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
