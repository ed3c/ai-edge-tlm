package io.ed3c.aiedge.contracts.v1

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
