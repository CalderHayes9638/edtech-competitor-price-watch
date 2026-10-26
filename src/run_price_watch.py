from __future__ import annotations

import re
from urllib.parse import urlparse

from price_watch_service import CourseWatch, InfraiClient, PriceWatchRequest, build_report, report_as_json


def main() -> None:
    request = PriceWatchRequest(
        educator="catalog-team",
        catalog=(
            CourseWatch("python-foundations", "self-paced", "2026-11-30", 80.0, ("https://www.python.org/doc/",)),
            CourseWatch("data-literacy", "instructor-led", "2026-12-15", 120.0, ("https://www.w3.org/WAI/fundamentals/accessibility-intro/",)),
        ),
    )
    client = InfraiClient()
    observed: dict[str, float | None] = {}
    for course in request.catalog:
        page = client.scrape(course.competitor_urls[0])
        text = str(page.get("content", page))
        match = re.search(r"(?:USD|\$)\s*(\d+(?:\.\d{1,2})?)", text)
        observed[course.course_id] = float(match.group(1)) if match else None
    report = build_report(request, observed)
    print(report_as_json(report))
    task_url = "https://catalog.example.edu/jobs/price-watch"
    schedule = client.schedule(task_url)
    print(f"scheduled job: {schedule['job_id']}")


if __name__ == "__main__":
    main()
