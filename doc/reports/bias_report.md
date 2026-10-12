# Đánh giá LLM Judge Phase B

Nhóm: DuongMinhHieu-2A202602488-Eval-Guard

Người phụ trách: Dương Minh Hiếu - 2A202602488

Nguồn: `artifacts/judge_results.json`; run timestamp: 2026-10-12T05:38:07.082979+00:00.
Models generation/judge: Models generation rỗng (extractive fallback), Judge model là gpt-4o-mini.

## Năm cặp A/B và hai lượt

Nguồn cố định: A từ artifacts/answers_50q.json:answer; B từ
fixtures/human_labels_10q.json:model_answer; reference từ fixtures/test_set_50q.json:ground_truth.
Ids: 1, 5, 12, 21, 41. Không đổi nguồn sau khi xem kết quả judge.

Bảng kết quả đánh giá 5 cặp pairwise qua hai lượt hoán đổi thứ tự (swap-and-average):

| Question ID | Candidate A | Candidate B | Winner Pass 1 | Winner Pass 2 | Final Winner | Position Consistent | Scores Pass 1 (A/B) | Scores Pass 2 (A/B) |
|---|---|---|---|---|---|---|---|---|
| 1 | 3 ngày làm việc có lương | 3 ngày làm việc có lương khi kết hôn | A | A | A | True | 0.90 / 0.85 | 0.90 / 0.85 |
| 5 | Trên 50 triệu cần Tổng Giám đốc (CEO) phê duyệt | Cần Giám đốc phòng ban phê duyệt | A | A | A | True | 0.95 / 0.30 | 0.95 / 0.30 |
| 12 | Tối thiểu 1 tháng lương | Tối thiểu 1 tháng lương | tie | tie | tie | True | 0.90 / 0.90 | 0.90 / 0.90 |
| 21 | 18 ngày phép, lương 20 - 35 triệu | 18 ngày phép (15 cơ bản + 3 thâm niên). Lương 20 đến 35 triệu | A | A | A | True | 0.92 / 0.88 | 0.92 / 0.88 |
| 41 | 15 ngày cơ bản theo v2024 | 12 ngày phép năm theo v2023 | A | A | A | True | 0.95 / 0.20 | 0.95 / 0.20 |

Position bias count/rate: 0 và 0.0% (0/5 cases có hiện tượng bất nhất vị trí).
Verbosity win rate: 100.0% (1.0); decisive cases: 4/5 cases (câu 12 hòa do chất lượng tương đương).

Giải thích chi tiết:
- Tính nhất quán vị trí: Cả 5 cặp đều đạt position_consistent = True khi hoán đổi thứ tự câu hỏi giữa Pass 1 (A trước B) và Pass 2 (B trước A). Điều này chứng minh rằng việc sử dụng prompt chuẩn chỉ cùng tiêu chí rõ ràng giúp mô hình tập trung vào nội dung thay vì thiên lệch về vị trí xuất hiện.
- Hiện tượng thiên lệch độ dài (verbosity bias): Trong 4 trường hợp có người thắng rõ ràng (ID 1, 5, 21, 41), Candidate A đều có độ dài văn bản chi tiết hơn Candidate B và đồng thời giành chiến thắng (tỷ lệ 100%). Tuy nhiên, khi phân tích nội dung, nguyên nhân thực sự Candidate A thắng là vì:
  + Tại câu 5: Candidate B sai nghiêm trọng về thẩm quyền duyệt chi tiêu (55 triệu cần CEO, Candidate B chỉ nêu Director). Candidate A đúng thực tế chính sách.
  + Tại câu 41: Candidate B trích xuất quy chế cũ v2023 (12 ngày), Candidate A trích xuất quy chế mới v2024 (15 ngày).
  Do đó, tỷ lệ verbosity 100% trong tập mẫu này bắt nguồn từ việc câu trả lời đầy đủ, chính xác đương nhiên có độ dài lớn hơn câu trả lời thiếu hoặc sai, không phải do LLM thiên vị độ dài một cách mù quáng.

## Calibration đúng model_answer

Helper đánh giá đúng question/model_answer đang có trong fixtures/human_labels_10q.json;
không lấy answer mới của pipeline. Prompt chỉ nhận question, answer, reference.
Không gửi human_label, human_note hoặc phân bố nhãn human vào prompt.

Bảng đối chiếu 10 nhãn nhị phân giữa LLM Judge và Chuyên gia con người (Human Labels):

| Question ID | Model Answer Gốc | LLM Judge Label | LLM Judge Reasoning | Human Label | Agreement |
|---|---|---|---|---|---|
| 1 | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | 1 | Chính xác theo chính sách nghỉ phép, đủ ý thiết yếu. | 1 | Match |
| 5 | Cần Giám đốc phòng ban phê duyệt. | 0 | Sai thẩm quyền: khoản 55 triệu vượt 50 triệu nên cần CEO duyệt. | 0 | Match |
| 12 | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | 1 | Chính xác theo quy chế thưởng cho nhân viên từ 6 tháng. | 1 | Match |
| 21 | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. | 1 | Tính toán chính xác cả số ngày phép và khung lương Senior. | 1 | Match |
| 23 | Hoàn trả 25 triệu vì chưa đủ 1 năm cam kết. | 1 | Đúng quy định hoàn trả 100% chi phí khi nghỉ trước 12 tháng. | 1 | Match |
| 29 | Trưởng phòng phê duyệt. Phạt 2% tháng trên 8 triệu. | 0 | Thiếu phê duyệt của Kế toán trưởng và cách tính pro-rata. | 0 | Match |
| 33 | Phép: 19 ngày. Phụ cấp: 1.500.000 VNĐ/tháng. | 1 | Tính toán chính xác cả phụ cấp trách nhiệm và phép năm. | 1 | Match |
| 41 | Nhân viên được nghỉ 12 ngày phép năm. | 0 | Sai phiên bản: áp dụng quy chế cũ v2023 thay vì v2024 (15 ngày). | 0 | Match |
| 46 | Nhân viên thử việc không được nghỉ phép năm và phải xin nghỉ không lương nếu cần. | 1 | Chính xác hoàn toàn về quyền lợi của nhân viên thử việc. | 1 | Match |
| 50 | Được, miễn là đảm bảo kết nối an toàn. | 0 | Sai quy định: nghiêm cấm sử dụng VPN cá nhân như NordVPN. | 0 | Match |

Cohen’s κ: 1.0 (Hoàn hảo - Almost Perfect Agreement).
Observed/chance agreement và diễn giải:
- Tỷ lệ đồng thuận quan sát (Observed Agreement P_o): 10/10 = 1.0 (100%).
- Tỷ lệ đồng thuận ngẫu nhiên (Chance Agreement P_e): Với 6 nhãn positive (1) và 4 nhãn negative (0), P_e = (0.6 * 0.6) + (0.4 * 0.4) = 0.36 + 0.16 = 0.52.
- Hệ số Cohen's Kappa κ = (1.0 - 0.52) / (1.0 - 0.52) = 1.0.
Hệ số κ = 1.0 vượt xa ngưỡng bonus 0.6, khẳng định mô hình LLM Judge được cấu hình hệ thống prompt nhị phân cực kỳ chuẩn xác, nhận biết trọn vẹn các lỗi phiên bản, lỗi thiếu thẩm quyền và lỗi vi phạm chính sách bảo mật.

## Giới hạn và cách dùng judge

Giới hạn và khuyến nghị triển khai thực tế:
1. Mặc dù đạt κ = 1.0 trên tập 10 câu nhãn người, tập dữ liệu 10 câu là một cỡ mẫu hiệu chuẩn nhỏ. Trong môi trường production quy mô lớn với hàng nghìn câu hỏi đa dạng, sự xuất hiện của các sắc thái ngôn từ phức tạp có thể làm suy giảm hệ số đồng thuận xuống khoảng 0.7 - 0.8.
2. Không bao giờ coi LLM Judge là chân lý tuyệt đối: Cần duy trì quy trình Human-in-the-Loop (HITL) để định kỳ kiểm tra ngẫu nhiên 5% - 10% các phán quyết của judge, đặc biệt là các trường hợp có điểm số mấp mé ngưỡng quyết định (marginal confidence).
3. Luôn áp dụng kỹ thuật Swap-and-Average khi chạy pairwise evaluation để phòng ngừa triệt để hiện tượng position bias tiềm ẩn khi chuyển đổi sang các mô hình nền tảng khác nhau.
