#!/bin/bash
set -euo pipefail

# Only run in remote (Claude Code on the web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Configure Gradle proxy so Java can resolve external hosts
# The sandbox routes traffic through an HTTP proxy; curl uses it automatically
# but Java's DNS doesn't, so we must set JVM proxy system properties.
if [ -n "${https_proxy:-}" ]; then
  PROXY_HOST=$(echo "$https_proxy" | sed 's|.*@||' | sed 's|:.*||')
  PROXY_PORT=$(echo "$https_proxy" | sed 's|.*:||')
  PROXY_USER=$(echo "$https_proxy" | sed 's|http://||' | sed 's|@.*||' | sed 's|:.*||')
  PROXY_PASS=$(echo "$https_proxy" | sed 's|http://||' | sed 's|@.*||' | sed 's|^[^:]*:||')

  mkdir -p ~/.gradle
  cat > ~/.gradle/gradle.properties << PROPEOF
systemProp.http.proxyHost=$PROXY_HOST
systemProp.http.proxyPort=$PROXY_PORT
systemProp.http.proxyUser=$PROXY_USER
systemProp.http.proxyPassword=$PROXY_PASS
systemProp.https.proxyHost=$PROXY_HOST
systemProp.https.proxyPort=$PROXY_PORT
systemProp.https.proxyUser=$PROXY_USER
systemProp.https.proxyPassword=$PROXY_PASS
systemProp.jdk.http.auth.tunneling.disabledSchemes=
systemProp.jdk.http.auth.proxying.disabledSchemes=
PROPEOF
fi

# Download Gradle distribution if not already cached
cd "$CLAUDE_PROJECT_DIR"
./gradlew --version > /dev/null 2>&1

# Warm Gradle dependency cache (downloads all plugins + dependencies)
./gradlew compileKotlin compileTestKotlin --no-daemon 2>/dev/null || true

# Install bun dependencies (for Tailwind CSS + Preact islands)
BUN="${BUN_INSTALL:-$HOME/.bun}/bin/bun"
if [ -x "$BUN" ] && [ -f "$CLAUDE_PROJECT_DIR/package.json" ]; then
  cd "$CLAUDE_PROJECT_DIR"
  "$BUN" install
fi
