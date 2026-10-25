# Published-server integration

This test-only SwiftPM harness depends on the root checkout's `PiSDK` product.
Its separate npm manifest pins `@manuelselch/pi-server@0.1.0`; the committed
lockfile records the full dependency tree and registry integrity. Neither package
is a runtime dependency of Swift consumers.

## Run

Use macOS with Xcode 26.1.1 / Swift 6.2.1 and Node 24:

```sh
# From the pi-sdk-swift repository root:
node --test scripts/run-server-integration.test.mjs
npm ci --ignore-scripts --prefix integration
npm test --prefix integration
```

The runner verifies the installed server version and public fixture export before
invoking Swift through `/usr/bin/xcrun`. It passes the absolute executable of its
own Node process to the driver, so the fixture never searches PATH. No global
server installation, SDK Git bundle, source compilation or lifecycle script is
needed. Run through the runner rather than directly invoking the SwiftPM harness;
missing Node configuration is an explicit error.

## Ownership and isolation

Scenarios use `ServerIntegrationDriver`; it owns waits, real SDK clients, process
lifetime and assertions. `LoopbackFixture` owns bounded readiness/shutdown and
retained diagnostics. Each server allocates private temporary state and an
ephemeral IPv4 loopback port. The public server fixture supplies a deterministic
fake runtime, not a live Pi/model session.

The successful scenario verifies:
- Initialize without creating a runtime, then create exactly one.
- Receive partial text and the final response in order.
- Disconnect without closing the runtime; reconnect and attach its snapshot.
- Stop a second streaming turn while preserving partial text.
- Shutdown explicitly closes the retained runtime, confirmed by the server's
  `cleanup.json` receipt.

The second scenario checks an unreachable endpoint fails within its deadline.
Runner regression tests check missing/wrong dependencies, broken public exports
and unsupported arguments fail before Swift is invoked.

Successful logs/workspaces are removed. Failures retain server logs under
`integration/.artifacts/` and the isolated fixture workspace; paths are printed
for inspection. CI uploads logs for seven days. The fixture's readiness record
also identifies its temporary workspace. Local failed workspaces can be removed
after inspection.

Unit/probe tests remain in the root package and do not require npm. Both suites
are required in CI; branch protection must separately require the relevant job.
This compatibility suite is not full Swift parity or a real-model acceptance test.
