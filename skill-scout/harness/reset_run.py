#!/usr/bin/env python3
"""Robust, reproducible reset for a skill-scout run. Replaces fragile shell globbing (a zsh
`rm a*.json b*.json` aborts entirely if any one glob has no match, leaving stale caches that the
scan then reuses — which silently bypassed the alias-aware scout in a trial).

Default (no flags): back up db/*.csv, reset all data tables to headers (conferences KEPT, rosters
cleared so every conference re-scans), preserve db/aliases.csv (human + learned memory), and clear
ALL harness run-caches (keeping *_speakers.json rosters so cached confs skip harvest).

Flags:
  --dry            print what would happen; change nothing
  --reset-aliases  also wipe db/aliases.csv back to its human `source=human` rows only
  --clear-rosters  also delete *_speakers.json (force a fresh harvest of every conference)
  --keep-rosters-stamp  do NOT clear conferences.roster_fetched_at (continue an interrupted run)
"""
import csv, io, os, sys, glob, datetime, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))          # harness/
DB = os.path.join(ROOT, "..", "db")
DRY = "--dry" in sys.argv
RESET_ALIASES = "--reset-aliases" in sys.argv
CLEAR_ROSTERS = "--clear-rosters" in sys.argv
KEEP_STAMP = "--keep-rosters-stamp" in sys.argv

HEADERS = {
    "speakers.csv": ["name", "norm_name", "affiliation"],
    "speaker_conferences.csv": ["norm_name", "conference"],
    "resolutions.csv": ["norm_name", "github_login", "confidence", "gh_name", "gh_company", "followers", "method", "resolved_at", "recheck_after"],
    "repos.csv": ["login", "name", "is_fork", "stars", "pushed_at", "head_sha", "last_scanned_at"],
    "skill_files.csv": ["login", "repo", "path", "status", "depth", "jvm_fit", "category", "lines", "notes", "reasoning", "first_seen", "last_seen"],
    "rejected.csv": ["login", "repo", "path", "reason", "reasoning", "first_seen", "last_seen"],
    "bundles.csv": ["login", "repo", "root", "name", "kind", "status", "depth", "members", "copies", "reasoning", "first_seen", "last_seen"],
    "runs.csv": ["started_at", "conference", "speakers", "resolved", "scanned_repos", "skipped_repos", "found", "parked", "notes"],
}
# harness run-cache families (NOT *_speakers.json rosters unless --clear-rosters)
CACHE_GLOBS = ["*_scout*.json", "*_chunk*.json", "*_prefilter.json", "*_bundles.json",
               "*_verdicts*.json", "*_ckpt.json", "*_conf.json", "*_aliases_add.csv"]


def main():
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bk = os.path.join(DB, f"_backup-{stamp}")
    print(f"reset_run {'(DRY) ' if DRY else ''}— db={os.path.normpath(DB)}")

    # 1) backup
    csvs = sorted(glob.glob(os.path.join(DB, "*.csv")))
    print(f"  backup {len(csvs)} CSVs -> {os.path.basename(bk)}/")
    if not DRY:
        os.makedirs(bk, exist_ok=True)
        for f in csvs:
            shutil.copy(f, bk)

    # 2) reset data tables to headers
    for f, cols in HEADERS.items():
        print(f"  reset  {f}")
        if not DRY:
            open(os.path.join(DB, f), "w").write(",".join(cols) + "\n")

    # 3) conferences: keep rows, clear roster_fetched_at (unless --keep-rosters-stamp)
    cpath = os.path.join(DB, "conferences.csv")
    rows = list(csv.DictReader(open(cpath)))
    cleared = 0
    for r in rows:
        if not KEEP_STAMP and r.get("roster_fetched_at"):
            r["roster_fetched_at"] = ""; cleared += 1
    print(f"  conferences: {len(rows)} kept, roster_fetched_at cleared on {cleared}")
    if not DRY:
        buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=["name", "url", "roster_fetched_at"], lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in ["name", "url", "roster_fetched_at"]})
        open(cpath, "w").write(buf.getvalue())

    # 4) aliases: preserve by default; --reset-aliases keeps only human rows
    apath = os.path.join(DB, "aliases.csv")
    if RESET_ALIASES and os.path.exists(apath):
        kept = [r for r in csv.DictReader(open(apath)) if r.get("source") == "human"]
        print(f"  aliases: reset to {len(kept)} human row(s) (dropped auto-learned)")
        if not DRY:
            cols = ["norm_name", "github_login", "decision", "source", "note", "decided_at"]
            buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n"); w.writeheader()
            for r in kept:
                w.writerow({c: r.get(c, "") for c in cols})
            open(apath, "w").write(buf.getvalue())
    else:
        print("  aliases: preserved (human + learned)")

    # 5) clear harness run-caches (robust: glob in Python, never aborts on empty match)
    globs = list(CACHE_GLOBS) + (["*_speakers.json"] if CLEAR_ROSTERS else [])
    files = sorted({p for g in globs for p in glob.glob(os.path.join(ROOT, g))})
    print(f"  clear {len(files)} cache file(s){'' if CLEAR_ROSTERS else ' (kept *_speakers.json rosters)'}")
    if not DRY:
        for p in files:
            os.remove(p)
    print("DONE" + (" (dry — nothing changed)" if DRY else ""))


if __name__ == "__main__":
    main()
