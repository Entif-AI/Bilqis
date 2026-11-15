# Admin Main Frame Atlas rendered acceptance evidence

Issue #1186 refines the Atlas route on top of the latest #1182 inspector-geometry
dependency (`6a9a066dc65c226ce379dca9466505ccdf097f42`). The route keeps the compact
semantic overview visible and groups the three heavyweight peer work surfaces into
one top-level tab set: Lookup, ABI, and Dossier.

The browser receipt in `output/playwright/1186/browser-result.json` drives the full
renderer in both production and explicit reference-fixture launch modes. Production
uses production-only Atlas records supplied through the production query boundary;
fixture mode uses the route-local Atlas fixture API loaded through the fixture-only
support module.

The six rendered variants cover dark/comfortable desktop, light/compact desktop,
and light/compact 390 px mobile width in both launch modes. The proof verifies one
three-tab Atlas workspace, query and ABI-input state retention across tabs, semantic
selection into the dossier, canonical/learned relationship lenses, shared contextual
help, shared temporal rendering, production/fixture provenance separation, global
inspector opening and resizing, bounded relationship-table geometry at realistic
canonical relation volume, and stable unique
test hooks.

Axe reports zero WCAG A/AA violations in all six variants. None of the variants creates
document-level horizontal overflow. The final browser receipt also runs after consuming
the #1182 responsive-inspector repair so the collapsed-navigation and resized-inspector
geometry exercised here matches the dependency being turned in.
