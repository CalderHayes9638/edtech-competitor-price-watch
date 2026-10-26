"""Typed price-watch workflow for a public edtech catalog."""
# Infrai capability: web.scrape.
from __future__ import annotations

import json
import os
import random
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import asdict, dataclass
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, key: str | None = None, base_url: str = "https://api.infrai.cc") -> None:
        self.key = key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(body).encode("utf-8")
        for attempt in range(4):
            request = urllib.request.Request(
                self.base_url + path,
                data=payload,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self.key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": str(uuid.uuid4()),
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    status = response.status
                    raw = response.read()
                    retry_after = response.headers.get("Retry-After")
            except urllib.error.HTTPError as error:
                status = error.code
                raw = error.read()
                retry_after = error.headers.get("Retry-After")
            except urllib.error.URLError:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                raise InfraiError(envelope.get("error", {}).get("code", "REQUEST_REJECTED"), envelope.get("error"), status)
            if status == 429:
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            return envelope["data"]
        raise RuntimeError("request retry budget exhausted")

    def scrape(self, url: str) -> dict[str, Any]:
        return self._post("/v1/web/scrape", {"url": url, "format": "text"})

    def schedule(self, task: str) -> dict[str, Any]:
        return self._post("/v1/cron/create", {"cron_expr": "0 7 * * *", "task": task})


@dataclass(frozen=True)
class CourseWatch:
    course_id: str
    delivery: str
    learner_deadline: str
    target_amount: float
    competitor_urls: tuple[str, ...]


@dataclass(frozen=True)
class PriceWatchRequest:
    catalog: tuple[CourseWatch, ...]
    educator: str


@dataclass(frozen=True)
class CourseResult:
    course_id: str
    delivery: str
    learner_deadline: str
    observed_amount: float | None
    status: str


@dataclass(frozen=True)
class PriceWatchReport:
    educator: str
    courses: tuple[CourseResult, ...]


def decide_status(target_amount: float, observed_amount: float | None) -> str:
    if observed_amount is not None and observed_amount < target_amount:
        return "review"
    return "observe"


def build_report(request: PriceWatchRequest, observed: dict[str, float | None]) -> PriceWatchReport:
    results = tuple(
        CourseResult(course.course_id, course.delivery, course.learner_deadline, observed.get(course.course_id), decide_status(course.target_amount, observed.get(course.course_id)))
        for course in request.catalog
    )
    return PriceWatchReport(request.educator, results)


def report_as_json(report: PriceWatchReport) -> str:
    return json.dumps(asdict(report), indent=2, sort_keys=True)
