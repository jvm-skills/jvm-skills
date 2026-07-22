#!/usr/bin/env bash
# Publish the current Big Sky presentation as a self-contained, notes-free deck.
# Usage: ./site/sync-big-sky-slides.sh [path/to/claude-code-for-spring-developers/presentation]

set -euo pipefail

site_dir="$(cd "$(dirname "$0")" && pwd)"
presentation_dir="${1:-$site_dir/../../claude-code-for-spring-developers/presentation}"
output_dir="$site_dir/big-sky-2026-slides"

if [[ ! -f "$presentation_dir/index.html" ]]; then
  echo "Big Sky presentation not found: $presentation_dir/index.html" >&2
  exit 1
fi

mkdir -p \
  "$output_dir/assets/fonts/big-sky" \
  "$output_dir/assets/pr96" \
  "$output_dir/assets/qr" \
  "$output_dir/assets/section5" \
  "$output_dir/sections" \
  "$output_dir/node_modules/reveal.js/dist/theme" \
  "$output_dir/node_modules/reveal.js/plugin/highlight" \
  "$output_dir/node_modules/reveal.js/plugin/markdown"

perl -0pe '
  s{<aside class="notes">.*?</aside>}{}gs;
  s{^\s*<link[^>]+asciinema-player[^>]+>\s*$}{}gm;
  s{^\s*<script[^>]+asciinema-player[^>]+></script>\s*$}{}gm;
  s{^\s*<script src="\./node_modules/reveal\.js/plugin/notes/notes\.js"></script>\s*$}{}gm;
  s/RevealNotes,\s*//g;
' "$presentation_dir/index.html" > "$output_dir/index.html"

cp "$presentation_dir/assets/velocity-chart.svg" "$output_dir/assets/"
cp "$presentation_dir/assets/pr96/step1.png" "$presentation_dir/assets/pr96/step2.png" "$output_dir/assets/pr96/"
cp "$presentation_dir/assets/qr/linkedin.png" "$presentation_dir/assets/qr/talk-resources.png" "$presentation_dir/assets/qr/jvmskills.png" "$output_dir/assets/qr/"
cp "$presentation_dir/assets/section5/graph-engineering-tweet.png" "$output_dir/assets/section5/"
cp "$presentation_dir/assets/fonts/big-sky/jersey15-latin.woff2" "$presentation_dir/assets/fonts/big-sky/source-code-pro-var.woff2" "$presentation_dir/assets/fonts/big-sky/source-code-pro-italic-var.woff2" "$output_dir/assets/fonts/big-sky/"
cp "$presentation_dir/sections/profilepic_small.jpeg" "$output_dir/sections/"

cp "$presentation_dir/node_modules/reveal.js/dist/reveal.css" "$presentation_dir/node_modules/reveal.js/dist/reveal.js" "$output_dir/node_modules/reveal.js/dist/"
cp "$presentation_dir/node_modules/reveal.js/dist/theme/black.css" "$output_dir/node_modules/reveal.js/dist/theme/"
cp "$presentation_dir/node_modules/reveal.js/plugin/highlight/monokai.css" "$presentation_dir/node_modules/reveal.js/plugin/highlight/highlight.js" "$output_dir/node_modules/reveal.js/plugin/highlight/"
cp "$presentation_dir/node_modules/reveal.js/plugin/markdown/markdown.js" "$output_dir/node_modules/reveal.js/plugin/markdown/"

echo "✓ Published Big Sky slides to $output_dir"
