"""integration-intake decision ledger: records adopt/reject/defer decisions for external repos, tools and
patterns, and enforces the surface gates in code instead of leaving them to a report template.

Ledger file (JSONL, append-only; for the same (source, candidate) the latest record wins):
  default  ~/.claude/intake/ledger.jsonl
  override --ledger PATH   or   environment variable INTAKE_LEDGER
  Each record: {"source": "https://github.com/x/y", "candidate": "one line",
                "verdict": "adopted|rejected|deferred|screened", "date": "YYYY-MM-DD", "reason": "...",
                "target_files": [...], "scope": "single|multi|future",
                "rule_only_reason": "...(text-only targets)", "next_path": "...(rejected: when to look again)",
                "screen": "APPROVE|REVISE|REJECT|UNREACHABLE (screened only)"}

Gates:
  adopted  - at least one target file; scope given; a text-only adoption (rules/CLAUDE.md/docs) needs
             rule_only_reason; scope multi|future needs a text-home target (rules/*.md or CLAUDE.md) so other
             and future assets inherit it
  screened - first-pass repo-sweep result. Not an adopt/reject decision, only "looked this far" - no gates.
  deferred - needs a STATE.md target (a tracked deferral with a trigger, never "just left alone")
  rejected - needs next_path (this method failed vs pattern dropped + when to look again)

usage (--ledger PATH may stand before or after the command name):
  python intake_ledger.py [--ledger PATH] record --source URL --candidate "..." --verdict adopted --reason "..." \
      --target-file skills/x/SKILL.md --scope single
  python intake_ledger.py stats
  python intake_ledger.py lookup https://github.com/owner/repo [--search PATH ...]   # prior verdicts (Phase 0.3)
  python intake_ledger.py review [--days 30] [--invocations-dir DIR]   # after adoption: target still there? used?
  python intake_ledger.py screen-batch --file merged.json   # repo-sweep merged table -> verdict=screened records
  python intake_ledger.py split --file urls.txt             # repo list -> PRIOR (in ledger) / FRESH + denominator

Repo keys: github.com URLs and bare owner/repo become "owner/repo"; any other host (gitlab, codeberg, npm
pages, ssh "git@host:owner/repo.git") becomes "host/path"; a name that is not a URL (a tool, "npm:left-pad",
"@scope/pkg") is keyed by its full lowercase string.

A ledger line that is not valid JSON (or not a JSON object) is skipped and counted on stderr. A record without
a verdict is tolerated (shown as "(no verdict)", reported as a gate violation by stats).

lookup also greps plain-text mentions of the repo (whole-word match: acme/widget does not hit acme/widget-pro). Default search locations (relative to the current directory):
STATE.md, EXTERNAL_REFERENCES.md, docs/plans/**/*.md. Add more with --search PATH (file or directory, repeatable)
or the INTAKE_SEARCH_PATHS environment variable (paths separated by os.pathsep).

exit: 0 recorded / found / 1 lookup found nothing / 2 gate refusal or usage error
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

DEFAULT_LEDGER = os.environ.get("INTAKE_LEDGER") or os.path.expanduser("~/.claude/intake/ledger.jsonl")
VERDICTS = ("adopted", "rejected", "deferred", "screened")
SCREENS = ("APPROVE", "REVISE", "REJECT", "UNREACHABLE")
SCOPES = ("single", "multi", "future")
SCREEN_CANDIDATE = "repo-sweep screening"
_SCRIPT_EXT = (".py", ".sh", ".js", ".ts", ".mjs", ".ps1")


# ---- surface gates -------------------------------------------------------------------------------------------

def _parts(path: str) -> list[str]:
    return [x for x in path.replace("\\", "/").lower().split("/") if x]


def targets_of(rec: dict) -> list:
    """target_files as a list; a bare string is one target, not a sequence of characters."""
    t = rec.get("target_files") or []
    if isinstance(t, str):
        return [t]
    return list(t) if isinstance(t, (list, tuple)) else [t]


def is_text_home(path: str) -> bool:
    """A text home is a file other and future assets inherit from: rules/*.md or a root-level CLAUDE.md."""
    parts = _parts(path)
    if not parts:
        return False
    name, parent = parts[-1], (parts[-2] if len(parts) > 1 else "")
    if parent == "rules" and name.endswith(".md") and "skills" not in parts and "docs" not in parts:
        return True
    return name == "claude.md" and not ({"skills", "agents", "docs"} & set(parts))


def surface_kind(path: str) -> str:
    """'exec' (script, SKILL.md, agent definition, STATE.md deferral queue) or 'text' (rules, docs, references)."""
    parts = _parts(path)
    if not parts:
        return "text"
    name, parent = parts[-1], (parts[-2] if len(parts) > 1 else "")
    if is_text_home(path):
        return "text"
    if name == "state.md" and "memory" not in parts:
        return "exec"
    if name.endswith(_SCRIPT_EXT):
        return "exec"
    if "docs" in parts[:-1]:
        return "text"
    if name == "skill.md" or (parent == "agents" and name.endswith(".md")):
        return "exec"
    if "references" in parts[:-1]:
        i = parts.index("references")
        if (i >= 2 and parts[i - 2] == "skills") or (i >= 1 and parts[i - 1] == "agents"):
            return "exec"
    return "text"


def _bad_targets(rec: dict) -> str | None:
    bad = [x for x in targets_of(rec) if not isinstance(x, str) or not x.strip()]
    return f"target_files entries must be non-empty strings, got {bad!r}" if bad else None


def scope_violation(rec: dict) -> str | None:
    if _bad_targets(rec):
        return _bad_targets(rec)
    scope = rec.get("scope")
    if scope not in SCOPES:
        return (f"scope must be one of {SCOPES} (single: one asset / multi: several existing assets / "
                f"future: also assets not built yet)")
    if scope in ("multi", "future") and not any(is_text_home(t) for t in targets_of(rec)):
        return (f"scope={scope} needs a text-home target so other and future assets inherit it: "
                "rules/*.md or CLAUDE.md")
    return None


def rule_only_violation(rec: dict) -> str | None:
    """Adopted with only text targets and no rule_only_reason."""
    targets = targets_of(rec)
    if not targets or any(surface_kind(t) == "exec" for t in targets):
        return None
    if (rec.get("rule_only_reason") or "").strip():
        return None
    return ("all target_files are rule/doc text - add an executable target (script/skill/agent, or STATE.md "
            "with a trigger) or give rule_only_reason explaining why it cannot be mechanized")


def violation(rec: dict) -> str | None:
    v = rec.get("verdict")
    if v not in VERDICTS:
        return f"verdict must be one of {VERDICTS}"
    if not (rec.get("source") or "").strip() or not (rec.get("candidate") or "").strip():
        return "source and candidate are required"
    if v == "screened":
        return None if rec.get("screen") in SCREENS else f"screened needs screen in {SCREENS}"
    if v == "adopted":
        if not targets_of(rec):
            return "adopted needs at least one --target-file (the file that now carries the pattern)"
        return rule_only_violation(rec) or scope_violation(rec)
    if v == "deferred":
        if not any(isinstance(t, str) and os.path.basename(t.replace("\\", "/")).lower() == "state.md"
                   for t in targets_of(rec)):
            return "deferred needs a STATE.md target (a tracked deferral with a trigger)"
        return None
    if not (rec.get("next_path") or "").strip():
        return "rejected needs --next-path (method failure vs pattern dropped + when to look again)"
    return None


# ---- ledger I/O ----------------------------------------------------------------------------------------------

def load_counted(path: str) -> tuple[list[dict], int]:
    """(records, number of skipped lines). A line that is not valid JSON or not a JSON object is skipped."""
    if not os.path.isfile(path):
        return [], 0
    recs, skipped = [], 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for x in fh:
            if not x.strip():
                continue
            try:
                r = json.loads(x)
            except json.JSONDecodeError:
                skipped += 1
                continue
            if isinstance(r, dict):
                recs.append(r)
            else:
                skipped += 1
    return recs, skipped


def load(path: str) -> list[dict]:
    recs, skipped = load_counted(path)
    if skipped:
        print(f"[WARN] skipped {skipped} malformed ledger line(s) in {path}", file=sys.stderr)
    return recs


def _append(path: str, rec: dict) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def cmd_record(a) -> int:
    rec = {"source": a.source, "candidate": a.candidate, "verdict": a.verdict, "reason": a.reason,
           "date": a.date or datetime.now(timezone.utc).strftime("%Y-%m-%d"), "target_files": a.target_file}
    for k in ("scope", "rule_only_reason", "next_path", "screen"):
        if getattr(a, k):
            rec[k] = getattr(a, k)
    why = violation(rec)
    if why:
        print(f"[ERROR] {why}", file=sys.stderr)
        return 2
    _append(a.ledger, rec)
    print(f"[INTAKE-LEDGER] recorded {rec['verdict']}: {rec['candidate'][:60]}")
    return 0


def cmd_stats(a) -> int:
    latest = {}
    for r in load(a.ledger):
        latest[(r.get("source"), r.get("candidate"))] = r
    by = {}
    for r in latest.values():
        v = r.get("verdict") or "(no verdict)"
        by[v] = by.get(v, 0) + 1
    bad = [r for r in latest.values() if violation(r)]
    print(f"[INTAKE-LEDGER] candidates {len(latest)} {by} | gate violations {len(bad)}")
    for r in bad:
        print(f"  VIOLATION {str(r.get('candidate', ''))[:60]}: {violation(r)}")
    return 0


# ---- lookup (Phase 0.3) --------------------------------------------------------------------------------------

_URL_MARKERS = {"tree", "blob", "-", "commit", "commits", "releases", "issues", "pull", "pulls", "tags",
                "wiki", "raw", "src", "merge_requests", "actions"}


def _repo_key(query: str) -> str:
    """Stable key for a repo or tool.
    - github.com URL or bare 'owner/repo' -> 'owner/repo' (lowercase, no .git/query/fragment/tree path)
    - any other host (https://gitlab.com/g/r, git@host:o/r.git, ssh://host/o/r) -> 'host/path'
    - not a URL (a tool, 'npm:left-pad', '@scope/pkg') -> the full lowercase string"""
    base = query.strip().lower().split("#", 1)[0].split("?", 1)[0].rstrip("/")
    host = path = None
    m = (re.match(r"^[a-z][a-z0-9+.-]*://(?:[^/@]*@)?([^/:]+)(?::\d+)?/?(.*)$", base)
         or re.match(r"^(?:[^/@\s]+@)?([a-z0-9-]+(?:\.[a-z0-9-]+)+):/?(.+)$", base)  # scp-like git@host:owner/repo
         or re.match(r"^([a-z0-9-]+(?:\.[a-z0-9-]+)+)/(.+)$", base))  # host/owner/repo without scheme
    if m:
        host, path = m.group(1), m.group(2)
    if host is None:
        parts = [p for p in base.split("/") if p]
        if len(parts) == 2 and not base.startswith("@") and ":" not in base and " " not in base:
            return f"{parts[0]}/{parts[1][:-4] if parts[1].endswith('.git') else parts[1]}"  # github shorthand
        return base
    if host.startswith("www."):
        host = host[4:]
    segs = []
    for p in path.split("/"):
        if not p:
            continue
        if p in _URL_MARKERS:
            break
        segs.append(p)
    if segs and segs[-1].endswith(".git"):
        segs[-1] = segs[-1][:-4]
    if host == "github.com":
        return "/".join(segs[:2]) if segs else host
    return "/".join([host] + segs)


def _key_pattern(key: str) -> "re.Pattern[str]":
    """Whole-word match of a repo key in text: 'acme/widget' must not match 'acme/widget-pro' or 'xacme/widget'."""
    return re.compile(r"(?<![\w.@-])" + re.escape(key) + r"(?![\w-])", re.IGNORECASE)


def _display_path(path: str) -> str:
    try:
        return os.path.relpath(path)
    except ValueError:  # different drive on Windows
        return path


def _search_files(extra: list[str]) -> list[str]:
    paths = [os.path.join(os.getcwd(), n) for n in ("STATE.md", "EXTERNAL_REFERENCES.md")]
    paths.append(os.path.join(os.getcwd(), "docs", "plans"))
    paths += [p for p in os.environ.get("INTAKE_SEARCH_PATHS", "").split(os.pathsep) if p]
    paths += extra or []
    files = []
    for p in paths:
        if os.path.isdir(p):
            for root, _dirs, names in os.walk(p):
                files += [os.path.join(root, n) for n in names if n.endswith(".md")]
        elif os.path.isfile(p):
            files.append(p)
    return sorted(set(files))


def _tag(r: dict) -> str:
    if r.get("verdict") == "screened":
        return f"screened/{r.get('screen', '?')}"
    return str(r.get("verdict") or "(no verdict)")


def cmd_lookup(a) -> int:
    """Prior verdicts and mentions of a repo before a new intake. exit 0 = something found, 1 = fresh intake."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    key = _repo_key(a.query)
    pat = _key_pattern(key)
    hits = [r for r in load(a.ledger) if _repo_key(str(r.get("source") or "")) == key]  # exact: acme/widget != acme/widget-pro
    for r in hits:
        print(f"[LEDGER] {r.get('date', '?')} {_tag(r)}: {str(r.get('candidate', ''))[:90]}")
        if r.get("reason"):
            print(f"         reason: {str(r['reason'])[:160]}")
        if r.get("next_path"):
            print(f"         next_path: {str(r['next_path'])[:120]}")
    shown = 0
    for path in _search_files(a.search):
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = [(i, ln.strip()) for i, ln in enumerate(fh, 1) if pat.search(ln)]
        if not lines:
            continue
        shown += 1
        for i, ln in lines[:2]:
            print(f"[DOC] {_display_path(path)}:{i}: {ln[:140]}")
        if shown >= 10:
            print("[DOC] ... (10 files shown, more exist)")
            break
    if not hits and not shown:
        print(f"[INTAKE-LEDGER] no prior record for {key} - fresh intake")
        return 1
    return 0


# ---- review (after adoption) ---------------------------------------------------------------------------------

def home_rel(target: str) -> str:
    """'~/.claude/skills/x/SKILL.md', '/home/u/.claude/agents/a.md' or 'agents/a.md' -> path under .claude."""
    t = target.replace("\\", "/")
    if "/.claude/" in t:
        return t.split("/.claude/", 1)[1]
    return t[2:] if t.startswith("~/") else t


def asset_of(rel: str) -> str | None:
    """skills/<name>/... -> skill name, agents/<name>.md -> agent name, anything else -> None (use not measurable)."""
    parts = rel.split("/")
    if len(parts) >= 2 and parts[0] == "skills":
        return parts[1]
    if len(parts) == 2 and parts[0] == "agents" and parts[1].endswith(".md"):
        return parts[1][:-3]
    return None


def invocations(inv_dir: str | None) -> list[dict]:
    """Rows of *.jsonl files in inv_dir: {"date": "YYYY-MM-DD", "skills": [...], "agents": [...]} (names as
    strings, or objects with a "skill"/"agent"/"name" key; rows from any "source" count).
    Optional: the folder is whatever your setup uses to log which skills/agents were actually called."""
    rows = []
    if not inv_dir or not os.path.isdir(inv_dir):
        return rows
    for name in sorted(os.listdir(inv_dir)):
        if not name.endswith(".jsonl"):
            continue
        with open(os.path.join(inv_dir, name), encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(r, dict) and r.get("date") and ("skills" in r or "agents" in r):
                    rows.append(r)  # rows without a date or skills/agents keys cannot show use; ignore them
    return rows


def _names(v) -> set:
    """Skill/agent names from a list of strings or objects {"skill"|"agent"|"name": ...}."""
    out = set()
    for x in v if isinstance(v, list) else []:
        if isinstance(x, str):
            out.add(x)
        elif isinstance(x, dict):
            n = x.get("skill") or x.get("agent") or x.get("name")
            if isinstance(n, str):
                out.add(n)
    return out


def review_rows(recs: list[dict], today: str, days: int, home: str, inv_dir: str | None) -> list[dict]:
    """For adopted entries at least `days` old: is the target still there (missing), and was its skill/agent
    invoked since the adoption date (observed / dormant)? Targets that are not a skill or agent are n/a.
    Without an invocation log, skill/agent targets that exist are reported as "unmeasured"."""
    latest = {}
    for r in recs:
        latest[(r.get("source"), r.get("candidate"))] = r
    inv = invocations(inv_dir)
    measurable = bool(inv)
    cutoff = datetime.strptime(today, "%Y-%m-%d").date()
    out = []
    for r in latest.values():
        if r.get("verdict") != "adopted":
            continue
        try:
            adopted = datetime.strptime(str(r.get("date", "")), "%Y-%m-%d").date()
        except ValueError:
            continue
        if (cutoff - adopted).days < days:
            continue
        rels = [home_rel(t) for t in targets_of(r) if isinstance(t, str)]
        missing = [x for x in rels if not os.path.exists(os.path.join(home, x))]
        assets = {a for a in (asset_of(x) for x in rels) if a}
        uses = sum(1 for i in inv if str(i.get("date", "")) >= r["date"]
                   and assets & (_names(i.get("skills")) | _names(i.get("agents"))))
        if missing:
            status = "missing"
        elif not assets:
            status = "n/a"
        elif not measurable:
            status = "unmeasured"
        else:
            status = "observed" if uses else "dormant"
        out.append({"candidate": r.get("candidate", ""), "date": r["date"], "status": status,
                    "uses": uses, "assets": sorted(assets), "missing": missing})
    return out


def cmd_review(a) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    home = a.home or os.path.expanduser("~/.claude")
    inv_dir = a.invocations_dir or os.environ.get("INTAKE_INVOCATIONS_DIR")
    rows = review_rows(load(a.ledger), today=a.today or datetime.now().strftime("%Y-%m-%d"), days=a.days,
                       home=home, inv_dir=inv_dir)
    by = {}
    for r in rows:
        by[r["status"]] = by.get(r["status"], 0) + 1
    print(f"[INTAKE-REVIEW] adopted >= {a.days}d: {len(rows)} {by}")
    for r in rows:
        if r["status"] in ("missing", "dormant"):
            extra = f"missing {r['missing']}" if r["missing"] else f"0 uses of {r['assets']} since {r['date']}"
            print(f"  {r['status'].upper():8} {r['candidate'][:70]} - {extra}")
    return 0


# ---- screening batches ---------------------------------------------------------------------------------------

def cmd_screen_batch(a) -> int:
    """Append one `screened` record per repo of a repo-sweep merge result ({"table": [...]}, or a bare array of
    {repo_url, verdict, reason}). A repo whose latest screened record already has the same screen result is
    skipped, so re-running the same file adds nothing."""
    with open(a.file, encoding="utf-8") as fh:
        data = json.load(fh)
    table = data.get("table", []) if isinstance(data, dict) else data
    latest = {}
    for r in load(a.ledger):
        if r.get("verdict") == "screened":
            latest[_repo_key(str(r.get("source") or ""))] = r
    date = a.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    done = skipped = 0
    for e in table:
        if not isinstance(e, dict):
            skipped += 1
            continue
        url = (e.get("repo_url") or "").strip()
        screen = str(e.get("verdict", "")).strip().upper()
        rec = {"source": url, "candidate": SCREEN_CANDIDATE, "verdict": "screened", "screen": screen,
               "reason": (e.get("reason") or e.get("rationale") or "").strip(), "date": date, "target_files": []}
        if e.get("safety_flag"):
            rec["safety_flag"] = e["safety_flag"]
        prev = latest.get(_repo_key(url))
        if not url or violation(rec) or (prev and prev.get("screen") == screen):
            skipped += 1
            continue
        _append(a.ledger, rec)
        done += 1
    print(f"[INTAKE-LEDGER] screened recorded {done} / skipped {skipped} (invalid or unchanged) of {len(table)}")
    return 0


def cmd_split(a) -> int:
    """Split a repo list into PRIOR (any ledger record) and FRESH, and print the denominator.
    The list comes from --file (one URL or owner/repo per line) and/or positional arguments."""
    queries = list(a.urls)
    if a.file:
        with open(a.file, encoding="utf-8") as fh:
            queries += [x.strip() for x in fh if x.strip() and not x.lstrip().startswith("#")]
    latest = {}
    for r in load(a.ledger):
        if r.get("source"):
            latest[_repo_key(str(r["source"]))] = r  # file order = time order, so the last record wins
    seen, prior, fresh = set(), [], []
    for q in queries:
        key = _repo_key(q)
        if key in seen:
            continue
        seen.add(key)
        (prior if key in latest else fresh).append((key, latest.get(key)))
    for key, r in prior:
        print(f"PRIOR {key} {r.get('date', '?')} {_tag(r)}")
    for key, _ in fresh:
        print(f"FRESH {key}")
    print(f"[SPLIT] {len(seen)} unique repos = PRIOR {len(prior)} + FRESH {len(fresh)}"
          f" (duplicates in input: {len(queries) - len(seen)})")
    return 0


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="integration-intake decision ledger")
    ap.add_argument("--ledger", default=DEFAULT_LEDGER)
    sub = ap.add_subparsers(dest="cmd", required=True)
    # the same option is accepted after the command name; SUPPRESS keeps the value given before it
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--ledger", default=argparse.SUPPRESS)
    r = sub.add_parser("record", parents=[common])
    r.add_argument("--source", required=True)
    r.add_argument("--candidate", required=True)
    r.add_argument("--verdict", required=True, choices=VERDICTS)
    r.add_argument("--reason", default="")
    r.add_argument("--target-file", action="append", default=[])
    r.add_argument("--scope", choices=SCOPES)
    r.add_argument("--rule-only-reason")
    r.add_argument("--next-path")
    r.add_argument("--screen", choices=SCREENS)
    r.add_argument("--date")
    r.set_defaults(func=cmd_record)
    s = sub.add_parser("stats", parents=[common])
    s.set_defaults(func=cmd_stats)
    lk = sub.add_parser("lookup", parents=[common])
    lk.add_argument("query", help="repo URL or owner/repo")
    lk.add_argument("--search", action="append", default=[], help="extra file or directory of .md files to grep")
    lk.set_defaults(func=cmd_lookup)
    rv = sub.add_parser("review", parents=[common], help="adopted entries: target still there? asset used since?")
    rv.add_argument("--days", type=int, default=30)
    rv.add_argument("--today")
    rv.add_argument("--home", help="folder that adopted target paths are relative to (default ~/.claude)")
    rv.add_argument("--invocations-dir", help="folder of *.jsonl rows {date, skills, agents} (or INTAKE_INVOCATIONS_DIR)")
    rv.set_defaults(func=cmd_review)
    sb = sub.add_parser("screen-batch", parents=[common], help="repo-sweep merged table -> verdict=screened records")
    sb.add_argument("--file", required=True)
    sb.add_argument("--date")
    sb.set_defaults(func=cmd_screen_batch)
    sp = sub.add_parser("split", parents=[common], help="repo list -> PRIOR (in ledger) / FRESH + denominator")
    sp.add_argument("urls", nargs="*")
    sp.add_argument("--file")
    sp.set_defaults(func=cmd_split)
    a = ap.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
