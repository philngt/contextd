# Synthetic cancellation fixture

**Legacy v1 compatibility.** New authoring uses the
[native OES v2 example](oes-native/README.md). This fixture retains its original
proposal semantics; it is not automatically migrated to an OES template.

These files are invented test data, not a surveyed repository or production behavior.

- Code permits NEW/PAID; no test or production command has been run to produce this claim.
- Spec requests PACKED as well and forbids SHIPPED.
- Manual describes packed-order cancellation.

`baseline.json` is an explicitly synthetic owner snapshot with one existing Action.
`proposal.json` reuses that action and retains current/target/reference assertions, precise
Evidence records and an implementation gap. It is not a Product Graph native import file.

From the contextd source root, run the [legacy command](../../docs/graph-authoring.md#legacy-v1-compatibility).
Normal validation exits 0 with a review warning; `--strict` exits 1 intentionally.
The test suite independently verifies the fixture source hashes. The validator itself does
not read source locators, run code, prove semantics or apply the proposal.
