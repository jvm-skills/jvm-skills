#!/usr/bin/env kotlin

@file:DependsOn("com.squareup.okhttp3:okhttp:4.12.0")
@file:DependsOn("com.fasterxml.jackson.module:jackson-module-kotlin:2.18.2")
@file:DependsOn("org.jsoup:jsoup:1.18.3")

import com.fasterxml.jackson.annotation.JsonIgnoreProperties
import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.fasterxml.jackson.module.kotlin.readValue
import okhttp3.FormBody
import okhttp3.OkHttpClient
import okhttp3.Request
import org.jsoup.Jsoup
import java.io.File
import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter

@JsonIgnoreProperties(ignoreUnknown = true)
data class ScrollResponse(
    val type: String,
    val html: String,
    val lastbatch: Boolean,
    val currentday: String,
)

data class BlogArticle(
    val url: String,
    val title: String,
    val description: String,
    val date: String,
    val tags: List<String>,
    val processed: Boolean = false,
)

val mapper = jacksonObjectMapper().writerWithDefaultPrettyPrinter()
val reader = jacksonObjectMapper()
val client = OkHttpClient()
val outputFile = File("build/jooq_blog_articles.json")
outputFile.parentFile.mkdirs()

var lastDate = "2026-02-20 06:51:59"
var currentDay = "20.02.26"
var page = 1
var retries = 0
val articles = mutableMapOf<String, BlogArticle>() // url -> article, dedup by url
val dbFmt = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")

fun parseArticles(html: String): List<BlogArticle> {
    val doc = Jsoup.parse(html)
    return doc.select("article").mapNotNull { article ->
        val titleEl = article.selectFirst("h2.entry-title a") ?: return@mapNotNull null
        val url = titleEl.attr("href").trimEnd('/')
        val title = titleEl.text()
        val timeEl = article.selectFirst("time.entry-date")
        val date = timeEl?.attr("datetime") ?: ""
        val descriptionEl = article.selectFirst("div.entry-content p")
        val description = descriptionEl?.text()
            ?.replace(Regex("\\s*Continue reading.*$"), "")
            ?.trim() ?: ""
        val classes = article.attr("class")
        val tags = Regex("(?:category|tag)-([\\w-]+)").findAll(classes)
            .map { it.groupValues[1] }
            .toList()
        BlogArticle(url = url, title = title, description = description, date = date, tags = tags)
    }
}

fun saveOutput() {
    val sorted = articles.values.sortedByDescending { it.date }
    outputFile.writeText(mapper.writeValueAsString(sorted))
}

while (page <= 150) {
    val body = FormBody.Builder()
        .add("action", "infinite_scroll")
        .add("page", page.toString())
        .add("currentday", currentDay)
        .add("order", "DESC")
        .add("query_args[posts_per_page]", "10")
        .add("query_args[order]", "DESC")
        .add("query_before", "2026-02-20 06:51:59")
        .add("last_post_date", lastDate)
        .build()

    val request = Request.Builder()
        .url("https://blog.jooq.org/?infinity=scrolling")
        .post(body)
        .header("content-type", "application/x-www-form-urlencoded; charset=UTF-8")
        .header("x-requested-with", "XMLHttpRequest")
        .header("user-agent", "Mozilla/5.0")
        .build()

    val response = client.newCall(request).execute()
    val responseText = response.body?.string() ?: ""

    if (!responseText.trimStart().startsWith("{")) {
        retries++
        val delay = 3000L * retries
        println("Page $page: 429 rate-limited, retry #$retries in ${delay}ms")
        Thread.sleep(delay)
        continue
    }
    retries = 0

    val scroll = reader.readValue<ScrollResponse>(responseText)
    val parsed = parseArticles(scroll.html)

    // Last datetime in the HTML = oldest post = cursor for next page
    val doc = Jsoup.parse(scroll.html)
    val lastDatetime = doc.select("time.entry-date").lastOrNull()?.attr("datetime")
    val newLastDate = lastDatetime?.let {
        runCatching { OffsetDateTime.parse(it).format(dbFmt) }.getOrNull()
    }

    if (parsed.isEmpty()) {
        println("Page $page: empty, stopping")
        break
    }

    val newCount = parsed.count { it.url !in articles }
    parsed.forEach { articles.putIfAbsent(it.url, it) }
    saveOutput()
    println("Page $page: ${parsed.size} articles (+$newCount new), total=${articles.size}, lastbatch=${scroll.lastbatch}")

    if (scroll.lastbatch || newLastDate == null) {
        println("Done (lastbatch=${scroll.lastbatch})")
        break
    }

    lastDate = newLastDate
    currentDay = scroll.currentday
    page++
    Thread.sleep(1500)
}

println("\nTotal unique articles: ${articles.size}")
println("Saved to ${outputFile.absolutePath}")
