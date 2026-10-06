"""Thử thách mở rộng 6b - vòng tiến hóa thứ hai (GUIDE Phần 6).

Tách biệt hoàn toàn khỏi thí nghiệm chính:
  - KHÔNG sửa skills/ (đã đóng băng bởi tag `freeze`); skill v2 ghi vào extension/skills-v2/.
  - KHÔNG ghi vào results/; kết quả ghi vào results-6b/.
  - KHÔNG sửa mã có sẵn; điều kiện `skills-v2` được đăng ký lúc chạy.

    python extension/evolve_round2.py curate            # vòng tiến hóa 2: hợp nhất skill v1 + phản hồi của skills-auto
    python extension/evolve_round2.py run --tasks all   # chạy điều kiện skills-v2
    python extension/evolve_round2.py table             # so sánh skills-auto (v1) với skills-v2
"""
import argparse
import json
import shutil
from pathlib import Path

from lab import runner
from lab.curator import TRACE_TAIL, parse_skill_blocks, validate_skill
from lab.model import make_model
from lab.tasks import ROOT, list_tasks

V1_DIR = ROOT / "skills" / "auto"
V2_DIR = ROOT / "extension" / "skills-v2"
RESULTS = ROOT / "results-6b"
CONDITION = "skills-v2"

PROMPT = """You maintain the SKILLS of a coding and data-analysis agent. This is the SECOND evolution round.
Below are (1) the CURRENT skills, written from earlier feedback, and (2) the failed checks (name and the grader's
feedback) and trace tails of new runs in which the agent HAD these skills. Rewrite the skill set so that the agent
avoids the remaining mistakes on NEW tasks of the same kind. You may keep, fix, split or merge skills.
Return the COMPLETE new set (at most {max_skills} skills): skills you do not return are deleted.

Rules:
- The agent never sees the grader's feedback: "RULE:" lines are organisation conventions NOT written in the task
  statement. Restate every convention concretely and completely (exact file names, headers, JSON keys and values,
  units, sort orders, naming formats). "Follow the rules" or "as specified" is useless.
- One skill per kind of task (code fixing, tabular data analysis, log parsing): a convention of one kind must not be
  applied to another kind, so each `description` must say precisely which kind of task it is for.
- Keep what already works; check the traces to see which instructions the agent skipped and make them harder to miss.
- Skills must be general: never name a task id, never name a data file, function or column specific to one task,
  never state an answer or a number computed for a task. File names, JSON keys or headings REQUIRED by a convention
  are allowed, because they are the convention itself.
- Each skill: YAML frontmatter with `name` (lower-case, hyphens) and `description` (one sentence starting with
  "Use when ..."), then at most 40 lines of imperative, numbered instructions ending with a short self-check list.
  No HTML or XML tags.
- Output format, exactly:
=== SKILL: <name> ===
---
name: <name>
description: <when to use>
---
1. <first instruction>
...
=== END ===

# Current skills
{skills}

# New runs (with the current skills)
{runs}
"""


def curate(source=ROOT / "results" / "skills-auto", max_skills=3, model=None):
    skills = "\n\n".join(f"## {p.parent.name}\n{p.read_text(encoding='utf-8')}" for p in sorted(V1_DIR.glob("*/SKILL.md")))
    sections = []
    for run_file in sorted(Path(source).glob("*/run.json")):
        r = json.loads(run_file.read_text(encoding="utf-8"))
        if r.get("role") != "learn":          # chỉ tác vụ học, như curator vòng 1
            continue
        trace_file = run_file.parent / "trace.md"
        trace = trace_file.read_text(encoding="utf-8")[-TRACE_TAIL:] if trace_file.exists() else ""
        failed = "\n".join(f"- {c['name']}: {c['detail']}" for c in r["checks"] if not c["passed"]) or "- (all checks passed)"
        sections.append(f"## Run of learning task {r['task']} (skills read: {r['skills_read']})\n"
                        f"### Failed checks\n{failed}\n### End of the trace\n{trace}")
    reply = (model or make_model()).invoke(PROMPT.format(max_skills=max_skills, skills=skills,
                                                         runs="\n\n".join(sections))).text
    blocks = parse_skill_blocks(reply)
    if not blocks:
        print("WARNING: no '=== SKILL: <name> ===' block in the reply")
        return []
    if V2_DIR.exists():
        shutil.rmtree(V2_DIR)
    written = []
    for name, text in blocks:
        if len(written) >= max_skills:
            break
        problems = validate_skill(text, expected_name=name)
        if problems:
            print(f"skip skill {name!r}: {', '.join(problems)}")
            continue
        path = V2_DIR / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
        written.append(path)
    return written


def run(task_args, recursion_limit=60):
    runner.CONDITIONS[CONDITION] = {"mode": "single", "skills_dir": str(V2_DIR.relative_to(ROOT))}
    if task_args == ["all"]:
        ids = [t.id for t in list_tasks()]
    elif task_args in (["learn"], ["eval"]):
        ids = [t.id for t in list_tasks(task_args[0])]
    else:
        ids = task_args
    for tid in ids:
        r = runner.run_task(tid, CONDITION, RESULTS, recursion_limit=recursion_limit)
        print(f"{CONDITION:13s} {tid:11s} score={r['passed']}/{r['total']} tokens={r['tokens']['total']} "
              f"calls={r['tool_calls']} skills_read={r['skills_read']} {r['seconds']}s"
              + (f" ERROR={r['error']}" if r["error"] else ""), flush=True)


def table():
    def load(d):
        return {p.parent.name: json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(d).glob("*/run.json"))}
    v1, v2 = load(ROOT / "results" / "skills-auto"), load(RESULTS / CONDITION)
    tasks = sorted(set(v1) | set(v2), key=lambda t: (t.split("-")[1] != "learn", t))
    lines = ["| Task | skills-auto (v1) | skills-v2 | tokens v1 | tokens v2 | skills_read v1 | skills_read v2 |",
             "|---|---|---|---|---|---|---|"]
    def score(r):
        return "-" if r is None else "{}/{}".format(r["passed"], r["total"])

    def tokens(r):
        return "-" if r is None else "{:,}".format(r["tokens"]["total"])

    def read(r):
        return "-" if r is None else str(r["skills_read"])

    def mean(runs, role):
        rs = [r["score"] for r in runs.values() if r["role"] == role]
        return sum(rs) / len(rs) if rs else 0.0

    for t in tasks:
        a, b = v1.get(t), v2.get(t)
        lines.append(f"| {t} | {score(a)} | {score(b)} | {tokens(a)} | {tokens(b)} | {read(a)} | {read(b)} |")
    for role in ("learn", "eval"):
        lines.append(f"| **Mean score - {role}** | {mean(v1, role):.2f} | {mean(v2, role):.2f} | | | | |")
    print("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["curate", "run", "table"])
    ap.add_argument("--tasks", nargs="+", default=["all"])
    ap.add_argument("--recursion-limit", type=int, default=60)
    args = ap.parse_args()
    if args.cmd == "curate":
        for p in curate():
            print("wrote", p)
    elif args.cmd == "run":
        run(args.tasks, args.recursion_limit)
    else:
        table()
