"""
🛡️ LỚP 3 — OUTPUT GUARDRAILS (Kiểm soát độ an toàn đầu ra)

Mục tiêu:
  1. Chống Hallucination — so sánh chéo output LLM với danh sách
     context_facts (thực tế đã biết từ tool observations).
  2. Enforce Structured Output — ép buộc output phải là JSON hợp lệ
     nếu tác vụ yêu cầu (score_candidate, rank_candidates, v.v.).

Giao diện công khai:
  validate_output(raw_output, context_facts, expected_format="text") -> dict
    Trả về: {
        "status"      : "ok" | "warning" | "error",
        "safe_output" : str — output đã kiểm tra,
        "warnings"    : list[str] — cảnh báo (rỗng khi status="ok"),
    }

Thiết kế: Không gọi LLM — hoàn toàn deterministic, độ trễ thấp.
"""

import json
import logging
import re

logger = logging.getLogger("guardrails.output")

# ---------------------------------------------------------------------------
# Ngưỡng phát hiện hallucination
# ---------------------------------------------------------------------------

# Tỉ lệ "token quan trọng" không khớp với context_facts để kích cảnh báo
_HALLUCINATION_WARNING_THRESHOLD = 0.3   # >30% tokens lạ → WARNING

# Độ dài tối thiểu để áp dụng hallucination check (quá ngắn → bỏ qua)
_MIN_CHECK_LENGTH = 20


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> set[str]:
    """Tách text thành set token lowercase (chữ cái, số, có dấu)."""
    return set(re.findall(r"[\w\u00C0-\u024F\u1E00-\u1EFF]+", text.lower()))


def _extract_numbers(text: str) -> set[str]:
    """Trích xuất tất cả số (nguyên + thập phân) trong text."""
    return set(re.findall(r"\b\d+(?:[.,]\d+)?\b", text))


def _check_hallucination_heuristic(output: str, context_facts: list[str]) -> list[str]:
    """
    Heuristic phát hiện hallucination bằng cách đối chiếu token + số.

    Logic:
      - Gộp tất cả context_facts thành một tập token biết-là-thật.
      - Trích xuất các số trong output.
      - Nếu 1 số trong output KHÔNG xuất hiện trong bất kỳ fact nào → cảnh báo.
      - Nếu có danh sách tên/thực thể trong context nhưng output đề cập thực thể
        hoàn toàn mới → cảnh báo.

    Lưu ý: Đây là heuristic — false positive có thể xảy ra với nội dung
    sáng tạo (câu hỏi phỏng vấn gợi ý). Chỉ áp dụng khi context_facts không rỗng.
    """
    warnings = []
    if not context_facts or len(output) < _MIN_CHECK_LENGTH:
        return warnings

    # Tập hợp tất cả thông tin "ground truth" từ tool observations
    all_facts_text = " ".join(context_facts)
    facts_numbers = _extract_numbers(all_facts_text)
    facts_tokens = _tokenize(all_facts_text)

    # ── Kiểm tra số trong output có tồn tại trong facts không ──
    output_numbers = _extract_numbers(output)
    # Loại trừ số quá phổ biến (năm, tháng, v.v.) để giảm false positive
    suspicious_numbers = {
        n for n in output_numbers
        if n not in facts_numbers
        and not re.match(r"^(19|20)\d{2}$", n)  # Không cảnh báo với năm
        and float(n.replace(",", ".")) > 9       # Không cảnh báo với số 0-9
    }
    if suspicious_numbers:
        warnings.append(
            f"⚠️ [HALLUCINATION-RISK] Output chứa số {suspicious_numbers} "
            "không xuất hiện trong dữ liệu tool đã trả về. "
            "Hãy kiểm tra lại tính chính xác."
        )

    # ── Kiểm tra tỉ lệ token lạ trong output ──
    output_tokens = _tokenize(output)
    # Chỉ xét token có độ dài ≥ 4 (bỏ qua từ ghép ngắn như "là", "và")
    significant_output = {t for t in output_tokens if len(t) >= 4}
    if significant_output:
        unknown = significant_output - facts_tokens
        ratio = len(unknown) / len(significant_output)
        if ratio > _HALLUCINATION_WARNING_THRESHOLD and len(context_facts) >= 2:
            # Chỉ cảnh báo khi có đủ context (≥2 facts) để so sánh
            sample = list(unknown)[:5]
            warnings.append(
                f"⚠️ [HALLUCINATION-RISK] {ratio:.0%} token trong output ({sample}…) "
                "không tìm thấy trong dữ liệu thực tế. "
                "Có thể LLM đang suy diễn ngoài phạm vi dữ liệu đã cho."
            )

    return warnings


def enforce_json_output(raw_text: str, expected_schema: dict | None = None) -> tuple[bool, dict | None, str]:
    """
    Kiểm tra và parse output thành JSON.

    Args:
        raw_text       : Chuỗi output thô từ LLM.
        expected_schema: Schema tối thiểu cần có (dict với các key bắt buộc).
                         Nếu None → chỉ kiểm tra valid JSON.

    Returns:
        (is_valid: bool, parsed_dict: dict|None, error_msg: str)
    """
    # Thử trích xuất JSON block từ markdown code fence
    code_fence = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", raw_text)
    candidate = code_fence.group(1) if code_fence else raw_text.strip()

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        logger.warning("enforce_json_output - không parse được JSON: %s", exc)
        return False, None, f"Output không phải JSON hợp lệ: {exc}"

    if expected_schema and isinstance(expected_schema, dict):
        missing = [k for k in expected_schema if k not in parsed]
        if missing:
            return (
                False,
                parsed,
                f"JSON thiếu các trường bắt buộc: {missing}. "
                f"Schema yêu cầu: {list(expected_schema.keys())}.",
            )

    return True, parsed, ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_output(
    raw_output: str,
    context_facts: list[str] | None = None,
    expected_format: str = "text",
    expected_schema: dict | None = None,
) -> dict:
    """
    Orchestrator Lớp 3: kiểm tra hallucination + đảm bảo định dạng output.

    Args:
        raw_output     : Chuỗi output thô từ LLM (Final Answer hoặc Observation).
        context_facts  : Danh sách thực tế ground-truth (từ tool observations).
                         VD: ["Nguyễn Văn A: 75 điểm", "Trần Thị B: 60 điểm"]
        expected_format: "text" (mặc định) hoặc "json".
        expected_schema: Chỉ dùng khi expected_format="json". Dict các key bắt buộc.
                         VD: {"score": None, "verdict": None}

    Returns:
        dict với:
          - status      : "ok" | "warning" | "error"
          - safe_output : output đã kiểm tra (giữ nguyên khi ok/warning)
          - warnings    : list cảnh báo (rỗng khi ok)
          - parsed_json : dict nếu expected_format="json" và parse thành công
    """
    warnings: list[str] = []
    parsed_json: dict | None = None

    if not raw_output or not raw_output.strip():
        return {
            "status": "error",
            "safe_output": raw_output or "",
            "warnings": ["Output rỗng từ LLM."],
            "parsed_json": None,
        }

    # ── Bước 1: Hallucination Check ──────────────────────────────────────
    hallucination_warns = _check_hallucination_heuristic(raw_output, context_facts or [])
    warnings.extend(hallucination_warns)
    if hallucination_warns:
        for w in hallucination_warns:
            logger.warning("validate_output - %s", w)

    # ── Bước 2: Format Enforcement ────────────────────────────────────────
    if expected_format == "json":
        is_valid, parsed_json, json_err = enforce_json_output(raw_output, expected_schema)
        if not is_valid:
            logger.warning("validate_output - JSON enforcement thất bại: %s", json_err)
            return {
                "status": "error",
                "safe_output": raw_output,
                "warnings": warnings + [json_err],
                "parsed_json": parsed_json,
            }

    # ── Kết quả ───────────────────────────────────────────────────────────
    status = "warning" if warnings else "ok"
    if status == "ok":
        logger.info("validate_output - output OK (%d ký tự).", len(raw_output))
    else:
        logger.warning("validate_output - output có %d cảnh báo.", len(warnings))

    return {
        "status": status,
        "safe_output": raw_output,
        "warnings": warnings,
        "parsed_json": parsed_json,
    }
