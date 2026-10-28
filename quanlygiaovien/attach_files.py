"""Tìm & gắn file PDF/Word gốc (lịch học, giấy tờ xe, hồ sơ giáo viên) vào
gói dữ liệu public. Tất cả các hàm chỉ KHỚP theo TÊN FILE (không đổi tên
file gốc) nên không cần sửa tay khi có file mới, miễn tên file theo đúng
quy ước đã dùng từ trước tới nay:

- Lịch học: "lop" (vd "BK0726") là 1 chuỗi con (so khớp không phân biệt
  hoa/thường, bỏ dấu cách/ký tự đặc biệt) trong tên file PDF
  (vd "LICH HOC THUC HANH BK0726.signed.pdf").
- Giấy tờ xe: biển số (vd "43A-389.36") sau khi bỏ hết ký tự không phải
  chữ/số -> "43A38936" -> là 1 chuỗi con trong tên file.
- Hồ sơ giáo viên: tên giáo viên (bỏ số thứ tự đầu file, chuẩn hoá khoảng
  trắng, so khớp không phân biệt hoa/thường).

Không tìm thấy file nào khớp thì trả về None, không báo lỗi.
"""
import re
import unicodedata
from pathlib import Path

_NON_ALNUM_RE = re.compile(r"[^A-Za-z0-9]")
_LEADING_NUMBERING_RE = re.compile(r"^\s*\d+\s*[\.\-_]\s*")


def normalize_plate(text):
    return _NON_ALNUM_RE.sub("", text or "").upper()


def normalize_name(text):
    text = unicodedata.normalize("NFC", text or "")
    text = _LEADING_NUMBERING_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.upper()


def find_lich_hoc_pdf(lop, candidate_files):
    """Tìm file lịch học PDF theo mã lớp (vd "BK0726") trong 1 danh sách
    file PDF đã chọn sẵn (không tự quét thư mục)."""
    code = normalize_plate(lop)  # chỉ dùng để bỏ dấu cách/ký tự đặc biệt
    if not code:
        return None
    for f in candidate_files:
        f = Path(f)
        if code in normalize_plate(f.stem):
            return f
    return None


def find_xe_doc(xe_bien_so, folder):
    """Tìm giấy tờ xe (.docx/.pdf) theo biển số, trong 1 thư mục cho trước."""
    plate = normalize_plate(xe_bien_so)
    folder = Path(folder) if folder else None
    if not plate or not folder or not folder.is_dir():
        return None
    candidates = []
    for f in sorted(folder.iterdir()):
        if f.suffix.lower() not in (".docx", ".pdf"):
            continue
        if plate in normalize_plate(f.stem):
            candidates.append(f)
    return candidates[0] if candidates else None


def find_ho_so_gv(ten_giao_vien, folder):
    """Tìm hồ sơ cá nhân (PDF) theo tên giáo viên, trong 1 thư mục cho trước."""
    target = normalize_name(ten_giao_vien)
    folder = Path(folder) if folder else None
    if not target or not folder or not folder.is_dir():
        return None
    for f in sorted(folder.iterdir()):
        if f.suffix.lower() != ".pdf":
            continue
        if normalize_name(f.stem) == target:
            return f
    # fallback: tên nằm trong tên file (phòng khi file có hậu tố thêm)
    for f in sorted(folder.iterdir()):
        if f.suffix.lower() != ".pdf":
            continue
        if target in normalize_name(f.stem):
            return f
    return None
