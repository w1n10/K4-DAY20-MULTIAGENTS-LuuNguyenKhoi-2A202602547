# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Lưu Nguyễn Khôi | 2A202602547 | Toàn bộ (làm cá nhân) |

- Mô hình: `LAB_MODEL=google_genai:gemini-3.1-flash-lite` (Google Gemini API, qua `langchain-google-genai`), `LAB_TEMPERATURE=0`, `recursion_limit=60` (mặc định).
  Ghi chú: ban đầu dùng cổng tương thích OpenAI của Gemini (cách 1 trong `.env`), nhưng mọi lần chạy lỗi 400 ngay lần gọi công cụ đầu tiên (`Function call is missing a thought_signature`): `ChatOpenAI` làm rơi `thought_signature` mà Gemini 3 bắt buộc. Các model Gemini 2.5 đã ngừng cấp cho tài khoản mới (404), nên chuyển sang thư viện chính chủ `langchain-google-genai` (thêm vào `pyproject.toml`); `model.py` không sửa.
- Deep Agents 0.7.21, Python 3.12 trong Docker (`python:3.12-slim`, image build từ `Dockerfile` của lab) trên Windows 11; shell của tác tử chạy trong container Linux.
- Số lần chạy tác vụ đã dùng / ngân sách: (điền ở cuối)
- Commit của tag `freeze`: (điền sau Phần 4.1)

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

> Chỉ dùng tác vụ học. Mỗi dòng là một check thất bại.

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| | | | |

Nhận xét: nhóm lỗi nào chiếm đa số? Skill có thể phòng ngừa nhóm đó không?

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa (tên, vai trò, lý do thiết kế):
- `subagent_calls` ở từng tác vụ và nhận xét (kể cả trường hợp bằng 0):
- Thông tin thiếu hoặc thừa khi giao việc (nếu có giao việc):
- Ảnh hưởng đến token và thời gian:

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator, số skill bị xóa và lý do:

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| | | | |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

> Dán nội dung `report/table.md` và kết quả `python scripts/check_breakdown.py`. Nêu các lần chạy có `error` hoặc `skills_modified = true` (nếu có) và cách xử lý.

```text
(dán bảng ở đây)
```

## 8. Phân tích

> Trả lời từng câu bằng số liệu từ mục 7 và bằng chứng từ vết. Kết quả âm hoặc không có khác biệt vẫn hợp lệ nếu được phân tích tốt.

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?
2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?
3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai).
4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?
5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Nhóm đã phòng tránh như thế nào?
6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?

## 9. Hạn chế và tính hợp lệ

> Nêu ít nhất 3 hạn chế và ảnh hưởng của từng hạn chế đến kết luận (ví dụ: chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần, nhiễu của mô hình, tác vụ do giảng viên thiết kế sẵn quy ước, chỉ một mô hình).

1.
2.
3.

## 10. Kết luận

> Tối đa 5 câu. Chỉ khẳng định điều số liệu hỗ trợ. Nêu một đề xuất cải tiến tiếp theo.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
- Thử thách mở rộng (nếu có): hướng chọn, kết quả, nhận xét.
- Ghi chú khác:
