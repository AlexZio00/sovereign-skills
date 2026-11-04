"""test_trigger_probe.py - exact skill matching, invoked_skills / served_model recording, eval-set location.
Run: python -m pytest test_trigger_probe.py -q   (no `claude` call is made: Popen is faked)."""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trigger_probe as tp


def test_exact_match_not_substring():
    assert tp.matches_skill("pdf", "pdf") and tp.matches_skill("/pdf", "pdf") and tp.matches_skill(" pdf ", "pdf")
    for other in ("pdf-tools", "anthropic-skills:pdf", "xpdf", "pd", ""):
        assert not tp.matches_skill(other, "pdf"), other


def test_skill_values_need_closing_quote():
    assert tp.skill_values('{"skill": "pd') == []                   # still streaming: prefix is not a value
    assert tp.skill_values('{"skill": "pdf"') == ["pdf"]
    assert tp.skill_values('{"skill":"a:b", "args": "x"}') == ["a:b"]


class _FakeProc:
    def __init__(self, events, returncode=0, stderr=b""):
        self.stdout = io.BytesIO(b"".join(json.dumps(e).encode() + b"\n" for e in events))
        self.stderr = io.BytesIO(stderr)
        self.returncode = returncode

    def poll(self):
        return self.returncode

    def kill(self):
        pass

    def wait(self, timeout=None):
        return self.returncode


def _run(monkeypatch, events, skill="pdf"):
    monkeypatch.setattr(tp, "CLAUDE_BIN", "claude")
    monkeypatch.setattr(tp.subprocess, "Popen", lambda *a, **k: _FakeProc(events))
    return tp.run_single_query("q", skill, 5, None)


def _stream_skill(partials, model="claude-test-1"):
    ev = [{"type": "stream_event", "event": {"type": "message_start", "message": {"model": model}}},
          {"type": "stream_event", "event": {"type": "content_block_start",
                                              "content_block": {"type": "tool_use", "name": "Skill"}}}]
    ev += [{"type": "stream_event", "event": {"type": "content_block_delta",
                                               "delta": {"type": "input_json_delta", "partial_json": p}}}
           for p in partials]
    return ev + [{"type": "result"}]


def test_streaming_prefix_and_lookalike_do_not_trigger(monkeypatch):
    r = _run(monkeypatch, _stream_skill(['{"skill": "pdf-', 'tools"}']))          # old code: "pdf" in text -> True
    assert r["triggered"] is False and r["invoked"] == ["pdf-tools"] and r["served_model"] == "claude-test-1"


def test_streaming_exact_triggers_and_records(monkeypatch):
    r = _run(monkeypatch, _stream_skill(['{"skill": "pd', 'f"}']))
    assert r["triggered"] is True and r["invoked"] == ["pdf"] and r["served_model"] == "claude-test-1"


def test_assistant_message_path_and_init_model_fallback(monkeypatch):
    ev = [{"type": "system", "subtype": "init", "model": "claude-init-1"},
          {"type": "assistant", "message": {"model": "claude-real-2", "content": [
              {"type": "tool_use", "name": "Skill", "input": {"skill": "docx"}},
              {"type": "tool_use", "name": "Skill", "input": {"skill": "anthropic-skills:pdf"}}]}},
          {"type": "result"}]
    r = _run(monkeypatch, ev, skill="pdf")
    assert r == {"triggered": False, "invoked": ["anthropic-skills:pdf", "docx"], "served_model": "claude-real-2",
                 "errored": False, "error": None}
    r = _run(monkeypatch, [{"type": "system", "subtype": "init", "model": "claude-init-1"}, {"type": "result"}])
    assert r["served_model"] == "claude-init-1" and r["triggered"] is False


def test_no_model_in_stream_is_none_not_guessed(monkeypatch):
    r = _run(monkeypatch, [{"type": "result"}])
    assert r["served_model"] is None


def test_run_probe_aggregates_invoked_and_models(monkeypatch):
    answers = iter([{"triggered": True, "invoked": ["pdf"], "served_model": "m1"},
                    {"triggered": False, "invoked": ["docx"], "served_model": "m1"},
                    {"triggered": False, "invoked": [], "served_model": None}])
    monkeypatch.setattr(tp, "run_single_query", lambda *a, **k: next(answers))
    out = tp.run_probe([{"query": "q", "should_trigger": True}], "pdf", 3, 5, 1, 0.5, "alias")
    r = out["results"][0]
    assert r["triggers"] == 1 and r["invoked_skills"] == {"docx": 1, "pdf": 1}
    assert r["served_models"] == ["m1"] and r["model_unrecorded_runs"] == 1
    assert out["requested_model"] == "alias" and out["served_models"] == ["m1"] and out["model_unrecorded_runs"] == 1


def test_eval_set_location_and_validation():
    assert tp.resolve_eval_set(None, "pdf") == os.path.join(tp.EVAL_DIR, "pdf.json")
    assert tp.resolve_eval_set("mine", "pdf") == os.path.join(tp.EVAL_DIR, "mine.json")
    assert tp.resolve_eval_set("a/b.json", "pdf") == "a/b.json"
    assert tp.EVAL_DIR.replace("\\", "/").endswith("/.trigger-evals")
    ok = [{"query": "make a pdf", "should_trigger": True}, {"query": "hello", "should_trigger": False}]
    assert tp.validate_eval_set(ok) is None
    for bad in ([], {}, [{"query": "x"}], [{"query": "", "should_trigger": True}], [{"query": "x", "should_trigger": 1}]):
        assert tp.validate_eval_set(bad) is not None, bad


def _capture(monkeypatch, events, returncode=0, stderr=b"", **kw):
    seen = {}

    def fake_popen(cmd, **k):
        seen["cmd"], seen["kwargs"] = cmd, k
        return _FakeProc(events, returncode, stderr)

    monkeypatch.setattr(tp, "CLAUDE_BIN", "claude")
    monkeypatch.setattr(tp.subprocess, "Popen", fake_popen)
    r = tp.run_single_query("q", "pdf", 5, None, **kw)
    return r, seen


def test_command_has_verbose_with_stream_json(monkeypatch):
    _, seen = _capture(monkeypatch, [{"type": "result"}])
    cmd = seen["cmd"]
    assert "--verbose" in cmd and cmd[cmd.index("--output-format") + 1] == "stream-json"
    assert "--strict-mcp-config" not in cmd and "--setting-sources" not in cmd   # opt-in only


def test_extra_args_and_cwd(monkeypatch, tmp_path):
    r, seen = _capture(monkeypatch, [{"type": "result"}], cwd=str(tmp_path),
                       extra_args=("--strict-mcp-config", "--setting-sources", "project"))
    assert seen["kwargs"]["cwd"] == str(tmp_path) and tmp_path.is_dir()          # given cwd is used and kept
    assert "--strict-mcp-config" in seen["cmd"] and seen["cmd"][-2:] == ["--setting-sources", "project"]
    assert r["errored"] is False


def test_default_cwd_is_isolated_temp_dir(monkeypatch):
    _, seen = _capture(monkeypatch, [{"type": "result"}])
    assert os.path.basename(seen["kwargs"]["cwd"]).startswith("trigger-probe-")
    assert not os.path.exists(seen["kwargs"]["cwd"])                              # removed afterwards


def test_nonzero_exit_is_errored_not_untriggered(monkeypatch):
    r, _ = _capture(monkeypatch, [], returncode=1, stderr=b"error: unknown option '--bogus'\n")
    assert r["errored"] is True and r["triggered"] is False
    assert "code 1" in r["error"] and "unknown option" in r["error"]


def test_error_result_event_is_errored(monkeypatch):
    r, _ = _capture(monkeypatch, [{"type": "result", "is_error": True, "result": "Credit balance is too low"}])
    assert r["errored"] is True and "Credit balance" in r["error"]


def test_timeout_is_errored(monkeypatch):
    monkeypatch.setattr(tp, "CLAUDE_BIN", "claude")
    monkeypatch.setattr(tp.subprocess, "Popen", lambda *a, **k: _FakeProc([]))
    r = tp.run_single_query("q", "pdf", 0, None)
    assert r["errored"] is True and "timeout" in r["error"]


def test_clean_run_without_trigger_is_not_errored(monkeypatch):
    r, _ = _capture(monkeypatch, [{"type": "result"}])
    assert r["errored"] is False and r["error"] is None and r["triggered"] is False


def test_run_probe_reports_errored_runs_separately(monkeypatch):
    answers = iter([{"triggered": True, "invoked": ["pdf"], "served_model": "m1", "errored": False, "error": None},
                    {"triggered": False, "invoked": [], "served_model": None, "errored": True, "error": "boom"},
                    {"triggered": False, "invoked": [], "served_model": None, "errored": True, "error": "boom"}])
    monkeypatch.setattr(tp, "run_single_query", lambda *a, **k: next(answers))
    out = tp.run_probe([{"query": "q", "should_trigger": True}], "pdf", 3, 5, 1, 0.5, None)
    r = out["results"][0]
    assert r["runs"] == 1 and r["errored_runs"] == 2 and r["errors"] == ["boom", "boom"]
    assert r["trigger_rate"] == 1.0 and r["pass"] is True and out["errored_runs"] == 2


def test_all_errored_query_is_neither_pass_nor_fail(monkeypatch):
    err = {"triggered": False, "invoked": [], "served_model": None, "errored": True, "error": "boom"}
    monkeypatch.setattr(tp, "run_single_query", lambda *a, **k: err)
    out = tp.run_probe([{"query": "q", "should_trigger": False}], "pdf", 2, 5, 1, 0.5, None)
    r = out["results"][0]
    assert r["pass"] is None and r["trigger_rate"] is None
    assert out["summary"] == {"total": 1, "passed": 0, "failed": 0, "errored": 1}


def test_worker_exception_counts_as_errored(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("spawn failed")
    monkeypatch.setattr(tp, "run_single_query", boom)
    out = tp.run_probe([{"query": "q", "should_trigger": True}], "pdf", 1, 5, 1, 0.5, None)
    assert out["results"][0]["pass"] is None and "spawn failed" in out["results"][0]["errors"][0]


def test_duplicate_queries_rejected():
    dup = [{"query": "make a pdf", "should_trigger": True}, {"query": " make a pdf ", "should_trigger": False}]
    msg = tp.validate_eval_set(dup)
    assert msg is not None and "item 1" in msg and "item 0" in msg


def test_dry_run_prints_estimated_time(tmp_path):
    import subprocess
    ev = tmp_path / "e.json"
    ev.write_text(json.dumps([{"query": "a", "should_trigger": True}, {"query": "b", "should_trigger": False}]))
    out = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "trigger_probe.py"),
                          "--skill-name", "x", "--eval-set", str(ev), "--runs-per-query", "3", "--timeout", "60",
                          "--num-workers", "2", "--dry-run"], capture_output=True, text=True)
    data = json.loads(out.stdout)
    assert data["total_api_calls"] == 6 and data["estimated_max_seconds"] == 3 * 60   # ceil(6 / 2) waves x 60 s
    assert data["estimated_max_minutes"] == 3.0


# --- split eval sets (tuning / heldout / review / real) ---

def _r(split, should, triggers, runs=2):
    return {"split": split, "should_trigger": should, "triggers": triggers, "runs": runs}


def test_split_metrics_per_split_and_overall_pass():
    results = ([_r("tuning", True, 2), _r("tuning", False, 0), _r("tuning", True, 2)]
               + [_r("heldout", True, 2), _r("heldout", False, 0), _r("heldout", False, 0)])
    m = tp.split_metrics(results)
    assert m["splits"]["tuning"]["precision"] == 1.0 and m["splits"]["heldout"]["recall"] == 1.0
    assert m["splits"]["tuning"]["verdict"] == "PASS" and m["verdict"] == "PASS"


def test_one_failing_split_fails_overall():
    results = ([_r("tuning", True, 2), _r("tuning", False, 0), _r("tuning", True, 2)]
               + [_r("real", True, 0), _r("real", False, 2), _r("real", True, 1)])
    m = tp.split_metrics(results)
    assert m["splits"]["real"]["verdict"] == "FAIL" and m["verdict"] == "FAIL"


def test_small_split_is_too_small_not_pass():
    results = [_r("tuning", True, 2), _r("tuning", False, 0), _r("tuning", True, 2),
               _r("review", True, 2), _r("review", False, 0)]
    m = tp.split_metrics(results)
    assert m["splits"]["review"]["verdict"] == "too_small"
    assert m["verdict"] == "INCOMPLETE"


def test_missing_split_defaults_to_tuning_and_zero_denominator_is_none():
    m = tp.split_metrics([{"should_trigger": False, "triggers": 0, "runs": 2}] * 3)
    s = m["splits"]["tuning"]
    assert s["cases"] == 3 and s["precision"] is None and s["recall"] is None and s["verdict"] == "UNMEASURED"


def test_all_errored_cases_do_not_count_toward_min_cases():
    # 3 cases, 2 with every run errored -> only 1 measured -> too_small
    results = [_r("heldout", True, 2), _r("heldout", True, 0, runs=0), _r("heldout", False, 0, runs=0)]
    s = tp.split_metrics(results)["splits"]["heldout"]
    assert s["cases"] == 3 and s["measured_cases"] == 1 and s["verdict"] == "too_small"


def test_unknown_split_rejected():
    assert "split" in tp.validate_eval_set([{"query": "a", "should_trigger": True, "split": "train"}])
    assert tp.validate_eval_set([{"query": "a", "should_trigger": True, "split": "heldout"}]) is None


def test_eval_set_sha256_is_stable_and_order_sensitive():
    a = [{"query": "x", "should_trigger": True}, {"query": "y", "should_trigger": False}]
    assert tp.eval_set_sha256(a) == tp.eval_set_sha256(json.loads(json.dumps(a)))
    assert tp.eval_set_sha256(a) != tp.eval_set_sha256(list(reversed(a)))
