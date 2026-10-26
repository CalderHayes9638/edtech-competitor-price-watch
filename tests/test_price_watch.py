from src.price_watch_service import CourseWatch, PriceWatchRequest, build_report


def test_below_target_course_enters_educator_review() -> None:
    request = PriceWatchRequest(
        educator="educator-1",
        catalog=(CourseWatch("algebra", "self-paced", "2026-12-01", 80.0, ("https://example.test/algebra",)),),
    )

    report = build_report(request, {"algebra": 59.0})

    assert report.courses[0].status == "review"
    assert report.courses[0].learner_deadline == "2026-12-01"
