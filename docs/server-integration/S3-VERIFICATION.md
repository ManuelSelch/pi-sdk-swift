# Server integration — Slice 3 verification

Verified locally on 2026-10-25 from clean source
`6c41df3a0aeff22530a6d983c157e2c9bbba558b`, exported without Git, build caches,
npm installations, Chat or sibling packages into a directory named
`Swift SDK checkout`. Toolchain: Xcode 26.1.1 / Swift 6.2.1; integration Node 24.22.1.

## Node-independent Swift package

With `integration/node_modules` absent and PATH restricted to
`/usr/bin:/bin:/usr/sbin:/sbin`, both Node and npm were unavailable:

- `xcrun swift build`: passed.
- `xcrun swift test --enable-code-coverage`: **34 Swift Testing + 6 XCTest probe tests passed**.

Separately, the pinned protocol snapshot check, **9** coverage-converter tests and
conversion of the resulting Swift coverage report passed. No Node-dependent
SwiftPM product, build plugin or root dependency was introduced.

## Published-server compatibility

- **4 runner prerequisite tests passed**.
- Running the actual integration runner before installing the server failed
  explicitly with the expected missing-dependency message.
- `npm ci --ignore-scripts --prefix integration`: passed using the committed lock.
- `npm test --prefix integration`: **2 real URLSession/server scenarios passed**.
  Verified initialization/create, partial/final streaming, retained runtime after
  disconnect, reattachment, Stop with retained partial text, bounded unreachable
  endpoint failure and shutdown receipt `{ created: 1, retained: 1, closed: 1 }`.

The harness depends on this export's root PiSDK product, not a Git bundle or an
installed SDK snapshot. Its public compiled fixture comes from **npm server 0.1.0**.
The server repository separately verified its current **0.1.1** source and packed
artifact; this does not expand the Swift suite's pinned-version claim.

## Ownership and limits

The SDK owns Swift behavior and real-transport compatibility, including driver
deadlines/process cleanup and failure diagnostics. The server owns the fixture
implementation and its package/regression checks; Chat owns no Swift validation.
Chat retains plain-Node installed-fixture safety checks, including cleanup-file
and symlink overwrite rejection; these were not dropped.

Inspected CI wiring: `server-integration` runs unconditionally for push,
pull_request and manual triggers, on macOS with Node 24 and the locked npm install.
The separate `swift` job needs no Node setup. Diagnostics upload on integration
failure. Branch-protection requirements still need separate remote configuration.

The integration install reported **3 npm audit findings (2 moderate, 1 high)**;
no dependency changes or audit fixes were made. These are deterministic fake-runtime
checks, not full Swift parity or real-model acceptance. No remote CI/Sonar run,
publication, push or live-service restart was performed.
