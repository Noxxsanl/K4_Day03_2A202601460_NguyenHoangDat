"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Developer / Integrator)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.

📍 TRẠNG THÁI HIỆN TẠI: MỐC 2 — CHATBOT BASELINE ĐÃ ĐƯỢC NỐI

Lộ trình lắp ráp của Role 4:
  - ✅ MỐC 1: Preflight check môi trường + kiểm tra tương thích Role 1/2/3.
  - ✅ MỐC 2: Nối hàm run_baseline_chatbot() ➔ Chatbot ĐÚNG 1 LLM call, 0 tool.
  - ⏳ MỐC 3: Nối hàm run_react_agent()      ➔ Vòng lặp Thought -> Action -> Observation + Guardrails.

Cách dùng:
    python src/app.py                        # Preflight check môi trường (mặc định)
    python src/app.py --live                 # Preflight + gọi thật 1 câu lên LLM để test API key
    python src/app.py --baseline             # MỐC 2: chạy Chatbot baseline trên TOÀN BỘ test case
    python src/app.py --baseline --case 3    # Chỉ chạy test case số 3
    python src/app.py --baseline --provider mock   # Chạy offline, không cần API key
    python src/app.py --baseline --save      # Ghi log thô ra docs/baseline_raw_log.md cho Role 5
"""

import argparse
import importlib
import inspect
import json
import logging
import os
import platform
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


def run_react_agent(user_query: str, provider):
    """
    [MỐC 3 — CHƯA TRIỂN KHAI] Vòng lặp ReAct: LLM sinh Thought/Action ➔ app parse Action
    ➔ app gọi tool thật ➔ app chèn Observation ➔ lặp lại, có phanh MAX_ITERATIONS.
    """
    print("⏳ [MỐC 3] run_react_agent() chưa được lắp. Hoàn thành Mốc 1 & 2 trước đã!")
    return None


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
                        help="MỐC 3: Chạy ReAct Agent (chưa lắp)")
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
    if not args.baseline and not args.agent:
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

    cases = load_test_cases()
    if not cases:
        return 1
    if args.case is not None:
        cases = [c for c in cases if c.get("id") == args.case]
        if not cases:
            print(f"❌ Không tìm thấy test case có id = {args.case} trong config/test_cases.json")
            return 1

    if args.agent:
        run_react_agent("", provider)
        return 0

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
