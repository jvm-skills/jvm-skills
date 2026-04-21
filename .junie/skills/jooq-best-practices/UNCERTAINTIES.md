# Uncertainties & Questions to Resolve

Items logged during blog processing that need verification or deeper investigation.

Format:
```
## [topic] Question or uncertainty
**From**: [Article title](url) (date)
**Status**: open | resolved
**Resolution**: (filled in when resolved)
```

---

<!-- Entries will be appended by the Ralph processing loop -->

## [stored-procedures] `var()` vs `variable()` for block variable declaration
**From**: [Translating Stored Procedures Between Dialects](https://blog.jooq.org/translating-stored-procedures-between-dialects) (2021-02-10)
**Status**: open
**Context**: The 2021-02-10 article uses `var(name("i"), INTEGER)` while the 2021-08-25 article uses `variable(unquotedName("i"), INTEGER)`. Unclear if `var()` was renamed to `variable()` or if both exist. Current entries use `variable()` as it comes from the newer source.
