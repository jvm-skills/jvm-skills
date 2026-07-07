#!/usr/bin/env python3
"""Reject taxonomy + auto-classifier for scout hits (the noise-family optimization).

Every scanned skill-file hit that is NOT promoted to skill_files.csv (found/needs_review)
gets a disposition + reason here, so nothing is silently dropped and the non-JVM
"general / workflow" skills stay reviewable.

reason vocabulary
  jvm-collection      real JVM skill, member of a found collection (promote-worthy)
  already-listed      repo already in skills/**/*.yaml (EXCLUDE) — re-found, do not re-promote
  off-topic-workflow  real reusable skill, generic agent/dev workflow, NOT JVM-specific  <-- review these
  off-topic-service   real skill for an external service integration (Stripe/Zoom/...), not JVM
  off-topic-tech      real skill for non-JVM tech (CSS, robotics, another language)
  demo                example / workshop / newsletter / fictional-company demo skill
  boilerplate         duplicated template family (OpenSpec, Tessl iikit, SDD 01-06)
  vendored            third-party skill copied into the repo (not authored by the speaker)
  project-doc         bare CLAUDE.md / AGENTS.md project instructions, not a reusable skill
  test-fixture        skill under src/test/ — a fixture, not an authored skill
  review              real SKILL.md we have NOT yet judged JVM-vs-offtopic (queue for a human)
"""
import re, os

# Portable: repo-root skills/ resolved relative to this script (harness/ -> skill-scout -> repo),
# with an env override for CI / non-standard layouts.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
SKILLS_DIR = os.environ.get("SKILL_SCOUT_SKILLS_DIR") or os.path.join(_ROOT, "skills")

def load_exclude():
    ex = set()
    for root, _, files in os.walk(SKILLS_DIR):
        for fn in files:
            if fn.endswith((".yaml", ".yml")):
                for ln in open(os.path.join(root, fn), errors="replace"):
                    m = re.match(r"\s*repo:\s*['\"]?([^'\"#\s]+)", ln)
                    if m: ex.add(m.group(1).strip().lower())
    return ex
EXCLUDE = load_exclude()

SKILLFILES = ("skill.md", "agents.md", "agent.md", "claude.md", ".cursorrules")

def base_of(path):
    parts = path.split("/")
    if parts[-1].lower() in SKILLFILES and len(parts) >= 2:
        return parts[-2]
    return parts[-1]

# Cheap name-based JVM signal (no content fetch) — helps a human triage the `review` queue.
JVM_TOKENS = ("java", "kotlin", "spring", "jpa", "hibernate", "jooq", "quarkus", "micronaut", "ktor",
              "gradle", "maven", "jvm", "jdk", "jakarta", "testcontainers", "junit", "jbang", "graalvm",
              "jfr", "reactor", "vertx", "kafka", "mcp")
OFF_TOKENS = ("react", "vue", "svelte", "angular", "css", "tailwind", "daisyui", "python", "rust",
              "golang", " go ", "dotnet", "csharp", "php", "node", "npm", "terraform", "astro",
              "nextjs", "flutter", "swift", "stripe", "hubspot", "zoom", "tekton", "helm", "podman")
def jvm_hint(*texts):
    blob = " " + " ".join(t.replace("-", " ").replace("_", " ").replace("/", " ") for t in texts).lower() + " "
    j = next((t.strip() for t in JVM_TOKENS if t in blob), None)
    o = next((t.strip() for t in OFF_TOKENS if t in blob), None)
    if j and not o: return f" [name hints JVM: {j}]"
    if o and not j: return f" [name hints non-JVM: {o}]"
    if j and o:     return f" [mixed signal: {j}/{o}]"
    return ""

# Curated content judgments (path heuristics can't tell JVM-ness of a real skill).
# key = (login_lower, repo_lower, skill_base_lower) or (login_lower, repo_lower, '*')
OVERLAY = {
  ("victorrentea", "petclinic", "multi-review"): ("off-topic-workflow", "review orchestration via review-boss agent; language-agnostic"),
  ("victorrentea", "petclinic", "regen-user-manual"): ("off-topic-workflow", "regenerate project user manual; generic workflow"),
  ("victorrentea", "ai-central", "caveman"): ("off-topic-workflow", "ultra-compressed comms mode; token efficiency, not JVM"),
  ("raphaeldelio", "agent-skills", "packet-orchestration"): ("off-topic-workflow", "parallel multi-agent packet orchestration; project-agnostic"),
  ("raphaeldelio", "agent-skills", "thread-branching"): ("off-topic-workflow", "handoff-prompt generator for new threads; not JVM"),
  ("jamesward", "skills", "zen-of-james"): ("off-topic-workflow", "personal FP coding philosophy; general, not JVM-specific"),
  ("adambien", "zsmith", "code-reviewer"): ("off-topic-workflow", "generic code review skill (zsmith demo)"),
  ("adambien", "zsmith", "explain"): ("off-topic-workflow", "generic code-explanation skill (zsmith demo)"),
  ("adambien", "zsmith", "java-modernizer"): ("test-fixture", "16-line skill under src/test/skills/ — JVM but shallow fixture"),
  ("johnsonr", "ecstasy-skill", "*"): ("off-topic-tech", "Ecstasy/XTC language assistance (non-JVM language)"),
  ("johnsonr", "pack-stripe", "*"): ("off-topic-service", "Stripe billing workflows (Embabel pack)"),
  ("johnsonr", "pack-hubspot", "*"): ("off-topic-service", "HubSpot CRM (Embabel pack)"),
  ("johnsonr", "pack-zoom", "*"): ("off-topic-service", "Zoom recordings (Embabel pack)"),
  ("johnsonr", "pack-google", "*"): ("off-topic-service", "Google Docs/Drive/Sheets workflows (Embabel pack)"),
  ("johnsonr", "pack-github", "*"): ("off-topic-service", "generic GitHub workflows (Embabel pack)"),
  ("johnsonr", "pack-research", "*"): ("off-topic-service", "web search (Embabel pack)"),
  ("johnsonr", "pack-movie", "*"): ("off-topic-service", "movie data (Embabel pack, demo)"),
  ("gamussa", "dotfiles", "tavily-search"): ("off-topic-service", "Tavily web search"),
  ("gamussa", "ai-assisted-engineering", "ui-ux-pro-max"): ("off-topic-tech", "UI/UX design skill"),
  ("asm0dey", "calit", "*"): ("off-topic-tech", "daisyUI CSS-framework skills"),
  ("thomasvitale", "agents-skills-oci-artifacts-spec", "manage-pull-requests"): ("off-topic-service", "Forgejo pull-request management"),
  ("myfear", "the-main-thread", "*"): ("demo", "newsletter/fictional-company content-pipeline demo skills"),
  ("markpollack", "loopy", "classpath-skill"): ("test-fixture", "classpath-skill test fixture"),
  ("martinfrancois", "java-streams-skill", "*"): ("already-listed", "EXCLUDE: skills/language/streams-java.yaml"),
  ("martinfrancois", "java-optionals-skill", "*"): ("already-listed", "EXCLUDE: skills/language/optional-java.yaml"),
  ("arturskowronski", "clawd-reachy-mini", "action-skill"): ("off-topic-tech", "Reachy-mini robot action skill (robotics, non-JVM)"),
  ("arturskowronski", "ksef-cli", "ksef-cli"): ("off-topic-service", "Polish KSeF e-invoice CLI (Python tool)"),
}

def classify(login, repo, path):
    p = path.lower(); r = repo.lower(); fname = path.split("/")[-1].lower()
    b = base_of(path).lower(); ll = login.lower()

    # already-listed in the directory (EXCLUDE)
    if f"{ll}/{r}" in EXCLUDE:
        ov = OVERLAY.get((ll, r, "*")) or OVERLAY.get((ll, r, b))
        return ov if ov else ("already-listed", "repo already in skills/**/*.yaml")

    # vendored third-party plugin (author != repo owner)
    m = re.search(r"\.tessl/plugins/([^/]+)/", p)
    if m and m.group(1).lower() != ll:
        return ("vendored", f"vendored 3rd-party plugin '{m.group(1)}' — not authored by speaker")

    # boilerplate template families
    if re.search(r"openspec-(apply|archive|continue|explore|new|propose|ff|onboard|sync|verify|bulk)", p):
        return ("boilerplate", "OpenSpec change-workflow template (duplicated set)")
    if "intent-integrity-kit" in p or re.search(r"/iikit-[0-9a-z]", p) or ".tessl/tiles/" in p:
        return ("boilerplate", "Tessl intent-integrity-kit / tile template")
    if re.search(r"/0[1-7]-(spec|specify|plan|clarify|checklist|task|implement|execute|analyze|design)", p):
        return ("boilerplate", "SDD numbered-step template (01-0x)")

    # AdamBien/airails — a real Java collection mixed with off-topic helpers
    if ll == "adambien" and r == "airails":
        if p.startswith("documentation/"): return ("off-topic-tech", f"doc tooling ({b}: mermaid/drawio/readme)")
        if p.startswith("web/"): return ("off-topic-tech", f"web frontend skill ({b})")
        if b == "enterprisifier": return ("off-topic-workflow", "overengineering novelty skill (comedic)")
        if fname == "skill.md": return ("jvm-collection", f"Adam Bien airails Java skill '{b}' — promote-worthy")

    # demo / example
    if re.search(r"(^|[-/_])(demo|workshop|sample|playground|kata)([-/_]|$)", r) or re.search(r"voxxed\w*\d{2,4}", r):
        return ("demo", "demo/workshop repo")
    if b in ("ai-tutor", "pdf", "travel-planner", "dogs", "hotel-booking"):
        return ("demo", "example/demo skill")

    # curated content judgments
    ov = OVERLAY.get((ll, r, b)) or OVERLAY.get((ll, r, "*"))
    if ov: return ov

    # bare project instructions (no /skills/ payload)
    if fname in ("claude.md", "agents.md", "agent.md", ".cursorrules") and "/skills/" not in p and ".claude/skills" not in p:
        return ("project-doc", "bare project AI-instructions file")

    # residual: a real SKILL.md not yet judged
    return ("review", "real SKILL.md — classify JVM vs off-topic")

# reasons that are NOT rejections (still recorded, but flagged as keep/promote/known)
NON_REJECT = {"jvm-collection", "already-listed", "review"}
