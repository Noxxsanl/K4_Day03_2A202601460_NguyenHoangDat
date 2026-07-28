"""
🛡️ GUARDRAILS PACKAGE
Gói bảo vệ 3 lớp cho ReAct Agent tuyển dụng.

Cách dùng nhanh:
    from guardrails import run_input_guard, execute_with_guard, validate_output

Lớp 1 — Input Guardrails  (input_guard.py):
    Chặn prompt injection, jailbreak, off-topic, làm sạch đầu vào.

Lớp 2 — Execution Guardrails (execution_guard.py):
    Validate tham số tool (Pydantic), error-feedback-loop, human-in-the-loop.

Lớp 3 — Output Guardrails (output_guard.py):
    Kiểm tra hallucination, ép buộc JSON output đúng schema.
"""

from guardrails.input_guard import run_input_guard
from guardrails.execution_guard import execute_with_guard, HIGH_RISK_TOOLS
from guardrails.output_guard import validate_output

__all__ = [
    "run_input_guard",
    "execute_with_guard",
    "HIGH_RISK_TOOLS",
    "validate_output",
]
