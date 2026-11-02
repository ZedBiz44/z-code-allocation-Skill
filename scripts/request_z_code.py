#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


def configuration() -> tuple[str, str, str]:
    url = os.getenv("ZCODE_ALLOCATOR_URL", "").rstrip("/")
    key = os.getenv("ZCODE_API_KEY", "")
    agent = os.getenv("ZCODE_AGENT_NAME", "").strip().lower()
    missing = [name for name, value in (("ZCODE_ALLOCATOR_URL", url), ("ZCODE_API_KEY", key), ("ZCODE_AGENT_NAME", agent)) if not value]
    if missing:
        raise RuntimeError("Missing required environment values: " + ", ".join(missing))
    return url, key, agent


def request(
    method: str,
    path: str,
    key: str,
    payload: dict | None = None,
    retries: int = 1,
    not_found_result: dict | None = None,
) -> dict:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(path, data=body, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(detail)
            except json.JSONDecodeError:
                parsed = {"error": detail}
            parsed_detail = parsed.get("detail")
            if (
                exc.code == 404
                and isinstance(parsed_detail, dict)
                and parsed_detail.get("code") == "not_found"
                and not_found_result is not None
            ):
                return not_found_result
            print(json.dumps({"http_status": exc.code, **parsed}, indent=2), file=sys.stderr)
            raise SystemExit(2) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt >= retries:
                raise RuntimeError(f"Z-Code allocator unavailable: {exc}") from exc
            time.sleep(1)
    raise RuntimeError("Z-Code request failed")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Use the authoritative ZedBiz Z-Code allocator", allow_abbrev=False)
    sub = root.add_subparsers(dest="command", required=True)
    allocate = sub.add_parser("allocate", allow_abbrev=False)
    allocate.add_argument("--request-id", required=True)
    allocate.add_argument("--name-key", required=True)
    allocate.add_argument("--folder", required=True)
    allocate.add_argument("--lane")
    allocate.add_argument("--page-type", required=True)
    confirm = sub.add_parser("confirm", allow_abbrev=False)
    confirm.add_argument("--z-code", required=True)
    confirm.add_argument("--notion-url", required=True)
    confirm.add_argument("--record-title", required=True)
    failed = sub.add_parser("failed", allow_abbrev=False)
    failed.add_argument("--z-code", required=True)
    failed.add_argument("--reason", required=True)
    status = sub.add_parser("status", allow_abbrev=False)
    status.add_argument("--request-id", required=True)
    lookup = sub.add_parser("lookup", allow_abbrev=False)
    lookup.add_argument("--name-key", required=True)
    sub.add_parser("catalogue")
    resolve = sub.add_parser("resolve", allow_abbrev=False)
    resolve.add_argument("--z-code", required=True)
    return root


def main() -> int:
    args = parser().parse_args()
    base_url, key, agent = configuration()
    if args.command == "allocate":
        payload = {
            "request_id": args.request_id,
            "name_key": args.name_key,
            "folder_key": args.folder,
            "knowledge_lane": args.lane,
            "page_type": args.page_type,
            "requested_by": agent,
        }
        if payload["knowledge_lane"] is None:
            del payload["knowledge_lane"]
        result = request("POST", f"{base_url}/v1/allocate", key, payload)
    elif args.command == "confirm":
        result = request(
            "POST",
            f"{base_url}/v1/confirm",
            key,
            {"z_code": args.z_code, "status": "active", "notion_url": args.notion_url,
             "record_title": args.record_title},
        )
    elif args.command == "failed":
        result = request(
            "POST",
            f"{base_url}/v1/confirm",
            key,
            {"z_code": args.z_code, "status": "failed", "reason": args.reason},
        )
    elif args.command == "catalogue":
        result = request("GET", f"{base_url}/v1/catalogue", key)
    elif args.command == "resolve":
        query = urllib.parse.urlencode({"z_code": args.z_code})
        result = request("GET", f"{base_url}/v1/resolve?{query}", key)
    elif args.command == "status":
        result = request("GET", f"{base_url}/v1/status/{urllib.parse.quote(args.request_id, safe='')}", key)
    else:
        query = urllib.parse.urlencode({"name_key": args.name_key})
        result = request(
            "GET",
            f"{base_url}/v1/lookup?{query}",
            key,
            not_found_result={"found": False, "name_key": args.name_key},
        )
    required = {"allocate": ["z_code", "request_id", "status", "mapping_version"], "confirm": ["z_code", "status"], "failed": ["z_code", "status"], "status": ["request_id", "status"], "resolve": ["z_code"], "catalogue": ["version", "folders"], "lookup": ["found", "name_key"] if isinstance(result, dict) and result.get("found") is False else ["name_key", "records"]}[args.command]
    if not isinstance(result, dict) or any(result.get(k) is None for k in required):
        raise RuntimeError("Incomplete success response; retain request details and reconcile")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


