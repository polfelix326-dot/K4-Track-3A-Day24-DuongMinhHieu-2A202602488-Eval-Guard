# Nhóm thực hiện K4 Track 3A

Tên nhóm: DuongMinhHieu-2A202602488-Eval-Guard

Repo chung: https://github.com/VinUni-AI20k/K4-Track-3A-Day24-DuongMinhHieu-2A202602488-Eval-Guard

Trưởng nhóm/người nộp: Dương Minh Hiếu - 2A202602488

Ngày lab/deadline áp dụng: 2026-10-12 23:59 — Asia/Ho_Chi_Minh (UTC+07:00)

Commit dùng để chấm: 89a09f4

Mỗi nhóm nộp một repo. Điền đủ thành viên và một mục INDIVIDUAL cho từng người.
Thực hiện độc lập theo nguyện vọng làm cá nhân hoàn chỉnh toàn bộ các phase của đề bài.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Dương Minh Hiếu | 2A202602488 | Thực hiện trọn vẹn toàn bộ pipeline: Tích hợp RAG m1-m5, Phase A RAGAS, Phase B Pairwise Judge và Cohen Kappa, Phase C Guardrails và Latency, báo cáo kỹ thuật | Commit Git, artifacts JSON, failure_clusters.md, bias_report.md, blueprint.md |

Người tích hợp/chạy batch/nộp link: Dương Minh Hiếu, thực hiện toàn bộ quá trình lập trình, kiểm thử unit test, chạy thực nghiệm batch và hoàn thiện toàn bộ báo cáo phân tích.

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler: Windows 11 64-bit, Python 3.12, MSVC Build Tools.
Virtualenv/dependencies/imports: Thiết lập virtualenv độc lập, cài đặt dependencies từ requirements.txt, constraints-core.txt, tích hợp đầy đủ thư viện OpenAI, Presidio, NeMo Guardrails, RAGAS, PyTest.
Models/Qdrant/50 answers đã chuẩn bị: Mô hình embedding BAAI/bge-m3, reranker BAAI/bge-reranker-v2-m3, Qdrant vector database (in-memory và service), pipeline hoàn thành 50 câu hỏi kiểm thử test set với chế độ extractive fallback và LLM provenance đầy đủ.
Toàn bộ 86 unit tests offline đều vượt qua tuyệt đối (100% PASS), đảm bảo tính chính xác và tuân thủ hợp đồng kỹ thuật nghiêm ngặt.

## INDIVIDUAL

### DuongMinhHieu-2A202602488

- Phần được giao và phần thực tế đã làm: Toàn quyền phụ trách cá nhân hoàn thành 100% khối lượng công việc của dự án, bao gồm:
  + Tích hợp 5 module RAG từ bài trước (m1_chunking, m2_search, m3_rerank, m4_eval, m5_enrichment) tuân thủ hợp đồng PIPELINE_INTERFACE.md.
  + Hoàn thiện Phase A (Tasks 1-4 trong phase_a_ragas.py): phân nhóm 50 câu hỏi theo phân phối (factual, multi_hop, adversarial), tích hợp đánh giá RAGAS 4 chỉ số, trích xuất bottom 10 câu yếu nhất và phân tích ma trận lỗi failure clusters.
  + Hoàn thiện Phase B (Tasks 5-8 trong phase_b_judge.py): xây dựng LLM-as-a-judge pairwise đánh giá câu trả lời A/B, cơ chế swap-and-average triệt tiêu position bias, tính toán hệ số đồng thuận Cohen Kappa giữa model judge và nhãn chuyên gia con người, báo cáo position bias và verbosity bias.
  + Hoàn thiện Phase C (Tasks 9a-12 trong phase_c_guard.py): thiết lập tầng bảo vệ kép Presidio quét và ẩn danh hóa dữ liệu định danh cá nhân Việt Nam (CCCD, SĐT, Email), tích hợp NeMo Guardrails kiểm soát input rails và output rails, chạy kiểm thử bộ 20 adversarial attacks kết hợp 8 clean controls và 4 output test cases, thực nghiệm đo độ trễ chuẩn P95 tuần tự sau warm-up.
  + Hoàn thành Task 13 và soạn thảo toàn diện 3 báo cáo kỹ thuật failure_clusters.md, bias_report.md, blueprint.md cùng doc/TEAM.md.
- Bằng chứng: Lịch sử commit Git, 4 file artifact JSON (answers_50q.json, ragas_50q.json, judge_results.json, guard_results.json), 3 báo cáo chi tiết trong doc/reports/ và kết quả kiểm tra check_lab.py đạt chuẩn tuyệt đối.
- Cách kiểm tra: Kiểm chứng qua hệ thống 86 unit tests offline với pytest (`python -m pytest tests/ -m "not integration" -q`), chạy script kiểm tra bài lab `python scripts/check_lab.py` đáp ứng toàn bộ các ràng buộc schema Draft 2020-12 và hợp đồng dữ liệu.
- Điều đã học: Nắm vững phương pháp đánh giá định lượng hệ thống RAG đa chiều thông qua 4 thành phần RAGAS (faithfulness, answer_relevancy, context_precision, context_recall); thấu hiểu bản chất thiên lệch vị trí và độ dài của LLM-as-a-judge cùng kỹ thuật đo đạc chuẩn hóa Cohen's Kappa; thành thạo kiến trúc phòng thủ chiều sâu nhiều lớp (defense-in-depth) kết hợp regex rule-based presidio và LLM guardrails cho hệ thống AI an toàn trong môi trường production.
- Giới hạn/cách xử lý: Quản lý chi phí token và giới hạn hạn ngạch API thông qua cơ chế extractive fallback kết hợp lưu vết provenance minh bạch; giải quyết bài toán độ trễ guardrail bằng kiến trúc tuần tự có đo đạc chi tiết P50/P95/P99.
- Nguồn/AI hỗ trợ nếu có: Sử dụng Antigravity IDE làm công cụ hỗ trợ lập trình, mọi thuật toán, logic xử lý, ma trận thống kê và nội dung báo cáo đều được kiểm tra, đối chiếu trực tiếp với mã nguồn và dữ liệu thực tế.

## Cập nhật sau khi nộp

Bản nộp chính thức hoàn thiện đầy đủ toàn bộ yêu cầu, không có cập nhật phát sinh sau hạn nộp.
