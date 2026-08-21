// swift-tools-version: 6.0
import PackageDescription
let package = Package(
    name: "IOSReferenceHost",
    products: [
        .library(name: "IOSReferenceHost", targets: ["IOSReferenceHost"]),
        .executable(name: "ios-reference-golden", targets: ["Golden"]),
    ],
    dependencies: [.package(path: "../../bindings/swift")],
    targets: [
        .target(name: "IOSReferenceHost", dependencies: [.product(name: "AIEdgeContracts", package: "swift")]),
        .executableTarget(name: "Golden", dependencies: ["IOSReferenceHost"]),
        .testTarget(name: "IOSReferenceHostTests", dependencies: ["IOSReferenceHost"]),
    ]
)
