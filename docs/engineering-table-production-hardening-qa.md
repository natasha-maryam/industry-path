# Engineering Table Production Hardening QA Checklist

Use this checklist against a real project with parsed data and live runtime updates enabled.

## Core Behavior + Runtime

1. Parse completes and behavior cache loads rows + edges.
   - Expected: deterministic table rows appear without manual reload.
2. Receive websocket full snapshot.
   - Expected: `Live Connected` badge and row count populated.
3. Receive websocket partial runtime updates.
   - Expected: only impacted rows patch; no full reset.
4. Search while updates are streaming.
   - Expected: search input and filtered result state remain stable.
5. Sort while updates are streaming.
   - Expected: sort order remains stable after partial patches.
6. Select a row and open lower details.
   - Expected: selection remains after partial updates and reconnect.

## Why Trace

7. Open `Why` from selected row.
   - Expected: right trace tab opens current selected tag.
8. Why trace API failure / missing tag handling.
   - Expected: clear error or no-trace message (no panel crash).
9. Click a why-trace step.
   - Expected: selected tag syncs back to workspace trace selection.

## Websocket Resilience

10. Force websocket disconnect/reconnect.
    - Expected: badge transitions `Reconnecting` -> `Live Connected`.
11. After reconnect, verify state persistence.
    - Expected: search text, sorting, selected row, and trace context remain.
12. Verify no duplicate subscriptions / duplicate row patching.
    - Expected: no repeated duplicate updates for same partial payload.

## System Layer + Connectors

13. Run UNS query with valid SELECT.
    - Expected: response row preview updates and status message shown.
14. Run UNS script with valid script.
    - Expected: script result + refreshed rows shown.
15. Submit empty query/script.
    - Expected: validation error before request.
16. Try invalid connector input (empty endpoint/host).
    - Expected: validation error; no crash.
17. Use advanced relational actions (trace/loops/bottlenecks).
    - Expected: structured response shown; empty/malformed data handled safely.

## Views / Snapshots / Diff

18. Create saved view.
    - Expected: views list refreshes and new view selected.
19. Create snapshot with selected view.
    - Expected: success status and refreshed version list.
20. Attempt snapshot with no selected view.
    - Expected: validation error.
21. Compare two different versions.
    - Expected: diff summary and diff viewer render.
22. Compare missing/same version IDs.
    - Expected: validation error.

## Tag Database + Export

23. Load tag database filters: all / unused / orphans / conflicts.
    - Expected: no crash on empty datasets.
24. Export CSV.
    - Expected: download succeeds; error shown for empty/failed exports.
25. Export JSON.
    - Expected: download succeeds; error shown for empty/failed exports.

## Integration Safety

26. Open Engineering Table alongside right panel modules.
    - Expected: tabs and module behavior align with workspace architecture.
27. Confirm no state reset on live updates.
    - Expected: scroll/selection/sort/search remain stable.
28. Confirm no silent failures.
    - Expected: unknown tags and ignored updates are exposed in debug metadata/logs.
