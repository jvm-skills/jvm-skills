#!/usr/bin/env kotlin

@file:DependsOn("org.yaml:snakeyaml:2.3")
@file:DependsOn("org.commonmark:commonmark:0.24.0")

import org.yaml.snakeyaml.Yaml
import org.commonmark.parser.Parser
import org.commonmark.renderer.html.HtmlRenderer
import java.io.File
import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

val siteDir = __FILE__.absoluteFile.parentFile
val rootDir = siteDir.parentFile
val skillsDir = File(rootDir, "skills")
val blogDir = File(rootDir, "blog")
val templateFile = File(siteDir, "template.html")
val blogPostTemplate = File(siteDir, "blog-post-template.html")
val blogIndexTemplate = File(siteDir, "blog-index-template.html")
val distDir = File(rootDir, "dist")
val outputFile = File(distDir, "index.html")
val blogDistDir = File(distDir, "blog")

val categories = listOf("framework", "language", "database", "testing", "fullstack", "web", "workflow", "tool")

fun htmlEscape(s: String): String = s
    .replace("&", "&amp;")
    .replace("<", "&lt;")
    .replace(">", "&gt;")
    .replace("\"", "&quot;")

// ── Parse all skills into a map for cross-referencing ──
data class SkillInfo(
    val name: String,
    val description: String,
    val repo: String,
    val skillPath: String,
    val author: String,
    val trust: String,
    val languages: List<String>,
    val tech: List<String>,
    val tags: List<String>
)

val yaml = Yaml()
val skillsMap = mutableMapOf<String, SkillInfo>()

for (category in categories) {
    val catDir = File(skillsDir, category)
    if (!catDir.isDirectory) continue

    val yamlFiles = catDir.listFiles { f -> f.extension == "yaml" || f.extension == "yml" }
        ?.sorted() ?: continue

    for (yamlFile in yamlFiles) {
        @Suppress("UNCHECKED_CAST")
        val skill = yaml.load<Map<String, Any>>(yamlFile.readText()) ?: continue
        val key = "$category/${yamlFile.nameWithoutExtension}"
        skillsMap[key] = SkillInfo(
            name = skill["name"]?.toString() ?: "",
            description = skill["description"]?.toString() ?: "",
            repo = skill["repo"]?.toString() ?: "",
            skillPath = skill["skill_path"]?.toString() ?: "",
            author = skill["author"]?.toString() ?: "",
            trust = skill["trust"]?.toString() ?: "community",
            languages = (skill["languages"] as? List<*>)?.map { it.toString() } ?: emptyList(),
            tech = (skill["tech"] as? List<*>)?.map { it.toString() } ?: emptyList(),
            tags = (skill["tags"] as? List<*>)?.map { it.toString() } ?: emptyList()
        )
    }
}

// ── Build skill card HTML ──
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
            val key = "$category/${yamlFile.nameWithoutExtension}"
            val skill = skillsMap[key] ?: continue

            val langsCsv = skill.languages.joinToString(",")
            val techCsv = skill.tech.joinToString(",")
            val tagsCsv = skill.tags.joinToString(",")

            val langsHtml = skill.languages.joinToString("") { "<span>$it</span>" }
            val techHtml = skill.tech.joinToString("") { "<span>${htmlEscape(it)}</span>" }
            val tagsHtml = skill.tags.joinToString("") { "<span>${htmlEscape(it)}</span>" }

            append("""<article class="skill-card" data-languages="$langsCsv" data-tech="$techCsv" data-trust="${skill.trust}" data-tags="$tagsCsv">""")
            append("\n")
            append("""<div class="card-titlebar">""")
            append("""<span class="card-dots"><span></span><span></span><span></span></span>""")
            append("</div>\n")
            append("""<div class="card-body">""")
            append("\n")
            val skillUrl = if (skill.skillPath.isNotEmpty()) "https://github.com/${htmlEscape(skill.repo)}/blob/main/${htmlEscape(skill.skillPath)}" else "https://github.com/${htmlEscape(skill.repo)}"
            val skillDir = if (skill.skillPath.contains("/")) skill.skillPath.substringBeforeLast("/") else ""
            val skillDirUrl = if (skillDir.isNotEmpty()) "https://github.com/${skill.repo}/tree/main/$skillDir" else "https://github.com/${skill.repo}"
            val skillSlug = if (skillDir.isNotEmpty()) skillDir.substringAfterLast("/") else skill.repo.substringAfterLast("/")
            val installText = "Fetch the skill from $skillDirUrl and save all files to .claude/skills/$skillSlug/"

            append("""<h3 class="skill-name"><a href="$skillUrl">${htmlEscape(skill.name)}</a></h3>""")
            append("\n")
            append("""<p class="skill-description">${htmlEscape(skill.description)}</p>""")
            append("\n")
            append("""<div class="skill-meta">""")
            append("""<span class="skill-author">by ${htmlEscape(skill.author)}</span>""")
            append("""<button class="copy-install" data-install="${htmlEscape(installText)}" type="button" title="Copy install instruction">install</button>""")
            append("</div>\n")
            append("""<div class="skill-languages">$langsHtml</div>""")
            append("\n")
            if (skill.tech.isNotEmpty()) {
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

// ── Build blog posts ──
data class BlogPost(
    val title: String,
    val slug: String,
    val date: String,
    val author: String,
    val description: String,
    val skills: List<String>,
    val tags: List<String>,
    val htmlContent: String
)

val mdParser = Parser.builder().build()
val mdRenderer = HtmlRenderer.builder().build()

fun parseFrontmatter(text: String): Pair<Map<String, Any>, String> {
    val trimmed = text.trimStart()
    if (!trimmed.startsWith("---")) return emptyMap<String, Any>() to text

    val end = trimmed.indexOf("---", 3)
    if (end < 0) return emptyMap<String, Any>() to text

    val frontmatterText = trimmed.substring(3, end).trim()
    val body = trimmed.substring(end + 3).trim()

    @Suppress("UNCHECKED_CAST")
    val frontmatter = yaml.load<Map<String, Any>>(frontmatterText) ?: emptyMap()
    return frontmatter to body
}

val blogPosts = mutableListOf<BlogPost>()

if (blogDir.isDirectory) {
    val mdFiles = blogDir.listFiles { f -> f.extension == "md" }?.sorted() ?: emptyList()

    for (mdFile in mdFiles) {
        val (fm, body) = parseFrontmatter(mdFile.readText())
        if (fm.isEmpty()) {
            System.err.println("  WARN: skipping ${mdFile.name} (no frontmatter)")
            continue
        }

        if (fm["draft"] == true) {
            System.err.println("  SKIP: ${mdFile.name} (draft)")
            continue
        }

        val document = mdParser.parse(body)
        val htmlContent = mdRenderer.render(document)

        blogPosts.add(BlogPost(
            title = fm["title"]?.toString() ?: mdFile.nameWithoutExtension,
            slug = fm["slug"]?.toString() ?: mdFile.nameWithoutExtension,
            date = when (val d = fm["date"]) {
                is java.util.Date -> java.text.SimpleDateFormat("yyyy-MM-dd").apply { timeZone = java.util.TimeZone.getTimeZone("UTC") }.format(d)
                else -> d?.toString() ?: ""
            },
            author = fm["author"]?.toString() ?: "",
            description = fm["description"]?.toString() ?: "",
            skills = (fm["skills"] as? List<*>)?.map { it.toString() } ?: emptyList(),
            tags = (fm["tags"] as? List<*>)?.map { it.toString() } ?: emptyList(),
            htmlContent = htmlContent
        ))
    }
}

// Sort posts newest first
blogPosts.sortByDescending { it.date }

// ── Generate blog output ──
if (blogPosts.isNotEmpty()) {
    blogDistDir.mkdirs()

    val postTemplate = blogPostTemplate.readText()
    val indexTemplate = blogIndexTemplate.readText()

    // Generate individual post pages
    for (post in blogPosts) {
        // Build related skills HTML
        val relatedSkillsHtml = if (post.skills.isNotEmpty()) {
            buildString {
                append("""<section class="related-skills">""")
                append("""<h2 class="related-skills-heading"><span class="prompt">$</span> Related Skills</h2>""")
                append("""<div class="related-skills-grid">""")
                for (skillRef in post.skills) {
                    val skill = skillsMap[skillRef] ?: continue
                    val skillUrl = if (skill.skillPath.isNotEmpty()) "https://github.com/${htmlEscape(skill.repo)}/blob/main/${htmlEscape(skill.skillPath)}" else "https://github.com/${htmlEscape(skill.repo)}"
                    val langsHtml = skill.languages.joinToString("") { """<span>$it</span>""" }
                    append("""<div class="related-skill-card">""")
                    append("""<h4><a href="$skillUrl">${htmlEscape(skill.name)}</a></h4>""")
                    append("""<p>${htmlEscape(skill.description.take(120))}${if (skill.description.length > 120) "..." else ""}</p>""")
                    append("""<div class="skill-langs">$langsHtml</div>""")
                    append("""</div>""")
                }
                append("""</div></section>""")
            }
        } else ""

        val postHtml = postTemplate
            .replace("{{POST_TITLE}}", htmlEscape(post.title))
            .replace("{{POST_SLUG}}", post.slug)
            .replace("{{PAGE_DESCRIPTION}}", htmlEscape(post.description))
            .replace("{{POST_DATE}}", post.date)
            .replace("{{POST_AUTHOR}}", htmlEscape(post.author))
            .replace("{{POST_CONTENT}}", post.htmlContent)
            .replace("{{RELATED_SKILLS}}", relatedSkillsHtml)
            .replace("{{GENERATED_DATE}}", "")  // filled below

        val postDir = File(blogDistDir, post.slug)
        postDir.mkdirs()
        File(postDir, "index.html").writeText(postHtml)
    }

    // Generate blog listing page
    val postsListHtml = buildString {
        append("""<ul class="blog-posts-list">""")
        for (post in blogPosts) {
            val tagsHtml = post.tags.joinToString("") { """<span>${htmlEscape(it)}</span>""" }
            append("""<li class="blog-post-entry">""")
            append("""<div class="blog-post-entry-date">${post.date}</div>""")
            append("""<h2 class="blog-post-entry-title"><a href="/blog/${post.slug}/">${htmlEscape(post.title)}</a></h2>""")
            append("""<p class="blog-post-entry-desc">${htmlEscape(post.description)}</p>""")
            append("""<div class="blog-post-entry-tags">$tagsHtml</div>""")
            append("""</li>""")
        }
        append("""</ul>""")
    }

    val indexHtml = indexTemplate
        .replace("{{BLOG_POSTS}}", postsListHtml)
        .replace("{{GENERATED_DATE}}", "")  // filled below

    File(blogDistDir, "index.html").writeText(indexHtml)
}

// ── Read template, replace placeholders, write output ──
val generatedDate = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm 'UTC'")
    .withZone(ZoneOffset.UTC)
    .format(Instant.now())

val template = templateFile.readText()
val output = template
    .replace("{{SKILL_CARDS}}", skillCards)
    .replace("{{GENERATED_DATE}}", generatedDate)

distDir.mkdirs()
outputFile.writeText(output)

// Patch generated date into blog files (date only, no time)
val generatedDateOnly = DateTimeFormatter.ofPattern("yyyy-MM-dd")
    .withZone(ZoneOffset.UTC)
    .format(Instant.now())

if (blogPosts.isNotEmpty()) {
    val blogIndexFile = File(blogDistDir, "index.html")
    blogIndexFile.writeText(blogIndexFile.readText().replace("{{GENERATED_DATE}}", generatedDateOnly))

    for (post in blogPosts) {
        val postFile = File(blogDistDir, "${post.slug}/index.html")
        if (postFile.exists()) {
            postFile.writeText(postFile.readText().replace("{{GENERATED_DATE}}", generatedDateOnly))
        }
    }
}

// Copy preview.webp to dist/
val previewSrc = File(siteDir, "preview.webp")
if (previewSrc.exists()) {
    previewSrc.copyTo(File(distDir, "preview.webp"), overwrite = true)
}

println("✓ Built dist/index.html ($totalSkills skills across ${categories.size} categories)")
if (blogPosts.isNotEmpty()) {
    println("✓ Built ${blogPosts.size} blog post(s) in dist/blog/")
}
println("  Generated: $generatedDate")
