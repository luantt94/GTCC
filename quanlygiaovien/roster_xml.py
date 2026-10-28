"""Đọc 2 file XML xuất từ hệ thống quản lý của Sở GTVT:

- DSGV_*.xml: danh sách TOÀN BỘ giáo viên (dùng để sinh mã QR cố định theo
  MaGV - mã chính thức, không bao giờ trùng lặp). File này còn có ảnh chân
  dung (base64) và số CMT/CCCD - CHỈ đọc tên + điện thoại, không bao giờ
  đụng tới các trường nhạy cảm đó.
- DSXTL_*.xml: danh sách xe tập lái (dùng để đối chiếu biển số, cảnh báo
  nếu biển số trong Excel không có trong danh sách chính thức).
"""
import xml.etree.ElementTree as ET


def parse_dsgv(path, active_only=True):
    """Trả về dict: ma_gv (str) -> {"ten": str, "dien_thoai": str}."""
    root = ET.parse(path).getroot()
    body = root.find("GIAOVIENS")
    if body is None:
        return {}
    out = {}
    for rec in body.findall("GIAOVIEN"):

        def g(tag):
            el = rec.find(tag)
            return (el.text or "").strip() if el is not None and el.text else ""

        if active_only and g("TrangThai") not in ("1", ""):
            continue
        ma_gv = g("MaGV")
        if not ma_gv:
            continue
        ho_ten_dem = g("HoTenDem")
        ten = g("TenGV")
        full_name = f"{ho_ten_dem} {ten}".strip()
        if not full_name:
            continue
        out[ma_gv] = {"ten": full_name, "dien_thoai": g("DienThoai")}
    return out


def parse_dsxtl(path, active_only=True):
    """Trả về dict: biển số (nguyên văn) -> {"nhan_hieu":..., "loai_xe":...}."""
    root = ET.parse(path).getroot()
    body = root.find("XETAPS")
    if body is None:
        return {}
    out = {}
    for rec in body.findall("XETAP"):

        def g(tag):
            el = rec.find(tag)
            return (el.text or "").strip() if el is not None and el.text else ""

        if active_only and g("TRANGTHAI") not in ("1", ""):
            continue
        bien_so = g("BIENSOXE")
        if not bien_so:
            continue
        out[bien_so] = {"nhan_hieu": g("NHANHIEU"), "loai_xe": g("LOAIXE")}
    return out
