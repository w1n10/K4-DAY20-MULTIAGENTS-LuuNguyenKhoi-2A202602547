# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Lưu Nguyễn Khôi | 2A202602547 | Toàn bộ (làm cá nhân) |

- Mô hình: `LAB_MODEL=google_genai:gemini-3.1-flash-lite` (Google Gemini API, qua `langchain-google-genai`), `LAB_TEMPERATURE=0`, `recursion_limit=60` (mặc định).
  Ghi chú: ban đầu dùng cổng tương thích OpenAI của Gemini (cách 1 trong `.env`), nhưng mọi lần chạy lỗi 400 ngay lần gọi công cụ đầu tiên (`Function call is missing a thought_signature`): `ChatOpenAI` làm rơi `thought_signature` mà Gemini 3 bắt buộc. Các model Gemini 2.5 đã ngừng cấp cho tài khoản mới (404), nên chuyển sang thư viện chính chủ `langchain-google-genai` (thêm vào `pyproject.toml`); `model.py` không sửa.
- Deep Agents 0.7.21, Python 3.12 trong Docker (`python:3.12-slim`, image build từ `Dockerfile` của lab) trên Windows 11; shell của tác tử chạy trong container Linux.
- Số lần chạy tác vụ đã dùng / ngân sách: khoảng 35 lần chạy tác vụ (16 lần trong bảng mục 7; 3 lần `skills-auto` ở Phần 3.4; còn lại là các lần lỗi hạ tầng hoặc bị CRLF ảnh hưởng, đã lưu trong `results/archive-*`). Không có ngân sách do giảng viên cấp; dùng key Gemini miễn phí (giới hạn 500 request/ngày/model), hạn mức này đã hết một lần giữa Phần 4.2.
- Commit của tag `freeze`: `08ca080` ("freeze skills"), commit giả thuyết `0c067a3` ("hypotheses").

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

Viết sau Phần 3 (chỉ dựa trên tác vụ học), trước khi chạy bất kỳ tác vụ đánh giá nào. Dự đoán chung: `skills-auto` đạt điểm trung bình cao nhất trên tác vụ đánh giá, `subagents` tốn token nhiều nhất.

- H1 (subagents so với baseline): `subagents` KHÔNG cải thiện đáng kể điểm tác vụ đánh giá (chênh lệch tổng không quá 2 check trên 3 tác vụ) nhưng tốn token gấp khoảng 2 lần trở lên. Căn cứ: trên tác vụ học, phần lớn check trượt là quy ước `rule_` (nhóm E) không có trong đề, nên giao việc cho explorer/implementer/reviewer không thể phát hiện chúng; subagents chỉ giúp được check kỹ thuật (ví dụ `north_q1_revenue` ở data-learn) trong khi `tokens.total` ở data-learn tăng khoảng 3 lần (145k lên 422k). Bài viết về hệ thống nghiên cứu đa tác tử của Anthropic cũng ghi nhận chi phí token khoảng 15 lần so với hội thoại thường.
- H2 (skills-auto so với baseline): `skills-auto` đạt điểm cao nhất trên tác vụ đánh giá, nhờ các check quy ước đã gặp ở tác vụ học: họ `logs` (skill `log-parsing-compliance` nêu cụ thể tên service, thứ tự sắp xếp, `schema_version`/`generated_by`) và họ `code` (type hints, `tests/test_regressions.py`, `CHANGELOG.md`). Lợi ích ở họ `data` nhỏ vì skill dữ liệu bị `validate_skill` loại và skill còn lại chỉ nhắc `meta`/integer cents mà không nêu đủ nội dung. Dự đoán mức tăng khiêm tốn (khoảng +2 đến +5 check trên tổng số check của 3 tác vụ đánh giá) và không chắc chắn: SkillsBench ghi nhận skill do mô hình tự sinh trung bình không có lợi, và tác tử có thể không đọc skill (`skills_read = 0`).
- H3 (tác vụ học so với tác vụ đánh giá): mức tăng của `skills-auto` so với `baseline` trên tác vụ học lớn hơn trên tác vụ đánh giá. Căn cứ: skill được rút ra từ phản hồi của chính tác vụ học (nguy cơ quá khớp, như SkillEvolBench ghi nhận), còn mỗi tác vụ đánh giá thêm một quy ước MỚI mà skill không thể biết, nên check quy ước mới đó sẽ trượt ở cả ba điều kiện.

## 3. Làm quen Deep Agents (Phần 0.3)

1. `scripts/tour.py` liệt kê 9 công cụ: công cụ tệp `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`; shell `execute`; giao việc `task`. Chỉ `execute` cho phép chạy lệnh (shell thật trên backend `LocalShellBackend`, thư mục làm việc là gốc sandbox).
2. Mô tả `task` nói `general-purpose` là tác tử đa dụng để nghiên cứu câu hỏi phức tạp, tìm tệp và nội dung, chạy tác vụ nhiều bước, và "has access to all tools as the main agent". Về ngữ cảnh: "Each invocation is stateless by default: the agent sees only the prompt you give it and returns a single final report" - subagent KHÔNG thấy lịch sử hội thoại hay system prompt của tác tử chính, chỉ thấy lời giao việc; báo cáo của nó cũng không hiện cho người dùng ("relay a summary yourself").
3. System prompt mặc định rỗng (`''`), hành vi được định hướng qua mô tả công cụ:
   - Từ `task`: "Launch multiple agents concurrently when their tasks are independent, using a single message with multiple tool calls."
   - Từ `execute`: "You MUST avoid using search commands like find and grep. Instead use the grep, glob tools to search. Use read_file rather than cat/head/tail."
   - Quan sát thêm: mô tả `execute` khuyên "Use absolute paths and avoid `cd`", mâu thuẫn với `PATHS_NOTE` của lab ("every path is relative ... never starts with '/'"). Đây là lý do lab phải đưa quy ước đường dẫn tương đối vào `BASE_PROMPT` và vào system prompt của từng subagent.

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| code-learn | `rule_type_hints` | E | `RULE: every public function ... has type annotations on all parameters and on the return value.` Đề không nhắc type hints; vết không có lần sửa chữ ký hàm nào ngoài phần sửa lỗi. |
| code-learn | `rule_regression_tests` | E | `RULE: add tests/test_regressions.py with one test function per bug you fixed (at least 3)`. Tác tử tự viết test nhưng đặt tên `tests/test_extra.py` (vết: 5 lần `write_file`/`edit_file` vào tệp này). |
| code-learn | `rule_changelog` | E | `RULE: record each fix in CHANGELOG.md under the heading '## Unreleased' ...`. Vết không có lần ghi nào vào `CHANGELOG.md` dù tệp có sẵn trong workspace. |
| data-learn | `north_q1_revenue` | D | `wrong value (got 3189.59)`. Vết: hàm `parse_date` cắt chuỗi ISO-8601 bằng `date_str.split('T')[0]`, bỏ mất phần lệch múi giờ (`-05:00`), nên đơn hàng sát ranh giới quý bị tính sai quý. |
| data-learn | `rule_money_in_cents` | E | `RULE: money values in answer.json are integer cents (1606.67 USD is written 160667).` Đề ghi kiểu `number`, tác tử ghi số thực USD. |
| data-learn | `rule_meta_block` | E | `RULE: answer.json has an object meta = {"source", "rows_in", "rows_used"}`. Đề chỉ ghi "plus whatever the Acme reporting conventions require". |
| data-learn | `rule_clean_csv` | E | `RULE: write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents ...`. Không tạo `clean.csv`. |
| logs-learn | `rule_service_names` | E | `RULE: service names in the output are lower-case with '-' replaced by '_'`. |
| logs-learn | `rule_sorted_errors` | E | `RULE: errors is sorted by service, then by timestamp_utc, ascending.` |
| logs-learn | `rule_schema_header` | E | `RULE: the top-level object has "schema_version": 2 and "generated_by": "log-triage".` |
| code-learn (lần chạy đầu, lưu ở `results/archive-crlf/baseline-run1`) | `low_stock_follows_docstring`, `csv_quoting_follows_docstring` | A | `low_stock returned ['b', 'A', 'c']`, `to_csv_row returned 'Desk, large "oak",10.00,2'`: chỉ sửa đến khi test hiển thị đạt, không đối chiếu docstring. Lần chạy này chạm `recursion_limit` 60 (G, xem dưới). |
| code-learn (lần chạy đầu) | (cả lần chạy) | G | `GraphRecursionError: Recursion limit of 60 reached`, 239k token. Ở `subagents` cùng hiện tượng: tác tử chạy test kiểu pytest bằng `unittest` rồi viết đi viết lại `tests/test_runner.py` (16 lệnh `execute`) thay vì gọi `pytest`. |

Thống kê (`python scripts/check_breakdown.py`, tác vụ học, `baseline`): check kỹ thuật đạt **17/18**, check quy ước `rule_` đạt **0/9**.

Nhận xét:

- Nhóm E chiếm đa số tuyệt đối: 9/10 check trượt ở lần chạy `baseline` chính thức là quy ước `rule_` không có trong đề. Bằng chứng phủ định cho A-D: 17/18 check kỹ thuật đạt; check kỹ thuật duy nhất trượt là `north_q1_revenue` (D, múi giờ). Không thấy nhóm B (tác tử chạy lại test/script sau khi sửa ở cả 3 vết), C hay F (báo cáo cuối chỉ nêu tệp thật sự sửa).
- Nhóm A và G chỉ xuất hiện ở lần chạy đầu của code-learn (trước khi sửa lỗi môi trường CRLF, xem mục 9); hai lần chạy cùng cấu hình cho 3/10 và 7/10, cho thấy nhiễu lớn ở tác vụ code.
- Skill phòng ngừa được nhóm E nếu nó **phát biểu lại quy ước cụ thể** (tên tệp, khóa, định dạng), vì quy ước này ổn định giữa các tác vụ cùng họ và tác tử không thể tự suy ra từ đề. Nhóm D (múi giờ) cũng có thể phòng ngừa bằng một checklist "parse offset trước khi so ngày", nhưng curator không sinh skill này.
- Lỗi hạ tầng: các lần chạy ban đầu lỗi 400 `thought_signature` (mục 1) và lỗi CRLF không được tính là lỗi của tác tử và không dùng làm bằng chứng ở trên (trừ hai dòng ghi rõ "lần chạy đầu").

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa (`src/lab/subagents.py`), theo mô hình đọc, làm, kiểm tra:
  - `explorer`: CHỈ ĐỌC; dùng đầu tiên để đọc README, CHANGELOG, docstring, test, mẫu dữ liệu và báo cáo mọi quy tắc, định dạng đầu ra, điểm bẩn của dữ liệu kèm trích dẫn. Lý do: nhắm vào nhóm A/D (bỏ qua đặc tả, dữ liệu bẩn).
  - `implementer`: thực hiện thay đổi theo đặc tả được giao, sửa nguyên nhân gốc, chạy test/script và báo cáo tệp đã sửa. Lý do: nhắm vào C và F.
  - `reviewer`: CHỈ ĐỌC; dùng cuối cùng để kiểm tra độc lập đầu ra, tính lại số liệu, báo PASS hoặc danh sách vấn đề. Lý do: nhắm vào B.
- `subagent_calls` (tác vụ học): code-learn **0**, data-learn **2** (`implementer` rồi `reviewer`), logs-learn **0**. Ở code-learn và logs-learn tác tử chính tự làm hết dù `SUBAGENTS_NOTE` khuyến khích giao việc: với mô hình nhỏ (flash-lite), sửa vài hàm hoặc viết một script parse được coi là "trivial step". `explorer` không bao giờ được gọi, vì tác tử chính tự đọc README trước.
- Thông tin khi giao việc (data-learn): lời giao cho `implementer` chép đầy đủ quy tắc của đề và README (trùng lặp, `-999`, ba định dạng ngày, chuẩn hóa vùng, năm khóa đầu ra). Thiếu hoàn toàn các quy ước Acme (`meta`, cents, `clean.csv`) vì chính tác tử chính không biết chúng (`grep` "meta|cents|clean.csv" trong vết: 0 kết quả). `reviewer` xác nhận "The calculations ... are correct" nhưng lại diễn giải `top_region` là vùng "with the most unique orders" thay vì tổng `amount`: tác tử chính không kiểm tra lại báo cáo này. Dù vậy, `implementer` parse múi giờ đúng nên `north_q1_revenue` đạt (3130.24), check kỹ thuật duy nhất mà `subagents` hơn `baseline`.
- Token và thời gian (tác vụ học): data-learn 422k token, 218 giây so với `baseline` 145k token, 84 giây (khoảng 2,9 lần, +1 check). Khi không giao việc, chi phí gần như bằng nhau (code-learn 149k so với 180k; logs-learn 77k so với 56k, chênh lệch do prompt dài hơn và nhiễu). Trung bình tác vụ học: `subagents` 216k so với `baseline` 127k token.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator: 3 (đúng giới hạn "chạy lại tối đa 2 lần"), không sửa tay skill nào.
  1. Lần 1: mô hình trả lời nhưng không ghi được skill nào: `curate_skills` đọc `.content`, mà Gemini 3 trả `content` dạng danh sách khối, nên `parse_skill_blocks` không tìm thấy dòng `=== SKILL:`. Đã sửa bằng `.text` và thêm cảnh báo khi không có khối nào.
  2. Lần 2: sinh 3 skill hợp lệ về định dạng (lưu ở `results/curator-attempts/run2/`). Nhóm XÓA cả 3 vì: `strict-rule-compliance` sai/vô dụng (bảo tác tử "extract all lines starting with RULE:", nhưng đề của tác vụ mới không có dòng `RULE:`, đó là phản hồi của bot chấm); `data-integrity-verification` quá mơ hồ ("as specified by the rules", không nêu các trường của `meta` hay header `clean.csv`); cả 3 bọc thân skill trong thẻ `<body>` do prompt dùng chỗ trống `<body>`. Prompt curator được bổ sung: tác tử dùng skill KHÔNG thấy phản hồi, nên skill phải phát biểu lại quy ước cụ thể và đầy đủ; bỏ chỗ trống `<body>`.
  3. Lần 3 (lần gọi trước đó bị `RemoteProtocolError`, mạng ngắt, không có phản hồi, không tính): sinh 3 skill; `validate_skill` LOẠI `data-processing-standards` vì "mentions evaluation material: orders" (`orders` là tên tệp `orders.json` của data-eval; ở đây đây là từ thông dụng "orders", tức bộ lọc báo nhầm nhưng an toàn). Giữ 2 skill dưới đây và đóng băng.
- Skill được sinh từ các lần chạy `baseline` trước khi sửa CRLF (mục 9); phản hồi `RULE:` của các tác vụ học giống hệt sau khi sửa, nên nội dung skill không bị ảnh hưởng.

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `enforce-project-conventions` | Tổng quát về hình thức (không nêu id tác vụ, tệp dữ liệu, hàm hay con số đáp án); nội dung là các quy ước Acme của họ code (type hints, `tests/test_regressions.py` có ít nhất 3 test, `CHANGELOG.md` mục `## Unreleased` dạng `- fix(<function_name>): ...`, không sửa `tests/`) cộng một phần quy ước data/log. | Đúng với `detail` cho phần code. Thiếu/sai ở phần data: chỉ ghi `"meta": {...}` và "integer cents", không nêu ba trường `source`, `rows_in`, `rows_used` và không nhắc `clean.csv`. Gộp quy ước của 3 họ vào một skill: có hại ở data-learn, tác tử áp quy ước code vào tác vụ dữ liệu (tạo `workspace/CHANGELOG.md`, `workspace/test_regressions.py`). | 7 dòng thân, 11 dòng tệp. `description` rộng ("Use when creating or updating project files ..."), nên được đọc ở cả code-learn và data-learn (`skills_read` = 1 mỗi tác vụ). |
| `log-parsing-compliance` | Tổng quát cho họ logs: nêu quy ước chứ không nêu tên tệp log, service hay số liệu. | Đúng, khớp đủ 3 `detail`: tên service chữ thường và `-` thành `_`, sắp xếp theo service rồi `timestamp_utc`, `schema_version: 2` và `generated_by: "log-triage"`. Bước 4-5 lặp lại yêu cầu đã có trong đề (thừa nhưng vô hại). | 6 dòng thân, 10 dòng tệp. `description` "Use when parsing log files ..." đúng tình huống kích hoạt; `skills_read` = 1 ở logs-learn, và logs-learn đạt 9/9 (`baseline` 6/9). |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

`python -m lab.compare > report/table.md`:

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 7/10 | 7/10 | 8/10 |
| data-learn | 4/8 | 5/8 | 5/8 |
| logs-learn | 6/9 | 6/9 | 9/9 |
| code-eval | 6/11 | 7/11 | 9/11 |
| data-eval | 5/9 | 5/9 | - |
| logs-eval | 6/10 | 6/10 | - |
| **Mean score - learning tasks** | 0.62 | 0.66 | 0.81 |
| **Mean score - evaluation tasks** | 0.57 | 0.60 | 0.82 |
| **Mean tokens per run** | 116,232 | 203,545 | 129,933 |
| **Runs that read a skill** | 0/6 | 0/6 | 4/4 |

`python scripts/check_breakdown.py`:

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval     17/18         0/12         105,368      0/3
baseline      learn    17/18         0/9          127,096      0/3
subagents     eval     18/18         0/12         190,871      0/3
subagents     learn    18/18         0/9          216,219      0/3
skills-auto   eval      7/7          2/4          175,739      1/1
skills-auto   learn    17/18         5/9          114,665      3/3
```

Lưu ý quan trọng khi đọc bảng:

- **`skills-auto` THIẾU `data-eval` và `logs-eval`.** Lần chạy `skills-auto --tasks all` đầu tiên bị lỗi 429 (hết hạn mức 500 request/ngày của Gemini, bản lỗi ở `results/archive-429/`); sau khi hạn mức reset chỉ kịp chạy 4/6 tác vụ trước hạn nộp. Vì vậy "Mean score - evaluation tasks" của `skills-auto` (0.82) chỉ tính trên MỘT tác vụ (code-eval) và KHÔNG so sánh được trực tiếp với 0.57/0.60 của hai điều kiện kia (tính trên 3 tác vụ). So sánh công bằng là theo từng hàng: code-eval 9/11 so với 6/11 (`baseline`) và 7/11 (`subagents`).
- Lần chạy có `error`: `baseline/data-eval` chạm `recursion_limit` 60 (`GraphRecursionError`), được chấm trên workspace hiện có như quy định; đây là hành vi của tác tử (lặp), không chạy lại. `subagents/logs-eval` lỗi 429 (hạ tầng) đã được chạy lại; bản trong bảng không có lỗi.
- Không lần chạy nào có `skills_modified = true`. `scripts/verify_freeze.py`: chạy trên Windows báo "skills differ from the frozen skills" vì `hash_skills` băm đường dẫn tương đối, mà Windows dùng `\` còn container Linux (nơi tác tử chạy) dùng `/`. Tính lại trong container Linux: `hash_skills(skills/auto)` = `0b495104a63a...` trùng `skills_sha256` của cả 4 lần chạy `skills-auto`; `git diff freeze -- skills/` rỗng; mọi lần chạy `skills-auto` bắt đầu sau tag (07:27-07:31 UTC so với tag 05:39 UTC); commit `hypotheses` có H1-H3 nằm trước tag. Trên Linux (môi trường chấm) kết quả mong đợi là OK.

## 8. Phân tích

1. **Học và đánh giá.** Trên tác vụ học, `skills-auto` cải thiện rõ nhất: 0.81 so với 0.62 (`baseline`), tức +5 check trên 27 (code-learn +1, data-learn +1, logs-learn +3); `subagents` chỉ +1 check (data-learn). Trên tác vụ đánh giá, xét cùng tác vụ đo được: code-eval `skills-auto` 9/11 so với 6/11 (+3) và `subagents` 7/11 (+1). `subagents` gần như không đổi trên cả hai vai trò (0.60 so với 0.57 trên tác vụ đánh giá). Không thấy điều kiện nào cải thiện tác vụ học mà mất hẳn ở tác vụ đánh giá trên code-eval; tuy nhiên ở họ logs (lợi ích lớn nhất trên tác vụ học, 6/9 lên 9/9) và data, `skills-auto` chưa có kết quả đánh giá, nên KHÔNG kiểm chứng được H3 (quá khớp) một cách đầy đủ.
2. **Kỹ thuật và quy ước.** Check kỹ thuật gần như bão hòa ở mọi điều kiện (17-18/18 cho `baseline` và `subagents`), nên mọi khác biệt nằm ở check quy ước `rule_`: `baseline` và `subagents` đạt 0/9 (học) và 0/12 (đánh giá), `skills-auto` đạt 5/9 (học) và 2/4 (code-eval). Skill giúp đúng những quy ước nó phát biểu cụ thể: `rule_regression_tests`, `rule_changelog` (họ code) và cả 3 quy ước của họ logs. Check quy ước MỚI của mỗi tác vụ đánh giá (`rule_version_bump` ở code-eval, `rule_sorted_keys_format` ở data-eval, `rule_source_line` ở logs-eval) trượt ở MỌI lần chạy đo được, kể cả `skills-auto/code-eval`: skill được rút ra từ phản hồi của tác vụ học nên không thể chứa quy ước chưa từng xuất hiện. Đây là giới hạn cơ bản của tiến hóa ở tầng ngữ cảnh từ phản hồi quá khứ.
3. **Một check skill giúp, một check không giúp (vết và `skills_read`).**
   - Giúp: `rule_changelog` và `rule_regression_tests` ở code-eval. `skills_read = 1`; vết cho thấy tác tử đọc `skills/enforce-project-conventions/SKILL.md` rồi ghi `workspace/CHANGELOG.md` và `workspace/tests/test_regressions.py`, đúng tên tệp và định dạng skill nêu (bước 4-5); `baseline` và `subagents` không tạo hai tệp này. Tương tự logs-learn 9/9 sau khi đọc `log-parsing-compliance`.
   - Không giúp, do đọc nhưng làm theo một phần: `rule_type_hints` trượt ở cả code-learn và code-eval dù skill có bước 3 "every public function ... has type annotations". Ở code-learn, báo cáo cuối ghi "Added type annotations to public functions" cho `pricing.py` và `report.py` nhưng không cho `export.py`; tác tử chỉ áp quy tắc cho tệp nó đang sửa, khớp với nhận xét ở `05_skill_quality.md` ("đọc nhưng chỉ làm một phần").
   - Không giúp, do skill thiếu hoặc sai: `rule_meta_block` và `rule_money_in_cents` ở data-learn. Skill chỉ ghi `"meta": {...}` và "integer cents" nhưng không nêu ba trường của `meta`; ở lần chạy Phần 3.4 tác tử còn áp nhầm quy ước của họ code vào tác vụ dữ liệu (tạo `workspace/CHANGELOG.md`, `workspace/test_regressions.py`), do skill gộp quy ước của 3 họ và `description` quá rộng.
4. **Chi phí.** Token trung bình mỗi lần chạy: `baseline` 116k, `skills-auto` 130k, `subagents` 204k. Tính điểm trung bình trên mỗi 100k token: `baseline` 0.60/1.16 khoảng 0.51; `subagents` 0.63/2.04 khoảng 0.31; `skills-auto` (4 tác vụ đo được) 0.81/1.30 khoảng 0.62. `skills-auto` hiệu quả nhất: skill làm tác tử đi thẳng đến đầu ra đúng (code-learn 107k so với 180k token của `baseline`), chỉ tốn thêm ở code-eval (176k, do viết thêm test và CHANGELOG). Đa tác tử KHÔNG đáng chi phí ở thí nghiệm này: chỉ giao việc ở data-learn và data-eval (khoảng 422-431k token, gấp khoảng 2,3-2,9 lần `baseline`) để đổi lấy +1 check kỹ thuật ở data-learn và 0 check ở data-eval; ở 4 tác vụ còn lại `subagent_calls = 0` nên chi phí và điểm tương đương `baseline`. H1 được ủng hộ.
5. **Rò rỉ và quá khớp.** Không thấy rò rỉ: curator chỉ đọc lần chạy có `role == "learn"` (có test `test_04` kiểm tra), `validate_skill` loại mọi skill chứa định danh của tác vụ đánh giá (đã loại `data-processing-standards` vì chứa "orders"), và không ai mở `check.py`/`run.json` của tác vụ đánh giá trước tag `freeze` (lịch sử git: commit `hypotheses` rồi `freeze` trước mọi lần chạy đánh giá). Dấu hiệu "quá khớp" theo nghĩa nội dung: skill chỉ chứa quy ước đã thấy ở tác vụ học, nên không giúp quy ước mới ở tác vụ đánh giá (câu 2); nhưng trên code-eval lợi ích vẫn chuyển giao (+3 check) vì hai tác vụ code dùng chung quy ước Acme. Skill không chứa tên tệp dữ liệu, hàm hay con số của tác vụ học.
6. **Nhiễu.** Cùng bộ skill, Phần 3.4 so với sau đóng băng: code-learn 8/10 và 8/10 (106.716 và 106.909 token), logs-learn 9/9 và 9/9 (67.365 và 67.362 token), data-learn 4/8 và 5/8 (98k và 170k token; chỉ check kỹ thuật `north_q1_revenue` đổi từ trượt sang đạt). Tổng chênh lệch 1 check trên 27 (0.04 điểm trung bình). Với `baseline`, code-learn dao động 3/10 đến 7/10 giữa hai lần chạy (một lần chạm giới hạn đệ quy, dù khác môi trường CRLF). Kết luận: chênh lệch 1 check trên một tác vụ nằm trong vùng nhiễu, nhất là ở data và code; còn chênh lệch có hệ thống ở các check `rule_` (0/9 lên 5/9 trên tác vụ học, lặp lại y hệt giữa hai lần chạy `skills-auto`) lớn hơn nhiễu nhiều và được vết giải thích, nên đáng tin hơn.

## 9. Hạn chế và tính hợp lệ

1. **Mẫu rất nhỏ: 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần.** Một tác vụ có 8-11 check, nên một check bằng 9-12 điểm phần trăm điểm tác vụ. Chênh lệch 1-2 check giữa hai điều kiện trên một tác vụ không phân biệt được với nhiễu. Kết luận chỉ đáng tin khi chênh lệch lặp lại có hệ thống (ví dụ cả 3 check `rule_` của một họ cùng đổi trạng thái) và được giải thích bằng vết.
2. **Nhiễu của mô hình và giới hạn đệ quy.** Dù `LAB_TEMPERATURE=0`, cùng cấu hình `baseline` trên code-learn cho 3/10 (chạm `recursion_limit` 60, 239k token) rồi 7/10 (180k token); data-learn chạy hai lần cùng 4/8 nhưng token 57k so với 145k. Ngược lại logs-learn lặp lại y hệt (6/9, 56.026 token cả hai lần). Nhiễu tập trung ở tác vụ nhiều bước (code, data), nơi một lần lặp vô ích có thể đẩy lần chạy chạm giới hạn. Google khuyến nghị giữ temperature 1.0 cho dòng Gemini 3 (thấp hơn có thể gây lặp); thí nghiệm giữ 0 theo mặc định của lab để các điều kiện so sánh được, đổi lại có thể làm tăng số lần lặp.
3. **Chỉ một mô hình, và là mô hình nhỏ** (`gemini-3.1-flash-lite`). Hành vi giao việc (subagent gần như không được dùng) và việc làm theo skill (bỏ sót một phần) có thể khác nhiều ở mô hình mạnh hơn; không thể tổng quát hóa kết luận về đa tác tử hay skill tự sinh sang mô hình khác.
4. **Tác vụ do giảng viên thiết kế sẵn quy ước ẩn.** Phần lớn điểm phân biệt giữa các điều kiện đến từ check `rule_` (quy ước không có trong đề). Thiết kế này ưu ái cơ chế "ghi nhớ quy ước" (skill) hơn là năng lực kỹ thuật; trong thực tế, quy ước thường được ghi trong tài liệu và baseline sẽ không thua xa như vậy.
5. **Sự cố hạ tầng làm thay đổi quy trình.** (a) Lỗi 400 `thought_signature` buộc đổi tầng tích hợp mô hình (`langchain-google-genai`) trước khi có kết quả hợp lệ. (b) `core.autocrlf=true` của Git trên Windows đổi `tasks/` sang CRLF, khiến `tests_not_modified` luôn trượt và tệp log có `\r`; phát hiện sau các lần chạy học đầu tiên, các lần chạy code-learn/logs-learn bị ảnh hưởng được lưu ở `results/archive-crlf/` và chạy lại. Curator vòng 1 đã dùng các lần chạy trước khi sửa; phản hồi `RULE:` giống hệt nên skill không bị ảnh hưởng, nhưng vết đưa vào curator có khác. (c) Hạn mức miễn phí 500 request/ngày của Gemini hết giữa Phần 4.2: lần chạy `subagents/logs-eval` bị lỗi 429 được chạy lại sau khi hạn mức reset (bản lỗi lưu ở `results/archive-429/`), nên các lần chạy chính thức không cùng một phiên.
6. **Bộ lọc rò rỉ thô.** `validate_skill` loại skill dữ liệu vì chứa từ thông dụng "orders" (trùng tên tệp `orders.json` của data-eval). Điều này an toàn (không rò rỉ) nhưng làm họ `data` mất skill của mình, nên kết quả `skills-auto` ở họ data không đo được lợi ích của một skill dữ liệu tốt.

7. **Thiếu 2/6 lần chạy `skills-auto`** (data-eval, logs-eval) do hết hạn mức API. Kết luận về `skills-auto` trên tác vụ đánh giá chỉ dựa trên code-eval; H2 và H3 chỉ được kiểm chứng một phần.

## 10. Kết luận

Trên các tác vụ đo được, skill do curator tự sinh là điều kiện tốt nhất: tác vụ học 0.81 so với 0.62 (`baseline`), code-eval 9/11 so với 6/11, với chi phí token tương đương `baseline`, và toàn bộ lợi ích đến từ các check quy ước mà skill phát biểu cụ thể. Đa tác tử gần như không cải thiện điểm (+1 check trên mỗi vai trò) trong khi tốn khoảng 1,75 lần token trung bình, vì tác tử chính hiếm khi giao việc và không subagent nào biết được quy ước ẩn. Không điều kiện nào vượt qua được quy ước mới của tác vụ đánh giá, đúng như H3 dự đoán: tiến hóa từ phản hồi quá khứ không tạo ra tri thức chưa từng thấy. Kết quả bị giới hạn bởi một lần chạy, một mô hình nhỏ và việc thiếu 2 lần chạy `skills-auto` trên tác vụ đánh giá. Đề xuất tiếp theo: tách skill theo họ tác vụ với `description` hẹp (tránh áp nhầm quy ước code vào tác vụ dữ liệu), thêm một bước "đối chiếu từng quy tắc với mọi tệp" vào skill, và chạy lặp ít nhất 3 lần mỗi điều kiện để đo nhiễu (hướng 6e).

## Phụ lục

- Lệnh đã chạy (theo thứ tự). Mọi lệnh `python` chạy trong container: `docker run --rm --env-file .env -v "${PWD}:/lab" lab-deepagents <lệnh>`; lệnh `git` và `scripts/verify_freeze.py`, `scripts/check_breakdown.py` chạy trên máy (image không có `git`).
  1. `docker build -t lab-deepagents .`, rồi thêm lớp `pip install "langchain-google-genai>=3.0"` (cùng phụ thuộc đã thêm vào `pyproject.toml`); `pytest` cho kết quả 29 passed.
  2. `python scripts/tour.py`
  3. `python -m lab.runner --condition baseline --tasks learn`; `python -m lab.runner --condition subagents --tasks learn`
  4. Sửa CRLF: `git config core.autocrlf false`, checkout lại `tasks/`; chạy lại `baseline` và `subagents` cho `code-learn logs-learn` (bản cũ ở `results/archive-crlf/`).
  5. `python -m lab.curator` (3 lần, xem mục 6); `python -m lab.runner --condition skills-auto --tasks learn` (Phần 3.4, sao lưu ở `results/skills-auto-dev/`)
  6. `git commit -m "hypotheses"`; `git commit --allow-empty -m "freeze skills"`; `git tag freeze`
  7. `python -m lab.runner --condition baseline --tasks eval`; `... --condition subagents --tasks eval`; `... --condition skills-auto --tasks all` (lần chạy bị 429 được chạy lại khi hạn mức reset)
  8. `python -m lab.compare > report/table.md`; `python scripts/check_breakdown.py`; `python scripts/verify_freeze.py`
- Thử thách mở rộng: không thực hiện. Đã chuẩn bị script cho hướng 6b (vòng tiến hóa thứ hai, `extension/evolve_round2.py`, ghi skill vào `extension/skills-v2/` và kết quả vào `results-6b/` để tách khỏi thí nghiệm chính và không đụng `skills/` đã đóng băng) nhưng chưa chạy do giới hạn hạn mức API.
- Ghi chú khác:
  - Mở rộng `run_task` theo gợi ý ở `03_runner.md` ý 8: dùng `agent.stream(..., stream_mode="values")` thay cho `invoke` để vẫn có vết khi gặp `GraphRecursionError` (lần chạy code-learn đầu tiên không có vết vì dùng `invoke`).
  - `final_message` và đầu ra của curator dùng `AIMessage.text`, vì Gemini 3 trả `content` dạng danh sách khối kèm `signature`.
  - Không lần chạy chính thức nào có `skills_modified = true`.
