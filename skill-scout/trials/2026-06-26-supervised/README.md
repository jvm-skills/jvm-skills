# Trial + supervised runs — archived 2026-06-26

Snapshot of the skill-scout DB after the 2 trials (Spring I/O 15, Devnexus 8) and 4 supervised
runs (jPrime 30, Spring I/O committers 20, Devnexus 20, GeeCON 19). The live `skill-scout/db`
was reset to empty after this archive so the full afk run is a clean pass.

## Restore (continue-mode instead of fresh)

To resume from this snapshot instead of starting empty, copy the archived tables back over the
live DB, then relaunch the loop:

```bash
# from the repo root
cp skill-scout/trials/2026-06-26-supervised/db/*.csv skill-scout/db/
```

Then run `/skill-scout` (or the Workflow directly) — the queue picks up wherever these CSVs left off.

## Tallies

Row counts in this snapshot (regenerate with the command below):

| Table | Rows |
|---|---|
| `conferences.csv` | 4 |
| `rejected.csv` | 222 |
| `repos.csv` | 7 |
| `resolutions.csv` | 93 |
| `runs.csv` | 6 |
| `skill_files.csv` | 7 |
| `speaker_conferences.csv` | 96 |
| `speakers.csv` | 93 |

```bash
# reproduce the tallies (data rows, excluding the header)
cd skill-scout/trials/2026-06-26-supervised/db && \
  for f in *.csv; do printf '%s: %s\n' "$f" "$(($(wc -l < "$f") - 1))"; done
```
