# Plain SQL Templating and String Usage in jOOQ

## Pattern: val() vs inline() — bind variable vs SQL literal
**Source**: [What's a "String" in the jOOQ API?](https://blog.jooq.org/whats-a-string-in-the-jooq-api) (2020-04-03)

- **`DSL.val(x)`** — renders as `?` bind parameter (safe, default for where-clause arguments)
- **`DSL.inline(x)`** — renders the value escaped directly into SQL (useful for forcing literal values, e.g. in skewed enum columns)

When you pass a raw value where jOOQ expects a `Field`, it implicitly wraps it with `val()`.

```kotlin
// Explicit bind value
val bind: Field<String> = DSL.`val`("abc")   // renders ?

// Explicit literal (inlined)
val lit: Field<String> = DSL.inline("xyz")   // renders 'xyz'

// Implicit bind value (jOOQ wraps automatically)
dsl.select(T.A).from(T).where(T.C.eq("xyz")).fetch()
```

---

## Pattern: Plain SQL templates — escaping vendor-specific SQL safely
**Source**: [What's a "String" in the jOOQ API?](https://blog.jooq.org/whats-a-string-in-the-jooq-api) (2020-04-03)

Use `DSL.field()`, `DSL.table()`, `DSL.condition()` to embed vendor-specific SQL jOOQ doesn't natively support. Always use the templating language — **never concatenate user input**.

```kotlin
// Typed field from plain SQL
val series: Table<*> = DSL.table("generate_series(1, 10)")
val score: Field<Int> = DSL.field("ts_rank(tsv, query)", Int::class.java)

// Safe parameterized templates (? or {0} placeholder)
.where(DSL.condition("some_function() = ?", 1))       // safe — bind var
.where(DSL.condition("some_function() = {0}", DSL.`val`(1))) // also safe

// NEVER do this — SQL injection risk
.where(DSL.condition("some_function() = " + userInput))   // UNSAFE
```

The `@PlainSQL` annotation marks these APIs. You can configure a static checker to restrict `@PlainSQL` usage to prevent accidental injection in large teams.

---

## Pattern: name() for type-safe identifiers in dynamic DDL
**Source**: [What's a "String" in the jOOQ API?](https://blog.jooq.org/whats-a-string-in-the-jooq-api) (2020-04-03)

Use `DSL.name()` to construct identifiers (table/column names) for DDL. These are auto-quoted by default, preventing SQL injection and handling reserved words.

```kotlin
val tbl: Name = DSL.name("t")
val col: Name = DSL.name("t", "col")   // qualified: "t"."col"

dsl.createTable(tbl)
    .column(col, SQLDataType.INTEGER)
    .execute()

// Shorthand strings are also auto-quoted:
dsl.createTable("my_table")
    .column("my_col", SQLDataType.INTEGER)
    .execute()
```

Disabling quoting via `RenderQuotedNames.EXPLICIT_DEFAULT_UNQUOTED` reintroduces injection risk — only do this if identifiers are fully controlled.

---

## Pattern: Text blocks for readable multi-line plain SQL
**Source**: [Using Java 13+ Text Blocks for Plain SQL with jOOQ](https://blog.jooq.org/using-java-13-text-blocks-for-plain-sql-with-jooq) (2020-03-05)
**Since**: Java 13 (preview), Java 15 (stable)

Use Java/Kotlin multi-line strings to write plain SQL inline without concatenation. jOOQ accepts these wherever it accepts a `String`. Combine with `{0}` placeholders to inject jOOQ `Field`/`Condition` expressions into otherwise-static SQL.

```kotlin
// Readable multi-line plain SQL
ctx.fetch("""
    SELECT table_schema, count(*)
    FROM information_schema.tables
    GROUP BY table_schema
    ORDER BY table_schema
    """)

// Mix text blocks with {0} template placeholders for dynamic field injection
val groupBy = field("table_schema")
ctx.fetch("""
    SELECT {0}, count(*), row_number() OVER (ORDER BY {0}) AS rn
    FROM information_schema.tables
    GROUP BY {0}
    ORDER BY {0}
    """, groupBy)
```

Use text blocks for **static or near-static** vendor-specific SQL that's awkward in the DSL. For fully dynamic queries prefer the DSL for type safety.

---

## Pattern: Wrap plain SQL templates in custom DSL helpers
**Source**: [Never Concatenate Strings With jOOQ](https://blog.jooq.org/never-concatenate-strings-with-jooq) (2020-03-04)

When you repeatedly use vendor-specific plain SQL, hide the template behind a typed helper function. This keeps `@PlainSQL` usage contained and gives callers a type-safe API.

```kotlin
// INSTEAD of repeating the template everywhere:
field("cool_function(1, {0}, 3)", MY_TABLE.MY_COLUMN)

// Encapsulate in a helper:
fun coolFunction(f: Field<*>): Field<String> =
    DSL.field("cool_function(1, {0}, 3)", String::class.java, f)

// Caller is now fully type-safe:
coolFunction(MY_TABLE.MY_COLUMN)
```

> **Supersedes**: Raw string concatenation like `field("cool_function(1, " + MY_TABLE.MY_COLUMN + ", 3)")` which calls `toString()` without dialect awareness and opens SQL injection vectors.

---

## Pattern: keyword() for consistent keyword rendering
**Source**: [What's a "String" in the jOOQ API?](https://blog.jooq.org/whats-a-string-in-the-jooq-api) (2020-04-03)

Wrap SQL keywords with `DSL.keyword()` when composing plain SQL templates, so jOOQ applies the configured keyword-casing style uniformly.

```kotlin
val current = DSL.keyword("current")
val time    = DSL.keyword("time")

val currentTime: Field<Time> = DSL.field(
    "{0} {1}", SQLDataType.TIME, current, time
)
// Renders as CURRENT TIME (or current time) per settings
```

---
