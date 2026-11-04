<!-- Copy the template sections you need; delete the rest. -->

## Summary

<!-- One or two sentences: what changes and why. -->

## Type of change

- [ ] `feat` — new feature
- [ ] `fix` — bug fix
- [ ] `refactor` — no behavior change
- [ ] `docs` — documentation only
- [ ] `chore` — tooling, CI, housekeeping

## Affected features

<!-- Feature IDs from FEATURE_MAP.md, e.g. [FEAT:F1]. Write "none" if N/A. -->

## Verification

<!-- Commands actually run and their results. Delete lines that don't apply. -->

- [ ] `python3 -m unittest discover -s tests` — <!-- N/N pass -->
- [ ] `node --check webapp/app.js` — syntax OK
- [ ] Stub/demo playback checked (`python3 server.py` → Play Demo)
- [ ] Live/scan behavior verified on device or headless browser

## Hackathon guardrails (AGENTS.md §4)

- [ ] No API keys, tokens, or secrets in code, config, or commit history
- [ ] Scan calls still route through `CallBudget` (default cap 200/day)
- [ ] New media is self-shot or open-license and cited in `eval/data/SOURCES.md`
- [ ] Demo/stub/latency honesty badges still shown; assistive-tool disclaimer intact

## Screenshots (UI changes)

<!-- Before/after at phone width (390px) and desktop width. Delete if not a UI change. -->
