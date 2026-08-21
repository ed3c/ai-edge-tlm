from __future__ import annotations

import re
from typing import Any

SWIFT_KEYWORDS = {
    "associatedtype", "class", "deinit", "enum", "extension", "fileprivate", "func",
    "import", "init", "inout", "internal", "let", "open", "operator", "private",
    "precedencegroup", "protocol", "public", "rethrows", "static", "struct", "subscript",
    "typealias", "var", "break", "case", "continue", "default", "defer", "do", "else",
    "fallthrough", "for", "guard", "if", "in", "repeat", "return", "switch", "where",
    "while", "as", "Any", "catch", "false", "is", "nil", "super", "self", "Self",
    "throw", "throws", "true", "try", "_", "await", "some", "any", "actor", "nonisolated",
}


def enum_case(value: str) -> str:
    parts = [part.lower() for part in re.split(r"[^A-Za-z0-9]+", value) if part]
    case = parts[0] + "".join(part.title() for part in parts[1:]) if parts else "value"
    return "_" + case if case[:1].isdigit() or case in SWIFT_KEYWORDS else case


def swift_type(t: Any, optional: bool = False) -> str:
    if isinstance(t, str):
        base = {
            "string": "String",
            "integer": "Int64",
            "number": "Double",
            "boolean": "Bool",
            "json": "JSONValue",
            "json_object": "[String: JSONValue]",
            "string_map": "[String: String]",
        }[t]
    elif "ref" in t:
        base = t["ref"]
    else:
        base = f"[{swift_type(t['array'])}]"
    return base + ("?" if optional else "")


def render_support() -> str:
    return '''import Foundation

public enum JSONValue: Codable, Equatable, Sendable {
    case string(String)
    case integer(Int64)
    case number(Double)
    case boolean(Bool)
    case object([String: JSONValue])
    case array([JSONValue])
    case null

    public init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if container.decodeNil() { self = .null; return }
        if let value = try? container.decode(Bool.self) { self = .boolean(value); return }
        if let value = try? container.decode(Int64.self) { self = .integer(value); return }
        if let value = try? container.decode(Double.self) { self = .number(value); return }
        if let value = try? container.decode(String.self) { self = .string(value); return }
        if let value = try? container.decode([String: JSONValue].self) { self = .object(value); return }
        if let value = try? container.decode([JSONValue].self) { self = .array(value); return }
        throw DecodingError.dataCorruptedError(in: container, debugDescription: "Unsupported JSON value")
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .string(let value): try container.encode(value)
        case .integer(let value): try container.encode(value)
        case .number(let value): try container.encode(value)
        case .boolean(let value): try container.encode(value)
        case .object(let value): try container.encode(value)
        case .array(let value): try container.encode(value)
        case .null: try container.encodeNil()
        }
    }
}
'''


def render_enums(spec: dict[str, Any]) -> str:
    lines = ["import Foundation", ""]
    for name, values in spec["enums"].items():
        lines.append(f"public enum {name}: String, Codable, Equatable, Sendable {{")
        for value in values:
            lines.append(f'    case {enum_case(value)} = "{value}"')
        lines += ["}", ""]
    return "\n".join(lines)


def render_records(spec: dict[str, Any], names: list[str]) -> str:
    lines = ["import Foundation", ""]
    for name in names:
        record = spec["records"][name]
        lines.append(f"/// {record['description']}")
        lines.append(f"public struct {name}: Codable, Equatable, Sendable {{")
        for field in record["fields"]:
            optional = not field.get("required", True)
            lines.append(f"    public let {field['name']}: {swift_type(field['type'], optional)}")
        lines += ["", "    public init("]
        for index, field in enumerate(record["fields"]):
            optional = not field.get("required", True)
            default = " = nil" if optional else ""
            comma = "," if index < len(record["fields"]) - 1 else ""
            lines.append(f"        {field['name']}: {swift_type(field['type'], optional)}{default}{comma}")
        lines.append("    ) {")
        for field in record["fields"]:
            lines.append(f"        self.{field['name']} = {field['name']}")
        lines += ["    }", "}", ""]
    return "\n".join(lines)


def render_swift_outputs(spec: dict[str, Any]) -> dict[str, str]:
    outputs = {
        "bindings/swift/Sources/AIEdgeContracts/JSONValue.swift": render_support(),
        "bindings/swift/Sources/AIEdgeContracts/Enums.swift": render_enums(spec),
        "bindings/swift/Package.swift": '''// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "AIEdgeContracts",
    platforms: [.iOS(.v16), .macOS(.v13)],
    products: [.library(name: "AIEdgeContracts", targets: ["AIEdgeContracts"])],
    targets: [.target(name: "AIEdgeContracts")]
)
''',
        "bindings/swift/README.md": "# Swift v1 contracts\n\nGenerated from the modular contract model. No provider SDK dependency is permitted.\n",
    }
    for group, names in spec["record_groups"].items():
        outputs[f"bindings/swift/Sources/AIEdgeContracts/{group.title()}Contracts.swift"] = render_records(spec, names)
    return outputs
