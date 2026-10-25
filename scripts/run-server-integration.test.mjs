import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { copyFileSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

function withCheckout(run) {
  const root = mkdtempSync(join(tmpdir(), "pi-swift-runner-test-"));
  try {
    mkdirSync(join(root, "scripts"));
    mkdirSync(join(root, "integration"));
    copyFileSync(new URL("./run-server-integration.mjs", import.meta.url), join(root, "scripts/run-server-integration.mjs"));
    writeFileSync(join(root, "integration/package.json"), '{"private":true,"type":"module"}');
    run(root);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
}

test("missing server dependency fails explicitly rather than skipping Swift integration", () => {
  withCheckout(root => {
    const result = spawnSync(process.execPath, [join(root, "scripts/run-server-integration.mjs")], { encoding: "utf8" });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /npm ci --ignore-scripts --prefix integration/);
    assert.doesNotMatch(result.stdout, /Test Suite.*passed/);
  });
});

test("unexpected installed server version fails before running Swift", () => {
  withCheckout(root => {
    const server = join(root, "integration/node_modules/@manuelselch/pi-server");
    mkdirSync(server, { recursive: true });
    writeFileSync(join(server, "package.json"), '{"version":"99.0.0"}');
    const result = spawnSync(process.execPath, [join(root, "scripts/run-server-integration.mjs")], { encoding: "utf8" });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /Expected integration server 0.1.0, got 99.0.0/);
  });
});

test("missing public fixture export fails before running Swift", () => {
  withCheckout(root => {
    const server = join(root, "integration/node_modules/@manuelselch/pi-server");
    mkdirSync(server, { recursive: true });
    writeFileSync(join(server, "package.json"), '{"version":"0.1.0","exports":{}}');
    const result = spawnSync(process.execPath, [join(root, "scripts/run-server-integration.mjs")], { encoding: "utf8" });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /Cannot load the public server loopback fixture/);
  });
});

test("runner does not accept an alternate fixture or checkout argument", () => {
  const result = spawnSync(process.execPath, [fileURLToPath(new URL("./run-server-integration.mjs", import.meta.url)), "untrusted"], { encoding: "utf8" });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /does not accept arguments/);
});
