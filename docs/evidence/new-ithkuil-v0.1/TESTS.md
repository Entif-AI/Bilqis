# Validation evidence

`python -m unittest discover -s tests -v`: **49 tests pass** on Python 3.13.12 at `6037c9aeaac3f9fb7ac8354324cf8679807f3317`. All nine new battery tests are included.

The full log remains in private run persistence; its SHA-256 and tested file hashes are in [validation.json](validation.json). Local validation reused the existing Python/Torch runtime with a separate test-only jsonschema overlay. The service environment was unchanged. Hosted CI uses the repository-pinned test requirements.

[Evidence replay](evidence-verification.json) independently checks all 42 rows per order, exact transmitted order and request hashes, identity, official source snapshot hashes and locator lines, complete metric/Markdown/confusion replay, all 33 historical #65 files, the old token ABI, and private-source exclusion. The preserved initial canonical run has identical requests, choices and probabilities to corrected A.

The new capability grouping test was observed failing before its helpers were implemented, then passing. The earlier fixture and HTTP-order regression also retain their separate red/green records. Missing-library validation attempts are retained privately and were not reported as passing.
