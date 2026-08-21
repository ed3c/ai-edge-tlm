// swift-tools-version: 6.0
import PackageDescription
let package = Package(
    name: "AppleLiteRtLmAdapter",
    platforms: [.iOS(.v15), .macOS(.v12)],
    products: [.library(name: "AppleLiteRtLmAdapter", targets: ["AppleLiteRtLmAdapter"])],
    dependencies: [.package(path: "../../../bindings/swift")],
    targets: [
        .target(name: "AppleLiteRtLmAdapter", dependencies: [.product(name: "AIEdgeContracts", package: "swift")]),
        .testTarget(name: "AppleLiteRtLmAdapterTests", dependencies: ["AppleLiteRtLmAdapter", .product(name: "AIEdgeContracts", package: "swift")])
    ]
)
