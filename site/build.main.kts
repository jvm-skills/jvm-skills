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
import java.awt.Color
import java.awt.Font
import java.awt.RenderingHints
import java.awt.image.BufferedImage
import javax.imageio.ImageIO

val siteDir = __FILE__.absoluteFile.parentFile
val rootDir = siteDir.parentFile
val skillsDir = File(rootDir, "skills")
val blogDir = File(rootDir, "blog")
val evalsDir = File(rootDir, "evals")
val templateFile = File(siteDir, "template.html")
val blogPostTemplate = File(siteDir, "blog-post-template.html")
val blogIndexTemplate = File(siteDir, "blog-index-template.html")
val evalViewerTemplate = File(siteDir, "eval-viewer-template.html")
val distDir = File(rootDir, "dist")
val outputFile = File(distDir, "index.html")
val blogDistDir = File(distDir, "blog")
val evalsDistDir = File(distDir, "evals")

val categories = listOf("framework", "language", "database", "testing", "fullstack", "web", "workflow", "tool")

val includeDrafts = System.getenv("INCLUDE_DRAFTS") == "1"

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
    val tags: List<String>,
    val eval: String  // path to benchmark.json relative to repo root, empty if none
)

// Parsed eval summary for rendering
data class EvalSummary(
    val withSkillPassRate: Double,
    val withoutSkillPassRate: Double,
    val delta: String,
    val evalsCount: Int,
    val slug: String  // for linking to /evals/<slug>/
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
            tags = (skill["tags"] as? List<*>)?.map { it.toString() } ?: emptyList(),
            eval = skill["eval"]?.toString() ?: ""
        )
    }
}

// ── Parse eval benchmarks ──
@Suppress("UNCHECKED_CAST")
fun parseEvalSummary(evalPath: String, slug: String): EvalSummary? {
    val benchmarkFile = File(rootDir, evalPath)
    if (!benchmarkFile.exists()) {
        System.err.println("  WARN: eval file not found: $evalPath")
        return null
    }
    try {
        val json = yaml.load<Map<String, Any>>(benchmarkFile.readText()) // snakeyaml parses JSON too
        val runSummary = json["run_summary"] as? Map<String, Any> ?: return null
        val delta = runSummary["delta"] as? Map<String, Any> ?: emptyMap()

        // Find with_skill and without_skill configs dynamically
        val configs = runSummary.keys.filter { it != "delta" }
        val withConfig = configs.firstOrNull { it.contains("with") && !it.contains("without") }
        val withoutConfig = configs.firstOrNull { it.contains("without") }

        fun extractMeanPassRate(config: String?): Double {
            if (config == null) return 0.0
            val c = runSummary[config] as? Map<String, Any> ?: return 0.0
            val pr = c["pass_rate"] as? Map<String, Any> ?: return 0.0
            return (pr["mean"] as? Number)?.toDouble() ?: 0.0
        }

        val metadata = json["metadata"] as? Map<String, Any> ?: emptyMap()
        val evalsRun = metadata["evals_run"] as? List<*> ?: emptyList<Any>()

        return EvalSummary(
            withSkillPassRate = extractMeanPassRate(withConfig),
            withoutSkillPassRate = extractMeanPassRate(withoutConfig),
            delta = delta["pass_rate"]?.toString() ?: "",
            evalsCount = evalsRun.size,
            slug = slug
        )
    } catch (e: Exception) {
        System.err.println("  WARN: failed to parse eval: $evalPath — ${e.message}")
        return null
    }
}

val evalSummaries = mutableMapOf<String, EvalSummary>()
for ((key, skill) in skillsMap) {
    if (skill.eval.isNotEmpty()) {
        val slug = key.substringAfterLast("/")
        parseEvalSummary(skill.eval, slug)?.let { evalSummaries[key] = it }
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

            // Eval badge
            val evalSummary = evalSummaries[key]
            if (evalSummary != null) {
                val withPct = (evalSummary.withSkillPassRate * 100).toInt()
                val withoutPct = (evalSummary.withoutSkillPassRate * 100).toInt()
                val deltaStr = evalSummary.delta
                // Convert raw delta (e.g., "+0.26") to percentage (e.g., "+26%")
                val deltaPct = try {
                    val raw = deltaStr.trim().replace("+", "").replace("-", "").toDoubleOrNull() ?: 0.0
                    val pct = (raw * 100).toInt()
                    if (deltaStr.startsWith("-")) "-$pct%" else "+$pct%"
                } catch (e: Exception) {
                    deltaStr
                }
                val evalUrl = "/evals/${evalSummary.slug}/"
                append("""<a href="$evalUrl" aria-label="View evaluation details for ${htmlEscape(skill.name)}">""")
                append("""<button class="skill-eval-badge" type="button" title="Skill eval: ${withPct}% pass rate with skill vs ${withoutPct}% baseline">""")
                append("""<span class="eval-label">eval</span>""")
                append("""<span class="eval-pass">${withPct}%</span>""")
                append("""<span class="eval-vs">vs ${withoutPct}%</span>""")
                append("""<span class="eval-delta">($deltaPct)</span>""")
                append("""<span class="eval-count">${evalSummary.evalsCount} tests</span>""")
                append("""</button></a>\n""")
            }

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

fun generateOgImage(post: BlogPost, outputFile: File) {
    val width = 1200
    val height = 630
    val image = BufferedImage(width, height, BufferedImage.TYPE_INT_RGB)
    val g = image.createGraphics()

    g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
    g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON)

    // Background
    g.color = Color.decode("#0a0e14")
    g.fillRect(0, 0, width, height)

    // Decorative logo ">_"
    g.color = Color.decode("#00ff41")
    g.font = Font("Monospaced", Font.BOLD, 60)
    g.drawString(">_", 60, 100)

    // Website name
    g.color = Color.decode("#8b949e")
    g.font = Font("Monospaced", Font.PLAIN, 24)
    g.drawString("jvmskills.com / blog", 160, 92)

    // Title
    g.color = Color.decode("#c9d1d9")
    val titleFont = Font("SansSerif", Font.BOLD, 72)
    g.font = titleFont
    
    val padding = 100
    val maxTextWidth = width - 2 * padding
    val words = post.title.split(" ")
    val lines = mutableListOf<String>()
    var currentLine = StringBuilder()
    val metrics = g.fontMetrics

    for (word in words) {
        val testLine = if (currentLine.isEmpty()) word else "$currentLine $word"
        if (metrics.stringWidth(testLine) < maxTextWidth) {
            currentLine = StringBuilder(testLine)
        } else {
            lines.add(currentLine.toString())
            currentLine = StringBuilder(word)
        }
    }
    if (currentLine.isNotEmpty()) lines.add(currentLine.toString())

    // Vertical center adjustment
    val totalHeight = lines.size * (metrics.height + 10)
    var y = (height - totalHeight) / 2 + metrics.ascent

    for (line in lines) {
        g.drawString(line, padding, y)
        y += metrics.height + 10
    }

    // Author and Date
    g.color = Color.decode("#8b949e")
    g.font = Font("SansSerif", Font.PLAIN, 32)
    g.drawString("${post.author} • ${post.date}", padding, height - 100)

    g.dispose()
    outputFile.parentFile.mkdirs()
    ImageIO.write(image, "png", outputFile)
}

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

        val isDraft = fm["draft"] == true
        if (isDraft && !includeDrafts) {
            System.err.println("  SKIP: ${mdFile.name} (draft)")
            continue
        }
        if (isDraft) {
            System.err.println("  DRAFT: ${mdFile.name} (included — INCLUDE_DRAFTS=1)")
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
                    append("""<h4><a href="$skillUrl" aria-label="View skill ${htmlEscape(skill.name)}"><button class="nav-link" type="button" style="padding: 4px 8px; font-size: 0.75rem; border: none; width: 100%; justify-content: flex-start;">${htmlEscape(skill.name)}</button></a></h4>""")
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
        generateOgImage(post, File(postDir, "og.png"))
    }

    // Generate blog listing page
    val postsListHtml = buildString {
        append("""<ul class="blog-posts-list">""")
        for (post in blogPosts) {
            val tagsHtml = post.tags.joinToString("") { """<span>${htmlEscape(it)}</span>""" }
            append("""<li class="blog-post-entry">""")
            append("""<div class="blog-post-entry-date">${post.date}</div>""")
            append("""<h2 class="blog-post-entry-title"><a href="/blog/${post.slug}/" aria-label="Read ${htmlEscape(post.title)}"><button class="nav-link" type="button" style="border: none; padding: 4px 0; font-size: inherit; text-align: left; background: transparent; cursor: pointer; width: 100%; justify-content: flex-start;">${htmlEscape(post.title)}</button></a></h2>""")
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

// ── Generate eval viewer pages ──
if (evalSummaries.isNotEmpty() && evalViewerTemplate.exists()) {
    val viewerTemplate = evalViewerTemplate.readText()

    for ((key, evalSum) in evalSummaries) {
        val skill = skillsMap[key] ?: continue
        val benchmarkFile = File(rootDir, skill.eval)
        if (!benchmarkFile.exists()) continue

        val benchmarkJson = benchmarkFile.readText().trim()
        val skillName = htmlEscape(skill.name)

        val viewerHtml = viewerTemplate
            .replace("{{SKILL_NAME}}", skillName)
            .replace("{{SKILL_SLUG}}", evalSum.slug)
            .replace("{{GENERATED_DATE}}", generatedDateOnly)
            .replace("/*__EMBEDDED_DATA__*/", "const BENCHMARK_DATA = $benchmarkJson;")

        val evalDir = File(evalsDistDir, evalSum.slug)
        evalDir.mkdirs()
        File(evalDir, "index.html").writeText(viewerHtml)
    }
    println("✓ Built ${evalSummaries.size} eval viewer page(s) in dist/evals/")
}

// Copy preview.webp to dist/
val previewSrc = File(siteDir, "preview.webp")
if (previewSrc.exists()) {
    previewSrc.copyTo(File(distDir, "preview.webp"), overwrite = true)
}

// ── Generate Spring I/O landing page ──
val springIoTemplate = File(siteDir, "spring-io-template.html")
if (springIoTemplate.exists()) {
    val springIoDir = File(distDir, "spring-io-2026")
    springIoDir.mkdirs()
    File(springIoDir, "index.html").writeText(springIoTemplate.readText())
    println("✓ Built dist/spring-io-2026/index.html")
}

// ── Copy Spring I/O 2026 talk slides ──
val slidesSrc = File(siteDir, "spring-io-2026-slides")
if (slidesSrc.isDirectory) {
    val slidesDest = File(distDir, "spring-io-2026/slides")
    slidesSrc.copyRecursively(slidesDest, overwrite = true)
    println("✓ Copied ${slidesSrc.name}/ → dist/spring-io-2026/slides/")
}

// ── Copy learn.md (interactive Claude Code tutor) ──
val learnMd = File(siteDir, "learn.md")
if (learnMd.exists()) {
    learnMd.copyTo(File(distDir, "spring-io-2026/learn.md"), overwrite = true)
    println("✓ Copied learn.md → dist/spring-io-2026/learn.md")
}

// ── Generate 404 page ──
val notFoundTemplate = File(siteDir, "404-template.html")
if (notFoundTemplate.exists()) {
    File(distDir, "404.html").writeText(notFoundTemplate.readText())
    println("✓ Built dist/404.html")
}

println("✓ Built dist/index.html ($totalSkills skills across ${categories.size} categories)")
if (blogPosts.isNotEmpty()) {
    println("✓ Built ${blogPosts.size} blog post(s) in dist/blog/")
}
println("  Generated: $generatedDate")
