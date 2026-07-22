export const meta = {
  name: 'review-pr-skills',
  description: 'Strict multi-rulebook review of skill listings added in open PRs',
  whenToUse: 'Open PRs add or change skills/**/*.yaml listings and need an approval verdict before merge',
  phases: [
    { title: 'Discover', detail: 'open PRs → changed skill listings', model: 'haiku' },
    { title: 'Evidence', detail: 'fetch SKILL.md skill-unit + repo signals per candidate', model: 'sonnet' },
    { title: 'Judge', detail: 'one strict judge per rulebook per candidate', model: 'opus' },
    { title: 'Verify', detail: 'adversarial refute + API spot-check on non-rejects', model: 'opus' },
    { title: 'Synthesize', detail: 'cross-candidate dedup + per-PR recommendation', model: 'opus' },
    { title: 'Challenge', detail: 'Sol deliberation-advisor challenges the closing recommendations' },
  ],
}

// args (all optional):
//   { prs: [25, 26], crossFamily: true }
//   prs         — restrict to these PR numbers; default = every open PR touching skills/**/*.yaml
//   crossFamily — verify approvals with the GPT `reviewer` agent (claudex-only); falls back to Opus

const RULEBOOKS = [
  {
    key: 'approval-rulebook',
    path: 'docs/skill-approval-rulebook.md',
    brief:
      'The consolidated jvm-skills Approval Rulebook. Run its §7 reviewer decision procedure IN ORDER and stop at the first kill. Apply hard gates H1–H8 (authorship, substance, depth, extractability, JVM fit incl. H5a–d, real APIs, reusability, metadata), the §4 rejection taxonomy with its precedence order, §5 category/trust guidance incl. the workflow-bundle carve-out, and the §6 dedup / best-in-class policy.',
  },
  {
    key: 'scout-eval',
    path: 'skill-scout/harness/rules/eval.md',
    brief:
      'The field-tested skill-scout judge/recheck rules. Judge as the STRICT Opus recheck, not the lenient scanner (the changelog shows the scanner over-promotes). Use its reject-reason vocabulary (demo, project-doc, vendored, test-fixture, boilerplate, off-topic-*, hallucinated-api, jvm-collection, already-listed).',
  },
  {
    key: 'contributing',
    path: 'CONTRIBUTING.md',
    brief:
      'The listing schema and trust policy. Verify the PR YAML has every required field, one of the 8 valid categories matching its directory, an honest trust level (community for PR submissions unless a maintainer vetted it; official only when the author made the library/tool the skill teaches), and that repo + skill_path resolve to a real SKILL.md.',
  },
]

const CANDIDATES_SCHEMA = {
  type: 'object',
  required: ['candidates'],
  properties: {
    candidates: {
      type: 'array',
      items: {
        type: 'object',
        required: ['pr', 'title', 'prAuthor', 'listingPath', 'yaml'],
        properties: {
          pr: { type: 'number' },
          title: { type: 'string' },
          prAuthor: { type: 'string' },
          listingPath: { type: 'string' },
          yaml: { type: 'string', description: 'full listing YAML content at the PR head' },
          repo: { type: 'string', description: 'owner/repo the listing points at' },
          skillPath: { type: 'string' },
          category: { type: 'string' },
          trust: { type: 'string' },
        },
      },
    },
  },
}

const EVIDENCE_SCHEMA = {
  type: 'object',
  required: ['skillBody', 'skillUnitFiles', 'repoSignals', 'provenanceFlags', 'dedupHits', 'apiClaims'],
  properties: {
    skillBody: { type: 'string', description: 'the fetched SKILL.md body (first ~300 lines + outline if longer)' },
    skillUnitFiles: { type: 'array', items: { type: 'string' }, description: 'sibling files in the skill dir with sizes' },
    repoSignals: { type: 'string', description: 'stars, fork?, primary language, pushed_at, author match' },
    provenanceFlags: { type: 'array', items: { type: 'string' } },
    dedupHits: { type: 'array', items: { type: 'string' } },
    apiClaims: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string' },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['verdict', 'rule', 'reasoning'],
  properties: {
    verdict: { enum: ['approve', 'needs_review', 'reject'] },
    rule: { type: 'string', description: 'the specific gate/reason from YOUR rulebook that decided it' },
    reasoning: { type: 'string' },
    metadataIssues: { type: 'array', items: { type: 'string' } },
  },
}

const REFUTE_SCHEMA = {
  type: 'object',
  required: ['refuted', 'reasoning'],
  properties: {
    refuted: { type: 'boolean' },
    reasoning: { type: 'string' },
    apiChecks: {
      type: 'array',
      items: {
        type: 'object',
        required: ['claim', 'exists'],
        properties: {
          claim: { type: 'string' },
          exists: { type: 'boolean' },
          evidence: { type: 'string' },
        },
      },
    },
  },
}

const SYNTH_SCHEMA = {
  type: 'object',
  required: ['perPr'],
  properties: {
    perPr: {
      type: 'array',
      items: {
        type: 'object',
        required: ['pr', 'recommendation', 'comment'],
        properties: {
          pr: { type: 'number' },
          recommendation: { enum: ['approve-and-merge', 'request-changes', 'close'] },
          comment: { type: 'string', description: 'ready-to-post PR review comment citing the decisive gate(s)' },
        },
      },
    },
    dedupNotes: { type: 'string' },
  },
}

// ---------------------------------------------------------------------------

phase('Discover')
const disc = await agent(
  'You are in the jvm-skills repo checkout (a curated directory of AI coding skills for JVM ' +
    'developers; each listing is a skills/<category>/<name>.yaml pointing at an external repo + ' +
    'skill_path). Find every skill listing changed by OPEN pull requests:\n' +
    '1. Run: gh pr list --state open --json number,title,headRefName,author --limit 100\n' +
    '2. For each PR run: gh pr diff <n> --name-only  — keep only files matching skills/**/*.yaml.\n' +
    '3. For each kept file, recover its FULL content at the PR head from the patch in ' +
    'gh pr diff <n> (added files carry the whole body; for modified files reconstruct the head ' +
    'version). Parse out repo, skill_path, category, trust when present.\n' +
    'Skip PRs that touch no skills/**/*.yaml. Return one candidate per changed listing file, ' +
    'raw data only.',
  { label: 'discover-prs', phase: 'Discover', model: 'haiku', effort: 'low', schema: CANDIDATES_SCHEMA }
)

let candidates = (disc && disc.candidates) || []
if (args && Array.isArray(args.prs) && args.prs.length) {
  candidates = candidates.filter((c) => args.prs.includes(c.pr))
}
if (!candidates.length) {
  log('No open PRs touch skills/**/*.yaml — nothing to review.')
  return { candidates: [], perPr: [] }
}
log(`${candidates.length} candidate listing(s) across PRs: ${[...new Set(candidates.map((c) => c.pr))].join(', ')}`)

// ---------------------------------------------------------------------------

const evidencePrompt = (c) =>
  'You are in the jvm-skills repo checkout. Gather EVIDENCE — facts only, no verdict — for this ' +
  `skill-listing candidate from PR #${c.pr} ("${c.title}", by ${c.prAuthor}):\n\n` +
  `Listing file: ${c.listingPath}\nListing YAML at PR head:\n${c.yaml}\n\n` +
  'Collect:\n' +
  '1. The skill-unit: resolve repo + skill_path from the YAML and fetch the SKILL.md body via ' +
  '"gh api repos/<owner>/<repo>/contents/<path>" (base64-decode) or raw.githubusercontent.com. ' +
  'List the sibling files in the same skill directory (references/, knowledge/, scripts) with ' +
  'byte sizes. If the body exceeds ~500 lines, include the first 300 lines verbatim plus a ' +
  'heading-level outline of the rest.\n' +
  '2. Repo signals: "gh api repos/<owner>/<repo>" → stargazers_count, fork, language, pushed_at, ' +
  'created_at, owner login. Note whether the repo owner matches the listing author field and the ' +
  `PR author (${c.prAuthor}).\n` +
  '3. Provenance red flags in body/frontmatter/path: import_url, "Original source"/"Adapted ' +
  'from" attribution, scope: repository, maturity: starter, vendor/ or foreign-login path ' +
  'segments, machine-local absolute paths, numbered-sibling pipeline references (01-*.md, ' +
  '"Phase 3", harness.sh), open injection slots, src/test/** or src/main/resources/** paths.\n' +
  '4. Dedup facts: grep the local skills/**/*.yaml for the same repo, same author, or an ' +
  'overlapping topic; grep skill-scout/db/rejected.csv and skill-scout/db/skill_files.csv for ' +
  'this owner/repo/path and quote hits verbatim with their dates and reasons.\n' +
  '5. Up to 6 verbatim claimed APIs / classes / config keys / commands from the body worth ' +
  'spot-checking later (list only — do NOT verify them yourself).\n' +
  'Report exact quotes and numbers. No judgment, no verdict.'

const judgePrompt = (c, ev, r) =>
  `You are a STRICT skill-approval judge for jvm-skills. Read ${r.path} in this repo first — ` +
  `that is your ONLY rulebook for this judgment. ${r.brief}\n\n` +
  'Default posture: the candidate must PROVE it deserves a listing; actively try to disqualify ' +
  'it. Judge on the evidence below, plus anything you verify yourself (you may read repo files ' +
  'and run gh).\n\n' +
  `Candidate: PR #${c.pr} adds ${c.listingPath}\nListing YAML:\n${c.yaml}\n\n` +
  `EVIDENCE:\n${JSON.stringify(ev, null, 1)}\n\n` +
  'Return: verdict (approve | needs_review | reject), the specific gate/reason from YOUR ' +
  'rulebook that decided it, 2–4 sentences naming what the skill actually teaches and the ' +
  'decisive signal, and any listing-metadata defects. Judge ONLY against your assigned rulebook ' +
  '— do not import rules from other documents.'

const refutePrompt = (c, ev, judgments) =>
  'You are an adversarial verifier for a jvm-skills listing approval. Your job is to REFUTE ' +
  'the case for listing this skill. Default to refuted=true if uncertain.\n\n' +
  `Candidate: PR #${c.pr} adds ${c.listingPath}\nListing YAML:\n${c.yaml}\n\n` +
  `Panel judgments so far:\n${JSON.stringify(judgments, null, 1)}\n\n` +
  `API claims to spot-check (gate H6 of docs/skill-approval-rulebook.md):\n${JSON.stringify(ev.apiClaims)}\n\n` +
  'Do all of:\n' +
  '1. Spot-check at least 3 of the claimed APIs/classes/config keys against the real library ' +
  'or tool (gh api / gh search code on the upstream source, raw.githubusercontent.com, or web ' +
  'fetch of official docs). Record each claim → exists true/false with evidence.\n' +
  '2. Attack extractability: could a practitioner drop the skill-unit into a different project ' +
  'unchanged?\n' +
  '3. Attack JVM fit: could the concrete content be lifted verbatim into a Python/JS project? ' +
  'Is the code JVM-native or REST/CLI ops of a Java-runtime service?\n' +
  '4. Attack authority/provenance: is the submitter plausibly the author? Any sign of copied ' +
  'or generated content?\n' +
  'Then decide: refuted=true if the approval should NOT stand, with your strongest argument.'

async function refute(c, ev, judgments, idx) {
  const opts = { label: `verify:pr${c.pr}`, phase: 'Verify', effort: 'high', schema: REFUTE_SCHEMA }
  if (args && args.crossFamily) {
    try {
      return await agent(refutePrompt(c, ev, judgments), { ...opts, agentType: 'reviewer' })
    } catch (e) {
      log(`cross-family reviewer unavailable for PR #${c.pr} (${e && e.message}); falling back to Opus`)
    }
  }
  return agent(refutePrompt(c, ev, judgments), { ...opts, model: 'opus' })
}

// Per-candidate chain: evidence → judge panel → adversarial verify. No barrier between
// candidates — one PR can be in Verify while another is still in Evidence.
const results = await pipeline(
  candidates,
  (c) =>
    agent(evidencePrompt(c), {
      label: `evidence:pr${c.pr}`,
      phase: 'Evidence',
      model: 'sonnet',
      effort: 'low',
      schema: EVIDENCE_SCHEMA,
    }),
  async (ev, c) => {
    if (!ev) return null
    const raw = await parallel(
      RULEBOOKS.map((r) => () =>
        agent(judgePrompt(c, ev, r), {
          label: `judge:${r.key}:pr${c.pr}`,
          phase: 'Judge',
          model: 'opus',
          effort: 'high',
          schema: VERDICT_SCHEMA,
        })
      )
    )
    const judgments = RULEBOOKS.map((r, i) => (raw[i] ? { rulebook: r.key, ...raw[i] } : null)).filter(Boolean)
    return { ev, judgments }
  },
  async (prev, c, idx) => {
    if (!prev) return null
    const { ev, judgments } = prev
    const unanimousReject = judgments.length > 0 && judgments.every((j) => j.verdict === 'reject')
    const refutation = unanimousReject ? null : await refute(c, ev, judgments, idx)
    if (unanimousReject) log(`PR #${c.pr} ${c.listingPath}: unanimous reject — skipping verify`)
    return { candidate: c, evidence: ev, judgments, refutation }
  }
)

const judged = results.filter(Boolean)

// ---------------------------------------------------------------------------
// Barrier is deliberate here: dedup (§6 best-in-class) and per-PR recommendations
// need ALL candidates' verdicts side by side — PRs from one author often overlap.

phase('Synthesize')
const synthesis = await agent(
  'You are the closing synthesizer for a jvm-skills PR review. Read ' +
    'docs/skill-approval-rulebook.md §5 (categories/trust) and §6 (dedup & best-in-class) in ' +
    'this repo, then produce the final per-PR recommendations from the panel results below.\n\n' +
    `PANEL RESULTS (evidence, one judgment per rulebook, adversarial refutation):\n` +
    `${JSON.stringify(judged.map((r) => ({
      pr: r.candidate.pr,
      listingPath: r.candidate.listingPath,
      yaml: r.candidate.yaml,
      judgments: r.judgments,
      refutation: r.refutation,
      dedupHits: r.evidence.dedupHits,
      repoSignals: r.evidence.repoSignals,
    })), null, 1)}\n\n` +
    'Rules:\n' +
    '- A hard-gate reject or a sustained refutation (refuted=true) cannot be outvoted by ' +
    'approvals; approve-and-merge requires every judge at approve/needs_review AND ' +
    'refuted=false AND clean metadata.\n' +
    '- Apply §6 across the candidates AND the existing skills/**/*.yaml listings: if two ' +
    'candidates teach substantially the same thing, at most one wins; the loser is ' +
    'request-changes or close with "duplicate-of" named.\n' +
    '- needs_review or fixable metadata defects → request-changes with the exact fixes listed.\n' +
    '- Each PR comment must cite the specific gate/reason (e.g. "H5 / off-topic-tech") and say ' +
    'in 1–3 sentences what the skill actually teaches — never a generic template.\n' +
    'Return one entry per PR (a PR with several listings gets one combined recommendation).',
  { label: 'synthesize', phase: 'Synthesize', model: 'opus', effort: 'high', schema: SYNTH_SCHEMA }
)

// ---------------------------------------------------------------------------
// Closing challenge: one Sol deliberation-advisor call on the DISTILLED
// recommendations (compact decisions + decisive evidence, never raw file dumps —
// Sol has a small context window). Guidance only; the synthesis stays authoritative,
// the challenge is surfaced alongside it for the maintainer.

phase('Challenge')
const challengeBrief = {
  task:
    'jvm-skills is a curated directory of AI coding skills for JVM developers; each listing is a ' +
    'YAML pointing at an external SKILL.md. Three open PRs from one author were panel-reviewed ' +
    '(three rulebook judges per candidate, then an adversarial verifier). Below are the final ' +
    'per-PR recommendations and the decisive evidence.',
  recommendations: (synthesis && synthesis.perPr) || [],
  dedupNotes: (synthesis && synthesis.dedupNotes) || '',
  decisiveEvidence: judged.map((r) => ({
    pr: r.candidate.pr,
    listing: r.candidate.listingPath,
    judgeVerdicts: r.judgments.map((j) => `${j.rulebook}: ${j.verdict} — ${j.rule}`),
    refuted: r.refutation ? r.refutation.refuted : null,
    refutationCore: r.refutation ? String(r.refutation.reasoning).slice(0, 1500) : 'skipped (unanimous reject)',
  })),
}
let challenge = null
try {
  challenge = await agent(
    'You are the closing deliberation advisor for a skill-directory review. Challenge these ' +
      'final recommendations before they go to the maintainer. Attack: (1) internal ' +
      'consistency — do the verdicts follow from the cited evidence, and are like cases treated ' +
      'alike across the three PRs? (2) the dedup call — is "substantially the same" really ' +
      'satisfied, or does the Kubernetes reframing carry distinct value? (3) proportionality — ' +
      'is any recommendation harsher or softer than its decisive evidence supports? (4) blind ' +
      'spots — what did every reviewer miss? End with: for each PR, CONCUR or DISSENT (with the ' +
      'change you would make), plus at most 3 questions the maintainer should answer before ' +
      'acting.\n\n' +
      JSON.stringify(challengeBrief, null, 1),
    { label: 'sol-challenge', phase: 'Challenge', agentType: 'deliberation-advisor', effort: 'high' }
  )
} catch (e) {
  log(`Sol deliberation-advisor unavailable (${e && e.message}) — returning synthesis unchallenged.`)
}

return {
  candidates: judged.map((r) => ({
    pr: r.candidate.pr,
    listingPath: r.candidate.listingPath,
    judgments: r.judgments.map((j) => ({ rulebook: j.rulebook, verdict: j.verdict, rule: j.rule, reasoning: j.reasoning, metadataIssues: j.metadataIssues || [] })),
    refutation: r.refutation,
  })),
  synthesis,
  solChallenge: challenge,
}
