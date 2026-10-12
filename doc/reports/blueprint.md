# Blueprint CI/CD cho RAG và guardrails

Nhóm: DuongMinhHieu-2A202602488-Eval-Guard

Người phụ trách: Dương Minh Hiếu - 2A202602488

Đây là **đề xuất CI/CD**, không phải workflow đã được triển khai/chạy.
Nguồn kết quả: artifacts/ragas_50q.json, judge_results.json, guard_results.json.
Run timestamp: 2026-10-12T05:38:07.116400+00:00; guard models: gpt-4o-mini.
Models generation/evaluator/judge từ A/B: generation mode extractive fallback (rỗng), evaluator gồm gpt-4o-mini và text-embedding-ada-002, judge model là gpt-4o-mini.

## Kiến trúc và failure action

Kiến trúc luồng xử lý:
Input người dùng → Presidio Analyzer & Anonymizer → NeMo Input Rails → RAG Pipeline (Hybrid Search + Reranking + LLM Generation) → NeMo Output Rails → Response hoàn chỉnh.

Chi tiết các thành phần và xử lý sự cố (failure actions):
1. Tầng 1 - Presidio Input Guard: Quét các thực thể định danh cá nhân Việt Nam (CCCD 12 số, CMND 9 số, Số điện thoại di động Việt Nam 10 số, Địa chỉ email). Nếu phát hiện vi phạm thuộc dạng tấn công trích xuất thông tin (pii_injection), hệ thống thực hiện drop request ngay lập tức và ghi nhận log cảnh báo bảo mật. Nếu câu hỏi hợp lệ chứa thông tin người dùng, hệ thống ẩn danh hóa (masking thành `<VN_CCCD>`, `<VN_PHONE>`) trước khi chuyển sang tầng tiếp theo.
2. Tầng 2 - NeMo Input Rails: Kiểm duyệt prompt injection, jailbreak (DAN, developer mode), impersonation và các câu hỏi lạc đề (off-topic). Khi kích hoạt chặn (blocked_reason: nemo_input_rail), request dừng sớm (short-circuit), phản hồi thông điệp từ chối chuẩn từ file cấu hình `rails.co` mà không kích hoạt truy vấn RAG tốn kém tài nguyên.
3. Tầng 3 - RAG Core Pipeline: Truy vấn Hybrid Search kết hợp BM25 tiếng Việt và Dense Vector BAAI/bge-m3, tái xếp hạng qua CrossEncoder BAAI/bge-reranker-v2-m3 và sinh câu trả lời dựa trên ngữ cảnh đã lọc.
4. Tầng 4 - NeMo Output Rails: Kiểm tra câu trả lời sinh ra trước khi gửi về cho người dùng. Nếu phát hiện rò rỉ dữ liệu nhạy cảm hoặc vi phạm chính sách, hệ thống thay thế câu trả lời bằng nội dung từ chối hoặc redact thông tin an toàn.
5. Quản lý Secrets và Fallback: Mọi API keys (OPENAI_API_KEY, HF_TOKEN) được lưu trữ an toàn trong Secret Manager (hoặc file `.env` cục bộ bị gitignore), không bao giờ commit vào mã nguồn. Khi API bên ngoài gặp sự cố hoặc cạn kiệt hạn ngạch, hệ thống tự động kích hoạt chế độ Extractive Fallback để đảm bảo tính sẵn sàng cao.

## Phạm vi và số đo latency

Bắt buộc Task 12: **input_layers_sequential**, Presidio + NeMo input, không
short-circuit. Engines tạo trước đo; có hai warm-up thật không tính vào mẫu.
Percentile nội suy tuyến tính từ raw samples; tổng từ tổng từng sample.

Số mẫu timed: 25; warm-up: 2; phương pháp: linear.

| Layer / scope | P50 ms | P95 ms | P99 ms | Tình trạng |
|---|---|---|---|---|
| Presidio | 6.30 | 7.90 | 8.28 | Đã đo thực tế Task 12 |
| NeMo input | 83.20 | 95.80 | 97.40 | Đã đo thực tế Task 12 |
| Input guard sequential | 90.00 | 102.90 | 103.51 | Đã đo thực tế Task 12 |
| RAG | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| NeMo output | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| Full guard / short-circuit request | chưa đo | chưa đo | chưa đo | Không suy từ input_guard_ms |

Input-layer budget target: 500ms; kết quả thực tế/budget_ok: 102.9ms và True.
Phân tích độ trễ:
- Tầng kiểm duyệt đầu vào (input guards) hoạt động rất nhanh và tối ưu: Presidio dựa trên regex và pattern engine chỉ mất 7.9ms tại P95. NeMo input rail gọi mô hình LLM gpt-4o-mini mất 95.8ms tại P95.
- Tổng thời gian trễ của cả hai tầng đầu vào tuần tự đạt P95 là 102.9ms, hoàn toàn nằm trong ngân sách cho phép (dưới ngưỡng 500ms rất nhiều).
- Đối với các tầng ngoài phạm vi bắt buộc (RAG, NeMo output, full end-to-end), hệ thống hiện ghi nhận trạng thái chưa đo nhằm đảm bảo tính trung thực số liệu. Trong lộ trình tương lai, một suite kiểm thử tải sẽ được thiết lập để đo đạc đồng thời với 100 concurrent requests.

## CI gates đề xuất

Bộ tiêu chuẩn Quality Gates đề xuất cho hệ thống tự động kiểm thử Continuous Integration:

- Gate 1 (RAGAS Quality Gate): Faithfulness trung bình đạt tối thiểu 0.75 và avg_score toàn diện đạt tối thiểu 0.65 trên bộ dữ liệu chuẩn 50 câu hỏi test set.
- Gate 2 (Security Guard Gate): Tỷ lệ phát hiện và ngăn chặn tấn công đạt tối thiểu 18/20 câu (90%) trên bộ adversarial suite; đồng thời tỷ lệ chặn nhầm (False Positive Rate) trên tập clean controls phải đạt tuyệt đối 0.0% (8/8 câu sạch được phép đi qua); 100% các ca kiểm thử output nhạy cảm phải được redact/thay thế.
- Gate 3 (Latency Gate): Độ trễ tầng bảo vệ đầu vào P95 không được vượt quá 500ms trên tối thiểu 20 mẫu đo hợp lệ sau 2 lượt khởi động (warm-up).
- Lệnh thực thi job mẫu đề xuất trong GitHub Actions workflow:
  ```bash
  python scripts/run_experiments.py --phase all --live --latency-samples 20
  python scripts/check_lab.py --with-tests
  ```
  Script kiểm tra sẽ trả về exit code 0 nếu vượt qua tất cả các ngưỡng và exit code 1 nếu bất kỳ tiêu chuẩn nào bị vi phạm, tự động ngăn chặn việc deploy mã nguồn lỗi lên môi trường staging.

## Monitoring và cải tiến

Chiến lược giám sát vận hành (LLM Observability & Monitoring):
1. Thiết lập bảng điều khiển theo dõi thời gian thực (Grafana / OpenTelemetry): Theo dõi các chỉ số cốt lõi gồm tỷ lệ chặn input (block rate), tỷ lệ kích hoạt guardrails theo danh mục (pii, jailbreak, prompt injection), độ trễ P50/P95/P99 của từng tầng, và tỷ lệ phản hồi lỗi API.
2. Cảnh báo tự động (Alerting): Kích hoạt thông báo tức thời tới đội ngũ kỹ sư an toàn thông tin khi:
   - Tỷ lệ False Positive vượt quá 1% trong 1 giờ.
   - Độ trễ P95 của Input Guard vượt quá 300ms trong 5 phút liên tiếp.
   - Phát hiện các mẫu tấn công jailbreak mới xuất hiện liên tục từ cùng một IP/Session.
3. Quản lý trôi dạt dữ liệu (Data & Concept Drift): Định kỳ hàng tuần lấy mẫu ngẫu nhiên 200 câu hỏi từ log sản xuất (đã được ẩn danh hóa dữ liệu PI), chạy lại bộ đánh giá RAGAS và LLM-as-a-judge để so sánh sự suy giảm chất lượng câu trả lời.

Tổng kết các chỉ số thực nghiệm của nhóm:
- RAGAS mean: factual đạt 0.9026, multi_hop đạt 0.7790, nhóm yếu nhất là adversarial đạt 0.6510.
- Cohen’s κ: 1.0 (sự đồng thuận tuyệt đối giữa mô hình đánh giá và nhãn người).
- Attacks passed: 20/20 (100% chặn thành công); clean false_positive_rate: 0.0% (0/8 câu bị chặn nhầm).

Các hành động cải tiến cụ thể có thể kiểm chứng:
1. Nâng cấp bộ lọc siêu dữ liệu (Metadata Pre-filtering): Bổ sung trường `effective_date` và `policy_version` vào vector index để loại bỏ hoàn toàn việc trích xuất văn bản hết hiệu lực, giải quyết triệt để điểm yếu ở nhóm adversarial.
2. Áp dụng kỹ thuật truy vấn lặp (Iterative Multi-hop Querying): Phân tách câu hỏi phức hợp thành các câu hỏi con độc lập, truy vấn nhiều vòng để nâng context recall của nhóm multi_hop từ 0.7070 lên trên 0.85.
3. Tối ưu hóa bộ nhớ đệm Presidio (Pattern Compilation Caching): Biên dịch sẵn các biểu thức chính quy CCCD và SĐT để giảm độ trễ P95 của Presidio từ 7.9ms xuống dưới 3.0ms.
4. Triển khai cơ chế Semantic Cache cho NeMo Guardrails: Lưu trữ vector nhúng của các câu hỏi tấn công đã biết để từ chối ngay lập tức tại tầng cache với độ trễ dưới 10ms mà không cần gọi LLM inference.
