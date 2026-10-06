"""GUIDE Phần 3 - Người tuyển chọn skill (skill curator): tự viết skill từ các lần chạy thất bại.   >>> SINH VIÊN CÀI ĐẶT curate_skills <<<

Pseudo-code: guides/pseudocode/04_curator.md
Kiểm tra:    pytest tests/test_04_curator.py
Chạy thật:   python -m lab.curator
"""
import json
import re
from pathlib import Path

from .model import make_model
from .tasks import ROOT, eval_markers   # có sẵn: định danh của tác vụ đánh giá, tính lúc chạy

TRACE_TAIL = 6000   # số ký tự cuối của trace.md đưa vào prompt

CURATOR_PROMPT = """You write SKILLS for a coding and data-analysis agent.
Below are the failed checks (name and the grader's feedback) and the end of the trace of several runs.
Find the general PROCESS mistakes and organisation conventions behind them (not specific answers) and write at most
{max_skills} short skills that prevent those mistakes on NEW tasks of the same kind.

Rules:
- The agent that will use your skills on a new task NEVER sees the grader's feedback: the "RULE:" lines below are
  organisation conventions that are NOT written in the task statement. So each skill must restate every convention
  concretely and completely (exact file names, headers, JSON keys and values, units, sort orders, naming formats),
  so that the agent can apply it without any feedback. "Follow the rules" or "as specified" is useless.
- Skills must be general: never name a task id, never name a data file, function or column specific to one task,
  never state an answer or a number computed for a task. File names, JSON keys or headings REQUIRED by a convention
  stated in the feedback (lines starting with "RULE:") are allowed, because they are the convention itself.
- Each skill has a YAML frontmatter with `name` (lower-case, hyphens) and `description` (one sentence starting with
  "Use when ..." that names the broad kind of task), then at most 40 lines of imperative, numbered instructions
  ending with a short self-check list. No HTML or XML tags.
- Output format, exactly (the instructions go directly after the second '---' line):
=== SKILL: <name> ===
---
name: <name>
description: <when to use>
---
1. <first instruction>
...
=== END ===

{runs}
"""

# ---- CÓ SẴN, KHÔNG SỬA: kiểm tra và tách khối skill (phần dễ sai và liên quan bảo mật) ----------------
SAFE_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate_skill(text: str, expected_name: str | None = None) -> list[str]:
    """Kiểm tra nội dung một SKILL.md. Trả về danh sách vấn đề (rỗng = hợp lệ).

    Quy tắc: có khối YAML frontmatter; `name` chữ thường/số/gạch ngang (tối đa 64 ký tự) và bằng `expected_name`
    nếu được truyền; có `description` (tối đa 1024 ký tự); phần thân tối đa 80 dòng; không chứa chuỗi nào của
    `eval_markers()`. Quy tắc về `name` cũng là biện pháp bảo mật: tên khối do LLM sinh ra được dùng để tạo
    đường dẫn, nên `../evil` không được lọt qua.
    """
    problems = []
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text.strip() + "\n", re.S)
    if not m:
        return ["missing YAML frontmatter"]
    front, body = m.groups()
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    n = name.group(1).strip() if name else ""
    if not SAFE_NAME.fullmatch(n) or len(n) > 64:
        problems.append("invalid name")
    elif expected_name is not None and n != expected_name:
        problems.append("name differs from the block name")
    if not desc or len(desc.group(1).strip()) > 1024:
        problems.append("missing or too long description")
    if len(body.strip().splitlines()) > 80:
        problems.append("body longer than 80 lines")
    low = text.lower()
    for marker in eval_markers():
        if marker in low:
            problems.append(f"mentions evaluation material: {marker}")
    return problems


def parse_skill_blocks(reply: str) -> list[tuple[str, str]]:
    """Tách câu trả lời của LLM thành danh sách (name, nội dung SKILL.md).

    Khuôn dạng: `=== SKILL: <name> ===` ... `=== END ===`. Một khối kết thúc ở điểm nào đến trước trong ba điểm:
    `=== END ===`, tiêu đề `=== SKILL:` kế tiếp, hoặc cuối văn bản (LLM đôi khi quên dòng END).
    """
    pattern = re.compile(r"^=== SKILL: (\S+) ===[ \t]*\n(.*?)(?=^=== END ===|^=== SKILL: |\Z)", re.S | re.M)
    return [(name, text.strip()) for name, text in pattern.findall(str(reply))]
# --------------------------------------------------------------------------------------------------


def curate_skills(results_dir="results", source_condition="baseline", out_dir=None, model=None, max_skills: int = 3) -> list[Path]:
    """Đọc các lần chạy của TÁC VỤ HỌC (role == "learn") trong `source_condition`, nhờ LLM viết skill, ghi file.

    Các bước: nạp run.json + trace.md -> (nếu không có check nào thất bại: in cảnh báo và trả về [] mà KHÔNG gọi LLM)
    -> dựng prompt -> model.invoke(prompt) -> parse_skill_blocks -> validate_skill(text, expected_name=name)
    -> ghi `<out_dir>/<name>/SKILL.md`. Mặc định `out_dir` = <gốc lab>/skills/auto (dùng `ROOT` từ lab.tasks).
    Giữ tối đa `max_skills` skill hợp lệ; skill không hợp lệ bị bỏ qua.
    Prompt chứa, với mỗi check thất bại, TÊN và trường `detail` (lời nhận xét của bot đánh giá: phát biểu quy tắc bị vi phạm)
    cùng phần cuối của vết (trace). Với tác vụ học, `detail` chỉ phát biểu quy tắc, không chứa đáp án.
    Tuyệt đối KHÔNG đưa dữ liệu của tác vụ đánh giá (role == "eval") vào prompt.
    model mặc định: make_model() (lab.model).
    Trả về: danh sách đường dẫn SKILL.md đã ghi.
    """
    out_dir = Path(out_dir) if out_dir is not None else ROOT / "skills" / "auto"
    runs = []
    for run_file in sorted(Path(results_dir, source_condition).glob("*/run.json")):
        r = json.loads(run_file.read_text(encoding="utf-8"))
        if r.get("role") != "learn":          # tuyệt đối không dùng dữ liệu tác vụ đánh giá
            continue
        trace_file = run_file.parent / "trace.md"
        trace = trace_file.read_text(encoding="utf-8")[-TRACE_TAIL:] if trace_file.exists() else ""
        failed = [(c["name"], c.get("detail", "")) for c in r.get("checks", []) if not c.get("passed")]
        runs.append({"task": r["task"], "failed": failed, "trace": trace})

    if not any(run["failed"] for run in runs):
        print("WARNING: không có check thất bại ở tác vụ học - không gọi mô hình.")
        return []

    sections = []
    for run in runs:
        checks = "\n".join(f"- {name}: {detail}" for name, detail in run["failed"]) or "- (all checks passed)"
        sections.append(f"## Run of learning task {run['task']}\n### Failed checks\n{checks}\n"
                        f"### End of the trace\n{run['trace']}")
    prompt = CURATOR_PROMPT.format(max_skills=max_skills, runs="\n\n".join(sections))
    reply = (model or make_model()).invoke(prompt).text     # .text: content có thể là danh sách khối (Gemini 3)

    blocks = parse_skill_blocks(reply)
    if not blocks:
        print("WARNING: câu trả lời của mô hình không có khối '=== SKILL: <name> ==='.")
    written = []
    for name, text in blocks:
        if len(written) >= max_skills:
            break
        problems = validate_skill(text, expected_name=name)
        if problems:
            print(f"skip skill {name!r}: {', '.join(problems)}")
            continue
        path = out_dir / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
        written.append(path)
    return written


if __name__ == "__main__":
    for p in curate_skills():
        print("wrote", p)
