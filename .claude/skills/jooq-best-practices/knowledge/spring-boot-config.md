# Spring Boot Configuration

## Pattern: DefaultConfigurationCustomizer callback
**Source**: [How to customise a jOOQ Configuration that is injected using Spring Boot](https://blog.jooq.org/how-to-customise-a-jooq-configuration-that-is-injected-using-spring-boot) (2021-12-16)
**Since**: Spring Boot 2.5

Use `DefaultConfigurationCustomizer` to modify jOOQ's `DefaultConfiguration` during Spring Boot auto-configuration. This is the idiomatic way to tweak settings without replacing the entire `DSLContext` bean.

```java
@Configuration
public class JooqConfig {
    @Bean
    public DefaultConfigurationCustomizer jooqConfigCustomizer() {
        return (DefaultConfiguration c) -> c.settings()
            .withRenderQuotedNames(RenderQuotedNames.EXPLICIT_DEFAULT_UNQUOTED);
    }
}
```

The callback receives the mutable `DefaultConfiguration` during initialization — you can change settings, add listeners, register converters, etc.

---

## Pattern: Enable allowMultiQueries for MySQL/MariaDB
**Source**: [MySQL's allowMultiQueries flag with JDBC and jOOQ](https://blog.jooq.org/mysqls-allowmultiqueries-flag-with-jdbc-and-jooq) (2021-08-23)
**Dialect**: MySQL / MariaDB

jOOQ internally generates multi-statement batches for several MySQL features: `GROUP_CONCAT` max-length adjustment, `CREATE OR REPLACE` emulation (DROP + CREATE), `FOR UPDATE WAIT` timeout, and anonymous procedural blocks (temp stored proc + call + drop). This requires enabling `allowMultiQueries=true` on the JDBC URL.

```
spring.datasource.url=jdbc:mysql://localhost:3306/mydb?allowMultiQueries=true
```

This is safe to enable when using jOOQ's DSL (no SQL injection risk), but keep in mind it only removes one layer of defense — parameterized queries remain the primary safeguard.

---
