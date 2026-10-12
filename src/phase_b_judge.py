from __future__ import annotations

"""Phase B: LLM-as-Judge — pairwise, swap-and-average, Cohen κ, bias analysis."""

import json
import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OPENAI_API_KEY, JUDGE_MODEL, HUMAN_LABELS_PATH


@dataclass
class JudgeResult:
    question: str
    answer_a: str
    answer_b: str
    winner_pass1: str       # "A" | "B" | "tie"  (original order)
    winner_pass2: str       # "A" | "B" | "tie"  (after swap, ALREADY converted back)
    final_winner: str       # consensus after swap-and-average
    reasoning_pass1: str
    reasoning_pass2: str
    position_consistent: bool  # True if both passes agree on same answer
    scores_pass1: dict = field(default_factory=dict)  # {"A": float, "B": float}
    scores_pass2: dict = field(default_factory=dict)


# ─── Task 5: Pairwise Judge ───────────────────────────────────────────────────

def pairwise_judge(question: str, answer_a: str, answer_b: str, reference: str = "") -> dict:
    """Task 5: Gọi LLM để chọn answer tốt hơn (A hoặc B) theo 3 tiêu chí.

    Tiêu chí đánh giá:
        - Độ chính xác (accuracy): có khớp với thực tế chính sách không?
        - Độ đầy đủ (completeness): có trả lời đủ câu hỏi không?
        - Tính súc tích (conciseness): có thừa / thiếu thông tin không?

    Returns:
        {"winner": "A"|"B"|"tie", "reasoning": str, "scores": {"A": float, "B": float}}
    """
    from openai import OpenAI
    client = OpenAI()

    prompt = (
        f"Bạn là một chuyên gia đánh giá chất lượng câu trả lời RAG.\n\n"
        f"Câu hỏi: {question}\n\n"
        f"Tài liệu tham chiếu / Ground truth: {reference}\n\n"
        f"Answer A:\n{answer_a}\n\n"
        f"Answer B:\n{answer_b}\n\n"
        f"Hãy đánh giá Answer A và Answer B dựa trên 3 tiêu chí: độ chính xác (accuracy so với reference), "
        f"độ đầy đủ (completeness) và tính súc tích (conciseness).\n"
        f"Quy định điểm scores: mỗi điểm trong khoảng [0.0, 1.0].\n"
        f"Winner là 'A', 'B' hoặc 'tie'.\n"
        f"Trả lời JSON (chỉ JSON, không text khác):\n"
        f'{{"winner": "A"|"B"|"tie", "reasoning": "giải thích ngắn gọn", "scores": {{"A": 0.0, "B": 0.0}}}}'
    )

    resp = client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[
            {"role": "system", "content": "Bạn là expert đánh giá RAG. Chỉ trả lời JSON."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )
    data = json.loads(resp.choices[0].message.content)
    winner = data.get("winner", "tie")
    if winner not in ("A", "B", "tie"):
        winner = "tie"
    reasoning = data.get("reasoning", "")
    scores = data.get("scores", {"A": 0.0, "B": 0.0})
    return {
        "winner": winner,
        "reasoning": str(reasoning),
        "scores": {
            "A": float(scores.get("A", 0.0)),
            "B": float(scores.get("B", 0.0)),
        },
    }


# ─── Task 6: Swap-and-Average ─────────────────────────────────────────────────

def swap_and_average(question: str, answer_a: str, answer_b: str, reference: str = "") -> JudgeResult:
    """Task 6: Chạy pairwise 2 lần (hoán đổi thứ tự), lấy kết quả nhất quán.

    Lý do: LLM thường có position bias (ưu tiên answer xuất hiện trước).
    Bằng cách swap, ta phát hiện và giảm bias này.

    Logic:
        Pass 1: judge(q, A, B) → winner_1 (trong không gian A/B)
        Pass 2: judge(q, B, A) → winner_2_raw (trong không gian B/A)
        Convert: nếu winner_2_raw="A" thì thực ra là B (vì đã swap)
        Final:   nếu winner_1 == winner_2 → final = winner_1
                 nếu khác nhau → final = "tie"
    """
    pass1 = pairwise_judge(question, answer_a, answer_b, reference=reference)
    pass2_raw = pairwise_judge(question, answer_b, answer_a, reference=reference)

    swap_map = {"A": "B", "B": "A", "tie": "tie"}
    winner_pass2 = swap_map.get(pass2_raw["winner"], "tie")

    position_consistent = (pass1["winner"] == winner_pass2)
    final = pass1["winner"] if position_consistent else "tie"

    scores_pass2_raw = pass2_raw.get("scores", {"A": 0.0, "B": 0.0})
    scores_pass2 = {
        "A": float(scores_pass2_raw.get("B", 0.0)),
        "B": float(scores_pass2_raw.get("A", 0.0)),
    }

    return JudgeResult(
        question=question,
        answer_a=answer_a,
        answer_b=answer_b,
        winner_pass1=pass1["winner"],
        winner_pass2=winner_pass2,
        final_winner=final,
        reasoning_pass1=pass1["reasoning"],
        reasoning_pass2=pass2_raw["reasoning"],
        position_consistent=position_consistent,
        scores_pass1={
            "A": float(pass1.get("scores", {}).get("A", 0.0)),
            "B": float(pass1.get("scores", {}).get("B", 0.0)),
        },
        scores_pass2=scores_pass2,
    )


# ─── Task 7: Cohen's κ ────────────────────────────────────────────────────────

def cohen_kappa(judge_labels: list[int], human_labels: list[int]) -> float:
    """Task 7: Tính Cohen's κ giữa LLM judge và human labels.

    Args:
        judge_labels:  nhãn từ LLM judge (0 = bad answer, 1 = good answer)
        human_labels:  nhãn từ human_labels_10q.json

    Returns:
        κ ∈ [-1, 1]
    """
    if not judge_labels or not human_labels or len(judge_labels) != len(human_labels):
        return 0.0
    n = len(judge_labels)
    p_o = sum(j == h for j, h in zip(judge_labels, human_labels)) / n
    p_e = (judge_labels.count(1) * human_labels.count(1) +
           judge_labels.count(0) * human_labels.count(0)) / (n * n)
    if p_e == 1.0:
        return 1.0 if p_o == 1.0 else 0.0
    return float((p_o - p_e) / (1.0 - p_e))


# ─── Task 8: Bias Report ──────────────────────────────────────────────────────

def bias_report(judge_results: list[JudgeResult]) -> dict:
    """Task 8: Đo lường position bias và verbosity bias.

    Position bias: LLM chọn answer theo vị trí (A hay B) thay vì chất lượng.
        → Đo bằng % cases where position_consistent = False

    Verbosity bias: LLM ưu tiên answer dài hơn dù không chính xác hơn.
        → Đo bằng: trong các case A thắng, A có dài hơn B không? Tương tự cho B.

    Returns:
        {
          "total_judged": int,
          "position_bias_rate": float,
          "position_bias_count": int,
          "verbosity_bias": float,
          "verbosity_details": {
            "a_wins_a_longer": int,
            "b_wins_b_longer": int,
            "total_decisive": int,
          },
          "interpretation": str,
        }
    """
    total = len(judge_results)
    if total == 0:
        return {
            "total_judged": 0,
            "position_bias_rate": 0.0,
            "position_bias_count": 0,
            "verbosity_bias": 0.0,
            "verbosity_details": {
                "a_wins_a_longer": 0,
                "b_wins_b_longer": 0,
                "total_decisive": 0,
            },
            "interpretation": "Không có dữ liệu đánh giá pairwise.",
        }

    position_bias_count = sum(1 for r in judge_results if not r.position_consistent)
    position_bias_rate = position_bias_count / total

    a_wins_a_longer = sum(
        1 for r in judge_results
        if r.final_winner == "A" and len(r.answer_a) > len(r.answer_b)
    )
    b_wins_b_longer = sum(
        1 for r in judge_results
        if r.final_winner == "B" and len(r.answer_b) > len(r.answer_a)
    )
    decisive = sum(1 for r in judge_results if r.final_winner != "tie")
    verbosity_bias = (a_wins_a_longer + b_wins_b_longer) / decisive if decisive > 0 else 0.0

    interpretation = (
        f"Position bias rate là {position_bias_rate:.1%} ({position_bias_count}/{total} cases bất nhất vị trí). "
        f"Verbosity bias rate là {verbosity_bias:.1%} ({a_wins_a_longer + b_wins_b_longer}/{decisive} decisive cases dài hơn chiến thắng). "
        + ("Position bias tồn tại, swap-and-average giúp trung hòa hiệu quả." if position_bias_count > 0 else "Judge thể hiện tính nhất quán vị trí tuyệt đối.")
    )

    return {
        "total_judged": total,
        "position_bias_rate": position_bias_rate,
        "position_bias_count": position_bias_count,
        "verbosity_bias": verbosity_bias,
        "verbosity_details": {
            "a_wins_a_longer": a_wins_a_longer,
            "b_wins_b_longer": b_wins_b_longer,
            "total_decisive": decisive,
        },
        "interpretation": interpretation,
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from scripts.run_experiments import main
    raise SystemExit(main(["--phase", "b", *sys.argv[1:]]))
