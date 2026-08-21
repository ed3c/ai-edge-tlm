from __future__ import annotations

import re
from typing import Any


def enum_case(value: str) -> str:
    case = re.sub(r"[^A-Za-z0-9_]", "_", value).upper()
    return "_" + case if case[:1].isdigit() else case


def kotlin_type(t: Any, optional: bool = False) -> str:
    if isinstance(t, str):
        base = {
            "string": "String", "integer": "Long", "number": "Double", "boolean": "Boolean",
            "json": "JsonValue", "json_object": "Map<String, JsonValue>", "string_map": "Map<String, String>",
        }[t]
    elif "ref" in t:
        base = t["ref"]
    else:
        base = f"List<{kotlin_type(t['array'])}>"
    return base + ("?" if optional else "")


def wire_expr(t: Any, value: str, enums: set[str], records: set[str]) -> str:
    if isinstance(t, str):
        if t == "json": return f"{value}.toWireValue()"
        if t == "json_object": return f"{value}.mapValues {{ it.value.toWireValue() }}"
        return value
    if "ref" in t:
        return f"{value}.wireValue" if t["ref"] in enums else f"{value}.toWireValue()"
    inner = t["array"]
    if isinstance(inner, dict) and "ref" in inner:
        item = "item.wireValue" if inner["ref"] in enums else "item.toWireValue()"
    elif inner == "json": item = "item.toWireValue()"
    elif inner == "json_object": item = "item.mapValues { it.value.toWireValue() }"
    else: item = "item"
    return f"{value}.map {{ item -> {item} }}"


def render_support(package: str) -> str:
    template = r'''PACKAGE_MARKER

interface WireEncodable { fun toWireValue(): Any? }

sealed interface JsonValue : WireEncodable
data class JsonString(val value: String) : JsonValue { override fun toWireValue(): Any? = value }
data class JsonInteger(val value: Long) : JsonValue { override fun toWireValue(): Any? = value }
data class JsonNumber(val value: Double) : JsonValue { override fun toWireValue(): Any? = value }
data class JsonBoolean(val value: Boolean) : JsonValue { override fun toWireValue(): Any? = value }
data class JsonObject(val value: Map<String, JsonValue>) : JsonValue {
    override fun toWireValue(): Any? = value.mapValues { it.value.toWireValue() }
}
data class JsonArray(val value: List<JsonValue>) : JsonValue {
    override fun toWireValue(): Any? = value.map { it.toWireValue() }
}
data object JsonNull : JsonValue { override fun toWireValue(): Any? = null }

object CanonicalJson {
    fun encode(value: Any?): String = buildString { appendValue(value) }
    private fun StringBuilder.appendValue(value: Any?) {
        when (value) {
            null -> append("null")
            is String -> appendQuoted(value)
            is Boolean -> append(if (value) "true" else "false")
            is Byte, is Short, is Int, is Long -> append(value.toString())
            is Float -> appendNumber(value.toDouble())
            is Double -> appendNumber(value)
            is Map<*, *> -> {
                append('{')
                value.entries.map { it.key as String to it.value }.sortedBy { it.first }.forEachIndexed { index, entry ->
                    if (index > 0) append(',')
                    appendQuoted(entry.first); append(':'); appendValue(entry.second)
                }
                append('}')
            }
            is Iterable<*> -> {
                append('[')
                value.forEachIndexed { index, item -> if (index > 0) append(','); appendValue(item) }
                append(']')
            }
            is WireEncodable -> appendValue(value.toWireValue())
            else -> error("Unsupported wire value: ${value::class.qualifiedName}")
        }
    }
    private fun StringBuilder.appendNumber(value: Double) {
        require(value.isFinite()) { "Non-finite JSON number" }; append(value.toString())
    }
    private fun StringBuilder.appendQuoted(value: String) {
        append('"')
        value.forEach { ch ->
            when (ch.code) {
                34 -> { append(92.toChar()); append(34.toChar()) }
                92 -> { append(92.toChar()); append(92.toChar()) }
                8 -> { append(92.toChar()); append('b') }
                12 -> { append(92.toChar()); append('f') }
                10 -> { append(92.toChar()); append('n') }
                13 -> { append(92.toChar()); append('r') }
                9 -> { append(92.toChar()); append('t') }
                else -> if (ch.code < 0x20) {
                    append(92.toChar()); append('u'); append("%04x".format(ch.code))
                } else append(ch)
            }
        }
        append('"')
    }
}
'''
    return template.replace("PACKAGE_MARKER", f"package {package}")


def render_enums(spec: dict[str, Any]) -> str:
    lines = [f"package {spec['package']['kotlin']}", ""]
    for name, values in spec["enums"].items():
        lines.append(f"enum class {name}(val wireValue: String) {{")
        for index, value in enumerate(values):
            lines.append(f'    {enum_case(value)}("{value}")' + ("," if index < len(values) - 1 else ";"))
        lines += ["", f"    companion object {{ fun fromWire(value: String): {name} = entries.first {{ it.wireValue == value }} }}", "}", ""]
    return "\n".join(lines)


def render_records(spec: dict[str, Any], names: list[str]) -> str:
    enums, records = set(spec["enums"]), set(spec["records"])
    lines = [f"package {spec['package']['kotlin']}", ""]
    for name in names:
        record = spec["records"][name]
        lines.append(f"data class {name}(")
        for index, field in enumerate(record["fields"]):
            optional = not field.get("required", True)
            suffix = "," if index < len(record["fields"]) - 1 else ""
            lines.append(f"    val {field['name']}: {kotlin_type(field['type'], optional)}" + (" = null" if optional else "") + suffix)
        lines += [") : WireEncodable {", "    override fun toWireValue(): Any? {", "        val out = linkedMapOf<String, Any?>()"]
        for field in record["fields"]:
            field_name = field["name"]
            if field.get("required", True):
                lines.append(f'        out["{field_name}"] = {wire_expr(field["type"], field_name, enums, records)}')
            else:
                lines.append(f'        {field_name}?.let {{ value -> out["{field_name}"] = {wire_expr(field["type"], "value", enums, records)} }}')
        lines += ["        return out", "    }", "}", ""]
    return "\n".join(lines)


def render_kotlin_outputs(spec: dict[str, Any]) -> dict[str, str]:
    package = spec["package"]["kotlin"]
    base = f"bindings/kotlin/src/main/kotlin/{package.replace('.', '/')}"
    outputs = {
        f"{base}/WireSupport.kt": render_support(package),
        f"{base}/Enums.kt": render_enums(spec),
        "bindings/kotlin/README.md": "# Kotlin v1 contracts\n\nGenerated from the modular contract model. No provider SDK dependency is permitted.\n",
        "bindings/kotlin/compile.sh": "#!/usr/bin/env bash\nset -euo pipefail\nroot=$(cd \"$(dirname \"$0\")/../..\" && pwd)\nmapfile -t files < <(find \"$root/bindings/kotlin/src/main/kotlin\" -name '*.kt' -print | sort)\nkotlinc \"${files[@]}\" -d \"${TMPDIR:-/tmp}/ai-edge-contracts-kotlin.jar\"\n",
    }
    for group, names in spec["record_groups"].items():
        outputs[f"{base}/{group.title()}Contracts.kt"] = render_records(spec, names)
    return outputs
