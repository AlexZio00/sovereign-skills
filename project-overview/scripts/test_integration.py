#!/usr/bin/env python3
"""
test_integration.py — end-to-end idempotency + marker-preservation test.
No pytest dependency. Run: python test_integration.py
Exit code 0 = all pass, 1 = failure.
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_overview import main

FAILURES = []


def check(name, condition):
    if condition:
        print(f"PASS: {name}")
    else:
        print(f"FAIL: {name}")
        FAILURES.append(name)


tmp_root = tempfile.mkdtemp(prefix="project-overview-test-")
try:
    # --- fixture: fake project with a real state-snapshot handoff ---
    proj_dir = os.path.join(tmp_root, "project-a")
    memory_dir = os.path.join(proj_dir, "memory")
    os.makedirs(memory_dir, exist_ok=True)
    handoff_path = os.path.join(memory_dir, "session-handoff-LATEST.md")
    with open(handoff_path, "w", encoding="utf-8") as f:
        f.write(
            '---\n'
            'name: Session Handoff — Latest\n'
            'description: test desc\n'
            'type: handoff\n'
            '---\n'
            '<!-- state-snapshot v1 -->\n'
            '```yaml\n'
            'ts: 2026-07-06\n'
            'ctx: "test context"\n'
            '```\n'
        )

    registry_path = os.path.join(tmp_root, "projects-registry.md")
    with open(registry_path, "w", encoding="utf-8") as f:
        f.write(f"# Projects Registry\n\n- ProjectA: {proj_dir}\n")

    output_path = os.path.join(tmp_root, "OVERVIEW.md")

    # --- pre-seed OVERVIEW.md with human-written text + no markers yet ---
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Project Overview\n\nHuman-written preface — must be preserved.\n")

    # --- run 1 ---
    rc1 = main(["--registry", registry_path, "--output", output_path])
    check("main() run1 exit code 0", rc1 == 0)

    with open(output_path, encoding="utf-8") as f:
        text_after_run1 = f.read()

    check("run1 preserves human preface", "Human-written preface — must be preserved." in text_after_run1)
    check("run1 creates AUTO markers", "<!-- AUTO:START -->" in text_after_run1)
    check("run1 includes project name", "ProjectA" in text_after_run1)
    check("run1 includes ts", "2026-07-06" in text_after_run1)
    check("run1 includes ctx", "test context" in text_after_run1)

    # --- append human text after markers (simulating manual edit) ---
    with open(output_path, "a", encoding="utf-8") as f:
        f.write("\nAdditional human-written note.\n")
    with open(output_path, encoding="utf-8") as f:
        text_before_run2 = f.read()

    # --- run 2 (idempotency + preservation check) ---
    rc2 = main(["--registry", registry_path, "--output", output_path])
    check("main() run2 exit code 0", rc2 == 0)

    with open(output_path, encoding="utf-8") as f:
        text_after_run2 = f.read()

    check(
        "run2 preserves manually appended text after markers",
        "Additional human-written note." in text_after_run2,
    )
    check("run2 preserves human preface", "Human-written preface — must be preserved." in text_after_run2)

    # Extract AUTO block from both runs to compare byte-identity of the
    # generated section specifically (ignoring the manually appended text
    # which lives outside the block and differs between run1/run2 snapshots).
    def extract_auto_block(text):
        s = text.find("<!-- AUTO:START -->")
        e = text.find("<!-- AUTO:END -->")
        return text[s:e + len("<!-- AUTO:END -->")]

    block1 = extract_auto_block(text_after_run1)
    block2 = extract_auto_block(text_after_run2)
    check("AUTO block byte-identical across run1 and run2 (idempotency oracle)", block1 == block2)

    # --- run 3 with unchanged inputs: full-file AUTO block must still match ---
    rc3 = main(["--registry", registry_path, "--output", output_path])
    with open(output_path, encoding="utf-8") as f:
        text_after_run3 = f.read()
    block3 = extract_auto_block(text_after_run3)
    check("AUTO block byte-identical across run2 and run3", block2 == block3)
    check(
        "run3 still preserves manually appended text",
        "Additional human-written note." in text_after_run3,
    )

    # --- missing registry -> BLOCKED, non-zero exit, no crash ---
    rc_missing = main(["--registry", os.path.join(tmp_root, "does-not-exist.md"), "--output", output_path])
    check("main() returns non-zero when registry missing", rc_missing == 1)

    # --- empty registry -> BLOCKED, non-zero exit ---
    empty_registry_path = os.path.join(tmp_root, "empty-registry.md")
    with open(empty_registry_path, "w", encoding="utf-8") as f:
        f.write("# Projects Registry\n\n(no projects)\n")
    rc_empty = main(["--registry", empty_registry_path, "--output", output_path])
    check("main() returns non-zero when registry has 0 projects", rc_empty == 1)

    # --- project with no handoff file -> entry shows 'no snapshot', no crash ---
    no_handoff_proj = os.path.join(tmp_root, "no-handoff-project")
    os.makedirs(no_handoff_proj, exist_ok=True)
    registry_with_missing = os.path.join(tmp_root, "registry-missing-handoff.md")
    with open(registry_with_missing, "w", encoding="utf-8") as f:
        f.write(f"- NoHandoffProject: {no_handoff_proj}\n")
    output_path2 = os.path.join(tmp_root, "OVERVIEW2.md")
    rc_nohandoff = main(["--registry", registry_with_missing, "--output", output_path2])
    check("main() handles project with missing handoff gracefully", rc_nohandoff == 0)
    with open(output_path2, encoding="utf-8") as f:
        text_nohandoff = f.read()
    check(
        "missing handoff renders as 'no snapshot'",
        "no snapshot" in text_nohandoff.lower(),
    )

    # --- malformed AUTO markers (END before START) -> recovered, not crashed ---
    malformed_output_path = os.path.join(tmp_root, "OVERVIEW_malformed.md")
    with open(malformed_output_path, "w", encoding="utf-8") as f:
        f.write(
            "# Project Overview\n\n"
            "<!-- AUTO:END -->\n"
            "stray content from a manual edit\n"
            "<!-- AUTO:START -->\n"
        )
    rc_malformed = main(["--registry", registry_path, "--output", malformed_output_path])
    check("main() handles malformed AUTO markers without crashing", rc_malformed == 0)
    with open(malformed_output_path, encoding="utf-8") as f:
        text_malformed = f.read()
    check(
        "malformed-marker recovery preserves prior content",
        "stray content from a manual edit" in text_malformed,
    )
    check(
        "malformed-marker recovery still renders the new AUTO block",
        "ProjectA" in text_malformed,
    )

finally:
    shutil.rmtree(tmp_root, ignore_errors=True)

print()
if FAILURES:
    print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
    sys.exit(1)
else:
    print("ALL PASS")
    sys.exit(0)
