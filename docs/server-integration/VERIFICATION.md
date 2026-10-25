# Server integration — Slice 1 verification

Verified locally on 2026-10-25 with Xcode/Swift 6.2.1. The new mandatory CI job is configured, not remotely executed by this task.

## Clean-source acceptance

Exported the staged repository into a new temporary directory named `Swift SDK checkout`, without `.git`, node_modules, build caches, Chat or sibling packages. The arbitrary checkout name and spaces are intentional; the harness explicitly names its local PiSDK dependency.

Passed before installing npm dependencies:
- `swift build`
- `swift test`: 34 Swift Testing tests and 6 XCTest probe tests.
- `python3 scripts/protocol-artifacts.py check`
- Coverage-converter unit tests: 9 passed.

After `npm ci --ignore-scripts --prefix integration`:
- Node 24.22.1 runner prerequisite tests: 4 passed (missing dependency, wrong version, missing export, unexpected argument).
- Node 24.22.1 integration runner: 2 Swift scenarios passed, using published `@manuelselch/pi-server@0.1.0` and the exported SDK sources.
- Real-server scenario checked streaming, Stop, disconnect/reattachment and `{ created: 1, retained: 1, closed: 1 }` shutdown receipt.
- Both integration scenarios also passed in the primary checkout with Node 26.5.0.

The missing-prerequisite runner failed explicitly before dependency installation; it did not silently skip the suite. Root Swift tests passed independently. Git diff whitespace checks passed.

## Limits and follow-up

- CI workflow execution and branch protection were not changed remotely; nothing was pushed or published.
- This uses a real server and real URLSession transport with a deterministic fake runtime, not a live model or full Swift parity acceptance.
- npm audit reports 3 findings (2 moderate, 1 high), originating from the published server's Pi/undici dependency tree. No automatic dependency fix is available for the pinned server; upgrading/publishing that dependency is outside this slice. Integration runs only the isolated loopback fake runtime with no model credentials.
- Chat's old Swift harness remains unchanged until slice 2. Server code and server-owned package/fixture tests are unchanged.
