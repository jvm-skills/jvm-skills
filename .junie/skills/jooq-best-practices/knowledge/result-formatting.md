# Result Formatting & Export

## Pattern: ASCII chart output with formatChart()
**Source**: [Formatting ASCII Charts With jOOQ](https://blog.jooq.org/formatting-ascii-charts-with-jooq) (2021-08-19)

jOOQ's `Formattable.formatChart()` renders any `Result` as an ASCII stacked bar chart in the console — no external dependencies needed. Uses the first column as category labels, remaining numeric columns as bar values.

```java
// Default: stacked bar chart, auto dimensions
result.formatChart();

// Configure height/width, select value columns, custom characters
result.formatChart(new ChartFormat()
    .dimensions(40, 8)
    .values(1, 2, 3)
    .shades('@', 'o', '.')
    .display(Display.HUNDRED_PERCENT_STACKED)
);
```

Useful for quick console-based data exploration or terminal reporting without exporting to Excel.

---
