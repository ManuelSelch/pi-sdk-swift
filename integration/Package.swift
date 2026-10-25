// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "PiServerIntegration",
    platforms: [.macOS(.v15)],
    dependencies: [.package(name: "PiSDK", path: "..")],
    targets: [.testTarget(
        name: "PiServerIntegrationTests",
        dependencies: [.product(name: "PiSDK", package: "PiSDK")]
    )]
)
