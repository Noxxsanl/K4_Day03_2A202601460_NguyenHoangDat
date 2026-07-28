"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.

Cải tiến (v2):
- Validate input đầu vào: kiểu dữ liệu, rỗng/None
- Xử lý exception với try/except và thông báo rõ ràng
- Logging đầy đủ ở mỗi bước (INFO / WARNING / ERROR)
- score_candidate: logic thực (đếm từ chung) + ngưỡng pass
- rank_candidates: parse có cấu trúc, sắp xếp thực, tie-breaking
- schedule_interview: validate định dạng ngày (YYYY-MM-DD), giờ (HH:MM),
  kiểm tra ngày trong tương lai
- call_tool(): fallback an toàn cho AVAILABLE_TOOLS registry
"""

import logging
import re
from datetime import datetime

# ---------------------------------------------------------------------------
# Cấu hình Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("tools")


# ---------------------------------------------------------------------------
# Helper dùng chung
# ---------------------------------------------------------------------------

def _require_non_empty_str(value, param_name: str) -> None:
    """Ném lỗi nếu value không phải str hoặc là chuỗi rỗng/khoảng trắng."""
    if not isinstance(value, str):
        raise TypeError(
            f"'{param_name}' phai la kieu str, nhan duoc: {type(value).__name__}"
        )
    if not value.strip():
        raise ValueError(
            f"'{param_name}' khong duoc la chuoi rong hoac chi chua khoang trang."
        )


# ---------------------------------------------------------------------------
# Tool 1 — extract_cv_information
# ---------------------------------------------------------------------------

def extract_cv_information(cv_content: str) -> str:
    """
    Trích xuất thông tin ứng viên từ CV.

    Args:
        cv_content (str): Nội dung CV dạng văn bản thuần.

    Returns:
        str: Thông tin ứng viên được trích xuất.

    Raises:
        TypeError: Nếu cv_content không phải str.
        ValueError: Nếu cv_content rỗng.
        RuntimeError: Nếu xảy ra lỗi trong quá trình xử lý.
    """
    logger.info(
        "extract_cv_information - nhan input dai %d ky tu.",
        len(cv_content) if isinstance(cv_content, str) else -1,
    )
    try:
        _require_non_empty_str(cv_content, "cv_content")

        # TODO: Thay thế bằng logic thực (LLM call, NLP, regex...)
        lines = cv_content.strip().splitlines()
        preview = lines[0][:80] if lines else "(khong ro)"
        result = (
            f"Da trich xuat thong tin ung vien tu CV ({len(lines)} dong). "
            f"Dong dau tien: '{preview}'."
        )

        logger.info("extract_cv_information - thanh cong.")
        return result

    except (TypeError, ValueError) as exc:
        logger.error("extract_cv_information - loi validation: %s", exc)
        raise
    except Exception as exc:
        logger.exception("extract_cv_information - loi khong mong muon.")
        raise RuntimeError(f"Loi khi trich xuat CV: {exc}") from exc


# ---------------------------------------------------------------------------
# Tool 2 — analyze_job_description
# ---------------------------------------------------------------------------

def analyze_job_description(job_description: str) -> str:
    """
    Phân tích yêu cầu từ mô tả công việc.

    Args:
        job_description (str): Nội dung mô tả công việc dạng văn bản thuần.

    Returns:
        str: Các yêu cầu chính của vị trí tuyển dụng.

    Raises:
        TypeError: Nếu job_description không phải str.
        ValueError: Nếu job_description rỗng.
        RuntimeError: Nếu xảy ra lỗi trong quá trình xử lý.
    """
    logger.info(
        "analyze_job_description - nhan input dai %d ky tu.",
        len(job_description) if isinstance(job_description, str) else -1,
    )
    try:
        _require_non_empty_str(job_description, "job_description")

        # TODO: Thay thế bằng logic thực (LLM call, keyword extraction...)
        word_count = len(job_description.split())
        result = (
            f"Da phan tich mo ta cong viec ({word_count} tu). "
            "Cac yeu cau chinh da duoc xac dinh (can tich hop logic thuc)."
        )

        logger.info("analyze_job_description - thanh cong.")
        return result

    except (TypeError, ValueError) as exc:
        logger.error("analyze_job_description - loi validation: %s", exc)
        raise
    except Exception as exc:
        logger.exception("analyze_job_description - loi khong mong muon.")
        raise RuntimeError(f"Loi khi phan tich JD: {exc}") from exc


# ---------------------------------------------------------------------------
# Tool 3 — score_candidate
# ---------------------------------------------------------------------------

PASS_THRESHOLD = 60  # Ngưỡng điểm để ứng viên được coi là phù hợp


def score_candidate(candidate_info: str, job_requirements: str) -> str:
    """
    Chấm điểm mức độ phù hợp của ứng viên.

    Args:
        candidate_info (str): Thông tin ứng viên.
        job_requirements (str): Yêu cầu của vị trí tuyển dụng.

    Returns:
        str: Điểm phù hợp và kết quả sàng lọc.

    Raises:
        TypeError: Nếu tham số không phải str.
        ValueError: Nếu tham số rỗng.
        RuntimeError: Nếu xảy ra lỗi trong quá trình xử lý.
    """
    logger.info(
        "score_candidate - candidate_info=%d ky tu, job_requirements=%d ky tu.",
        len(candidate_info) if isinstance(candidate_info, str) else -1,
        len(job_requirements) if isinstance(job_requirements, str) else -1,
    )
    try:
        _require_non_empty_str(candidate_info, "candidate_info")
        _require_non_empty_str(job_requirements, "job_requirements")

        # TODO: Thay thế bằng logic thực (cosine similarity, LLM scoring...)
        # Giả lập: tính tỉ lệ từ chung giữa candidate và requirements
        cand_words = set(candidate_info.lower().split())
        req_words = set(job_requirements.lower().split())
        common = cand_words & req_words
        score = min(100, int(len(common) / max(len(req_words), 1) * 100))

        verdict = "phu hop de phong van" if score >= PASS_THRESHOLD else "chua du tieu chuan"
        result = (
            f"Ung vien dat {score}/100 diem va {verdict}. "
            f"(Nguong pass: {PASS_THRESHOLD})"
        )

        logger.info("score_candidate - thanh cong: diem=%d.", score)
        return result

    except (TypeError, ValueError) as exc:
        logger.error("score_candidate - loi validation: %s", exc)
        raise
    except Exception as exc:
        logger.exception("score_candidate - loi khong mong muon.")
        raise RuntimeError(f"Loi khi cham diem ung vien: {exc}") from exc


# ---------------------------------------------------------------------------
# Tool 4 — rank_candidates
# ---------------------------------------------------------------------------

def rank_candidates(candidate_scores: str) -> str:
    """
    Xếp hạng các ứng viên theo điểm phù hợp.

    Format đầu vào mong đợi (mỗi dòng một ứng viên):
        Ten Ung Vien: diem_so
    Vi du:
        Nguyen Van A: 85
        Tran Thi B: 72
        Le Van C: 90

    Args:
        candidate_scores (str): Danh sách ứng viên và điểm số.

    Returns:
        str: Danh sách ứng viên đã được xếp hạng từ cao xuống thấp.

    Raises:
        TypeError: Nếu candidate_scores không phải str.
        ValueError: Nếu candidate_scores rỗng hoặc không parse được.
        RuntimeError: Nếu xảy ra lỗi trong quá trình xử lý.
    """
    logger.info(
        "rank_candidates - nhan input dai %d ky tu.",
        len(candidate_scores) if isinstance(candidate_scores, str) else -1,
    )
    try:
        _require_non_empty_str(candidate_scores, "candidate_scores")

        # Parse dữ liệu đầu vào theo định dạng "Ten: diem"
        candidates = []
        for line in candidate_scores.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            if ":" not in line:
                logger.warning("rank_candidates - bo qua dong khong hop le: '%s'", line)
                continue
            name, _, score_str = line.rpartition(":")
            try:
                score = float(score_str.strip())
            except ValueError:
                logger.warning(
                    "rank_candidates - khong parse duoc diem cho '%s', bo qua.", name.strip()
                )
                continue
            candidates.append((name.strip(), score))

        if not candidates:
            raise ValueError(
                "Khong tim thay du lieu ung vien hop le. "
                "Dinh dang moi dong: 'Ten ung vien: diem'"
            )

        # Sắp xếp giảm dần theo điểm; tie-breaking theo tên alphabet
        ranked = sorted(candidates, key=lambda x: (-x[1], x[0]))

        lines_out = [
            f"  #{i + 1}. {name} - {score:.1f} diem"
            for i, (name, score) in enumerate(ranked)
        ]
        result = "Ket qua xep hang ung vien:\n" + "\n".join(lines_out)

        logger.info("rank_candidates - thanh cong, xep hang %d ung vien.", len(ranked))
        return result

    except (TypeError, ValueError) as exc:
        logger.error("rank_candidates - loi validation: %s", exc)
        raise
    except Exception as exc:
        logger.exception("rank_candidates - loi khong mong muon.")
        raise RuntimeError(f"Loi khi xep hang ung vien: {exc}") from exc


# ---------------------------------------------------------------------------
# Tool 5 — schedule_interview
# ---------------------------------------------------------------------------

_DATE_FORMAT = "%Y-%m-%d"                               # ISO 8601: 2025-08-15
_TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")  # HH:MM (00:00-23:59)


def schedule_interview(
    candidate_name: str,
    interview_date: str,
    interview_time: str,
) -> str:
    """
    Tạo lịch phỏng vấn cho ứng viên.

    Args:
        candidate_name (str): Tên ứng viên (không được rỗng).
        interview_date (str): Ngày phỏng vấn — định dạng YYYY-MM-DD.
        interview_time (str): Giờ phỏng vấn — định dạng HH:MM (24h).

    Returns:
        str: Thông tin lịch phỏng vấn đã được xác nhận.

    Raises:
        TypeError: Nếu tham số không phải str.
        ValueError: Nếu ngày/giờ không hợp lệ hoặc đã qua.
        RuntimeError: Nếu xảy ra lỗi trong quá trình xử lý.
    """
    logger.info(
        "schedule_interview - candidate='%s', date='%s', time='%s'.",
        candidate_name, interview_date, interview_time,
    )
    try:
        _require_non_empty_str(candidate_name, "candidate_name")
        _require_non_empty_str(interview_date, "interview_date")
        _require_non_empty_str(interview_time, "interview_time")

        # Validate định dạng ngày
        try:
            parsed_date = datetime.strptime(interview_date.strip(), _DATE_FORMAT).date()
        except ValueError:
            raise ValueError(
                f"'interview_date' khong hop le: '{interview_date}'. "
                f"Dinh dang yeu cau: YYYY-MM-DD (vi du: 2025-08-15)."
            )

        # Ngày phải từ hôm nay trở đi
        today = datetime.now().date()
        if parsed_date < today:
            raise ValueError(
                f"'interview_date' ({interview_date}) la ngay trong qua khu. "
                f"Vui long chon ngay tu {today} tro di."
            )

        # Validate định dạng giờ HH:MM
        if not _TIME_PATTERN.match(interview_time.strip()):
            raise ValueError(
                f"'interview_time' khong hop le: '{interview_time}'. "
                "Dinh dang yeu cau: HH:MM (24h, vi du: 09:30 hoac 14:00)."
            )

        # TODO: Tích hợp Google Calendar / Outlook API để kiểm tra conflict lịch
        result = (
            f"Da dat lich phong van cho ung vien '{candidate_name}' "
            f"vao luc {interview_time.strip()}, "
            f"ngay {parsed_date.strftime('%d/%m/%Y')}."
        )

        logger.info("schedule_interview - thanh cong: %s", result)
        return result

    except (TypeError, ValueError) as exc:
        logger.error("schedule_interview - loi validation: %s", exc)
        raise
    except Exception as exc:
        logger.exception("schedule_interview - loi khong mong muon.")
        raise RuntimeError(f"Loi khi dat lich phong van: {exc}") from exc


# ---------------------------------------------------------------------------
# Tool Registry — đăng ký các tool để Agent sử dụng
# ---------------------------------------------------------------------------

AVAILABLE_TOOLS: dict = {
    "extract_cv_information": extract_cv_information,
    "analyze_job_description": analyze_job_description,
    "score_candidate": score_candidate,
    "rank_candidates": rank_candidates,
    "schedule_interview": schedule_interview,
}


def call_tool(tool_name: str, **kwargs) -> str:
    """
    Gọi một tool theo tên với fallback an toàn.

    Args:
        tool_name (str): Tên tool cần gọi (phải có trong AVAILABLE_TOOLS).
        **kwargs: Tham số truyền vào tool.

    Returns:
        str: Kết quả từ tool.

    Raises:
        KeyError: Nếu tool_name không tồn tại trong registry.
    """
    if tool_name not in AVAILABLE_TOOLS:
        available = ", ".join(f"'{t}'" for t in AVAILABLE_TOOLS)
        logger.error(
            "call_tool - tool '%s' khong ton tai. Cac tool hop le: %s",
            tool_name, available,
        )
        raise KeyError(
            f"Tool '{tool_name}' khong ton tai. "
            f"Cac tool hop le: {available}"
        )

    logger.info(
        "call_tool - goi tool '%s' voi tham so: %s", tool_name, list(kwargs.keys())
    )
    return AVAILABLE_TOOLS[tool_name](**kwargs)