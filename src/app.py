"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Developer / Integrator)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.

📍 TRẠNG THÁI HIỆN TẠI: MỐC 3 — REACT AGENT LOOP ĐÃ ĐƯỢC LẮP

Lộ trình lắp ráp của Role 4:
  - ✅ MỐC 1: Preflight check môi trường + kiểm tra tương thích Role 1/2/3.
  - ✅ MỐC 2: Nối hàm run_baseline_chatbot() ➔ Chatbot ĐÚNG 1 LLM call, 0 tool.
  - ✅ MỐC 3: Nối hàm run_react_agent()      ➔ Vòng lặp Thought -> Action -> Observation + Guardrails.
  - ⏳ MỐC 4: Cross-audit liên nhóm + Hybrid Flowchart.

Cách dùng:
    python src/app.py                        # Preflight check môi trường (mặc định)
    python src/app.py --live                 # Preflight + gọi thật 1 câu lên LLM để test API key

    python src/app.py --baseline --save      # MỐC 2: Chatbot baseline 5 case + ghi log Role 5
    python src/app.py --agent --save         # MỐC 3: ReAct Agent 5 case + ghi trace log Role 5
    python src/app.py --compare              # Chạy CẢ HAI rồi in bảng so sánh

    python src/app.py --agent --case 4       # Chỉ chạy test case số 4
    python src/app.py --agent --max-steps 6  # Nới phanh MAX_ITERATIONS để thử nghiệm
    python src/app.py --ask "câu hỏi..."     # Hỏi Agent 1 câu tự do (Cross-Audit Mốc 4)
    python src/app.py --agent --provider mock  # Chạy offline, không cần API key
"""

import argparse
import importlib
import inspect
import json
import logging
import os
import platform
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

MIN_PYTHON = (3, 10)

# Thư viện bắt buộc phải có để app import được (module_name -> tên gói pip)
REQUIRED_PACKAGES = {
    "dotenv": "python-dotenv",
    "requests": "requests",
}

# Thư viện chỉ cần khi dùng provider tương ứng (provider -> (module, tên gói pip))
PROVIDER_PACKAGES = {
    "gemini": ("google.genai", "google-genai"),
    "openai": ("openai", "openai"),
    "anthropic": ("anthropic", "anthropic"),
    "openrouter": ("requests", "requests"),
    "mock": (None, None),
}

# Tên biến API key tương ứng từng provider
PROVIDER_KEYS = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "mock": None,
}

OK, WARN, FAIL = "OK", "WARN", "FAIL"
ICONS = {OK: "✅", WARN: "⚠️ ", FAIL: "❌"}

# Kết quả các bước kiểm tra: list các dict {level, label, detail, hint}
RESULTS = []


def add(level: str, label: str, detail: str, hint: str = "") -> None:
    """Ghi lại kết quả một bước kiểm tra và in ngay ra màn hình."""
    RESULTS.append({"level": level, "label": label, "detail": detail, "hint": hint})
    print(f"  {ICONS[level]} {label}: {detail}")
    if hint and level != OK:
        print(f"      ↳ 🔧 Cách sửa: {hint}")


def section(title: str) -> None:
    print(f"\n{title}")
    print("-" * 78)


def safe_import(module_name: str):
    """Import module và trả về (module, error_message). Không bao giờ raise."""
    try:
        return importlib.import_module(module_name), None
    except Exception as e:  # noqa: BLE001 - cần bắt cả ImportError, SyntaxError của file bạn khác
        return None, f"{type(e).__name__}: {e}"


# =============================================================================
# 1. KIỂM TRA PYTHON & HỆ ĐIỀU HÀNH
# =============================================================================

def check_python() -> None:
    section("🐍 [1/6] PYTHON & HỆ ĐIỀU HÀNH")

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    if version[:2] >= MIN_PYTHON:
        add(OK, "Phiên bản Python", f"{version_str} (yêu cầu >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]})")
    else:
        add(
            FAIL,
            "Phiên bản Python",
            f"{version_str} quá cũ (yêu cầu >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]})",
            "Cài Python 3.10+ tại python.org rồi tạo lại virtual environment.",
        )

    add(OK, "Hệ điều hành", f"{platform.system()} {platform.release()}")

    # Đang chạy trong virtual environment hay python toàn hệ thống?
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if in_venv:
        add(OK, "Virtual environment", f"Đang chạy trong venv: {sys.prefix}")
    else:
        add(
            WARN,
            "Virtual environment",
            "Đang chạy bằng Python toàn hệ thống, không phải .venv",
            r"Chạy: .venv\Scripts\Activate.ps1  (PowerShell) rồi gõ lại python src/app.py",
        )

    add(OK, "Thư mục gốc dự án", str(BASE_DIR))


# =============================================================================
# 2. KIỂM TRA THƯ VIỆN
# =============================================================================

def check_packages() -> None:
    section("📦 [2/6] THƯ VIỆN PYTHON")

    for module_name, pip_name in REQUIRED_PACKAGES.items():
        mod, err = safe_import(module_name)
        if mod:
            add(OK, f"Thư viện {pip_name}", "Đã cài đặt")
        else:
            add(
                FAIL,
                f"Thư viện {pip_name}",
                f"Chưa cài được ({err})",
                "Chạy: python -m pip install -r requirements.txt",
            )


# =============================================================================
# 3. KIỂM TRA CẤU HÌNH .env & LLM PROVIDER
# =============================================================================

def check_env_config() -> str:
    section("🔑 [3/6] CẤU HÌNH .env & LLM PROVIDER")

    env_path = BASE_DIR / ".env"
    if env_path.exists():
        add(OK, "File .env", "Đã tồn tại")
        dotenv, _ = safe_import("dotenv")
        if dotenv:
            dotenv.load_dotenv(env_path)
    else:
        add(
            WARN,
            "File .env",
            "Chưa có (hệ thống sẽ tự chạy chế độ mock offline)",
            "Chạy: Copy-Item .env.example .env  rồi điền API key vào.",
        )

    provider_name = (os.getenv("LLM_PROVIDER") or "mock").lower().strip()
    add(OK, "LLM_PROVIDER", f"'{provider_name}'")

    # Kiểm tra API key của provider đang chọn
    key_var = PROVIDER_KEYS.get(provider_name)
    if key_var:
        key_value = (os.getenv(key_var) or "").strip()
        placeholder = key_value.startswith("your_") or not key_value
        if placeholder:
            add(
                WARN,
                f"API key {key_var}",
                "Chưa điền (vẫn còn giá trị mẫu) ➔ chưa gọi được LLM thật",
                f"Mở file .env, dán key thật vào {key_var}=... "
                f"(Mốc 1 chưa cần key, nhưng Mốc 2 cần để thấy Chatbot ảo giác).",
            )
        else:
            add(OK, f"API key {key_var}", f"Đã điền ({len(key_value)} ký tự)")
    else:
        add(
            WARN,
            "API key",
            "Đang dùng provider 'mock' — không gọi LLM thật, chạy offline",
            "Đổi LLM_PROVIDER trong .env sang gemini/openai/anthropic/openrouter khi có key.",
        )

    # Kiểm tra SDK tương ứng provider đã được cài chưa
    module_name, pip_name = PROVIDER_PACKAGES.get(provider_name, (None, None))
    if module_name:
        mod, err = safe_import(module_name)
        if mod:
            add(OK, f"SDK cho '{provider_name}'", f"{pip_name} đã cài đặt")
        else:
            add(
                FAIL,
                f"SDK cho '{provider_name}'",
                f"Thiếu gói {pip_name} ({err})",
                f"Chạy: python -m pip install {pip_name}",
            )

    model = (os.getenv("LLM_MODEL") or "").strip()
    add(OK, "LLM_MODEL", model or "(để trống ➔ dùng model mặc định của provider)")

    return provider_name


# =============================================================================
# 4. KIỂM TRA config/test_cases.json (Role 1)
# =============================================================================

def check_test_cases() -> list:
    section("🟢 [4/6] BỘ TEST CASES — config/test_cases.json (Role 1)")

    path = BASE_DIR / "config" / "test_cases.json"
    if not path.exists():
        add(FAIL, "File test_cases.json", f"Không tìm thấy tại {path}",
            "Role 1 cần tạo file config/test_cases.json rồi git push.")
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            cases = json.load(f)
    except json.JSONDecodeError as e:
        add(FAIL, "Cú pháp JSON", f"File bị lỗi JSON: {e}",
            "Kiểm tra dấu phẩy / ngoặc trong config/test_cases.json (dùng jsonlint hoặc VS Code).")
        return []

    add(OK, "Đọc file JSON", f"Thành công, có {len(cases)} test case")

    # Kiểm tra từng case có đủ field cần thiết cho vòng chạy Mốc 2 & 3
    required_fields = ("id", "category", "question")
    problems = [
        f"case #{i + 1} thiếu field {[f for f in required_fields if f not in c]}"
        for i, c in enumerate(cases)
        if not all(f in c for f in required_fields)
    ]
    if problems:
        add(WARN, "Cấu trúc test case", "; ".join(problems),
            "Mỗi case cần tối thiểu: id, category, question.")
    else:
        add(OK, "Cấu trúc test case", f"Đủ field {required_fields} cho cả {len(cases)} case")

    if len(cases) < 5:
        add(WARN, "Số lượng test case", f"Chỉ có {len(cases)}/5 case tối thiểu",
            "Rubric yêu cầu >= 5 case: 2 đơn giản + multi-step + cần 2 tool + edge case.")
    else:
        add(OK, "Số lượng test case", f"{len(cases)} case (>= 5 theo rubric)")

    for c in cases:
        print(f"      #{c.get('id', '?')} [{c.get('category', 'chưa phân loại')}] {c.get('question', '')[:60]}")

    return cases


# =============================================================================
# 5. KIỂM TRA src/tools.py (Role 2)
# =============================================================================

def check_tools():
    section("🛠️ [5/6] TOOL REGISTRY — src/tools.py (Role 2)")

    tools_mod, err = safe_import("tools")
    if not tools_mod:
        add(FAIL, "Import src/tools.py", f"Không import được ({err})",
            "Mở src/tools.py xem lỗi cú pháp, hoặc chờ Role 2 git push bản mới.")
        return None

    add(OK, "Import src/tools.py", "Thành công")

    registry = getattr(tools_mod, "AVAILABLE_TOOLS", None)
    if not isinstance(registry, dict) or not registry:
        add(FAIL, "Dictionary AVAILABLE_TOOLS", "Không tồn tại hoặc đang rỗng",
            "Role 2 cần khai báo AVAILABLE_TOOLS = {'ten_tool': ham_tool, ...} ở cuối src/tools.py.")
        return tools_mod

    add(OK, "Dictionary AVAILABLE_TOOLS", f"Đã đăng ký {len(registry)} tool")

    # Liệt kê signature + docstring của từng tool để cả nhóm biết gọi thế nào
    no_doc = []
    for name, fn in registry.items():
        if not callable(fn):
            add(FAIL, f"Tool '{name}'", "Giá trị trong registry không phải là hàm gọi được",
                "Kiểm tra lại AVAILABLE_TOOLS: value phải là tên hàm, không có dấu ngoặc ().")
            continue
        try:
            sig = str(inspect.signature(fn))
        except (TypeError, ValueError):
            sig = "(không đọc được signature)"
        doc = (inspect.getdoc(fn) or "").strip().splitlines()
        summary = doc[0] if doc else ""
        if not summary:
            no_doc.append(name)
        print(f"      • {name}{sig} — {summary or '⚠️ CHƯA CÓ DOCSTRING'}")

    if no_doc:
        add(WARN, "Docstring của tool", f"{len(no_doc)} tool chưa có docstring: {', '.join(no_doc)}",
            "Rubric chấm 'Tool description rõ ràng' ➔ Role 2 bổ sung docstring input/output/error.")
    else:
        add(OK, "Docstring của tool", "Tất cả tool đều có mô tả")

    # 🔍 LINT HỢP ĐỒNG TOOL: tool phải TRẢ VỀ chuỗi lỗi, KHÔNG được raise làm crash Agent
    logging.getLogger("tools").setLevel(logging.CRITICAL)  # tạm tắt log ồn khi thử input sai
    raising = []
    for name, fn in registry.items():
        if not callable(fn):
            continue
        try:
            params = [
                p for p in inspect.signature(fn).parameters.values()
                if p.default is inspect.Parameter.empty
                and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
            ]
            fn(*[""] * len(params))  # gọi với tham số rỗng - kịch bản người dùng nhập sai
        except Exception as e:  # noqa: BLE001
            raising.append(f"{name} ➔ raise {type(e).__name__}")
    logging.getLogger("tools").setLevel(logging.INFO)

    if raising:
        add(
            WARN,
            "Hợp đồng xử lý lỗi (error contract)",
            f"{len(raising)}/{len(registry)} tool RAISE EXCEPTION khi input sai: {'; '.join(raising)}",
            "CODELAB yêu cầu tool trả về chuỗi 'LỖI: ...' thay vì raise, để Agent đọc và tự đổi hướng "
            "(nếu raise, Role 4 buộc phải bọc try/except trong app.py ở Mốc 3).",
        )
    else:
        add(OK, "Hợp đồng xử lý lỗi (error contract)", "Mọi tool trả về chuỗi lỗi, không raise")

    if callable(getattr(tools_mod, "call_tool", None)):
        add(OK, "Hàm call_tool()", "Có sẵn — Role 4 sẽ dùng để dispatch tool ở Mốc 3")

    return tools_mod


# =============================================================================
# 6. KIỂM TRA src/prompts.py (Role 3) + ĐỘ KHỚP VỚI TOOL
# =============================================================================

def check_prompts(tools_mod) -> None:
    section("🧠 [6/6] PROMPTS & GUARDRAILS — src/prompts.py (Role 3)")

    prompts_mod, err = safe_import("prompts")
    if not prompts_mod:
        add(FAIL, "Import src/prompts.py", f"Không import được ({err})",
            "Mở src/prompts.py xem lỗi cú pháp, hoặc chờ Role 3 git push bản mới.")
        return

    add(OK, "Import src/prompts.py", "Thành công")

    for var in ("CHATBOT_BASELINE_PROMPT", "REACT_SYSTEM_PROMPT"):
        value = getattr(prompts_mod, var, None)
        if isinstance(value, str) and value.strip():
            add(OK, f"Biến {var}", f"Đã có ({len(value)} ký tự)")
        else:
            add(FAIL, f"Biến {var}", "Chưa khai báo hoặc đang rỗng",
                f"Role 3 cần soạn {var} trong src/prompts.py.")

    max_iter = getattr(prompts_mod, "MAX_ITERATIONS", None)
    if isinstance(max_iter, int) and max_iter > 0:
        add(OK, "Guardrail MAX_ITERATIONS", f"{max_iter} vòng lặp (phanh an toàn đã cài)")
    else:
        add(FAIL, "Guardrail MAX_ITERATIONS", "Chưa khai báo hoặc giá trị không hợp lệ",
            "Role 3 cần đặt MAX_ITERATIONS = 5 (số nguyên > 0) trong src/prompts.py.")

    # 🔍 KIỂM TRA ĐỘ KHỚP (DRIFT) GIỮA PROMPT VÀ TOOL REGISTRY
    # Đây là lỗi tích hợp kinh điển: Role 2 đổi tên tool nhưng prompt của Role 3 vẫn ghi tên cũ
    # ➔ Agent sẽ gọi tool không tồn tại và fail 100% ở Mốc 3.
    react_prompt = getattr(prompts_mod, "REACT_SYSTEM_PROMPT", "") or ""
    registry = getattr(tools_mod, "AVAILABLE_TOOLS", {}) if tools_mod else {}
    if react_prompt and registry:
        missing = [name for name in registry if name not in react_prompt]
        if missing:
            add(
                WARN,
                "Độ khớp Prompt ↔ Tool",
                f"{len(missing)}/{len(registry)} tool CHƯA được mô tả trong REACT_SYSTEM_PROMPT: "
                f"{', '.join(missing)}",
                "Role 3 cập nhật danh sách tool trong REACT_SYSTEM_PROMPT cho khớp AVAILABLE_TOOLS "
                "(mẹo: import TOOLS_DESCRIPTION từ tools.py để không bao giờ bị lệch). "
                "BẮT BUỘC xong trước Mốc 3.",
            )
        else:
            add(OK, "Độ khớp Prompt ↔ Tool", "Prompt đã mô tả đủ tên các tool trong registry")


# =============================================================================
# 7. SMOKE TEST PIPELINE PROVIDER
# =============================================================================

def check_provider_pipeline(provider_name: str, live: bool):
    section("🔌 SMOKE TEST — src/providers.py (Multi-Provider Adapter)")

    providers_mod, err = safe_import("providers")
    if not providers_mod:
        add(FAIL, "Import src/providers.py", f"Không import được ({err})",
            "Thường do thiếu thư viện ➔ chạy python -m pip install -r requirements.txt")
        return None

    add(OK, "Import src/providers.py", "Thành công")

    try:
        provider = providers_mod.get_llm_provider()
    except Exception as e:  # noqa: BLE001
        add(FAIL, "Khởi tạo provider", f"{type(e).__name__}: {e}",
            "Kiểm tra lại LLM_PROVIDER trong .env.")
        return None

    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    add(OK, "Khởi tạo provider", f"{provider.__class__.__name__} (model: {model_name})")

    is_mock = provider.__class__.__name__ == "MockProvider"
    if is_mock or live:
        try:
            answer = provider.generate("Xin chào, đây là bài test kết nối. Trả lời ngắn gọn.")
            preview = " ".join(str(answer).split())[:120]
            failed = str(answer).startswith("[") and "Error" in str(answer)
            add(
                WARN if failed else OK,
                "Gọi thử LLM",
                preview,
                "Provider trả về lỗi ➔ kiểm tra API key và tên model trong .env." if failed else "",
            )
        except Exception as e:  # noqa: BLE001
            add(FAIL, "Gọi thử LLM", f"{type(e).__name__}: {e}",
                "Kiểm tra mạng, API key và tên model.")
    else:
        add(OK, "Gọi thử LLM", "Bỏ qua để không tốn quota (thêm cờ --live nếu muốn gọi thật)")

    return provider


# =============================================================================
# 📋 TỔNG KẾT
# =============================================================================

def print_summary() -> int:
    fails = [r for r in RESULTS if r["level"] == FAIL]
    warns = [r for r in RESULTS if r["level"] == WARN]

    print("\n" + "=" * 78)
    print("📋 TỔNG KẾT PREFLIGHT CHECK (MỐC 1)")
    print("=" * 78)
    print(f"  ✅ Đạt: {len(RESULTS) - len(fails) - len(warns)}   ⚠️  Cảnh báo: {len(warns)}   ❌ Lỗi chặn: {len(fails)}")

    if fails:
        print("\n❌ MÔI TRƯỜNG CHƯA SẴN SÀNG — cần xử lý các lỗi chặn sau:")
        for i, r in enumerate(fails, 1):
            print(f"  {i}. [{r['label']}] {r['detail']}")
            if r["hint"]:
                print(f"     ➔ {r['hint']}")
    else:
        print("\n✅ MÔI TRƯỜNG SẴN SÀNG — `python src/app.py` chạy được, không có lỗi chặn.")

    if warns:
        print("\n⚠️  VIỆC CẦN LÀM TIẾP (không chặn Mốc 1, nhưng phải xong trước Mốc 2/3):")
        for i, r in enumerate(warns, 1):
            print(f"  {i}. [{r['label']}] {r['detail']}")
            if r["hint"]:
                print(f"     ➔ {r['hint']}")

    print("\n🗺️  LỘ TRÌNH LẮP RÁP CỦA ROLE 4:")
    print("  ✅ Mốc 1: Preflight check môi trường (file này) — ĐANG Ở ĐÂY")
    print("  ⏳ Mốc 2: git pull ➔ nối run_baseline_chatbot() chạy 1 LLM call, 0 tool")
    print("  ⏳ Mốc 3: git pull ➔ nối run_react_agent() với parser + executor + MAX_ITERATIONS")
    print("  ⏳ Mốc 4: Cross-audit liên nhóm + Hybrid Flowchart")
    print("=" * 78)

    return 1 if fails else 0


# =============================================================================
# 🤖 MỐC 2 — CHATBOT BASELINE (Cấp độ 2: LLM thuần, KHÔNG có Tool)
# =============================================================================

def _looks_like_provider_error(text: str) -> bool:
    """Nhận diện chuỗi lỗi do provider trả về (VD: '[Gemini Error]: Chưa cấu hình...')."""
    head = str(text).lstrip()[:40]
    return head.startswith("[") and ("Error" in head or "Exception" in head)


def _guess_output_type(answer: str) -> str:
    """
    Gợi ý phân loại output theo CODELAB: safe fallback / có thể hallucinated.
    ⚠️ Chỉ là GỢI Ý bằng từ khóa — Role 5 vẫn phải đọc và chấm lại bằng mắt.
    """
    text = str(answer).lower()
    fallback_signals = (
        "không có quyền truy cập", "không thể truy cập", "không có dữ liệu",
        "không tra cứu được", "tôi không chắc", "vui lòng sử dụng hệ thống",
        "chatbot cơ bản", "không có khả năng tra cứu",
    )
    if any(sig in text for sig in fallback_signals):
        return "🟡 safe fallback (bot tự nhận không có dữ liệu)"
    return "⚪ cần Role 5 chấm tay (correct / hallucinated?)"


def run_baseline_chatbot(user_query: str, provider, system_prompt: str = None, verbose: bool = True) -> dict:
    """
    [MỐC 2] Chatbot baseline (Cấp độ 2) — đường cơ sở để so sánh với ReAct Agent.

    Protocol bắt buộc theo CODELAB:
        system prompt + user message  ➔  ĐÚNG 1 LLM call  ➔  final response

    Ràng buộc (đây là điều làm nó trở thành "baseline công bằng"):
        - KHÔNG gọi bất kỳ tool nào       ➔ tool_calls luôn = 0
        - KHÔNG nhúng sẵn kết quả tool vào prompt
        - KHÔNG lặp nhiều lượt suy luận   ➔ llm_calls luôn = 1

    Returns:
        dict: {question, answer, tool_calls, llm_calls, elapsed, provider, model, is_error, output_type}
              ➔ Role 5 dùng dict này để lập bảng so sánh trong docs/trace_eval.md
    """
    # Lấy prompt của Role 3 (import mềm để app không chết nếu prompts.py đang lỗi)
    if system_prompt is None:
        prompts_mod, err = safe_import("prompts")
        if not prompts_mod or not getattr(prompts_mod, "CHATBOT_BASELINE_PROMPT", None):
            print(f"❌ Không lấy được CHATBOT_BASELINE_PROMPT từ src/prompts.py ({err or 'biến rỗng'})")
            return {}
        system_prompt = prompts_mod.CHATBOT_BASELINE_PROMPT

    if verbose:
        print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
        print(f"⚙️  System Prompt: {len(system_prompt)} ký tự | 🛠️ Số tool được cấp: 0")

    # ⬇️ ĐÚNG 1 LẦN GỌI LLM DUY NHẤT — không vòng lặp, không tool
    start = time.perf_counter()
    answer = provider.generate(user_query, system_prompt=system_prompt)
    elapsed = time.perf_counter() - start

    is_error = _looks_like_provider_error(answer)
    result = {
        "question": user_query,
        "answer": str(answer).strip(),
        "tool_calls": 0,      # ⬅️ Bằng chứng baseline: không hề gọi tool
        "llm_calls": 1,
        "elapsed": round(elapsed, 2),
        "provider": provider.__class__.__name__,
        "model": getattr(provider, "model_name", "mock"),
        "is_error": is_error,
        "output_type": "❌ lỗi provider" if is_error else _guess_output_type(answer),
    }

    if verbose:
        icon = "❌" if is_error else "🤖"
        print(f"{icon} Chatbot trả lời ({result['elapsed']}s):")
        for line in result["answer"].splitlines():
            print(f"    {line}")
        print(f"📊 Thống kê: llm_calls=1 | tool_calls=0 | phân loại: {result['output_type']}")

    return result


def run_baseline_suite(provider, cases: list, save: bool = False) -> list:
    """Chạy Chatbot baseline trên toàn bộ test case của Role 1 và in bảng tổng kết."""
    prompts_mod, err = safe_import("prompts")
    if not prompts_mod or not getattr(prompts_mod, "CHATBOT_BASELINE_PROMPT", None):
        print(f"❌ Không lấy được CHATBOT_BASELINE_PROMPT từ src/prompts.py ({err or 'biến rỗng'})")
        return []
    system_prompt = prompts_mod.CHATBOT_BASELINE_PROMPT

    print("=" * 78)
    print("🤖 MỐC 2 — CHẠY CHATBOT BASELINE (Cấp độ 2: LLM thuần, KHÔNG có Tool)")
    print(f"🔌 Provider: {provider.__class__.__name__} "
          f"(model: {getattr(provider, 'model_name', 'mock')}) | 📋 Số test case: {len(cases)}")
    print("=" * 78)

    results = []
    for case in cases:
        print(f"\n{'─' * 78}")
        print(f"🧪 TEST CASE #{case.get('id', '?')} — {case.get('category', '')}")
        print(f"{'─' * 78}")
        res = run_baseline_chatbot(case["question"], provider, system_prompt=system_prompt)
        if res:
            res["id"] = case.get("id")
            res["category"] = case.get("category", "")
            res["expected_behavior"] = case.get("expected_behavior", "")
            results.append(res)

    # 📊 Bảng tổng kết
    print("\n" + "=" * 78)
    print("📊 TỔNG KẾT CHATBOT BASELINE")
    print("=" * 78)
    print(f"{'#':<3} {'Loại câu hỏi':<34} {'LLM':<5} {'Tool':<5} {'Giây':<6} Phân loại output")
    print("-" * 78)
    for r in results:
        print(f"{r['id']:<3} {r['category'][:33]:<34} {r['llm_calls']:<5} "
              f"{r['tool_calls']:<5} {r['elapsed']:<6} {r['output_type']}")

    errors = [r for r in results if r["is_error"]]
    print("-" * 78)
    print(f"✅ Bằng chứng baseline công bằng: tổng tool_calls = "
          f"{sum(r['tool_calls'] for r in results)} (phải = 0) | "
          f"tổng llm_calls = {sum(r['llm_calls'] for r in results)} (= 1 mỗi case)")

    if errors:
        print(f"\n⚠️  {len(errors)}/{len(results)} case KHÔNG có câu trả lời thật vì provider báo lỗi.")
        print("    ➔ Đây là lỗi cấu hình API key, KHÔNG phải lỗi code. Cách xử lý:")
        print("      1. Lấy API key miễn phí tại https://aistudio.google.com/apikey")
        print("      2. Dán vào file .env:  GEMINI_API_KEY=AIza...")
        print("      3. Chạy lại:  python src/app.py --baseline --save")
        print("    ➔ Hoặc chạy offline để kiểm tra đường ống: python src/app.py --baseline --provider mock")
    else:
        print("\n👉 Việc của Role 5: đọc từng câu trả lời ở trên, phân loại thành "
              "correct / safe fallback / hallucinated rồi dán vào docs/trace_eval.md.")

    if save and results:
        save_baseline_log(results, provider)

    return results


def save_baseline_log(results: list, provider) -> None:
    """Ghi log thô ra docs/baseline_raw_log.md để Role 5 copy vào docs/trace_eval.md."""
    out_path = BASE_DIR / "docs" / "baseline_raw_log.md"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# 📝 LOG THÔ — CHATBOT BASELINE (Mốc 2)",
        "",
        f"> File này do `python src/app.py --baseline --save` sinh tự động lúc {stamp}.",
        f"> Provider: `{provider.__class__.__name__}` — model: `{getattr(provider, 'model_name', 'mock')}`.",
        "> 👉 Role 5 copy nội dung cần dùng sang `docs/trace_eval.md` rồi chấm điểm.",
        "",
        "| # | Loại câu hỏi | LLM calls | Tool calls | Thời gian | Gợi ý phân loại |",
        "| :--- | :--- | :---: | :---: | :---: | :--- |",
    ]
    for r in results:
        lines.append(
            f"| {r['id']} | {r['category']} | {r['llm_calls']} | {r['tool_calls']} "
            f"| {r['elapsed']}s | {r['output_type']} |"
        )
    lines.append("")

    for r in results:
        lines += [
            f"## Test case #{r['id']} — {r['category']}",
            "",
            f"**Câu hỏi**: {r['question']}",
            "",
            f"**Kỳ vọng (Role 1)**: {r['expected_behavior']}",
            "",
            "**Chatbot baseline trả lời**:",
            "",
            "```text",
            r["answer"],
            "```",
            "",
            f"**Thống kê**: `llm_calls = {r['llm_calls']}` · `tool_calls = {r['tool_calls']}` "
            f"· `{r['elapsed']}s` · gợi ý phân loại: {r['output_type']}",
            "",
            "---",
            "",
        ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n💾 Đã ghi log thô cho Role 5: {out_path}")


# =============================================================================
# 🧠 MỐC 3 — REACT AGENT LOOP (Cấp độ 3: Thought -> Action -> Observation)
# =============================================================================
#
# 4 NGUYÊN TẮC BẤT BIẾN được cài đặt ở đây:
#   1. Không lặp vô hạn        ➔ phanh cứng MAX_ITERATIONS của Role 3.
#   2. Mỗi Action ➔ đúng 1 Observation do APP chèn từ tool thật.
#      LLM tự viết "Observation:" sẽ bị CẮT BỎ (_strip_hallucinated_observation).
#   3. Observation quay lại prompt làm ngữ cảnh cho Thought kế tiếp (scratchpad).
#   4. Không khẳng định khi thiếu bằng chứng ➔ chạm phanh thì trả Safe Fallback.
# =============================================================================

# Bắt "Action: ten_tool[...]" hoặc "Action: ten_tool(...)" — DOTALL vì tham số
# (nội dung CV, JD) có thể trải dài nhiều dòng.
ACTION_RE = re.compile(
    r"Action\s*:\s*\**\s*([A-Za-z_]\w*)\s*\**\s*[\[\(](.*?)[\]\)]\s*(?:\n|$)",
    re.DOTALL,
)
FINAL_ANSWER_RE = re.compile(r"Final\s*Answer\s*:\s*(.*)", re.DOTALL | re.IGNORECASE)
THOUGHT_RE = re.compile(r"Thought\s*:\s*(.*)")
OBSERVATION_RE = re.compile(r"^\s*\**\s*Observation\s*\**\s*:", re.IGNORECASE | re.MULTILINE)


def _strip_hallucinated_observation(text: str):
    """
    🛡️ NGUYÊN TẮC 2: LLM KHÔNG được tự bịa Observation.
    Cắt bỏ mọi thứ từ chỗ LLM tự viết "Observation:" trở đi — chỉ app mới có quyền
    chèn Observation, và chỉ chèn kết quả THẬT từ tool.

    Returns: (text_đã_cắt, có_bịa_hay_không)
    """
    match = OBSERVATION_RE.search(text or "")
    if match:
        return text[: match.start()].rstrip(), True
    return (text or "").strip(), False


def _split_action_args(raw: str) -> list:
    """
    Tách tham số trong Action: tool["a, b", "c"] ➔ ['a, b', 'c'].

    Ưu tiên lấy các chuỗi trong dấu nháy — vì tham số của bài này (nội dung CV,
    yêu cầu tuyển dụng) BẢN THÂN NÓ chứa dấu phẩy, tách bừa theo dấu phẩy sẽ sai.
    """
    raw = (raw or "").strip()
    if not raw:
        return []

    quoted = re.findall(r'"([^"]*)"|\'([^\']*)\'', raw, re.DOTALL)
    if quoted:
        return [(a or b).strip() for a, b in quoted]

    # Không có dấu nháy ➔ đành tách theo dấu phẩy
    return [part.strip() for part in raw.split(",") if part.strip()]


def parse_llm_step(text: str) -> dict:
    """
    Bóc tách phản hồi thô của LLM thành 1 bước ReAct.

    Returns dict:
        kind      : 'final' | 'action' | 'malformed' | 'none'
        thought   : nội dung dòng Thought (nếu có)
        answer    : nội dung Final Answer (khi kind='final')
        tool/args : tên tool và list tham số (khi kind='action')
    """
    thought_match = THOUGHT_RE.search(text)
    thought = thought_match.group(1).strip() if thought_match else ""

    final_match = FINAL_ANSWER_RE.search(text)
    action_match = ACTION_RE.search(text)

    # Nếu có cả hai, ưu tiên cái xuất hiện TRƯỚC trong phản hồi
    if final_match and (not action_match or final_match.start() < action_match.start()):
        return {"kind": "final", "thought": thought, "answer": final_match.group(1).strip()}

    if action_match:
        return {
            "kind": "action",
            "thought": thought,
            "tool": action_match.group(1).strip(),
            "args": _split_action_args(action_match.group(2)),
        }

    # Có chữ "Action:" nhưng không parse được ➔ sai cú pháp
    if re.search(r"Action\s*:", text, re.IGNORECASE):
        bad_line = next(
            (ln.strip() for ln in text.splitlines() if re.search(r"Action\s*:", ln, re.IGNORECASE)),
            text.strip()[:80],
        )
        return {"kind": "malformed", "thought": thought, "raw": bad_line}

    return {"kind": "none", "thought": thought, "raw": text.strip()[:120]}


def execute_tool_call(tools_mod, tool_name: str, args: list) -> str:
    """
    🛠️ EXECUTOR: gọi tool THẬT và luôn trả về chuỗi Observation, không bao giờ crash.

    Ánh xạ tham số theo VỊ TRÍ sang tên tham số của hàm, rồi dispatch qua
    call_tool() của Role 2 (nếu có) để tôn trọng thiết kế registry của bạn ấy.
    """
    registry = getattr(tools_mod, "AVAILABLE_TOOLS", {}) or {}

    # ❌ Tool không tồn tại ➔ trả về danh sách tool hợp lệ để Agent tự sửa
    if tool_name not in registry:
        return (
            f"Lỗi: Tool '{tool_name}' không tồn tại. "
            f"Các tool hợp lệ gồm: {', '.join(registry.keys())}. "
            f"Hãy chọn lại một tool trong danh sách này."
        )

    fn = registry[tool_name]
    try:
        param_names = [
            p.name for p in inspect.signature(fn).parameters.values()
            if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
        ]
    except (TypeError, ValueError):
        param_names = []

    # ❌ Sai số lượng tham số ➔ trả về hướng dẫn cú pháp đúng
    if len(args) != len(param_names):
        mau = ", ".join(f'"<{p}>"' for p in param_names)
        return (
            f"Lỗi: Tool '{tool_name}' cần {len(param_names)} tham số "
            f"({', '.join(param_names)}), nhưng bạn truyền {len(args)}. "
            f'Cú pháp đúng: Action: {tool_name}[{mau}]'
        )

    kwargs = dict(zip(param_names, args))
    try:
        caller = getattr(tools_mod, "call_tool", None)
        if callable(caller):
            return str(caller(tool_name, **kwargs))
        return str(fn(**kwargs))
    except Exception as e:  # noqa: BLE001 - lưới an toàn cuối, tool không được phép giết Agent
        return f"Lỗi khi chạy tool '{tool_name}': {type(e).__name__}: {e}"


def _shorten(text: str, limit: int = 300) -> str:
    """Rút gọn chuỗi dài khi in ra màn hình (scratchpad vẫn giữ bản đầy đủ)."""
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit] + " […]"


def run_react_agent(user_query: str, provider, max_steps: int = None, verbose: bool = True) -> dict:
    """
    [MỐC 3] Vòng lặp ReAct hoàn chỉnh.

    Mỗi vòng:
        1. Gửi (system prompt + Question + scratchpad) lên LLM
        2. Cắt bỏ Observation nếu LLM tự bịa
        3. Parse ra Thought / Action / Final Answer
        4. Nếu là Action ➔ APP gọi tool thật ➔ lấy Observation
        5. Nối Thought + Action + Observation vào scratchpad ➔ quay lại bước 1

    Dừng khi: có Final Answer, hoặc chạm phanh MAX_ITERATIONS (➔ Safe Fallback).
    """
    prompts_mod, err1 = safe_import("prompts")
    tools_mod, err2 = safe_import("tools")
    if not prompts_mod or not tools_mod:
        print(f"❌ Thiếu module: prompts({err1}) tools({err2})")
        return {}

    system_prompt = getattr(prompts_mod, "REACT_SYSTEM_PROMPT", "")
    max_steps = max_steps or getattr(prompts_mod, "MAX_ITERATIONS", 5)

    scratchpad = ""          # 🧠 Bộ nhớ vòng lặp: Thought + Action + Observation các bước trước
    trace = []               # 📊 Log có cấu trúc cho Role 5
    seen_actions = {}        # 🔁 Phát hiện lặp lại đúng 1 Action với đúng tham số
    llm_calls = tool_calls = faked_obs = 0
    tools_used, final_answer, terminated_by, last_error = [], None, None, None

    if verbose:
        print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
        print(f"⚙️  System Prompt: {len(system_prompt)} ký tự | "
              f"🛠️ Tool được cấp: {len(getattr(tools_mod, 'AVAILABLE_TOOLS', {}))} | "
              f"🛡️ MAX_ITERATIONS = {max_steps}")

    start = time.perf_counter()
    step = 0
    while step < max_steps:
        step += 1
        if verbose:
            print(f"\n  ┌─ 🔄 Vòng lặp ReAct — Step {step}/{max_steps} " + "─" * 34)

        # ── 1. Gọi LLM với toàn bộ ngữ cảnh đã tích lũy ──────────────────────
        prompt = f"Question: {user_query}\n\n{scratchpad}"
        raw = provider.generate(prompt, system_prompt=system_prompt)
        llm_calls += 1

        if _looks_like_provider_error(raw):
            terminated_by = "provider_error"
            last_error = str(raw)
            if verbose:
                print(f"  │ ❌ Provider lỗi: {_shorten(raw, 200)}")
            break

        # ── 2. Chặn LLM tự bịa Observation ──────────────────────────────────
        text, faked = _strip_hallucinated_observation(raw)
        if faked:
            faked_obs += 1
            if verbose:
                print("  │ ⚠️  LLM tự bịa 'Observation:' ➔ đã CẮT BỎ (chỉ app được chèn Observation)")

        # ── 3. Parse bước ReAct ─────────────────────────────────────────────
        parsed = parse_llm_step(text)
        if verbose and parsed.get("thought"):
            print(f"  │ 🧠 Thought: {_shorten(parsed['thought'], 220)}")

        # ── 4a. Kết thúc: có Final Answer ───────────────────────────────────
        if parsed["kind"] == "final":
            final_answer = parsed["answer"]
            terminated_by = "final_answer"
            trace.append({"step": step, "thought": parsed.get("thought", ""),
                          "action": None, "observation": None, "final": final_answer})
            if verbose:
                print(f"  │ 🏁 Final Answer: {_shorten(final_answer, 400)}")
                print("  └" + "─" * 74)
            break

        # ── 4b. Xác định Observation cho bước này ───────────────────────────
        action_label = None
        if parsed["kind"] == "action":
            tool_name, args = parsed["tool"], parsed["args"]
            action_label = f"{tool_name}[{', '.join(repr(a) for a in args)}]"
            if verbose:
                print(f"  │ 🛠️ Action: {_shorten(action_label, 220)}")

            key = (tool_name, tuple(args))
            if key in seen_actions:
                # 🔁 Tự phục hồi: chặn Agent lặp lại y hệt hành động đã làm
                observation = (
                    f"Lỗi lặp hành động: Bạn đã gọi {tool_name} với đúng tham số này ở bước trước "
                    f"và nhận kết quả: \"{_shorten(seen_actions[key], 150)}\". "
                    f"Tool cho kết quả cố định nên gọi lại cũng không đổi. "
                    f"Hãy đổi tham số, đổi tool, hoặc trả về Final Answer."
                )
                last_error = observation
                if verbose:
                    print("  │ 🔁 Phát hiện LẶP hành động ➔ chèn cảnh báo thay vì gọi lại tool")
            else:
                observation = execute_tool_call(tools_mod, tool_name, args)
                tool_calls += 1
                seen_actions[key] = observation
                if tool_name not in tools_used:
                    tools_used.append(tool_name)
                if observation.strip().lower().startswith("lỗi"):
                    last_error = observation

        elif parsed["kind"] == "malformed":
            observation = (
                f"Lỗi cú pháp Action: không đọc được dòng '{parsed['raw']}'. "
                f'Cú pháp đúng là: Action: tên_tool["tham_số_1", "tham_số_2"] '
                f"— nhớ đủ dấu ngoặc vuông và dấu nháy kép."
            )
            last_error = observation
            if verbose:
                print(f"  │ ❌ Action sai cú pháp: {parsed['raw']}")

        else:  # kind == 'none'
            observation = (
                "Lỗi định dạng: Phản hồi của bạn không có dòng 'Action:' cũng không có "
                "'Final Answer:'. Hãy trả lời lại đúng định dạng: Thought: ... rồi "
                'Action: tên_tool["tham_số"] hoặc Final Answer: ...'
            )
            last_error = observation
            if verbose:
                print("  │ ❌ Không tìm thấy Action lẫn Final Answer trong phản hồi")

        if verbose:
            icon = "❌" if observation.strip().lower().startswith("lỗi") else "👁️"
            print(f"  │ {icon} Observation: {_shorten(observation, 320)}")
            print("  └" + "─" * 74)

        # ── 5. Nối vào scratchpad ➔ làm ngữ cảnh cho Thought kế tiếp ────────
        scratchpad += f"{text}\nObservation: {observation}\n\n"
        trace.append({"step": step, "thought": parsed.get("thought", ""),
                      "action": action_label, "observation": observation, "final": None})

    # ── 6. 🛡️ GUARDRAIL: chạm phanh mà chưa có Final Answer ────────────────
    if final_answer is None and terminated_by != "provider_error":
        terminated_by = "guardrail_max_iterations"
        final_answer = (
            f"Xin lỗi, tôi chưa thể hoàn tất yêu cầu này một cách chắc chắn. "
            f"Sau {step} bước tra cứu, hệ thống vẫn chưa trả về dữ liệu hợp lệ "
            f"(nguyên nhân gần nhất: {_shorten(last_error or 'không xác định', 160)}). "
            f"Để tránh cung cấp thông tin sai, tôi xin dừng tại đây và đề nghị bạn "
            f"kiểm tra lại thông tin đầu vào hoặc chuyển yêu cầu cho chuyên viên HR phụ trách."
        )
        if verbose:
            print(f"\n  🛡️ GUARDRAIL KÍCH HOẠT: đã chạm giới hạn {max_steps} bước ➔ ngắt lặp an toàn.")
            print(f"  🏁 Safe Fallback: {_shorten(final_answer, 400)}")

    result = {
        "question": user_query,
        "final_answer": final_answer or "",
        "steps": step,
        "llm_calls": llm_calls,
        "tool_calls": tool_calls,
        "tools_used": tools_used,
        "faked_observations": faked_obs,
        "terminated_by": terminated_by,
        "elapsed": round(time.perf_counter() - start, 2),
        "trace": trace,
    }

    if verbose:
        print(f"\n📊 Thống kê: steps={result['steps']} | llm_calls={result['llm_calls']} | "
              f"tool_calls={result['tool_calls']} | tools={result['tools_used'] or '(không gọi tool)'} | "
              f"dừng bởi: {result['terminated_by']} | {result['elapsed']}s")

    return result


# =============================================================================
# 🛡️ MỐC 3 (GUARDRAILS) — REACT AGENT + 3 LỚP BẢO VỆ
# =============================================================================

def run_react_agent_with_guardrails(
    user_query: str,
    provider,
    max_steps: int = None,
    verbose: bool = True,
) -> dict:
    """
    [MỐC 3 + GUARDRAILS] Vòng lặp ReAct được bọc bởi 3 lớp Middleware bảo vệ:

      Lớp 1 (Input Guard)     : Phát hiện injection, sanitize, kiểm tra chủ đề.
      Lớp 2 (Execution Guard) : Validate tham số Pydantic, error-feedback-loop,
                                human-in-the-loop confirmation cho tool nguy hiểm.
      Lớp 3 (Output Guard)    : Kiểm tra hallucination, enforce JSON nếu cần.

    Tham số y hệt run_react_agent() để dễ hoán đổi trong test suite.
    """
    # ── Import Guardrails ────────────────────────────────────────────────
    try:
        from guardrails.input_guard import run_input_guard
        from guardrails.execution_guard import execute_with_guard, HIGH_RISK_TOOLS
        from guardrails.output_guard import validate_output
        _guardrails_ok = True
    except ImportError as e:
        if verbose:
            print(f"⚠️  Không import được guardrails ({e}). Chạy lại không có guardrails.")
        return run_react_agent(user_query, provider, max_steps=max_steps, verbose=verbose)

    prompts_mod, err1 = safe_import("prompts")
    tools_mod, err2 = safe_import("tools")
    if not prompts_mod or not tools_mod:
        print(f"❌ Thiếu module: prompts({err1}) tools({err2})")
        return {}

    system_prompt = getattr(prompts_mod, "REACT_SYSTEM_PROMPT", "")
    max_steps = max_steps or getattr(prompts_mod, "MAX_ITERATIONS", 5)

    if verbose:
        print(f"\n🤖 [REACT AGENT + GUARDRAILS] Câu hỏi: {user_query}")
        print(f"⚙️  System Prompt: {len(system_prompt)} ký tự | "
              f"🛠️ Tool được cấp: {len(getattr(tools_mod, 'AVAILABLE_TOOLS', {}))} | "
              f"🛡️ MAX_ITERATIONS = {max_steps} | 🔒 Guardrails: 3 lớp")

    # ── LAYER 1: Input Guardrails ────────────────────────────────────────
    if verbose:
        print("\n  🔒 [LAYER 1] Kiểm tra đầu vào...")
    input_result = run_input_guard(user_query)
    if input_result["status"] == "blocked":
        if verbose:
            print(f"  🚫 [LAYER 1 BLOCKED] {input_result['reason']}")
        return {
            "question": user_query,
            "final_answer": input_result["response"],
            "steps": 0,
            "llm_calls": 0,
            "tool_calls": 0,
            "tools_used": [],
            "faked_observations": 0,
            "terminated_by": "input_guardrail",
            "elapsed": 0.0,
            "trace": [],
            "guardrail_warnings": [input_result["reason"]],
        }
    if verbose:
        print("  ✅ [LAYER 1 OK] Đầu vào hợp lệ.")

    clean_query = input_result["clean_text"]
    context_facts: list[str] = []       # Thu thập facts từ tool observations
    scratchpad = ""
    trace = []
    seen_actions = {}
    llm_calls = tool_calls = faked_obs = 0
    tools_used, final_answer, terminated_by, last_error = [], None, None, None
    all_guardrail_warnings: list[str] = []

    start = time.perf_counter()
    step = 0
    while step < max_steps:
        step += 1
        if verbose:
            print(f"\n  ┌─ 🔄 Vòng lặp ReAct+Guard — Step {step}/{max_steps} " + "─" * 30)

        # ── 1. Gọi LLM ──────────────────────────────────────────────────
        prompt = f"Question: {clean_query}\n\n{scratchpad}"
        raw = provider.generate(prompt, system_prompt=system_prompt)
        llm_calls += 1

        if _looks_like_provider_error(raw):
            terminated_by = "provider_error"
            last_error = str(raw)
            if verbose:
                print(f"  │ ❌ Provider lỗi: {_shorten(raw, 200)}")
            break

        # ── 2. Chặn LLM tự bịa Observation ─────────────────────────────
        text, faked = _strip_hallucinated_observation(raw)
        if faked:
            faked_obs += 1
            if verbose:
                print("  │ ⚠️  LLM tự bịa 'Observation:' ➔ đã CẮT BỎ")

        # ── 3. Parse bước ReAct ─────────────────────────────────────────
        parsed = parse_llm_step(text)
        if verbose and parsed.get("thought"):
            print(f"  │ 🧠 Thought: {_shorten(parsed['thought'], 220)}")

        # ── 4a. Final Answer → chạy Output Guard ─────────────────────
        if parsed["kind"] == "final":
            final_answer = parsed["answer"]
            terminated_by = "final_answer"

            # LAYER 3: Output Guard
            if verbose:
                print(f"  │ 🏁 Final Answer: {_shorten(final_answer, 400)}")
                print("  │ 🔒 [LAYER 3] Kiểm tra output...")
            out_result = validate_output(final_answer, context_facts=context_facts)
            if out_result["warnings"]:
                all_guardrail_warnings.extend(out_result["warnings"])
                if verbose:
                    for w in out_result["warnings"]:
                        print(f"  │   ⚠️  {w}")
            else:
                if verbose:
                    print("  │   ✅ [LAYER 3 OK] Output không có dấu hiệu hallucination.")

            trace.append({"step": step, "thought": parsed.get("thought", ""),
                          "action": None, "observation": None, "final": final_answer})
            if verbose:
                print("  └" + "─" * 74)
            break

        # ── 4b. Xử lý Action ─────────────────────────────────────────
        action_label = None
        if parsed["kind"] == "action":
            tool_name, args = parsed["tool"], parsed["args"]
            action_label = f"{tool_name}[{', '.join(repr(a) for a in args)}]"
            if verbose:
                print(f"  │ 🛠️ Action: {_shorten(action_label, 220)}")

            key = (tool_name, tuple(args))
            if key in seen_actions:
                observation = (
                    f"Lỗi lặp hành động: Bạn đã gọi {tool_name} với đúng tham số này ở bước trước "
                    f"và nhận kết quả: \"{_shorten(seen_actions[key], 150)}\". "
                    f"Hãy đổi tham số, đổi tool, hoặc trả về Final Answer."
                )
                last_error = observation
                if verbose:
                    print("  │ 🔁 Phát hiện LẶP hành động ➔ chèn cảnh báo")
            else:
                # LAYER 2: Execution Guard
                # Ánh xạ args theo vị trí → dict tham số
                fn = getattr(tools_mod, "AVAILABLE_TOOLS", {}).get(tool_name)
                if fn:
                    try:
                        param_names = [
                            p.name for p in inspect.signature(fn).parameters.values()
                            if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
                        ]
                        params_dict = dict(zip(param_names, args))
                    except (TypeError, ValueError):
                        params_dict = {}
                else:
                    params_dict = {}

                if verbose:
                    print("  │ 🔒 [LAYER 2] Validate tham số + kiểm tra high-risk...")
                exec_result = execute_with_guard(
                    tool_name=tool_name,
                    params=params_dict,
                    tools_mod=tools_mod,
                    require_confirm=(tool_name in HIGH_RISK_TOOLS),
                )

                if exec_result["status"] == "ok":
                    observation = exec_result["result"]
                    context_facts.append(observation)   # Thu thập fact thật
                    tool_calls += 1
                    seen_actions[key] = observation
                    if tool_name not in tools_used:
                        tools_used.append(tool_name)
                    if verbose:
                        print("  │   ✅ [LAYER 2 OK] Tool thực thi thành công.")
                else:
                    # Error Feedback Loop: chuyển lỗi thành context cho LLM
                    observation = exec_result["error_context"]
                    last_error = observation
                    all_guardrail_warnings.append(
                        f"Layer 2 ({exec_result['status']}): {observation[:80]}"
                    )
                    if verbose:
                        print(f"  │   ❌ [LAYER 2 ERROR] {exec_result['status']}: "
                              f"{_shorten(observation, 160)}")

        elif parsed["kind"] == "malformed":
            observation = (
                f"Lỗi cú pháp Action: không đọc được dòng '{parsed['raw']}'. "
                f'Cú pháp đúng là: Action: tên_tool["tham_số_1", "tham_số_2"] '
                f"— nhớ đủ dấu ngoặc vuông và dấu nháy kép."
            )
            last_error = observation
            if verbose:
                print(f"  │ ❌ Action sai cú pháp: {parsed['raw']}")
        else:
            observation = (
                "Lỗi định dạng: Phản hồi của bạn không có dòng 'Action:' cũng không có "
                "'Final Answer:'. Hãy trả lời lại đúng định dạng: Thought: ... rồi "
                'Action: tên_tool["tham_số"] hoặc Final Answer: ...'
            )
            last_error = observation
            if verbose:
                print("  │ ❌ Không tìm thấy Action lẫn Final Answer")

        if verbose:
            icon = "❌" if str(observation).strip().lower().startswith(("lỗi", "[tool", "[valid", "[human")) else "👁️"
            print(f"  │ {icon} Observation: {_shorten(observation, 320)}")
            print("  └" + "─" * 74)

        scratchpad += f"{text}\nObservation: {observation}\n\n"
        trace.append({"step": step, "thought": parsed.get("thought", ""),
                      "action": action_label, "observation": observation, "final": None})

    # ── 6. Guardrail: chạm phanh MAX_ITERATIONS ─────────────────────────
    if final_answer is None and terminated_by != "provider_error":
        terminated_by = "guardrail_max_iterations"
        final_answer = (
            f"Xin lỗi, tôi chưa thể hoàn tất yêu cầu này một cách chắc chắn. "
            f"Sau {step} bước tra cứu, hệ thống vẫn chưa trả về dữ liệu hợp lệ "
            f"(nguyên nhân gần nhất: {_shorten(last_error or 'không xác định', 160)}). "
            f"Để tránh cung cấp thông tin sai, tôi xin dừng tại đây và đề nghị bạn "
            f"kiểm tra lại thông tin đầu vào hoặc chuyển yêu cầu cho chuyên viên HR phụ trách."
        )
        if verbose:
            print(f"\n  🛡️ GUARDRAIL KÍCH HOẠT: đã chạm giới hạn {max_steps} bước ➔ ngắt lặp an toàn.")
            print(f"  🏁 Safe Fallback: {_shorten(final_answer, 400)}")

    elapsed = round(time.perf_counter() - start, 2)
    result = {
        "question": user_query,
        "final_answer": final_answer or "",
        "steps": step,
        "llm_calls": llm_calls,
        "tool_calls": tool_calls,
        "tools_used": tools_used,
        "faked_observations": faked_obs,
        "terminated_by": terminated_by,
        "elapsed": elapsed,
        "trace": trace,
        "guardrail_warnings": all_guardrail_warnings,
    }

    if verbose:
        warn_count = len(all_guardrail_warnings)
        print(f"\n📊 Thống kê+Guard: steps={result['steps']} | llm_calls={result['llm_calls']} | "
              f"tool_calls={result['tool_calls']} | tools={result['tools_used'] or '(không gọi tool)'} | "
              f"dừng bởi: {result['terminated_by']} | ⚠️guard_warnings={warn_count} | {elapsed}s")

    return result


def run_agent_suite(provider, cases: list, save: bool = False, max_steps: int = None) -> list:

    """Chạy ReAct Agent trên toàn bộ test case của Role 1 và in bảng tổng kết."""
    print("=" * 78)
    print("🧠 MỐC 3 — CHẠY REACT AGENT (Cấp độ 3: Thought -> Action -> Observation)")
    print(f"🔌 Provider: {provider.__class__.__name__} "
          f"(model: {getattr(provider, 'model_name', 'mock')}) | 📋 Số test case: {len(cases)}")
    print("=" * 78)

    results = []
    for case in cases:
        print(f"\n{'─' * 78}")
        print(f"🧪 TEST CASE #{case.get('id', '?')} — {case.get('category', '')}")
        print(f"{'─' * 78}")
        res = run_react_agent(case["question"], provider, max_steps=max_steps)
        if res:
            res["id"] = case.get("id")
            res["category"] = case.get("category", "")
            res["expected_behavior"] = case.get("expected_behavior", "")
            results.append(res)

    print("\n" + "=" * 78)
    print("📊 TỔNG KẾT REACT AGENT")
    print("=" * 78)
    print(f"{'#':<3} {'Loại câu hỏi':<32} {'Step':<5} {'LLM':<4} {'Tool':<5} {'Giây':<6} Dừng bởi")
    print("-" * 78)
    for r in results:
        print(f"{r['id']:<3} {r['category'][:31]:<32} {r['steps']:<5} {r['llm_calls']:<4} "
              f"{r['tool_calls']:<5} {r['elapsed']:<6} {r['terminated_by']}")
    print("-" * 78)

    guard = [r for r in results if r["terminated_by"] == "guardrail_max_iterations"]
    faked = sum(r["faked_observations"] for r in results)
    print(f"🛠️ Tổng lượt gọi tool THẬT: {sum(r['tool_calls'] for r in results)} "
          f"(Chatbot baseline = 0) | 🛡️ Guardrail ngắt: {len(guard)} case | "
          f"⚠️ Lần LLM bịa Observation bị chặn: {faked}")
    print("👉 Việc của Role 5: copy chuỗi Thought -> Action -> Observation ở trên vào docs/trace_eval.md.")

    if save and results:
        save_agent_log(results, provider, max_steps)

    return results


def save_agent_log(results: list, provider, max_steps: int = None) -> None:
    """Ghi trace log ra docs/agent_raw_log.md để Role 5 copy vào docs/trace_eval.md."""
    out_path = BASE_DIR / "docs" / "agent_raw_log.md"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# 🧠 LOG TRACE — REACT AGENT (Mốc 3)",
        "",
        f"> File này do `python src/app.py --agent --save` sinh tự động lúc {stamp}.",
        f"> Provider: `{provider.__class__.__name__}` — model: `{getattr(provider, 'model_name', 'mock')}`"
        f" — MAX_ITERATIONS: `{max_steps or 'theo prompts.py'}`.",
        "> 👉 Role 5 copy trace cần dùng sang `docs/trace_eval.md` rồi chấm điểm.",
        "",
        "| # | Loại câu hỏi | Steps | LLM calls | Tool calls | Tool đã gọi | Dừng bởi |",
        "| :--- | :--- | :---: | :---: | :---: | :--- | :--- |",
    ]
    for r in results:
        lines.append(
            f"| {r['id']} | {r['category']} | {r['steps']} | {r['llm_calls']} | {r['tool_calls']} "
            f"| {', '.join(r['tools_used']) or '—'} | {r['terminated_by']} |"
        )
    lines.append("")

    for r in results:
        lines += [
            f"## Test case #{r['id']} — {r['category']}",
            "",
            f"**Câu hỏi**: {r['question']}",
            "",
            f"**Kỳ vọng (Role 1)**: {r['expected_behavior']}",
            "",
            "**Trace đầy đủ**:",
            "",
            "```text",
            f"Question: {r['question']}",
            "",
        ]
        for t in r["trace"]:
            if t["thought"]:
                lines.append(f"Thought: {t['thought']}")
            if t["action"]:
                lines.append(f"Action: {t['action']}")
            if t["observation"]:
                lines.append(f"Observation: {t['observation']}")
            if t["final"]:
                lines.append(f"Final Answer: {t['final']}")
            lines.append("")
        if r["terminated_by"] == "guardrail_max_iterations":
            lines.append(f"[🛡️ GUARDRAIL] Chạm giới hạn {r['steps']} bước ➔ ngắt lặp an toàn.")
            lines.append(f"Safe Fallback: {r['final_answer']}")
        lines += [
            "```",
            "",
            f"**Thống kê**: `steps = {r['steps']}` · `llm_calls = {r['llm_calls']}` "
            f"· `tool_calls = {r['tool_calls']}` · tool đã gọi: {', '.join(r['tools_used']) or '—'} "
            f"· dừng bởi `{r['terminated_by']}` · {r['elapsed']}s",
            "",
            "---",
            "",
        ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n💾 Đã ghi trace log cho Role 5: {out_path}")


def run_compare_suite(provider, cases: list, max_steps: int = None) -> None:
    """
    So sánh trực tiếp Chatbot baseline vs ReAct Agent trên cùng bộ test case.
    Đây là bảng Role 5 cần cho phần đánh giá trong docs/trace_eval.md.
    """
    prompts_mod, _ = safe_import("prompts")
    system_prompt = getattr(prompts_mod, "CHATBOT_BASELINE_PROMPT", "") if prompts_mod else ""

    rows = []
    for case in cases:
        print("\n" + "=" * 78)
        print(f"🧪 TEST CASE #{case.get('id', '?')} — {case.get('category', '')}")
        print(f"❓ {case['question']}")
        print("=" * 78)

        print("\n--- 🤖 CHATBOT BASELINE (Cấp 2) ---")
        base = run_baseline_chatbot(case["question"], provider, system_prompt=system_prompt)

        print("\n--- 🧠 REACT AGENT (Cấp 3) ---")
        agent = run_react_agent(case["question"], provider, max_steps=max_steps)

        rows.append({
            "id": case.get("id"),
            "category": case.get("category", ""),
            "base_tools": base.get("tool_calls", 0),
            "base_time": base.get("elapsed", 0),
            "agent_tools": agent.get("tool_calls", 0),
            "agent_steps": agent.get("steps", 0),
            "agent_time": agent.get("elapsed", 0),
            "agent_stop": agent.get("terminated_by", ""),
        })

    print("\n" + "=" * 78)
    print("📊 BẢNG SO SÁNH CHATBOT vs REACT AGENT")
    print("=" * 78)
    print(f"{'#':<3} {'Loại câu hỏi':<30} {'Bot tool':<9} {'Bot giây':<9} "
          f"{'Agent tool':<11} {'Agent giây':<11} Agent dừng bởi")
    print("-" * 78)
    for r in rows:
        print(f"{r['id']:<3} {r['category'][:29]:<30} {r['base_tools']:<9} {r['base_time']:<9} "
              f"{r['agent_tools']:<11} {r['agent_time']:<11} {r['agent_stop']}")
    print("-" * 78)
    print("💡 Đọc bảng: câu đơn giản ➔ Chatbot nhanh & rẻ hơn (Agent tốn nhiều LLM call hơn).")
    print("             câu cần dữ liệu thật ➔ chỉ Agent mới có tool_calls > 0 ➔ có bằng chứng.")


def run_preflight(live: bool) -> int:
    """MỐC 1: Kiểm tra môi trường + độ tương thích file của Role 1/2/3."""
    print("=" * 78)
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("📌 Đề tài 9: Trợ lý Sàng lọc Hồ sơ Tuyển dụng & Hẹn Phỏng vấn")
    print("🔧 MỐC 1 — PREFLIGHT CHECK (Role 4: Core Developer / Integrator)")
    print("=" * 78)

    check_python()
    check_packages()
    provider_name = check_env_config()
    check_test_cases()
    tools_mod = check_tools()
    check_prompts(tools_mod)
    check_provider_pipeline(provider_name, live)

    return print_summary()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lab 3 - Chatbot vs ReAct Agent (Đề tài 9: Sàng lọc hồ sơ & Hẹn phỏng vấn)",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--baseline", action="store_true",
                        help="MỐC 2: Chạy Chatbot baseline (1 LLM call, 0 tool) trên bộ test case")
    parser.add_argument("--agent", action="store_true",
                        help="MỐC 3: Chạy ReAct Agent (Thought -> Action -> Observation + Guardrails)")
    parser.add_argument("--guardrails", action="store_true",
                        help="MỐC 3+G: ReAct Agent với 3 lớp Guardrails (Input/Execution/Output Guard)")
    parser.add_argument("--compare", action="store_true",
                        help="Chạy CẢ HAI (Chatbot vs Agent) trên cùng test case rồi in bảng so sánh")
    parser.add_argument("--max-steps", type=int, metavar="N", dest="max_steps",
                        help="Ghi đè MAX_ITERATIONS của prompts.py để thử nghiệm phanh an toàn")
    parser.add_argument("--ask", metavar="CÂU HỎI",
                        help="Hỏi Agent 1 câu tự do (dùng khi bị nhóm khác 'tấn công' ở Mốc 4)")
    parser.add_argument("--case", type=int, metavar="ID",
                        help="Chỉ chạy 1 test case theo id (VD: --case 3)")
    parser.add_argument("--provider", metavar="TÊN",
                        help="Ép dùng provider: gemini | openai | anthropic | openrouter | mock")
    parser.add_argument("--save", action="store_true",
                        help="Ghi log thô ra docs/baseline_raw_log.md cho Role 5")
    parser.add_argument("--live", action="store_true",
                        help="Ở chế độ preflight: gọi thật 1 câu lên LLM để test API key")
    args = parser.parse_args()

    # Không truyền cờ nào ➔ chạy preflight check của Mốc 1
    if not (args.baseline or args.agent or args.guardrails or args.compare or args.ask):
        return run_preflight(args.live)

    # Nạp .env rồi khởi tạo provider
    dotenv, _ = safe_import("dotenv")
    if dotenv:
        dotenv.load_dotenv(BASE_DIR / ".env")

    providers_mod, err = safe_import("providers")
    if not providers_mod:
        print(f"❌ Không import được src/providers.py ({err})")
        print("   ➔ Chạy: python -m pip install -r requirements.txt")
        return 1
    provider = providers_mod.get_llm_provider(args.provider)

    # Hỏi tự do 1 câu (không cần test case) — dùng cho Cross-Audit ở Mốc 4
    if args.ask:
        if args.guardrails:
            run_react_agent_with_guardrails(args.ask, provider, max_steps=args.max_steps)
        else:
            run_react_agent(args.ask, provider, max_steps=args.max_steps)
        return 0

    cases = load_test_cases()
    if not cases:
        return 1
    if args.case is not None:
        cases = [c for c in cases if c.get("id") == args.case]
        if not cases:
            print(f"❌ Không tìm thấy test case có id = {args.case} trong config/test_cases.json")
            return 1

    if args.compare:
        run_compare_suite(provider, cases, max_steps=args.max_steps)
    elif args.guardrails:
        # MỐC 3+G: ReAct Agent + 3 lớp Guardrails
        print("=" * 78)
        print("🛡️ MỐC 3+G — REACT AGENT + 3 LỚP GUARDRAILS")
        print("  Layer 1: Input Guard (Injection / Sanitize / Topic Restriction)")
        print("  Layer 2: Execution Guard (Pydantic Validate / Error Feedback / Human Confirm)")
        print("  Layer 3: Output Guard (Hallucination Check / Structured Output)")
        print("=" * 78)
        for case in cases:
            print(f"\n{'─' * 78}")
            print(f"🧪 TEST CASE #{case.get('id', '?')} — {case.get('category', '')}")
            print(f"{'─' * 78}")
            run_react_agent_with_guardrails(
                case["question"], provider, max_steps=args.max_steps
            )
    elif args.agent:
        run_agent_suite(provider, cases, save=args.save, max_steps=args.max_steps)
    else:
        run_baseline_suite(provider, cases, save=args.save)
    return 0


def load_test_cases() -> list:
    """Đọc bộ test cases từ config/test_cases.json của Role 1."""
    path = BASE_DIR / "config" / "test_cases.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Không tìm thấy {path} — Role 1 cần push config/test_cases.json.")
    except json.JSONDecodeError as e:
        print(f"❌ File config/test_cases.json bị lỗi cú pháp JSON: {e}")
    return []


if __name__ == "__main__":
    sys.exit(main())
