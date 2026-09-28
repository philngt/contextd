# Synthetic cancellation fixture

These files are invented test data, not a surveyed repository or production behavior.

- Code permits NEW/PAID; no test or production command has been run to produce this claim.
- Spec requests PACKED as well and forbids SHIPPED.
- Manual describes packed-order cancellation.

`baseline.json` is an explicitly synthetic owner snapshot with one existing Action.
`proposal.json` reuses that action and retains current/target/reference assertions, precise
Evidence records and an implementation gap. It is not a Product Graph native import file.

From the contextd source root, run the command in [the guide](../../docs/graph-authoring.md).
Normal validation exits 0 with a review warning; `--strict` exits 1 intentionally.
The test suite independently verifies the fixture source hashes. The validator itself does
not read source locators, run code, prove semantics or apply the proposal.
