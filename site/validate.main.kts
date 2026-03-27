#!/usr/bin/env kotlin

@file:DependsOn("org.yaml:snakeyaml:2.3")

import org.yaml.snakeyaml.Yaml
import java.io.File
import kotlin.system.exitProcess

val requiredFields = listOf("name", "description", "repo", "category", "tools", "languages", "trust", "author")
val validCategories = setOf("database", "web", "infrastructure", "testing", "architecture", "workflow")
val validTrust = setOf("official", "curated", "community")

val rootDir = File(__FILE__).parentFile.parentFile.absoluteFile
val skillsDir = File(rootDir, "skills")
val yaml = Yaml()
val errors = mutableListOf<String>()

skillsDir.walk()
    .filter { it.isFile && (it.extension == "yaml" || it.extension == "yml") }
    .sorted()
    .forEach { file ->
        val relativePath = file.relativeTo(rootDir)
        @Suppress("UNCHECKED_CAST")
        val data = try {
            yaml.load<Map<String, Any>>(file.readText())
        } catch (e: Exception) {
            errors.add("$relativePath: invalid YAML — ${e.message}")
            return@forEach
        }

        if (data == null) {
            errors.add("$relativePath: empty or invalid YAML")
            return@forEach
        }

        for (field in requiredFields) {
            val value = data[field]
            if (value == null || (value is String && value.isBlank()) || (value is List<*> && value.isEmpty())) {
                errors.add("$relativePath: missing required field \"$field\"")
            }
        }

        val category = data["category"]?.toString() ?: ""
        if (category !in validCategories) {
            errors.add("$relativePath: invalid category \"$category\" (must be one of $validCategories)")
        }

        val trust = data["trust"]?.toString() ?: ""
        if (trust !in validTrust) {
            errors.add("$relativePath: invalid trust \"$trust\" (must be expert or community)")
        }
    }

if (errors.isNotEmpty()) {
    println("Validation errors:")
    errors.forEach { println("  ✗ $it") }
    exitProcess(1)
} else {
    val count = skillsDir.walk().count { it.isFile && (it.extension == "yaml" || it.extension == "yml") }
    println("✓ All $count skill YAML files valid")
}
