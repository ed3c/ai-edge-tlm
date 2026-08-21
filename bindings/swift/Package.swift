// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "AIEdgeContracts",
    platforms: [.iOS(.v16), .macOS(.v13)],
    products: [.library(name: "AIEdgeContracts", targets: ["AIEdgeContracts"])],
    targets: [.target(name: "AIEdgeContracts")]
)
