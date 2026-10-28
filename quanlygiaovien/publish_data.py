"""Pipeline cập nhật dữ liệu công khai cho trang web (GitHub Pages):

1. Convert Excel -> data.json (dữ liệu đầy đủ, chỉ dùng nội bộ, KHÔNG commit lên git)
2. Gán mã cố định (GV001, GV002, ...) cho giáo viên mới, lưu vào teacher_ids.json
3. Build docs/public_data.json: chỉ tên giáo viên + số học viên đang dạy
4. Sinh mã QR cho giáo viên mới vào qr_codes/<ma>.png

Không đụng tới git ở đây - phần git do git_publish.py xử lý.
"""
import json
from pathlib import Path

import convert_excel_to_json
from data_model import DataModel

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent  # docs/ phải nằm ở root repo để GitHub Pages phục vụ được
TEACHER_IDS_FILE = APP_DIR / "teacher_ids.json"
DOCS_DIR = REPO_ROOT / "docs"
PUBLIC_DATA_FILE = DOCS_DIR / "public_data.json"
QR_DIR = APP_DIR / "qr_codes"

BASE_URL = "https://luantt94.github.io/GTCC/gv.html"


def _load_teacher_ids():
    if TEACHER_IDS_FILE.exists():
        return json.loads(TEACHER_IDS_FILE.read_text(encoding="utf-8"))
    return {}


def _save_teacher_ids(mapping):
    TEACHER_IDS_FILE.write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _next_id(mapping):
    used = set(mapping.values())
    n = 1
    while True:
        candidate = f"GV{n:03d}"
        if candidate not in used:
            return candidate
        n += 1


def _assign_ids(mapping, names):
    """Thêm id cho các tên giáo viên mới xuất hiện. Trả về list tên mới được gán."""
    new_names = []
    for name in sorted(names):
        if name not in mapping:
            mapping[name] = _next_id(mapping)
            new_names.append(name)
    return new_names


def _generate_qr(tid):
    import qrcode

    QR_DIR.mkdir(exist_ok=True)
    url = f"{BASE_URL}?id={tid}"
    img = qrcode.make(url)
    img.save(QR_DIR / f"{tid}.png")


def run_pipeline():
    """Chạy toàn bộ pipeline. Trả về dict kết quả để hiển thị cho người dùng."""
    excel_path = APP_DIR / convert_excel_to_json.EXCEL_FILE
    data_json_path = APP_DIR / convert_excel_to_json.OUTPUT_FILE

    if not excel_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file Excel: {excel_path.name}")

    import sys

    old_argv = sys.argv
    sys.argv = ["convert_excel_to_json.py", str(excel_path), str(data_json_path)]
    try:
        convert_excel_to_json.main()
    finally:
        sys.argv = old_argv

    model = DataModel(data_json_path)
    teacher_ids = _load_teacher_ids()

    teaching_now = {}
    for c in model.all_courses():
        if model.status_of(c) != "Đang đào tạo":
            continue
        for g in c.get("groups", []):
            name = g.get("giao_vien")
            if not name:
                continue
            teaching_now[name] = teaching_now.get(name, 0) + len(g.get("hoc_vien", []))

    all_names = set(model.all_teachers()) | set(teaching_now)
    new_names = _assign_ids(teacher_ids, all_names)
    _save_teacher_ids(teacher_ids)

    for name in new_names:
        _generate_qr(teacher_ids[name])

    DOCS_DIR.mkdir(exist_ok=True)
    teachers_out = {}
    for name, so_hv in teaching_now.items():
        tid = teacher_ids[name]
        teachers_out[tid] = {"ten": name, "so_hoc_vien": so_hv}
    # giáo viên không dạy khóa nào hiện tại vẫn hiển thị với số 0
    for name, tid in teacher_ids.items():
        teachers_out.setdefault(tid, {"ten": name, "so_hoc_vien": 0})

    out = {"generated_at": model.generated_at, "teachers": teachers_out}
    PUBLIC_DATA_FILE.write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {
        "so_giao_vien": len(teachers_out),
        "giao_vien_moi": [(name, teacher_ids[name]) for name in new_names],
        "generated_at": model.generated_at,
    }
