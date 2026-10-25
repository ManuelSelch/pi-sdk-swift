import Testing

@Test func actualServerStreamsStopsAndRetainsRuntimeAcrossDisconnect() async throws {
    try await ServerIntegrationDriver.run { server in
        try await server.connectAndCreateOneRuntime()
        try await server.completeStreamedTurn()
        try await server.disconnectAndReattachRetainedRuntime()
        try await server.stopNextTurnAndRetainPartialText()
    }
}

@Test func unreachableEndpointFailsWithoutIndefiniteConnecting() async throws {
    try await ServerIntegrationDriver.expectUnreachableEndpointFailure()
}
