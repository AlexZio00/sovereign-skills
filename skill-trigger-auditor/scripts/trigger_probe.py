#!/usr/bin/env python3
"""Empirical trigger probe: measurement engine for the skill-trigger-auditor HOLDOUT_TEST.

Adapted from the measurement engine of Anthropic's skill-creator plugin (run_eval.py):
spawn a tool-restricted subprocess and parse its stream-json output to observe real Skill
tool_use calls. The original plants a temporary `.claude/commands/{uuid}.md` file to
test a not-yet-registered candidate skill; this script validates the description of an
already registered skill, so that workaround is not needed here. The train/test
auto-improvement loop and automatic description rewriting are also left out: they would
conflict with the auditor's rule that an audit never edits the skill it audits. This
script only measures.

Safety design:
- A holdout query may look like a real work order, so the subprocess runs with
  --disallowedTools Bash,Write,Edit,NotebookEdit and, by default, an isolated scratch temp
  directory as its cwd. Pass --cwd to probe project skills (a project's .claude/skills only
  loads when the subprocess runs inside that project).
- Isolation limit: the subprocess still loads your user settings, hooks and MCP servers.
  --strict-mcp-config skips MCP servers; --setting-sources limits which settings files load.
  Both are opt-in because they can also change which skills are visible: keep a positive
  control query in the eval set.
- A run whose subprocess fails (non-zero exit, timeout, error result) is reported as
  `errored`, never as "not triggered".
- Hard cap on total calls (len(queries) * runs_per_query) of 100; exceeding it is an
  immediate error.
- If the `claude` CLI is not found the script stops. It never falls back silently.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_TOTAL_CALLS = 100
FLOOR_MAX_CALLS = 5  # hard cap in --floor mode, enforced here regardless of what the docs say
DISALLOWED_TOOLS = "Bash,Write,Edit,NotebookEdit"
# Saved eval sets: <skill-name>.json = [{"query": "...", "should_trigger": true|false}, ...]
# Folder defaults to ./.trigger-evals in the working directory; override with TRIGGER_EVAL_DIR.
EVAL_DIR = os.environ.get("TRIGGER_EVAL_DIR") or os.path.join(os.getcwd(), ".trigger-evals")

# Resolved once at import time. On Windows, `claude` resolves to a `.cmd` shim
# (npm global install) — subprocess.Popen(["claude", ...]) with shell=False
# fails with WinError 2 on some Python/Windows combos because CreateProcess
# doesn't apply PATHEXT resolution the way cmd.exe does. Using the fully
# resolved path (with .CMD extension) fixes it without needing shell=True.
CLAUDE_BIN = shutil.which("claude")


for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def check_claude_cli() -> None:
    """Hard-stop if the `claude` binary isn't on PATH — no silent fallback."""
    if CLAUDE_BIN is None:
        print(
            "ERROR: empirical mode was requested but the `claude` CLI was not found on PATH. "
            "Not falling back to the default judgment mode; check the installation.",
            file=sys.stderr,
        )
        sys.exit(2)


def _read_stream(pipe, q: queue.Queue) -> None:
    """Background thread: push raw lines onto the queue until pipe closes.

    select.select() on a subprocess pipe only works on POSIX — on Windows it
    can only be used with sockets and raises WinError 10093 (WSAStartup) when
    given a pipe file descriptor. A reader thread + queue works on both.
    """
    try:
        for raw_line in iter(pipe.readline, b""):
            q.put(raw_line)
    finally:
        q.put(None)  # sentinel: stream closed


def _drain_stderr(pipe, sink: list) -> None:
    """Background thread: keep stderr (it must be read or a full pipe blocks the child); only the tail is kept."""
    try:
        for raw_line in iter(pipe.readline, b""):
            sink.append(raw_line.decode("utf-8", errors="replace"))
            if len(sink) > 50:
                del sink[0]
    except (OSError, ValueError):
        pass


_SKILL_KEY = re.compile(r'"skill"\s*:\s*"((?:[^"\\]|\\.)*)"')


def skill_values(partial_json: str) -> list[str]:
    """Complete `"skill": "<value>"` strings found in a (possibly still streaming) Skill tool input.
    A value counts only once its closing quote has arrived, so a prefix like "pd" never reads as "pdf"."""
    out = []
    for raw in _SKILL_KEY.findall(partial_json):
        try:
            out.append(json.loads(f'"{raw}"'))
        except json.JSONDecodeError:
            out.append(raw)
    return out


def matches_skill(value: str, skill_name: str) -> bool:
    """Exact match (an optional leading slash is ignored). The old `skill_name in value` substring test counted
    `pdf-tools` or `anthropic-skills:pdf` as a hit for `pdf` and inflated trigger rates."""
    return value.strip().lstrip("/") == skill_name


def resolve_eval_set(arg: str | None, skill_name: str) -> str:
    """--eval-set path, or a bare name / nothing -> EVAL_DIR/<name or skill>.json (the saved-sets location)."""
    if not arg:
        return os.path.join(EVAL_DIR, f"{skill_name}.json")
    if os.path.isfile(arg) or os.sep in arg or "/" in arg or arg.endswith(".json"):
        return arg
    return os.path.join(EVAL_DIR, f"{arg}.json")


def validate_eval_set(queries) -> str | None:
    """None if queries is a non-empty list of {query: str, should_trigger: bool}, else the problem."""
    if not isinstance(queries, list) or not queries:
        return "eval set must be a non-empty JSON list"
    seen: dict[str, int] = {}
    for i, q in enumerate(queries):
        if not (isinstance(q, dict) and isinstance(q.get("query"), str) and q["query"].strip()
                and isinstance(q.get("should_trigger"), bool)):
            return f"item {i} needs a non-empty string `query` and a boolean `should_trigger`"
        key = q["query"].strip()
        if key in seen:
            return f"item {i} repeats the query of item {seen[key]} (each query must be unique, results are keyed by query)"
        seen[key] = i
    return None


def run_single_query(
    query: str,
    skill_name: str,
    timeout: int,
    model: str | None,
    cwd: str | None = None,
    extra_args: tuple = (),
) -> dict:
    """Spawn a tool-restricted `claude -p` and check whether it invokes the Skill tool for `skill_name`
    (exact name; plugin skills are named `plugin:skill`). Runs in `cwd`, or in an isolated temp directory if None.
    Returns {"triggered": bool, "invoked": [every Skill name seen, sorted],
    "served_model": the model that answered, or None if the stream did not say,
    "errored": bool, "error": short reason or None}. A failed run (non-zero exit, timeout, error result)
    has errored=True and must not be read as "not triggered"."""
    scratch_dir = None if cwd else tempfile.mkdtemp(prefix="trigger-probe-")
    run_dir = cwd or scratch_dir
    cmd = [
        CLAUDE_BIN,
        "-p", query,
        "--output-format", "stream-json",
        "--verbose",  # stream-json with -p is rejected without --verbose
        "--include-partial-messages",
        "--disallowedTools", DISALLOWED_TOOLS,
    ]
    if model:
        cmd.extend(["--model", model])
    cmd.extend(extra_args)

    # Remove CLAUDECODE env var to allow nesting claude -p inside a Claude
    # Code session (same pattern as the source skill-creator scripts).
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=run_dir,
        env=env,
    )

    line_queue: queue.Queue = queue.Queue()
    reader = threading.Thread(target=_read_stream, args=(process.stdout, line_queue), daemon=True)
    reader.start()
    stderr_tail: list = []
    err_thread = threading.Thread(target=_drain_stderr, args=(process.stderr, stderr_tail), daemon=True)
    err_thread.start()

    triggered = False
    invoked: set[str] = set()
    served_model: str | None = None
    start_time = time.time()
    pending_tool_name: str | None = None
    accumulated_json = ""
    error: str | None = None
    stream_closed = False

    def result() -> dict:
        return {"triggered": triggered, "invoked": sorted(invoked), "served_model": served_model,
                "errored": error is not None and not triggered,
                "error": None if triggered else error}  # an observed trigger is real evidence even if the run later failed

    try:
        while time.time() - start_time < timeout:
            try:
                raw_line = line_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if raw_line is None:
                stream_closed = True
                break  # stream closed (sentinel)

            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if event.get("type") == "system" and event.get("subtype") == "init" and not served_model:
                served_model = event.get("model") or served_model  # fallback; message models below win
            if event.get("type") == "stream_event":
                se = event.get("event", {})
                se_type = se.get("type", "")
                if se_type == "message_start":
                    served_model = se.get("message", {}).get("model") or served_model
                elif se_type == "content_block_start":
                    cb = se.get("content_block", {})
                    if cb.get("type") == "tool_use" and cb.get("name") == "Skill":
                        pending_tool_name = "Skill"
                        accumulated_json = ""
                elif se_type == "content_block_delta" and pending_tool_name:
                    delta = se.get("delta", {})
                    if delta.get("type") == "input_json_delta":
                        accumulated_json += delta.get("partial_json", "")
                        names = skill_values(accumulated_json)
                        invoked.update(names)
                        if any(matches_skill(n, skill_name) for n in names):
                            triggered = True
                            return result()
                elif se_type in ("content_block_stop", "message_stop"):
                    pending_tool_name = None
            elif event.get("type") == "assistant":
                message = event.get("message", {})
                served_model = message.get("model") or served_model
                for item in message.get("content", []):
                    if item.get("type") == "tool_use" and item.get("name") == "Skill":
                        value = str(item.get("input", {}).get("skill", ""))
                        invoked.add(value)
                        if matches_skill(value, skill_name):
                            triggered = True
            elif event.get("type") == "result":
                if event.get("is_error"):
                    error = "result event reported an error: " + str(event.get("result", ""))[:200]
                break
        else:
            error = f"timeout after {timeout}s before the run finished"

        if stream_closed:
            # The child closed stdout without a result event: check how it ended.
            try:
                code = process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                code = None
            if code not in (0, None):
                err_thread.join(timeout=2)
                tail = "".join(stderr_tail).strip()[-300:]
                error = f"claude exited with code {code}" + (f": {tail}" if tail else "")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        if scratch_dir:
            shutil.rmtree(scratch_dir, ignore_errors=True)

    return result()


def run_probe(
    queries: list[dict],
    skill_name: str,
    runs_per_query: int,
    timeout: int,
    num_workers: int,
    trigger_threshold: float,
    model: str | None,
    call_cap: int = MAX_TOTAL_CALLS,
    cwd: str | None = None,
    extra_args: tuple = (),
) -> dict:
    """Run the full holdout set and return per-query trigger rates and pass/fail."""
    total_calls = len(queries) * runs_per_query
    if total_calls > call_cap:
        raise ValueError(
            f"Requested call count ({total_calls} = {len(queries)} queries x {runs_per_query} runs) "
            f"exceeds the cap ({call_cap}); lower runs_per_query or the number of queries."
        )

    results = []
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_item = {}
        for item in queries:
            triggers = []
            futures = [
                executor.submit(run_single_query, item["query"], skill_name, timeout, model, cwd, extra_args)
                for _ in range(runs_per_query)
            ]
            future_to_item[item["query"]] = (item, futures)

        for query, (item, futures) in future_to_item.items():
            triggers = []
            invoked: dict[str, int] = {}  # Skill name -> number of runs that called it (any skill, not just the target)
            models: set[str] = set()
            unrecorded = 0
            errors: list[str] = []
            for f in as_completed(futures):
                try:
                    r = f.result()
                except Exception as e:
                    print(f"Warning: query failed: {e}", file=sys.stderr)
                    errors.append(f"{type(e).__name__}: {e}"[:300])
                    continue
                if r.get("errored"):
                    errors.append(str(r.get("error") or "unknown error"))
                    continue
                triggers.append(r["triggered"])
                for name in r["invoked"]:
                    invoked[name] = invoked.get(name, 0) + 1
                if r["served_model"]:
                    models.add(r["served_model"])
                else:
                    unrecorded += 1
            should_trigger = item["should_trigger"]
            if triggers:
                trigger_rate = sum(triggers) / len(triggers)
                did_pass = (
                    trigger_rate >= trigger_threshold
                    if should_trigger
                    else trigger_rate < trigger_threshold
                )
            else:  # every run errored: no measurement, so neither pass nor fail
                trigger_rate = None
                did_pass = None
            results.append({
                "query": query,
                "should_trigger": should_trigger,
                "trigger_rate": trigger_rate,
                "triggers": sum(triggers),
                "runs": len(triggers),
                "errored_runs": len(errors),
                "errors": errors[:3],
                "pass": did_pass,
                "invoked_skills": dict(sorted(invoked.items())),
                "served_models": sorted(models),
                "model_unrecorded_runs": unrecorded,
            })

    passed = sum(1 for r in results if r["pass"] is True)
    failed = sum(1 for r in results if r["pass"] is False)
    errored_queries = sum(1 for r in results if r["pass"] is None)
    errored_runs = sum(r["errored_runs"] for r in results)
    total = len(results)
    tp = sum(r["triggers"] for r in results if r["should_trigger"])
    pos_runs = sum(r["runs"] for r in results if r["should_trigger"])
    fn = pos_runs - tp
    fp = sum(r["triggers"] for r in results if not r["should_trigger"])
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0

    served = sorted({m for r in results for m in r["served_models"]})
    return {
        "skill_name": skill_name,
        "requested_model": model,  # alias such as "haiku" may serve a different model than expected - compare with served_models
        "served_models": served,
        "model_unrecorded_runs": sum(r["model_unrecorded_runs"] for r in results),
        "results": results,
        "summary": {"total": total, "passed": passed, "failed": failed, "errored": errored_queries},
        "errored_runs": errored_runs,  # runs whose subprocess failed: excluded from rates, never counted as "not triggered"
        "precision": precision,
        "recall": recall,
        "total_api_calls": total_calls,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Empirical trigger probe for a registered skill")
    parser.add_argument("--skill-name", required=True, help="Exact skill name as registered")
    parser.add_argument("--eval-set", default=None,
        help="Path to a JSON list of {query, should_trigger}, or a bare name; default = "
        "./.trigger-evals/<skill-name>.json (override the folder with TRIGGER_EVAL_DIR)")
    parser.add_argument("--runs-per-query", type=int, default=5)
    parser.add_argument(
        "--timeout", type=int, default=90,
        help="Per-call timeout in seconds. Sessions with extended thinking can need more "
        "than 45s before the tool_use decision, and an early kill gives a false negative, "
        "so the default is 90s. Raise it if calls still time out.",
    )
    parser.add_argument("--num-workers", type=int, default=5)
    parser.add_argument("--trigger-threshold", type=float, default=0.5)
    parser.add_argument("--model", default=None)
    parser.add_argument("--cwd", default=None,
        help="Run each probe inside this folder instead of an isolated temp directory. Needed to probe "
        "project skills (.claude/skills of that project). The folder is not modified by the probe "
        "(Bash/Write/Edit are disallowed) and not deleted.")
    parser.add_argument("--strict-mcp-config", action="store_true",
        help="Pass --strict-mcp-config to claude so no MCP servers load (none are given with --mcp-config). "
        "Opt-in: probes otherwise load your configured MCP servers.")
    parser.add_argument("--setting-sources", default=None,
        help="Pass --setting-sources <list> (user, project, local) to claude to limit which settings files "
        "(and their hooks) load. Opt-in: it can also change which skills are visible, so keep a positive "
        "control query in the eval set.")
    parser.add_argument("--dry-run", action="store_true",
        help="Print planned call count and estimated worst-case time, then exit; no dispatch")
    parser.add_argument("--floor", action="store_true",
        help=f"Small mandatory-floor mode: hard cap of {FLOOR_MAX_CALLS} calls regardless of "
        "eval-set size. The caller must still get user confirmation before dispatch.")
    args = parser.parse_args()

    eval_path = resolve_eval_set(args.eval_set, args.skill_name)
    if not os.path.isfile(eval_path):
        print(f"ERROR: eval set not found: {eval_path}", file=sys.stderr)
        sys.exit(2)
    with open(eval_path, encoding="utf-8") as f:
        queries = json.load(f)
    problem = validate_eval_set(queries)
    if problem:
        print(f"ERROR: {eval_path}: {problem}", file=sys.stderr)
        sys.exit(2)

    if args.cwd is not None and not os.path.isdir(args.cwd):
        print(f"ERROR: --cwd folder not found: {args.cwd}", file=sys.stderr)
        sys.exit(2)
    extra_args: list[str] = []
    if args.strict_mcp_config:
        extra_args.append("--strict-mcp-config")
    if args.setting_sources:
        extra_args.extend(["--setting-sources", args.setting_sources])

    call_cap = FLOOR_MAX_CALLS if args.floor else MAX_TOTAL_CALLS
    total_calls = len(queries) * args.runs_per_query
    if args.dry_run:
        waves = math.ceil(total_calls / max(1, args.num_workers))
        print(json.dumps({
            "planned_queries": len(queries),
            "runs_per_query": args.runs_per_query,
            "total_api_calls": total_calls,
            "within_limit": total_calls <= call_cap,
            "limit": call_cap,
            "mode": "floor" if args.floor else "full",
            "num_workers": args.num_workers,
            "timeout_per_call_s": args.timeout,
            # upper bound: calls x timeout / workers, rounded up to whole waves; most calls end sooner
            "estimated_max_seconds": waves * args.timeout,
            "estimated_max_minutes": round(waves * args.timeout / 60, 1),
            "cwd": args.cwd or "(isolated temp directory)",
            "extra_claude_args": extra_args,
        }, indent=2))
        return

    check_claude_cli()

    output = run_probe(
        queries=queries,
        skill_name=args.skill_name,
        runs_per_query=args.runs_per_query,
        timeout=args.timeout,
        num_workers=args.num_workers,
        trigger_threshold=args.trigger_threshold,
        model=args.model,
        call_cap=call_cap,
        cwd=args.cwd,
        extra_args=tuple(extra_args),
    )
    print(json.dumps(output, indent=2, ensure_ascii=False))
    if output["errored_runs"]:
        print(f"WARNING: {output['errored_runs']} run(s) errored and were excluded from the rates; "
              "see `errors` per query. Exit code 3.", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
