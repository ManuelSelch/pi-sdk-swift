import Foundation
import Testing
import PiSDK

/// Scenarios speak SDK behavior; this driver owns waits, clients and fixture cleanup.
final class ServerIntegrationDriver {
    private let fixture: LoopbackFixture
    private let ready: LoopbackFixture.Ready
    private var client: PiClient
    private var session: DemoSession?

    private init(fixture: LoopbackFixture, ready: LoopbackFixture.Ready) {
        self.fixture = fixture
        self.ready = ready
        client = PiClient(endpoint: ready.endpoint)
    }

    static func run(_ scenario: (ServerIntegrationDriver) async throws -> Void) async throws {
        let fixture = try LoopbackFixture()
        let ready = try await fixture.start()
        let driver = ServerIntegrationDriver(fixture: fixture, ready: ready)
        do {
            try await scenario(driver)
            await driver.client.disconnect()
            try await fixture.stop()
            struct Cleanup: Decodable { let created: Int; let retained: Int; let closed: Int }
            let directory = URL(fileURLWithPath: ready.directory)
            let cleanup = try JSONDecoder().decode(Cleanup.self, from: Data(contentsOf: directory.appendingPathComponent("cleanup.json")))
            try #require(cleanup.created == 1)
            try #require(cleanup.retained == 1)
            try #require(cleanup.closed == 1)
            try fixture.removeSuccessfulArtifacts()
        } catch {
            await driver.client.disconnect()
            try? await fixture.stop()
            fixture.reportRetainedDiagnostics()
            throw error
        }
    }

    func connectAndCreateOneRuntime() async throws {
        try await client.connect(takingControl: true)
        try #require(await client.catalogue.sessions.isEmpty)
        try await waitFor { await self.client.catalogue.projects.first?.quickChats == true }
        let created = try await client.createSession(projectPath: ready.directory)
        try #require(created.projectPath == ready.directory)
        try #require(await client.state == .ready(created))
        session = created
    }

    func completeStreamedTurn() async throws {
        try await client.send("Say hello")
        try await waitFor { await self.client.projection?.messages.last?.isPartial == true }
        let prefix = await client.projection?.messages.last?.text
        try await waitFor { await self.client.projection?.status == .idle }
        try #require(await client.projection?.messages.map(\.text) == ["Say hello", "Hello from the isolated Swift demo."])
        try #require(prefix != "Hello from the isolated Swift demo.")
    }

    func disconnectAndReattachRetainedRuntime() async throws {
        let session = try #require(session)
        await client.disconnect()
        client = PiClient(endpoint: ready.endpoint)
        try await client.connect(takingControl: true)
        try #require(await client.catalogue.sessions.count == 1)
        _ = try await client.attachSession(sessionId: session.sessionId)
        try #require(await client.projection?.messages.count == 2)
    }

    func stopNextTurnAndRetainPartialText() async throws {
        try await client.send("A second response to stop")
        try await waitFor { await self.client.projection?.messages.last?.isPartial == true }
        try await client.stop()
        try await waitFor { await self.client.projection?.status == .idle }
        // Include the authoritative finishWork snapshot, not just abort settlement.
        try await Task.sleep(for: .milliseconds(150))
        try #require(await client.projection?.messages.count == 4)
        try #require(await client.projection?.messages.last?.text.isEmpty == false)
    }

    static func expectUnreachableEndpointFailure() async throws {
        let client = PiClient(endpoint: URL(string: "ws://127.0.0.1:1/ws")!, requestTimeout: .seconds(1))
        await #expect(throws: PiError.self) { try await client.connectDemo(projectPath: "/tmp/pi-studio-demo", takingControl: true) }
        guard case .failed = await client.state else {
            Issue.record("Expected failed state")
            await client.disconnect()
            return
        }
        await client.disconnect()
    }
}
