---
name: log-parsing-compliance
description: Use when parsing log files to ensure correct aggregation, sorting, and output formatting.
---
1. When parsing service names, transform them to lower-case and replace all hyphens with underscores (e.g., `payment-service` becomes `payment_service`).
2. Ensure the `errors` list in the output JSON is sorted primarily by `service` (alphabetical) and secondarily by `timestamp_utc` (ascending).
3. The output JSON must contain the top-level keys `schema_version` (set to 2) and `generated_by` (set to "log-triage").
4. Ensure all timestamps are converted to UTC and formatted as `YYYY-MM-DDTHH:MM:SSZ`.
5. Verify that the aggregation logic (e.g., `counts_by_service`) correctly sums the `repeat_count` for each service.
6. Self-check: Are service names formatted with underscores? Is the `errors` list sorted by service then time? Are the required top-level keys present? Is the timestamp format consistent?
