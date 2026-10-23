# SonarQube Cloud — Design

## Proposed Design
- Follow the existing Pi Chat SonarQube Cloud setup for `ManuelSelch/pi-sdk-swift` in organization `manuelselch`.
- Add `sonar-project.properties` with UTF-8 encoding and exclusion-based scope; omit explicit `sonar.sources` and `sonar.tests`.
- Analyze SDK implementation. Exclude `.build`, `.swiftpm`, `.pi`, tests, generated contract snapshots, generation experiments, scripts, documentation, and package configuration from analysis.
- Extend the existing macOS GitHub Actions job to run Swift tests with coverage, export production Swift line coverage into Sonar generic coverage XML, and run a pinned SonarSource scanner action after successful checks.
- Read project identity from repository variables `SONAR_ORGANIZATION` and `SONAR_PROJECT_KEY`; read the analysis credential only from `SONAR_TOKEN`.
- Skip fork pull requests, which cannot access repository secrets. Require configuration explicitly on eligible runs rather than silently skipping missing credentials.
- Wait for the quality gate so a failed gate fails CI.

## Decisions & Trade-offs
- Use SonarQube Cloud, not the unrelated SonarQube MCP server, matching the existing organization setup.
- Use SwiftPM coverage with LLVM export and a small tested generic-format converter; SwiftPM does not produce an Xcode `.xcresult` bundle for the documented `xccov` workflow.
- Keep export and scan in the macOS job so coverage paths match the checkout; no extra artifact transfer is necessary.
- Excluded test files are not classified as Sonar test sources. Their execution still contributes implementation coverage.
- Import the repository into SonarQube Cloud and disable automatic analysis in favor of CI analysis. Project provisioning and the token remain external prerequisites; no credentials are currently configured in GitHub.

## Verification
- Test coverage conversion with covered/uncovered lines, merged regions, filename escaping, source filtering and malformed input.
- Generate coverage from real Swift tests and validate the resulting XML.
- Run all existing local pipeline suites and review workflow/configuration syntax.
- After credentials are available and changes are pushed, verify a real Cloud scan and quality-gate result. Branch-protection changes are outside this scope.

## Open Questions
None. Proposed defaults: organization `manuelselch`, project key `ManuelSelch_pi-sdk-swift`, coverage and quality-gate enforcement enabled.
