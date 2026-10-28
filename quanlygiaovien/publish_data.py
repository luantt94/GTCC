"""Pipeline cập nhật dữ liệu công khai cho trang web (GitHub Pages):

1. Đọc các nguồn trong data_sources.json (xem load_data_sources()):
   - File Excel "BIÊN CHẾ XE KHÓA xxxx.xlsx" (mỗi khóa 1 file)
   - File PDF "LICH HOC THUC HANH xxxx.pdf" (mỗi khóa 1 file)
   - File DSGV_*.xml (danh sách toàn bộ giáo viên, nguồn ID chính thức)
   - File DSXTL_*.xml (danh sách xe tập lái, dùng để đối chiếu biển số)
   - Thư mục giấy tờ xe (.docx/.pdf) và thư mục hồ sơ cá nhân giáo viên (.pdf)
2. Convert Excel -> data.json (dữ liệu đầy đủ, chỉ dùng nội bộ, KHÔNG commit lên git)
3. Build docs/public_data.json: tên giáo viên + chi tiết từng khóa đang đào tạo
   (khóa/lớp, thời gian, xe, SĐT, danh sách tên học viên) + file PDF/Word gắn kèm
4. Sinh mã QR cho MỌI giáo viên trong DSGV (mã QR = MaGV - mã chính thức, cố
   định, không bao giờ trùng lặp) vào qr_codes/<MaGV>.png, có ghi tên bên dưới

Lưu ý: public_data.json có TÊN học viên (theo yêu cầu) nhưng KHÔNG có
ngày sinh / địa chỉ / CMT / ảnh - những trường đó không bao giờ được đọc ra
khỏi data.json nội bộ hay file DSGV (chỉ lấy tên + điện thoại).

Không đụng tới git ở đây - phần git do git_publish.py xử lý.
"""
import hashlib
import json
import shutil
from pathlib import Path

import attach_files
import convert_excel_to_json
import roster_xml
from data_model import DataModel

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent  # docs/ phải nằm ở root repo để GitHub Pages phục vụ được
DATA_DIR = APP_DIR / "data"
DOCS_DIR = REPO_ROOT / "docs"
PUBLIC_DATA_FILE = DOCS_DIR / "public_data.json"
FILES_OUT_DIR = DOCS_DIR / "files"
QR_DIR = APP_DIR / "qr_codes"
APP_SETTINGS_FILE = APP_DIR / "app_settings.json"
DATA_SOURCES_FILE = APP_DIR / "data_sources.json"

BASE_URL = "https://luantt94.github.io/GTCC/gv.html"

DEFAULT_XE_FOLDER_NAME = "Xe tập lái"
DEFAULT_HO_SO_FOLDER_NAME = "HO SO GV (2026_GTCC)"


# ---------------- cài đặt chung (mật khẩu hồ sơ cá nhân) ----------------
def load_app_settings():
    if APP_SETTINGS_FILE.exists():
        return json.loads(APP_SETTINGS_FILE.read_text(encoding="utf-8"))
    return {}


def save_app_settings(settings):
    APP_SETTINGS_FILE.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ---------------- nguồn dữ liệu (data_sources.json) ----------------
def _scan_default_sources():
    """Tự động quét thư mục data/ để gợi ý sẵn danh sách nguồn lần đầu mở app."""
    bien_che = sorted(str(p) for p in DATA_DIR.glob("*.xlsx") if "BIÊN CHẾ XE KHÓA" in p.name.upper())
    lich_hoc = sorted(str(p) for p in DATA_DIR.glob("*.pdf") if "LICH HOC" in p.name.upper())
    dsgv = sorted(DATA_DIR.glob("DSGV_*.xml"))
    dsxtl = sorted(DATA_DIR.glob("DSXTL_*.xml"))
    xe_folder = DATA_DIR / DEFAULT_XE_FOLDER_NAME
    ho_so_folder = DATA_DIR / DEFAULT_HO_SO_FOLDER_NAME
    return {
        "bien_che_files": bien_che,
        "lich_hoc_files": lich_hoc,
        "dsgv_file": str(dsgv[-1]) if dsgv else "",
        "dsxtl_file": str(dsxtl[-1]) if dsxtl else "",
        "xe_folder": str(xe_folder) if xe_folder.is_dir() else "",
        "ho_so_folder": str(ho_so_folder) if ho_so_folder.is_dir() else "",
    }


def load_data_sources():
    """Danh sách nguồn dữ liệu đã chọn (lưu lại giữa các lần mở app).
    Lần đầu (chưa có file cấu hình) sẽ tự quét thư mục data/ để gợi ý sẵn."""
    if DATA_SOURCES_FILE.exists():
        saved = json.loads(DATA_SOURCES_FILE.read_text(encoding="utf-8"))
        saved["bien_che_files"] = [p for p in saved.get("bien_che_files", []) if Path(p).exists()]
        saved["lich_hoc_files"] = [p for p in saved.get("lich_hoc_files", []) if Path(p).exists()]
        return saved
    return _scan_default_sources()


def save_data_sources(sources):
    DATA_SOURCES_FILE.write_text(
        json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ---------------- QR ----------------
def _load_caption_font(size):
    import os

    from PIL import ImageFont

    windir = os.environ.get("WINDIR", "C:\\Windows")
    for name in ("segoeui.ttf", "arial.ttf"):
        path = os.path.join(windir, "Fonts", name)
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _generate_qr(ma_gv, ten):
    """Tạo mã QR (link cố định theo MaGV) kèm tên giáo viên in bên dưới,
    để dễ phân biệt các mã QR đã in."""
    import qrcode
    from PIL import Image, ImageDraw

    QR_DIR.mkdir(exist_ok=True)
    url = f"{BASE_URL}?id={ma_gv}"
    qr_img = qrcode.make(url).convert("RGB")

    font = _load_caption_font(20)
    caption_h = 34
    canvas = Image.new("RGB", (qr_img.width, qr_img.height + caption_h), "white")
    canvas.paste(qr_img, (0, 0))
    draw = ImageDraw.Draw(canvas)
    bbox = draw.textbbox((0, 0), ten, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = max((canvas.width - text_w) // 2, 0)
    y = qr_img.height + max((caption_h - text_h) // 2, 0)
    draw.text((x, y), ten, fill="black", font=font)
    canvas.save(QR_DIR / f"{ma_gv}.png")


def _copy_public_file(src_path, rel_subdir, dest_stem):
    """Copy 1 file gốc vào docs/files/<rel_subdir>/<dest_stem><ext>.
    Trả về đường dẫn tương đối (vd "files/xe/43A38936.docx") để nhúng vào
    public_data.json, hoặc None nếu src_path rỗng."""
    if not src_path:
        return None
    dest_dir = FILES_OUT_DIR / rel_subdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"{dest_stem}{src_path.suffix.lower()}"
    shutil.copyfile(src_path, dest_path)
    return f"files/{rel_subdir}/{dest_path.name}"


def run_pipeline(sources=None):
    """Chạy toàn bộ pipeline theo data_sources.json (hoặc sources truyền vào).
    Trả về dict kết quả để hiển thị cho người dùng."""
    if sources is None:
        sources = load_data_sources()

    bien_che_files = sources.get("bien_che_files") or []
    if not bien_che_files:
        raise FileNotFoundError(
            "Chưa chọn file Excel 'BIÊN CHẾ XE KHÓA ...' nào."
        )
    for p in bien_che_files:
        if not Path(p).exists():
            raise FileNotFoundError(f"Không tìm thấy file Excel: {p}")

    dsgv_file = sources.get("dsgv_file") or ""
    if not dsgv_file or not Path(dsgv_file).exists():
        raise FileNotFoundError(
            "Chưa chọn file danh sách giáo viên (DSGV_*.xml). File này là "
            "nguồn mã QR chính thức cho giáo viên, bắt buộc phải có."
        )

    data_json_path = APP_DIR / "data.json"
    data, overwritten = convert_excel_to_json.build_data(bien_che_files)
    data_json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    model = DataModel(data_json_path)
    dsgv = roster_xml.parse_dsgv(dsgv_file)

    dsxtl_file = sources.get("dsxtl_file") or ""
    dsxtl = roster_xml.parse_dsxtl(dsxtl_file) if dsxtl_file and Path(dsxtl_file).exists() else {}
    dsxtl_plates = {attach_files.normalize_plate(p) for p in dsxtl}

    lich_hoc_files = sources.get("lich_hoc_files") or []
    xe_folder = sources.get("xe_folder") or ""
    ho_so_folder = sources.get("ho_so_folder") or ""

    name_to_magv = {attach_files.normalize_name(rec["ten"]): magv for magv, rec in dsgv.items()}

    warnings = []

    # Dọn sạch file public cũ (PDF/Word) trước khi gắn lại cho đúng danh sách
    # giáo viên/khóa đang active hiện tại (tránh file cũ của khóa/giáo viên
    # không còn dạy nằm lại trên web public).
    shutil.rmtree(FILES_OUT_DIR, ignore_errors=True)

    lich_hoc_pdf_cache = {}  # ma_khoa -> rel path (hoặc None), tránh copy trùng
    teaching_now = {}  # ma_gv -> [khoa...]

    for c in model.all_courses():
        if model.status_of(c) != "Đang đào tạo":
            continue
        ma_khoa = c["ma_khoa"]
        lop = c.get("lop", "")
        if ma_khoa not in lich_hoc_pdf_cache:
            src = attach_files.find_lich_hoc_pdf(lop, lich_hoc_files)
            lich_hoc_pdf_cache[ma_khoa] = _copy_public_file(src, "lich_hoc", ma_khoa or lop)
        lich_hoc_pdf = lich_hoc_pdf_cache[ma_khoa]

        for g in c.get("groups", []):
            name = g.get("giao_vien")
            if not name:
                continue
            ma_gv = name_to_magv.get(attach_files.normalize_name(name))
            if not ma_gv:
                warnings.append(
                    f"Không khớp được giáo viên '{name}' (khóa {ma_khoa}) với "
                    "danh sách DSGV - kiểm tra lại chính tả tên."
                )
                continue

            hoc_vien = g.get("hoc_vien", [])
            xe = g.get("xe", "")
            if dsxtl_plates and xe and attach_files.normalize_plate(xe) not in dsxtl_plates:
                warnings.append(f"Biển số '{xe}' (GV {name}, khóa {ma_khoa}) không có trong DSXTL.")
            xe_doc_src = attach_files.find_xe_doc(xe, xe_folder)
            giay_to_xe_file = _copy_public_file(
                xe_doc_src, "xe", attach_files.normalize_plate(xe) or "xe"
            )
            teaching_now.setdefault(ma_gv, []).append(
                {
                    "ma_khoa": ma_khoa,
                    "lop": lop,
                    "tu_ngay": c.get("tu_ngay", ""),
                    "den_ngay": c.get("den_ngay", ""),
                    "xe": xe,
                    "sdt": g.get("sdt", ""),
                    "so_hoc_vien": len(hoc_vien),
                    "hoc_vien": [hv["ho_ten"] for hv in hoc_vien],
                    "lich_hoc_pdf": lich_hoc_pdf,
                    "giay_to_xe_file": giay_to_xe_file,
                }
            )

    DOCS_DIR.mkdir(exist_ok=True)
    QR_DIR.mkdir(exist_ok=True)
    existing_qr = {f.stem for f in QR_DIR.glob("*.png")}
    giao_vien_moi = []

    teachers_out = {}
    for ma_gv, rec in dsgv.items():
        ho_so_src = attach_files.find_ho_so_gv(rec["ten"], ho_so_folder)
        ho_so_file = _copy_public_file(ho_so_src, "ho_so_gv", ma_gv)
        teachers_out[ma_gv] = {
            "ten": rec["ten"],
            "khoa_dang_day": teaching_now.get(ma_gv, []),
            "ho_so_file": ho_so_file,
        }
        if ma_gv not in existing_qr:
            _generate_qr(ma_gv, rec["ten"])
            giao_vien_moi.append((rec["ten"], ma_gv))

    app_settings = load_app_settings()
    ho_so_password = (app_settings.get("ho_so_password") or "").strip()
    ho_so_password_hash = (
        hashlib.sha256(ho_so_password.encode("utf-8")).hexdigest()
        if ho_so_password
        else None
    )

    out = {
        "generated_at": model.generated_at,
        "teachers": teachers_out,
        "ho_so_password_hash": ho_so_password_hash,
    }
    PUBLIC_DATA_FILE.write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {
        "so_giao_vien": len(teachers_out),
        "giao_vien_moi": giao_vien_moi,
        "generated_at": model.generated_at,
        "ma_khoa_trung": overwritten,
        "so_file_excel": len(bien_che_files),
        "canh_bao": warnings,
    }
