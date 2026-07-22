#!/usr/bin/env kotlin

@file:DependsOn("org.yaml:snakeyaml:2.3")

import org.yaml.snakeyaml.Yaml
import java.io.File
import kotlin.system.exitProcess

val requiredFields = listOf("name", "description", "repo", "category", "languages", "trust", "author")
val validCategories = setOf("framework", "language", "database", "testing", "fullstack", "web", "workflow", "tool")
val validTrust = setOf("official", "curated", "community")

val rootDir = __FILE__.absoluteFile.parentFile.parentFile
val skillsDir = File(rootDir, "skills")
val siteDir = File(rootDir, "site")
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

val sharedThemeTemplates = listOf(
    "template.html",
    "blog-index-template.html",
    "blog-post-template.html",
    "eval-viewer-template.html",
    "404-template.html"
)
val versionedThemeReference = "/jvm-skills-theme.css?v={{THEME_VERSION}}"

sharedThemeTemplates.forEach { templateName ->
    val template = File(siteDir, templateName)
    if (!template.readText().contains(versionedThemeReference)) {
        errors.add("site/$templateName: shared theme URL must include the generated content version")
    }
}

val brandAssets = listOf("preview.png", "preview.webp", "favicon.svg", "apple-touch-icon.png")
brandAssets.forEach { assetName ->
    val asset = File(siteDir, assetName)
    if (!asset.isFile || asset.length() == 0L) {
        errors.add("site/$assetName: required brand asset is missing or empty")
    }
}

val brandedTemplates = sharedThemeTemplates + listOf("big-sky-template.html", "spring-io-template.html")
brandedTemplates.forEach { templateName ->
    val html = File(siteDir, templateName).readText()
    if (!html.contains("href=\"/favicon.svg\"") || !html.contains("href=\"/apple-touch-icon.png\"")) {
        errors.add("site/$templateName: must reference the shared favicon and Apple touch icon")
    }
}

if (errors.isNotEmpty()) {
    println("Validation errors:")
    errors.forEach { println("  ✗ $it") }
    exitProcess(1)
} else {
    val count = skillsDir.walk().count { it.isFile && (it.extension == "yaml" || it.extension == "yml") }
    println("✓ All $count skill YAML files and shared site assets valid")
}
