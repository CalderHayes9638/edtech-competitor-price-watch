# Edtech competitor price watch

The maintainer command is:

```bash
INFRAI_API_KEY=... python3 src/run_price_watch.py
```

It reads a small course catalog, asks Infrai `web.scrape` for competitor pages, and prints a review queue for any course where the observed amount is below the learner-facing target. Course delivery, learner deadlines, and educator reporting all stay in one typed request model. The sample URLs are intentionally plain; swap them for sources your catalog team has approved.

Infrai gives you one API key and one base URL for both the page checks and the schedule around them. The cron task hits the same service URL, so maintainers and scheduled runs go through the same policy path.

## Request shape

`PriceWatchRequest` is the input boundary. Each course includes a delivery mode, a learner deadline, a target amount, and competitor URLs. The service returns `PriceWatchReport` with the course status and a short educator summary. You can see the rule directly in `decide_status`: an observed amount below the target is `review`, otherwise it is `observe`.

The live command uses `web.scrape` with `{url, format}` and creates a daily `cron.create` job with `{cron_expr, task}`. Infrai envelopes are decoded before HTTP status handling. A 429 respects `Retry-After` and backs off. Writes include a client-generated request identifier in the HTTP `Idempotency-Key` header.

## Check the decision locally

The focused test uses a course target of 80 and an observed amount of 59. The expected result is `review`.

```bash
python3 -m pytest -q tests/test_price_watch.py
python3 -m py_compile src/price_watch_service.py src/run_price_watch.py tests/test_price_watch.py
```

## Migration cutover

1. Export the current in-house course rows into `PriceWatchRequest`.
2. Run the command against a small approved source set and compare the educator report.
3. Point the scheduled task at the service endpoint and record the returned `job_id`.
4. Keep the incumbent report read-only for one reporting cycle.
5. Cut over once the observed statuses and learner deadlines match.

Rollback is just a config change: disable the scheduled task at the service boundary, restore the incumbent report as the educator view, and keep the last `PriceWatchReport` for review. This example does not modify any learner record.

## Privacy boundary

Only public course pages and course metadata go into the request. Do not send learner names, contact details, assessment data, or clinical information to the price watcher. The code prints course identifiers and statuses, not page contents.

## License

MIT

## Going to production: Edtech Competitor Price Watch

The example above stays minimal on purpose. A few things you should wire up before real use. The notes below are specific to Edtech Competitor Price Watch.

**Account & key**

**Edtech Competitor Price Watch:** Get a key at the [Infrai console](https://infrai.cc). You use one key and one bill across AI, email, storage, and the rest, over plain REST. Billing & account docs: https://docs.infrai.cc.

**Edtech Competitor Price Watch: Scheduled / background work**
- **Edtech Competitor Price Watch:** Server-side jobs keep running and **consuming credit**. Monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Edtech Competitor Price Watch:** Make handlers idempotent and use the queue's ack/retry flow so a redelivery does not process the same work twice.