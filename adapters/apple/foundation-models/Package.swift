// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "AppleFoundationAdapter",
    platforms: [.iOS(.v18), .macOS(.v15)],
    products: [
        .library(name: "AppleFoundationAdapter", targets: ["AppleFoundationAdapter"])
    ],
    dependencies: [
        .package(path: "../../../bindings/swift")
    ],
    targets: [
        .target(
            name: "AppleFoundationAdapter",
            dependencies: [.product(name: "AIEdgeContracts", package: "swift")]
        ),
        .testTarget(
            name: "AppleFoundationAdapterTests",
            dependencies: ["AppleFoundationAdapter", .product(name: "AIEdgeContracts", package: "swift")]
        )
    ]
)
