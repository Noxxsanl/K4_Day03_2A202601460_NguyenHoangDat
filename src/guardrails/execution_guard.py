"""
🛡️ LỚP 2 — EXECUTION GUARDRAILS (Kiểm soát thực thi Tool)

Mục tiêu:
  1. Validate tham số trước khi gọi tool — dùng Pydantic models.
  2. Error Feedback Loop — chuyển Exception → chuỗi context nạp lại cho LLM.
  3. Human-in-the-loop — yêu cầu xác nhận người dùng trước khi thực thi
     các tool có rủi ro cao (schedule_interview, v.v.)

Giao diện công khai:
  execute_with_guard(tool_name, params, tools_mod, require_confirm=None) -> dict
    Trả về: {"status": "ok" | "error", "result": str | "error_context": str}

Thiết kế: Mỗi tool nguy hiểm có Pydantic model riêng. Khi thêm tool mới,
chỉ cần thêm model + đăng ký vào _VALIDATORS dict.
"""

import inspect
import logging
import sys
from datetime import date, datetime

logger = logging.getLogger("guardrails.execution")

# ---------------------------------------------------------------------------
# Dependency: Pydantic (bắt buộc cho Lớp 2)
# ---------------------------------------------------------------------------
try:
    from pydantic import BaseModel, Field, field_validator
    _PYDANTIC_OK = True
except ImportError:
    _PYDANTIC_OK = False
    logger.warning(
        "execution_guard - pydantic chưa được cài. "
        "Chạy: pip install pydantic>=2.0 để bật validation."
    )

# ---------------------------------------------------------------------------
# Danh sách tool yêu cầu human confirmation trước khi thực thi
# ---------------------------------------------------------------------------
HIGH_RISK_TOOLS: frozenset[str] = frozenset({
    "schedule_interview",
    # Mở rộng sau: "send_email", "delete_candidate_record"
})

# ---------------------------------------------------------------------------
# Pydantic Models — mỗi model ứng với 1 tool
# ---------------------------------------------------------------------------

if _PYDANTIC_OK:

    class ScheduleInterviewParams(BaseModel):
        """Validate tham số cho tool schedule_interview."""
        candidate_name: str = Field(..., min_length=1, description="Tên ứng viên")
        interview_date: str = Field(..., description="Ngày phỏng vấn YYYY-MM-DD")
        interview_time: str = Field(..., description="Giờ phỏng vấn HH:MM (24h)")

        @field_validator("candidate_name")
        @classmethod
        def name_not_whitespace(cls, v: str) -> str:
            if not v.strip():
                raise ValueError("candidate_name không được chỉ chứa khoảng trắng.")
            return v.strip()

        @field_validator("interview_date")
        @classmethod
        def date_must_be_future(cls, v: str) -> str:
            v = v.strip()
            try:
                parsed = datetime.strptime(v, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(
                    f"Định dạng ngày không hợp lệ: '{v}'. "
                    "Yêu cầu: YYYY-MM-DD (ví dụ: 2026-08-15)."
                )
            today = date.today()
            if parsed < today:
                raise ValueError(
                    f"Ngày '{v}' đã qua. "
                    f"Vui lòng chọn ngày từ {today.strftime('%Y-%m-%d')} trở đi."
                )
            return v

        @field_validator("interview_time")
        @classmethod
        def time_format_hhmm(cls, v: str) -> str:
            import re
            v = v.strip()
            if not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", v):
                raise ValueError(
                    f"Định dạng giờ không hợp lệ: '{v}'. "
                    "Yêu cầu: HH:MM 24h (ví dụ: 09:30 hoặc 14:00)."
                )
            return v

    class ScoreCandidateParams(BaseModel):
        """Validate tham số cho tool score_candidate."""
        candidate_info: str = Field(..., min_length=1)
        job_requirements: str = Field(..., min_length=1)

        @field_validator("candidate_info", "job_requirements")
        @classmethod
        def not_whitespace(cls, v: str) -> str:
            if not v.strip():
                raise ValueError("Tham số không được chỉ chứa khoảng trắng.")
            return v.strip()

    class RankCandidatesParams(BaseModel):
        """Validate tham số cho tool rank_candidates."""
        candidate_scores: str = Field(..., min_length=1)

        @field_validator("candidate_scores")
        @classmethod
        def has_colon_format(cls, v: str) -> str:
            v = v.strip()
            lines = [l.strip() for l in v.splitlines() if l.strip()]
            valid = [l for l in lines if ":" in l]
            if not valid:
                raise ValueError(
                    "candidate_scores phải có ít nhất 1 dòng hợp lệ dạng 'Tên ứng viên: điểm'. "
                    f"Nhận được: '{v[:80]}'"
                )
            return v

    # Map tên tool → Pydantic model tương ứng
    _VALIDATORS: dict[str, type] = {
        "schedule_interview": ScheduleInterviewParams,
        "score_candidate": ScoreCandidateParams,
        "rank_candidates": RankCandidatesParams,
    }

else:
    _VALIDATORS: dict = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_params(tool_name: str, params: dict) -> tuple[bool, str]:
    """
    Validate params theo Pydantic model nếu có model cho tool này.

    Returns:
        (is_valid: bool, error_message: str)
        error_message rỗng khi is_valid = True.
    """
    if not _PYDANTIC_OK or tool_name not in _VALIDATORS:
        return True, ""  # Không có model → bỏ qua, để tool tự xử lý

    model_cls = _VALIDATORS[tool_name]
    try:
        model_cls(**params)
        logger.info("_validate_params - tool '%s': params hợp lệ.", tool_name)
        return True, ""
    except Exception as exc:  # noqa: BLE001
        # Pydantic ValidationError có thể có nhiều lỗi cùng lúc
        try:
            # Pydantic v2: exc.errors() trả về list
            errors = exc.errors()  # type: ignore[attr-defined]
            messages = "; ".join(e["msg"] for e in errors)
        except AttributeError:
            messages = str(exc)
        logger.warning("_validate_params - tool '%s' params không hợp lệ: %s", tool_name, messages)
        return False, messages


def error_to_context(exception: Exception, tool_name: str) -> str:
    """
    Chuyển exception (từ validation hoặc tool execution) thành chuỗi
    ngữ cảnh thân thiện, nạp ngược vào scratchpad để LLM tự hiểu và
    hỏi lại người dùng.

    Format chuẩn:
        [TOOL_ERROR] <tool_name>: <mô tả lỗi ngắn gọn>. <gợi ý sửa>.
    """
    raw = str(exception)
    # Rút gọn stacktrace nếu có
    if "\n" in raw:
        raw = raw.splitlines()[-1]

    return (
        f"[TOOL_ERROR] {tool_name}: {raw} "
        f"Hãy xin lỗi người dùng, giải thích lỗi và hỏi lại thông tin đúng."
    )


def request_human_confirmation(action_desc: str, params: dict) -> bool:
    """
    Hiển thị tóm tắt hành động sắp thực thi và yêu cầu xác nhận y/n.

    Args:
        action_desc: Mô tả ngắn hành động (tên tool).
        params     : Dict tham số sẽ truyền vào tool.

    Returns:
        True nếu người dùng xác nhận, False nếu từ chối.
    """
    print("\n" + "=" * 60)
    print("🚨 [HUMAN-IN-THE-LOOP] Xác nhận trước khi thực thi")
    print("=" * 60)
    print(f"  🛠️ Hành động: {action_desc}")
    print("  📋 Tham số:")
    for key, val in params.items():
        short_val = str(val)[:80] + "…" if len(str(val)) > 80 else str(val)
        print(f"      {key}: {short_val}")
    print("=" * 60)

    try:
        answer = input("  ❓ Xác nhận thực thi? (y/n): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        # Môi trường không interactive (CI, pipe) → tự động từ chối để an toàn
        print("  ⚠️  Không có input terminal — tự động từ chối (an toàn).")
        return False

    confirmed = answer in ("y", "yes", "có", "co")
    if confirmed:
        logger.info("request_human_confirmation - người dùng XÁC NHẬN '%s'.", action_desc)
        print("  ✅ Xác nhận — tiến hành thực thi.\n")
    else:
        logger.info("request_human_confirmation - người dùng TỪ CHỐI '%s'.", action_desc)
        print("  ❌ Từ chối — hủy bỏ hành động.\n")
    return confirmed


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def execute_with_guard(
    tool_name: str,
    params: dict,
    tools_mod,
    require_confirm: bool | None = None,
) -> dict:
    """
    Orchestrator Lớp 2: validate → (optional) confirm → gọi tool → bắt lỗi.

    Args:
        tool_name     : Tên tool (phải có trong tools_mod.AVAILABLE_TOOLS).
        params        : Dict tham số truyền vào tool.
        tools_mod     : Module tools đã import (chứa AVAILABLE_TOOLS + call_tool).
        require_confirm: True/False để ép; None = tự động theo HIGH_RISK_TOOLS.

    Returns:
        dict với:
          - status         : "ok" | "validation_error" | "rejected" | "error"
          - result         : kết quả str từ tool (khi status="ok")
          - error_context  : chuỗi lỗi nạp cho LLM (khi status khác "ok")
          - tool_name      : echo lại tên tool
    """
    # ── 1. Pydantic Validation ───────────────────────────────────────────
    is_valid, err_msg = _validate_params(tool_name, params)
    if not is_valid:
        ctx = (
            f"[VALIDATION_ERROR] {tool_name}: {err_msg} "
            "Hãy xin lỗi người dùng và hỏi lại thông tin đúng định dạng."
        )
        logger.warning("execute_with_guard - validation thất bại tool '%s': %s", tool_name, err_msg)
        return {"status": "validation_error", "error_context": ctx, "tool_name": tool_name}

    # ── 2. Human-in-the-loop Confirmation ───────────────────────────────
    needs_confirm = require_confirm if require_confirm is not None else (tool_name in HIGH_RISK_TOOLS)
    if needs_confirm:
        confirmed = request_human_confirmation(tool_name, params)
        if not confirmed:
            ctx = (
                f"[HUMAN_REJECTED] Người dùng đã từ chối xác nhận hành động '{tool_name}'. "
                "Hãy hỏi người dùng xem họ muốn thay đổi thông tin hay hủy bỏ yêu cầu."
            )
            return {"status": "rejected", "error_context": ctx, "tool_name": tool_name}

    # ── 3. Gọi Tool thật ────────────────────────────────────────────────
    registry = getattr(tools_mod, "AVAILABLE_TOOLS", {})
    if tool_name not in registry:
        ctx = (
            f"[TOOL_ERROR] Tool '{tool_name}' không tồn tại trong registry. "
            f"Các tool hợp lệ: {', '.join(registry.keys())}."
        )
        return {"status": "error", "error_context": ctx, "tool_name": tool_name}

    try:
        caller = getattr(tools_mod, "call_tool", None)
        if callable(caller):
            result = str(caller(tool_name, **params))
        else:
            result = str(registry[tool_name](**params))

        logger.info("execute_with_guard - tool '%s' thành công.", tool_name)
        return {"status": "ok", "result": result, "tool_name": tool_name}

    except Exception as exc:  # noqa: BLE001
        ctx = error_to_context(exc, tool_name)
        logger.error("execute_with_guard - tool '%s' ném lỗi: %s", tool_name, exc)
        return {"status": "error", "error_context": ctx, "tool_name": tool_name}
