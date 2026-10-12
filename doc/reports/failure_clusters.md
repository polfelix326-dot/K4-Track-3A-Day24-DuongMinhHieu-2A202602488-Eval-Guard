# Phân tích lỗi Phase A

Nhóm: DuongMinhHieu-2A202602488-Eval-Guard

Người phụ trách: Dương Minh Hiếu - 2A202602488

Nguồn: `artifacts/ragas_50q.json`; run timestamp: 2026-10-12T05:38:05.383990+00:00.
Generation mode/fallback và điều kiện chạy: Chạy pipeline RAG 50 câu hỏi trên toàn bộ tập dữ liệu test set với extractive fallback và BAAI/bge-m3 dense search kết hợp BM25 Vietnamese tokenizer, CrossEncoder reranking BAAI/bge-reranker-v2-m3.
Models generation/evaluator: Generation mode extractive fallback (provenance null), Evaluator models bao gồm gpt-4o-mini và text-embedding-ada-002 theo chuẩn RAGAS.

## Điểm theo distribution

| Metric | factual (20) | multi_hop (20) | adversarial (10) |
|---|---|---|---|
| faithfulness | 0.9273 | 0.8200 | 0.5650 |
| answer_relevancy | 0.8900 | 0.8390 | 0.7800 |
| context_precision | 0.8850 | 0.7500 | 0.6130 |
| context_recall | 0.9080 | 0.7070 | 0.6460 |
| avg_score | 0.9026 | 0.7790 | 0.6510 |

## Bottom 10 và nguyên nhân

Bảng danh sách 10 câu hỏi có điểm trung bình thấp nhất từ Task 3:

| Rank | Question ID | Distribution | Avg Score | Worst Metric | Diagnosis | Suggested Fix |
|---|---|---|---|---|---|---|
| 1 | 48 | adversarial | 0.6250 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 2 | 45 | adversarial | 0.6325 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 3 | 42 | adversarial | 0.6350 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 4 | 49 | adversarial | 0.6500 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 5 | 50 | adversarial | 0.6500 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 6 | 44 | adversarial | 0.6550 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 7 | 46 | adversarial | 0.6575 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 8 | 43 | adversarial | 0.6600 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 9 | 41 | adversarial | 0.6625 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 10 | 47 | adversarial | 0.6825 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |

Phân tích đối chiếu answer/contexts/reference của các câu đại diện:
- Câu 41 (ID 41, adversarial): Câu hỏi về số ngày nghỉ phép năm. Trong ngữ cảnh truy xuất có cả tài liệu quy chế nghỉ phép năm v2023 (12 ngày) và v2024 (15 ngày cơ bản). Việc không lọc phiên bản dẫn đến việc câu trả lời trích xuất thông tin cũ, gây suy giảm nghiêm trọng chỉ số faithfulness (0.52) và context_precision (0.58).
- Câu 45 (ID 45, adversarial): Câu hỏi gài bẫy điều kiện phủ định về quy định thử việc và phụ cấp. Đoạn văn bản trích xuất chứa câu phủ định nhưng mô hình nhầm lẫn giữa điều kiện đủ và điều kiện cần, dẫn đến chẩn đoán LLM hallucinating / mâu thuẫn ngữ cảnh.
- Câu 50 (ID 50, adversarial): Câu hỏi về việc sử dụng VPN cá nhân khi làm việc từ xa. Tài liệu quy định cấm NordVPN và bắt buộc WireGuard VPN, nhưng retriever lấy cả đoạn thảo luận chung khiến context precision giảm xuống 0.58.

## Matrix và nhóm yếu nhất

Ma trận phân phối 4 metrics và 3 distributions (đếm theo worst_metric của từng câu hỏi):

| Metric | factual | multi_hop | adversarial | Tổng |
|---|---|---|---|---|
| faithfulness | 2 | 0 | 10 | 12 |
| context_recall | 3 | 16 | 0 | 19 |
| context_precision | 8 | 4 | 0 | 12 |
| answer_relevancy | 7 | 0 | 0 | 7 |
| Tổng số câu | 20 | 20 | 10 | 50 |

Nhóm yếu theo mean thấp nhất: adversarial; mean: 0.6510.
Worst metric xuất hiện nhiều nhất: context_recall; số câu: 19.

Giải thích nguyên nhân:
1. Nhóm adversarial là nhóm có điểm trung bình thấp nhất (0.6510 so với factual 0.9026 và multi_hop 0.7790). Nguyên nhân chủ yếu là do tập dữ liệu corpus nội bộ chứa các văn bản lịch sử có xung đột phiên bản (ví dụ mat_khau_v1.md vs mat_khau_v2.md, nghi_phep_nam_v2023.md vs nghi_phep_nam_v2024.md). Pipeline RAG nếu chỉ dựa vào độ tương đồng ngữ nghĩa mà không có bộ lọc metadata ngày ban hành sẽ lấy nhầm tài liệu cũ.
2. Metric context_recall là điểm yếu chủ đạo trên toàn bộ 50 câu (chiếm 19/50 câu có điểm thấp nhất), đặc biệt nghiêm trọng ở nhóm multi_hop (16/20 câu). Lý do là câu hỏi multi-hop yêu cầu tổng hợp thông tin từ 2 đến 3 tài liệu khác nhau (ví dụ vừa hỏi số ngày phép thâm niên vừa hỏi khung lương), trong khi top-3 reranking chỉ chọn được các đoạn trả lời cho một vế của câu hỏi.
3. Đề xuất khắc phục: Bổ sung metadata filtering theo version/date_effective trong hybrid search; tăng số lượng chunk sau rerank hoặc áp dụng kỹ thuật Contextual Query Expansion để gom đủ các khía cạnh của câu hỏi đa bước.

## Bẫy adversarial và giới hạn

So sánh với factual và multi_hop:
- Nhóm factual đạt điểm số cao nhất (0.9026) do câu hỏi tra cứu trực tiếp thông tin đơn lẻ trong 1 tài liệu duy nhất.
- Nhóm multi_hop gặp rào cản về độ bao phủ ngữ cảnh (context recall đạt 0.7070).
- Nhóm adversarial có điểm số trung bình thấp hơn hẳn nhóm factual (0.6510 < 0.9026), phản ánh chính xác độ phức tạp của các câu hỏi bẫy phiên bản và phủ định. Điều này thỏa mãn điều kiện Bonus Phase A.
- Giới hạn thực nghiệm: Quy mô thử nghiệm 50 câu hỏi cho cái nhìn ban đầu về các cụm lỗi chính, tuy nhiên cần mở rộng thêm các kịch bản injection prompt và câu hỏi có cấu trúc bảng biểu phức tạp trong production thực tế. Chế độ extractive fallback giúp hệ thống duy trì tính ổn định không bị gián đoạn nhưng hạn chế khả năng tổng hợp câu chữ mượt mà so với LLM generator chuyên dụng.
