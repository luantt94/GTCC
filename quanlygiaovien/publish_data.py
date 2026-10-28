"""Pipeline cập nhật dữ liệu công khai cho trang web (GitHub Pages):

1. Convert Excel -> data.json (dữ liệu đầy đủ, chỉ dùng nội bộ, KHÔNG commit lên git)
2. Gán mã cố định (GV001, GV002, ...) cho giáo viên mới, lưu vào teacher_ids.json
3. Build docs/public_data.json: tên giáo viên + chi tiết từng khóa đang đào tạo
   (khóa/lớp, thời gian, xe, SĐT, danh sách tên học viên, lịch học)
4. Sinh mã QR cho giáo viên mới vào qr_codes/<ma>.png

Lưu ý: public_data.json có TÊN học viên (theo yêu cầu) nhưng KHÔNG có
ngày sinh / địa chỉ - những trường đó chỉ nằm trong data.json nội bộ.

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
SELECTED_FILES_FILE = APP_DIR / "selected_excel_files.json"

BASE_URL = "https://luantt94.github.io/GTCC/gv.html"


def load_selected_excel_files():
    """Danh sách file Excel đã chọn lần gần nhất (lưu lại giữa các lần mở app)."""
    if SELECTED_FILES_FILE.exists():
        paths = json.loads(SELECTED_FILES_FILE.read_text(encoding="utf-8"))
        return [p for p in paths if Path(p).exists()]
    return []


def save_selected_excel_files(paths):
    SELECTED_FILES_FILE.write_text(
        json.dumps([str(p) for p in paths], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


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


def run_pipeline(excel_paths=None):
    """Chạy toàn bộ pipeline cho 1 hoặc nhiều file Excel (gộp theo mã khóa).
    Trả về dict kết quả để hiển thị cho người dùng."""
    if excel_paths is None:
        excel_paths = load_selected_excel_files()
        if not excel_paths:
            # tương thích ngược: chưa chọn file nào thì dùng file mặc định cũ
            default_path = APP_DIR / convert_excel_to_json.EXCEL_FILE
            if default_path.exists():
                excel_paths = [default_path]

    if not excel_paths:
        raise FileNotFoundError(
            "Chưa chọn file Excel nào. Hãy bấm 'Chọn file Excel...' trước."
        )
    for p in excel_paths:
        if not Path(p).exists():
            raise FileNotFoundError(f"Không tìm thấy file Excel: {p}")

    data_json_path = APP_DIR / convert_excel_to_json.OUTPUT_FILE
    data, overwritten = convert_excel_to_json.build_data(excel_paths)
    data_json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    model = DataModel(data_json_path)
    teacher_ids = _load_teacher_ids()

    teaching_now = {}
    for c in model.all_courses():
        if model.status_of(c) != "Đang đào tạo":
            continue
        lich_hoc = [
            d for d in c.get("lich_hoc", []) if d["sang"] or d["chieu"] or d["toi"]
        ]
        for g in c.get("groups", []):
            name = g.get("giao_vien")
            if not name:
                continue
            hoc_vien = g.get("hoc_vien", [])
            teaching_now.setdefault(name, []).append(
                {
                    "ma_khoa": c["ma_khoa"],
                    "lop": c.get("lop", ""),
                    "tu_ngay": c.get("tu_ngay", ""),
                    "den_ngay": c.get("den_ngay", ""),
                    "xe": g.get("xe", ""),
                    "sdt": g.get("sdt", ""),
                    "so_hoc_vien": len(hoc_vien),
                    "hoc_vien": [hv["ho_ten"] for hv in hoc_vien],
                    "lich_hoc": lich_hoc,
                }
            )

    all_names = set(model.all_teachers()) | set(teaching_now)
    new_names = _assign_ids(teacher_ids, all_names)
    _save_teacher_ids(teacher_ids)

    for name in new_names:
        _generate_qr(teacher_ids[name])

    DOCS_DIR.mkdir(exist_ok=True)
    teachers_out = {}
    for name, khoa_list in teaching_now.items():
        tid = teacher_ids[name]
        teachers_out[tid] = {"ten": name, "khoa_dang_day": khoa_list}
    # giáo viên không dạy khóa nào hiện tại vẫn hiển thị, danh sách khóa rỗng
    for name, tid in teacher_ids.items():
        teachers_out.setdefault(tid, {"ten": name, "khoa_dang_day": []})

    out = {"generated_at": model.generated_at, "teachers": teachers_out}
    PUBLIC_DATA_FILE.write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {
        "so_giao_vien": len(teachers_out),
        "giao_vien_moi": [(name, teacher_ids[name]) for name in new_names],
        "generated_at": model.generated_at,
        "ma_khoa_trung": overwritten,
        "so_file_excel": len(excel_paths),
    }
