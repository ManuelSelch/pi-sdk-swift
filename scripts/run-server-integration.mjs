import { spawnSync } from "node:child_process";
import { readFileSync, realpathSync } from "node:fs";
import { fileURLToPath } from "node:url";

try {
  if (process.argv.length !== 2) throw new Error("The integration runner does not accept arguments.");
  const integration = fileURLToPath(new URL("../integration/", import.meta.url));
  const install = "Run npm ci --ignore-scripts --prefix integration first.";
  let manifest;
  try {
    manifest = JSON.parse(readFileSync(new URL("../integration/node_modules/@manuelselch/pi-server/package.json", import.meta.url), "utf8"));
  } catch {
    throw new Error(`Missing installed integration server. ${install}`);
  }
  if (manifest.version !== "0.1.0") throw new Error(`Expected integration server 0.1.0, got ${manifest.version}. ${install}`);
  const node = realpathSync(process.execPath);
  const fixture = spawnSync(node, ["--input-type=module", "--eval", 'await import("@manuelselch/pi-server/testing/loopback");'], {
    cwd: integration, encoding: "utf8", timeout: 30_000,
  });
  if (fixture.error || fixture.status !== 0) throw new Error(`Cannot load the public server loopback fixture. ${install}\n${fixture.error?.message ?? fixture.stderr}`);
  if (process.platform !== "darwin") throw new Error("Swift server integration requires macOS and Xcode 26.1.1.");
  const result = spawnSync("/usr/bin/xcrun", ["swift", "test", "--package-path", integration], {
    cwd: integration,
    env: { ...process.env, PI_SWIFT_NODE: node },
    stdio: "inherit",
    timeout: 300_000,
  });
  if (result.error) throw result.error;
  process.exitCode = result.status ?? 1;
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
