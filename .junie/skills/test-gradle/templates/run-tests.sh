#!/usr/bin/env bash
# Run tests and output only failures.
# Usage: ./scripts/run-tests.sh [--tests "pattern"]...
# Examples:
#   ./scripts/run-tests.sh                                    # all tests
#   ./scripts/run-tests.sh --tests "*RankingGameSetupTest"    # single class
#   ./scripts/run-tests.sh --tests "*SetupTest" --tests "*LobbyTest"  # multiple
# Exit code: 0 if all passed, 1 if failures found, 2 if no results

set -uo pipefail

RESULTS_DIR="build/test-results/test"

# Forward all arguments to gradle (e.g. --tests patterns)
./gradlew test -Pplaywright.headless=true "$@" > build/gradle-test-out.txt 2>&1
TEST_EXIT=$?

if [ "$TEST_EXIT" -eq 0 ]; then
  echo "All tests passed."
  exit 0
fi

# Tests failed — parse results
if [ ! -d "$RESULTS_DIR" ]; then
  echo "ERROR: No test results directory at $RESULTS_DIR"
  echo "Gradle output:"
  tail -50 build/gradle-test-out.txt
  exit 2
fi

xml_files=("$RESULTS_DIR"/TEST-*.xml)
if [ ! -e "${xml_files[0]}" ]; then
  echo "ERROR: No TEST-*.xml files in $RESULTS_DIR"
  exit 2
fi

echo "## Failed Tests"
echo ""

failure_count=0

for xml_file in "${xml_files[@]}"; do
  # Skip files with no failures and no errors
  if grep -q 'failures="0"' "$xml_file" && grep -q 'errors="0"' "$xml_file"; then
    continue
  fi

  # Extract failing testcases using POSIX-compatible awk (no gawk capture groups)
  awk '
    /<testcase / {
      classname = ""
      name = ""
      # Extract classname="..." without gawk capture groups
      s = $0
      if (match(s, /classname="/)) {
        s = substr(s, RSTART + 11)
        classname = substr(s, 1, index(s, "\"") - 1)
      }
      s = $0
      if (match(s, /name="/)) {
        s = substr(s, RSTART + 6)
        name = substr(s, 1, index(s, "\"") - 1)
      }
      in_testcase = 1
      in_failure = 0
      failure_msg = ""
      failure_text = ""
    }
    in_testcase && (/<failure/ || /<error/) {
      in_failure = 1
      # Extract message="..."
      s = $0
      if (match(s, /message="/)) {
        s = substr(s, RSTART + 9)
        failure_msg = substr(s, 1, index(s, "\"") - 1)
      }
      # Capture text after > on same line
      if (match($0, />/)) {
        line = substr($0, RSTART + 1)
        sub(/<\/(failure|error)>.*/, "", line)
        if (line != "") failure_text = failure_text line "\n"
      }
      next
    }
    in_failure && (/<\/failure>/ || /<\/error>/) { in_failure = 0; next }
    in_failure { failure_text = failure_text $0 "\n" }
    /<\/testcase>/ || (in_testcase && /\/>$/) {
      if (failure_msg != "" || failure_text != "") {
        printf "### %s > %s FAILED\n", classname, name
        if (failure_msg != "") printf "%s\n", substr(failure_msg, 1, 500)
        n = split(failure_text, lines, "\n")
        printed = 0
        for (i = 1; i <= n && printed < 5; i++) {
          if (lines[i] ~ /tschuehly/) {
            gsub(/^[[:space:]]+/, "  ", lines[i])
            printf "%s\n", lines[i]
            printed++
          }
        }
        printf "---\n"
      }
      in_testcase = 0; in_failure = 0; failure_msg = ""; failure_text = ""
    }
  ' "$xml_file"

  # Count failures from this file
  file_failures=$(grep -o 'failures="[0-9]*"' "$xml_file" | grep -o '[0-9]*')
  file_errors=$(grep -o 'errors="[0-9]*"' "$xml_file" | grep -o '[0-9]*')
  failure_count=$((failure_count + file_failures + file_errors))
done

echo ""
echo "Summary: $failure_count test failure(s)"
exit 1
