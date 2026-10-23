# PiSDK — Swift

Independent SwiftPM repository; `Package.swift` and the public `PiSDK` product are at the repository root. No Node, npm, TypeScript, Pi Chat or sibling checkout is required to build or run SDK unit/probe tests.

## Build and test

```sh
swift build
swift test
python3 scripts/protocol-artifacts.py check
```

Swift tools 6.2, iOS 26.1 and macOS 15 minimums are unchanged. Use a Git URL and an explicit revision for SwiftPM consumers. No remote exists yet; local Git URLs work for verification. Nothing is published; see [SOURCE.md](SOURCE.md).

## SonarQube Cloud

GitHub Actions runs coverage-enabled Swift tests, converts SwiftPM's LLVM JSON to
Sonar generic line coverage, then scans handwritten SDK code and waits for the
quality gate. Fork PRs still run tests but skip authenticated analysis.

Repository variables are `SONAR_ORGANIZATION=manuelselch` and
`SONAR_PROJECT_KEY=ManuelSelch_pi-sdk-swift`. Add the repository Actions secret
`SONAR_TOKEN`, import this repository into SonarQube Cloud, and disable automatic
analysis in favor of CI analysis. Eligible runs fail explicitly if configuration
is missing. Requiring the CI check for merges is a separate branch-protection setting.

Reproduce coverage locally:

```sh
python3 -m unittest discover -s scripts/sonar -p 'test_*.py'
swift test --enable-code-coverage
python3 scripts/sonar/coverage_to_sonar.py "$(swift test --show-codecov-path)" coverage/sonar.xml
```

Generated contracts, experiments, tests and tooling are excluded from analysis;
there is no explicit `sonar.sources` or `sonar.tests` override. Tests still
contribute coverage for SDK implementation. Coverage reports are ignored by Git.

## Protocol authority

`pi-sdk-typescript` owns the authoritative Zod protocol and generated artifacts. This repository contains an exact pinned snapshot, not a separate definition. `protocol/SOURCE.json` records the upstream Git revision and SHA-256 hashes. Swift tests verify snapshot hashes and exact bundled-schema/probe drift.

To import a new explicitly selected **clean, committed** TypeScript SDK checkout:

```sh
python3 scripts/protocol-artifacts.py import /path/to/pi-sdk-typescript
python3 scripts/protocol-artifacts.py check
swift test
```

Review and commit the resulting snapshot/manifest together. The script never discovers or writes to a sibling repository. Protocol generators emit portable artifacts in the TypeScript repository.

## Server integration ownership

Real Pi Server loopback tests live in Pi Chat's `test/swift-integration` harness and run there against its server and this Git-pinned SDK. They are deliberately not silently skipped in this repository: they are a separate mandatory integration suite. SDK unit tests use injected transports; passing them alone is not proof of real-server or full Swift parity.

## Swift session browsing and streaming subset (Pi Studio / Pi Pocket)

Baseline: stable **Xcode 26.1.1 (17B100), Swift 6.2.1**, unchanged iOS **26.1**
Simulator target. SwiftPM uses tools version 6.2. No beta-toolchain or older-iOS
compatibility work was added.

Public API: `PiClient`, injectable `PiTransport`, `URLSessionPiTransport`,
`PiDemoConnection`, `PiConnectionState`, `PiSessionEvent`, `DemoSession`, `DemoSessionProjection`,
`DemoMessage`, `DemoRunStatus`, `PiError`.
`connectDemo(projectPath:takingControl:)` initializes v2 with no optional
capabilities, then creates exactly one isolated runtime. `takingControl: true`
must follow explicit user consent: the existing server replaces its previous
controller on initialization. Server-canonical project paths are returned. The caller
must create the server-side demo directory before using this demo convenience API.

Product clients use `PiSessionConnection`: `connect(takingControl:)` initializes
without creating/selecting a session; `catalogues()` publishes complete conflated
`PiCatalogue` values with independent project/inventory revisions. Project records
include Quick Chats, saved history paths and worktree metadata. `attachSession(sessionId:)`
fetches a current snapshot of an existing runtime; `openSession(sessionPath:)`
attaches a known runtime by saved path or opens that history through the server;
`createSession(projectPath:)` explicitly creates a session. The app owns selection
and navigation. Rejected opens do not create fallback sessions or poison the connection.
Attachment buffers bounded in-flight events and validates response identity; repeat
attachment retains observed partial text for the currently selected runtime. Exactly one
runtime is observed at a time: selecting another session replaces the projection, and the
previous runtime keeps running on the server. Selection is refused only while another
selection is in flight, so switching a tab is never blocked by an admitted run or a
pending mutation, and responses are matched by request identity rather than by arrival
order. `send(_:)` and `stop()` are bound to the runtime observed when they were issued; a
late result only settles while that same runtime is still observed.

`sessionEvents()` is part of that contract, so a workspace can observe them through the
protocol rather than a concrete client. It publishes bounded identity events for the
observed runtime:
`.closed(sessionId:)` when the server ends it, and `.replaced(previous:current:)` when an
atomic runtime replacement moves the work to a new identity. A replacement also swaps the
open-session inventory entry immediately so no consumer sees neither identity; navigation
remains application-owned.

`states()` is a conflated stream of complete connection states, not a raw event
queue. Actor ownership, bounded keyed request correlation (at most eight requests in
flight, matched by request identity), ten-second default waits,
16 MiB text-frame bounds and one attempt per client bound the lifecycle.
`projections()` similarly conflates complete SDK-owned text projections; a slow
consumer does not lose text deltas. Transcript storage is bounded to 4,096 visible
messages / 16 MiB UTF-8 text, with explicit failure on overflow.
`disconnect()` cancels local waits/receiving and closes the transport; it never
sends abort/close. Mutation timeout/disconnect/cancellation is an unknown
outcome, never an automatic retry. Construct a fresh client only for another
explicit connection. Call disconnect on app teardown; the provided app model
also disposes its connection on deinit.

Supported operations: `server.initialize`, `session.create`, `session.open`,
`session.snapshot`, catalogue/inventory events, `message.send`, `run.abort`, local disconnect. `send(_:)` permits one nonempty plain-text turn
while idle (no slash/bash commands or steering). Acceptance is not completion:
starting/running/aborting states settle from authoritative runtime lifecycle.
`stop()` retains observed text and waits for settlement after an accepted abort;
a completed abort response is an authoritative idle no-op. Missing start/stop
settlement has a bounded ten-second default deadline and an unknown-outcome
failure, never an indefinite local admission spinner or automatic retry. That
deadline belongs to the runtime it was admitted for: a stale deadline cannot fail a
session that happens to be observed later, and another session's idle snapshot does not
cancel it.

Core events are validated against the shared contract, checked for process/runtime
identity and sequence, and finalized text is upserted without duplicating drafts.
Snapshots cannot regress watermarks. Locally observed stopped text is retained
when a snapshot has no finalized answer. Thinking/tools are validated but not
rendered; they still advance sequence. Structured questions and event gaps fail
explicitly when attached (blocked background sessions can still be listed). A closed
selected runtime publishes `PiSessionEvent.closed` and returns the connection to browsing;
replacement publishes `PiSessionEvent.replaced` and transfers its projection atomically to
the new identity. **Gap recovery is not implemented in
this MVP**; it terminates rather than showing an incomplete valid-looking stream.

No dialogs, public close API, reconnect/gap recovery, optional capabilities,
auth, UI, or full Swift SDK parity is claimed. Production Swift slice 7 and
real-Pi model conversation acceptance remain incomplete.

The internal schema evaluator supports only the vocabulary emitted by the v2 exporter, not arbitrary JSON Schema documents. Refresh bundled artifacts only with the explicit import command above; drift tests reject local divergence.

Tests check exact artifact drift, shared valid/malformed fixtures, denied
initialization/create, deadlines/unknown outcomes, duplicate connection guards,
cancellation, stale callbacks, unexpected closure and unreachable endpoints.
