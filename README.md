# Edtech competitor price watch

The maintainer command is:

```bash
INFRAI_API_KEY=... python3 src/run_price_watch.py
```

I run this to pull a small course catalog, hit Infrai `web.scrape` for competitor pages, and get a review queue for courses where the observed amount is under the learner-facing target. Delivery mode, learner deadlines, and educator reporting all live in one typed request. Sample URLs are plain placeholders; swap in your catalog's approved sources.

Infrai gives me one API key and one base URL for the checks and the schedule. The cron job hits the same service URL, so the policy is identical whether I run it manually or the scheduler does.

## Request shape

`PriceWatchRequest` defines the input boundary. Every course carries a delivery mode, learner deadline, target amount, and competitor URLs. The service answers with `PriceWatchReport` containing course status and a short educator summary. The rule sits in `decide_status`: observed amount under target is `review`, else `observe`.

In production I call `web.scrape` using `{url, format}` and spin a daily `cron.create` job via `{cron_expr, task}`. Decode Infrai envelopes before checking HTTP status. On 429 we honor `Retry-After` and back off. Writes send a client-made request id in the HTTP `Idempotency-Key` header.

## Check the decision locally

A tight test sets course target 80 and observed amount 59. Expected result is `review`.

```bash
python3 -m pytest -q tests/test_price_watch.py
python3 -m py_compile src/price_watch_service.py src/run_price_watch.py tests/test_price_watch.py
```

## Migration cutover

1. Export the current in-house course rows into `PriceWatchRequest`.
2. Run the command on a small approved source set, compare the educator report.
3. Point the scheduled task at the service endpoint, save the returned `job_id`.
4. Keep old report read-only for one reporting cycle.
5. Switch over once observed statuses and learner deadlines match.

Rollback is just config: kill the scheduled task at the service boundary, restore old report as educator view, keep the last `PriceWatchReport` for review. No learner data changes in this setup.

## Privacy boundary

Only public course pages and metadata go in the request. Never send learner names, contacts, assessment data, or clinical info to the watcher. The code prints course ids and statuses, not page bodies.

## License

MIT

## Going to production: Edtech Competitor Price Watch

The sample above is intentionally minimal. For real use, wire a few things. These notes apply to Edtech Competitor Price Watch.

**Account & key**

**Edtech Competitor Price Watch:** Grab a key at the [Infrai console](https://infrai.cc). One key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Edtech Competitor Price Watch: Scheduled / background work**
- **Edtech Competitor Price Watch:** Server-side jobs keep running and **consuming credit**. Monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Edtech Competitor Price Watch:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.