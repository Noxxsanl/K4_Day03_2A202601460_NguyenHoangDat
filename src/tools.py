"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
"""
def extract_cv_information(cv_content: str) -> str:
    """
    Trích xuất thông tin ứng viên từ CV.

    Args:
        cv_content (str): Nội dung CV của ứng viên.

    Returns:
        str: Thông tin ứng viên được trích xuất.
    """
    return "Thông tin ứng viên đã được trích xuất từ CV."


def analyze_job_description(job_description: str) -> str:
    """
    Phân tích yêu cầu từ mô tả công việc.

    Args:
        job_description (str): Nội dung mô tả công việc.

    Returns:
        str: Các yêu cầu chính của vị trí tuyển dụng.
    """
    return "Đã phân tích yêu cầu của vị trí tuyển dụng."


def score_candidate(candidate_info: str, job_requirements: str) -> str:
    """
    Chấm điểm mức độ phù hợp của ứng viên.

    Args:
        candidate_info (str): Thông tin ứng viên.
        job_requirements (str): Yêu cầu của vị trí tuyển dụng.

    Returns:
        str: Điểm phù hợp và kết quả sàng lọc.
    """
    return "Ứng viên đạt 80/100 điểm và phù hợp để phỏng vấn."


def rank_candidates(candidate_scores: str) -> str:
    """
    Xếp hạng các ứng viên theo điểm phù hợp.

    Args:
        candidate_scores (str): Danh sách ứng viên và điểm số.

    Returns:
        str: Danh sách ứng viên đã được xếp hạng.
    """
    return "Đã xếp hạng danh sách ứng viên."


def schedule_interview(
    candidate_name: str,
    interview_date: str,
    interview_time: str,
) -> str:
    """
    Tạo lịch phỏng vấn cho ứng viên.

    Args:
        candidate_name (str): Tên ứng viên.
        interview_date (str): Ngày phỏng vấn.
        interview_time (str): Giờ phỏng vấn.

    Returns:
        str: Thông tin lịch phỏng vấn.
    """
    return (
        f"Đã đặt lịch phỏng vấn cho {candidate_name} "
        f"vào {interview_time}, ngày {interview_date}."
    )


# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "extract_cv_information": extract_cv_information,
    "analyze_job_description": analyze_job_description,
    "score_candidate": score_candidate,
    "rank_candidates": rank_candidates,
    "schedule_interview": schedule_interview,
}