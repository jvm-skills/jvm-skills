#!/usr/bin/env kotlin

@file:DependsOn("org.yaml:snakeyaml:2.3")

import org.yaml.snakeyaml.Yaml
import java.io.File
import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

val siteDir = __FILE__.absoluteFile.parentFile
val rootDir = siteDir.parentFile
val skillsDir = File(rootDir, "skills")
val templateFile = File(siteDir, "template.html")
val distDir = File(rootDir, "dist")
val outputFile = File(distDir, "index.html")

val categories = listOf("framework", "language", "database", "testing", "fullstack", "web", "workflow", "tool")

fun htmlEscape(s: String): String = s
    .replace("&", "&amp;")
    .replace("<", "&lt;")
    .replace(">", "&gt;")
    .replace("\"", "&quot;")

// Build card HTML
val yaml = Yaml()
var totalSkills = 0
val skillCards = buildString {
    for (category in categories) {
        val catDir = File(skillsDir, category)
        if (!catDir.isDirectory) continue

        val yamlFiles = catDir.listFiles { f -> f.extension == "yaml" || f.extension == "yml" }
            ?.sorted() ?: continue
        if (yamlFiles.isEmpty()) continue

        append("""<section class="category-section" data-category="$category">""")
        append("\n")
        append("""<h2 class="category-header"><span class="prompt">~/skills/$category/</span> <span class="ls-marker">ls</span></h2>""")
        append("\n")
        append("""<div class="skills-grid">""")
        append("\n")

        for (yamlFile in yamlFiles) {
            @Suppress("UNCHECKED_CAST")
            val skill = yaml.load<Map<String, Any>>(yamlFile.readText()) ?: continue

            val name = skill["name"]?.toString() ?: ""
            val description = skill["description"]?.toString() ?: ""
            val repo = skill["repo"]?.toString() ?: ""
            val skillPath = skill["skill_path"]?.toString() ?: ""
            val author = skill["author"]?.toString() ?: ""
            val trust = skill["trust"]?.toString() ?: "community"

            val languages = (skill["languages"] as? List<*>)?.map { it.toString() } ?: emptyList()
            val tech = (skill["tech"] as? List<*>)?.map { it.toString() } ?: emptyList()
            val tags = (skill["tags"] as? List<*>)?.map { it.toString() } ?: emptyList()

            val langsCsv = languages.joinToString(",")
            val techCsv = tech.joinToString(",")
            val tagsCsv = tags.joinToString(",")

            val langsHtml = languages.joinToString("") { "<span>$it</span>" }
            val techHtml = tech.joinToString("") { "<span>${htmlEscape(it)}</span>" }
            val tagsHtml = tags.joinToString("") { "<span>${htmlEscape(it)}</span>" }

            append("""<article class="skill-card" data-languages="$langsCsv" data-tech="$techCsv" data-trust="$trust" data-tags="$tagsCsv">""")
            append("\n")
            append("""<div class="card-titlebar">""")
            append("""<span class="card-dots"><span></span><span></span><span></span></span>""")
            append("</div>\n")
            append("""<div class="card-body">""")
            append("\n")
            val skillUrl = if (skillPath.isNotEmpty()) "https://github.com/${htmlEscape(repo)}/blob/main/${htmlEscape(skillPath)}" else "https://github.com/${htmlEscape(repo)}"
            val skillDir = if (skillPath.contains("/")) skillPath.substringBeforeLast("/") else ""
            val skillDirUrl = if (skillDir.isNotEmpty()) "https://github.com/$repo/tree/main/$skillDir" else "https://github.com/$repo"
            val skillSlug = if (skillDir.isNotEmpty()) skillDir.substringAfterLast("/") else repo.substringAfterLast("/")
            val installText = "Fetch the skill from $skillDirUrl and save all files to .claude/skills/$skillSlug/"

            append("""<h3 class="skill-name"><a href="$skillUrl">${htmlEscape(name)}</a></h3>""")
            append("\n")
            append("""<p class="skill-description">${htmlEscape(description)}</p>""")
            append("\n")
            append("""<div class="skill-meta">""")
            append("""<span class="skill-author">by ${htmlEscape(author)}</span>""")
            append("""<button class="copy-install" data-install="${htmlEscape(installText)}" type="button" title="Copy install instruction">install</button>""")
            append("</div>\n")
            append("""<div class="skill-languages">$langsHtml</div>""")
            append("\n")
            if (tech.isNotEmpty()) {
                append("""<div class="skill-tech">$techHtml</div>""")
                append("\n")
            }
            append("""<div class="skill-tags">$tagsHtml</div>""")
            append("\n")
            append("</div>\n</article>\n")
            totalSkills++
        }

        append("</div>\n</section>\n")
    }
}

// Read template, replace placeholders, write output
val generatedDate = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm 'UTC'")
    .withZone(ZoneOffset.UTC)
    .format(Instant.now())

val template = templateFile.readText()
val output = template
    .replace("{{SKILL_CARDS}}", skillCards)
    .replace("{{GENERATED_DATE}}", generatedDate)

distDir.mkdirs()
outputFile.writeText(output)

println("✓ Built dist/index.html ($totalSkills skills across ${categories.size} categories)")
println("  Generated: $generatedDate")
