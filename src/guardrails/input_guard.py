"""
🛡️ LỚP 1 — INPUT GUARDRAILS (Kiểm soát tại cổng vào)

Mục tiêu:
  1. Phát hiện và chặn Prompt Injection / Jailbreak (regex + keyword blacklist).
  2. Sanitize đầu vào — loại bỏ script tags, null bytes, shell patterns.
  3. Giới hạn chủ đề (Topic Restriction) — chỉ cho phép domain HR/tuyển dụng.

Giao diện công khai:
  run_input_guard(user_input: str) -> dict
    Trả về: {"status": "ok" | "blocked", "clean_text": str, "reason": str}

Thiết kế: KHÔNG phụ thuộc bất kỳ LLM call nào — thuần Python, độ trễ ~0ms.
"""

import logging
import re

logger = logging.getLogger("guardrails.input")

# ---------------------------------------------------------------------------
# 1. PROMPT INJECTION / JAILBREAK — Danh sách pattern nguy hiểm
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS: list[re.Pattern] = [
    # Tiếng Anh — các câu lệnh thao túng phổ biến nhất
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above)", re.IGNORECASE),
    re.compile(r"\bact\s+as\b.{0,30}(DAN|jailbreak|evil|unfiltered|uncensored)", re.IGNORECASE),
    re.compile(r"\bpretend\s+(you\s+are|to\s+be)\b", re.IGNORECASE),
    re.compile(r"\byou\s+are\s+now\b.{0,20}(mode|version|ai|bot)", re.IGNORECASE),
    re.compile(r"\bdo\s+anything\s+now\b", re.IGNORECASE),
    re.compile(r"\bno\s+restrictions?\b", re.IGNORECASE),
    re.compile(r"\bsystem\s*prompt\b", re.IGNORECASE),
    re.compile(r"<\s*/?system\s*>", re.IGNORECASE),
    # Tiếng Việt — các biến thể phổ biến
    re.compile(r"bỏ\s+qua\s+(tất\s+cả\s+)?(lệnh|hướng dẫn|quy tắc)\s+(trước|trên|cũ)", re.IGNORECASE),
    re.compile(r"quên\s+(tất\s+cả\s+)?(lệnh|hướng dẫn|quy tắc)\s+(trước|trên|cũ)", re.IGNORECASE),
    re.compile(r"giả\s+vờ\s+(bạn\s+là|như)", re.IGNORECASE),
    re.compile(r"hãy\s+(trở\s+thành|đóng\s+vai)\b", re.IGNORECASE),
    re.compile(r"không\s+có\s+(giới\s+hạn|hạn\s+chế)", re.IGNORECASE),
    re.compile(r"bỏ\s+qua\s+(guardrail|giới hạn|phanh)", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# 2. INPUT SANITIZATION — Patterns nguy hiểm trong dữ liệu đầu vào (CV text)
# ---------------------------------------------------------------------------

# Thay thế bằng chuỗi rỗng (xóa sạch)
_SANITIZE_REMOVE = [
    re.compile(r"<script[\s\S]*?</script>", re.IGNORECASE),   # XSS script tags
    re.compile(r"<[^>]{1,200}>"),                              # HTML tags chung
    re.compile(r"\x00"),                                       # Null bytes
    re.compile(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]"),         # Control characters (giữ \t \n \r)
]

# Thay thế bằng dấu cách (normalize)
_SANITIZE_REPLACE = [
    re.compile(r";\s*(rm|del|format|drop|truncate|shutdown)\b", re.IGNORECASE),  # Shell/SQL injection
    re.compile(r"`[^`]{0,200}`"),                                                 # Backtick execution
    re.compile(r"\$\([^)]{0,200}\)"),                                             # Command substitution $()
]

# ---------------------------------------------------------------------------
# 3. TOPIC RESTRICTION — Từ khóa domain HR được phép
# ---------------------------------------------------------------------------

_HR_KEYWORDS: frozenset[str] = frozenset([
    # Quy trình tuyển dụng
    "tuyển dụng", "ứng viên", "hồ sơ", "cv", "resume", "phỏng vấn", "interview",
    "job", "việc làm", "tuyển", "nhân sự", "hr", "recruiter", "headhunter",
    "offer", "onboarding", "screening", "shortlist",
    # Vị trí / chức danh
    "developer", "engineer", "backend", "frontend", "fullstack", "data",
    "python", "java", "javascript", "sql", "nosql", "golang", "rust",
    "devops", "cloud", "aws", "gcp", "azure", "machine learning", "ai",
    "analyst", "manager", "intern", "senior", "junior", "lead", "architect",
    # Kỹ năng / công nghệ
    "django", "fastapi", "react", "vue", "angular", "docker", "kubernetes",
    "postgresql", "mongodb", "redis", "elasticsearch", "spark", "airflow",
    "git", "github", "agile", "scrum", "jira", "tableau", "power bi",
    # Thuật ngữ HR
    "jd", "job description", "kpi", "okr", "performance", "salary", "lương",
    "phúc lợi", "benefit", "kinh nghiệm", "kỹ năng", "bằng cấp", "chứng chỉ",
    "portfolio", "linkedin", "technical test", "bài test", "assessment",
    "reference", "background check", "probation", "thử việc",
    # Lịch / thời gian
    "lịch", "hẹn", "đặt lịch", "schedule", "tuần", "ngày", "giờ", "buổi",
])

_OFF_TOPIC_RESPONSE = (
    "Xin lỗi, tôi chỉ hỗ trợ các tác vụ liên quan đến tuyển dụng và nhân sự (HR). "
    "Vui lòng đặt câu hỏi về: quy trình tuyển dụng, đánh giá CV/hồ sơ, "
    "kỹ năng kỹ thuật cho các vị trí IT, hoặc lên lịch phỏng vấn."
)

_INJECTION_RESPONSE = (
    "Yêu cầu của bạn chứa nội dung không được phép (có thể là lệnh can thiệp hệ thống). "
    "Tôi chỉ có thể hỗ trợ các tác vụ HR hợp lệ."
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_prompt_injection(text: str) -> tuple[bool, str]:
    """
    Quét text tìm dấu hiệu Prompt Injection / Jailbreak.

    Returns:
        (is_injected: bool, matched_pattern: str)
    """
    for pattern in _INJECTION_PATTERNS:
        m = pattern.search(text)
        if m:
            logger.warning("detect_prompt_injection - phát hiện pattern: '%s'", m.group(0)[:80])
            return True, m.group(0)[:80]
    return False, ""


def sanitize_input(text: str) -> str:
    """
    Làm sạch đầu vào: xóa script/HTML, null bytes, shell injection patterns.
    Không thay đổi nội dung CV hợp lệ (text, số, dấu câu thông thường).

    Args:
        text: Chuỗi đầu vào thô (có thể từ plaintext CV).

    Returns:
        Chuỗi đã được làm sạch.
    """
    cleaned = text
    for pattern in _SANITIZE_REMOVE:
        cleaned = pattern.sub("", cleaned)
    for pattern in _SANITIZE_REPLACE:
        cleaned = pattern.sub(" [REMOVED] ", cleaned)
    # Chuẩn hóa khoảng trắng thừa
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    if cleaned != text:
        logger.info("sanitize_input - đã làm sạch %d ký tự → %d ký tự.", len(text), len(cleaned))
    return cleaned.strip()


def restrict_topic(text: str) -> tuple[bool, str]:
    """
    Kiểm tra xem câu hỏi có nằm trong domain HR/tuyển dụng không.

    Heuristic: text (chuỗi thường) phải chứa ít nhất 1 từ khóa HR.
    Chấp nhận rộng hơn để không chặn nhầm câu hỏi hợp lệ.

    Returns:
        (is_allowed: bool, reason: str)
    """
    lower = text.lower()
    for kw in _HR_KEYWORDS:
        if kw in lower:
            return True, f"Tìm thấy từ khóa HR: '{kw}'"

    logger.warning("restrict_topic - không tìm thấy từ khóa HR. Input: '%s'", text[:80])
    return False, "Không tìm thấy từ khóa HR trong câu hỏi"


def run_input_guard(user_input: str) -> dict:
    """
    Orchestrator Lớp 1: chạy tuần tự 3 bước kiểm soát đầu vào.

    Thứ tự ưu tiên:
      1. Kiểm tra injection → BLOCKED nếu phát hiện
      2. Sanitize đầu vào → luôn làm sạch
      3. Kiểm tra chủ đề → BLOCKED nếu off-topic

    Args:
        user_input: Câu hỏi thô từ người dùng.

    Returns:
        dict với các trường:
          - status     : "ok" | "blocked"
          - clean_text : chuỗi đã được sanitize (kể cả khi blocked)
          - reason     : mô tả lý do blocked (rỗng khi ok)
          - response   : câu trả lời sẵn sàng gửi user (khi blocked)
    """
    if not isinstance(user_input, str) or not user_input.strip():
        return {
            "status": "blocked",
            "clean_text": "",
            "reason": "Đầu vào rỗng hoặc không hợp lệ.",
            "response": "Vui lòng nhập câu hỏi của bạn.",
        }

    # Bước 1: Injection check (trên text gốc, TRƯỚC khi sanitize)
    is_injected, matched = detect_prompt_injection(user_input)
    if is_injected:
        clean = sanitize_input(user_input)
        return {
            "status": "blocked",
            "clean_text": clean,
            "reason": f"Phát hiện Prompt Injection: '{matched}'",
            "response": _INJECTION_RESPONSE,
        }

    # Bước 2: Sanitize
    clean = sanitize_input(user_input)

    # Bước 3: Topic restriction (trên text đã sanitize)
    is_allowed, topic_reason = restrict_topic(clean)
    if not is_allowed:
        return {
            "status": "blocked",
            "clean_text": clean,
            "reason": f"Off-topic: {topic_reason}",
            "response": _OFF_TOPIC_RESPONSE,
        }

    logger.info("run_input_guard - OK. Input: '%s'", clean[:60])
    return {
        "status": "ok",
        "clean_text": clean,
        "reason": "",
        "response": "",
    }
