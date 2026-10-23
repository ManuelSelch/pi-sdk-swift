import CryptoKit
import Foundation
import Testing

@Test func pinnedProtocolArtifactsMatchTheirSourceManifest() throws {
    let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    struct Manifest: Decodable { let sourceRevision: String; let files: [String: String] }
    let manifest = try JSONDecoder().decode(Manifest.self, from: Data(contentsOf: root.appendingPathComponent("protocol/SOURCE.json")))
    #expect(manifest.sourceRevision.range(of: "^[0-9a-f]{40}$", options: .regularExpression) != nil)
    #expect(!manifest.files.isEmpty)
    for (path, expected) in manifest.files {
        let bytes = try Data(contentsOf: root.appendingPathComponent("protocol").appendingPathComponent(path))
        #expect(SHA256.hash(data: bytes).map { String(format: "%02x", $0) }.joined() == expected, "Artifact drift: \\(path)")
    }
    #expect(try Data(contentsOf: root.appendingPathComponent("experiments/swift-generation/Sources/GeneratedModels.swift")) == Data(contentsOf: root.appendingPathComponent("protocol/swift/GeneratedModels.swift")))
}
