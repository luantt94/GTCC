"""Chuyển dữ liệu từ 2 sheet PHÂN XE và LỊCH HỌC trong file Excel sang data.json
để app PySide6 (sheet TRA CỨU) sử dụng để tra cứu.
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import openpyxl
from openpyxl.utils import get_column_letter

EXCEL_FILE = "DÙNG QR CODE ĐỂ XUẤT DỮ LIỆU ĐÀO TẠO TỪ GIÁO VIÊN.xlsx"
OUTPUT_FILE = "data.json"

DAY_COLS = [chr(c) for c in range(ord("B"), ord("Q") + 1)]  # B..Q


def clean_text(value):
    if value is None:
        return ""
    text = str(value).strip()
    # loại artifact kiểu "...TÊNB18:B20" lẫn vào nội dung do lỗi nhập liệu nguồn
    # (PHÂN XE chỉ có cột A..F nên giới hạn ký tự cột A-F, tránh ăn nhầm chữ tên như "VY")
    text = re.sub(r"[A-F]{1,2}\d+:[A-F]{1,2}\d+$", "", text).strip()
    return text


def parse_phan_xe(ws):
    """Trả về dict: ma_khoa -> {lop, tu_ngay, den_ngay, groups:[...]}"""
    courses = {}
    current = None
    current_group = None

    title_re = re.compile(
        r"KHÓA\s+(\S+)\s*\(([^)]+)\)\s*\n\(Từ ngày:\s*([^\n]+?)\s*đến ngày:\s*([^)]+)\)",
        re.UNICODE,
    )

    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=6):
        a_val = row[0].value
        a_str = str(a_val).strip() if a_val is not None else ""

        if a_str.startswith("BIÊN CHẾ XE KHÓA"):
            m = title_re.search(a_str)
            if m:
                ma_khoa, lop, tu_ngay, den_ngay = (g.strip() for g in m.groups())
            else:
                ma_khoa, lop, tu_ngay, den_ngay = a_str, "", "", ""
            current = courses.setdefault(
                ma_khoa,
                {"ma_khoa": ma_khoa, "lop": lop, "tu_ngay": tu_ngay, "den_ngay": den_ngay, "groups": []},
            )
            current_group = None
            continue

        if a_str == "Stt" or current is None:
            continue

        if isinstance(a_val, (int, float)):
            stt = int(a_val)
            ho_ten = clean_text(row[1].value)
            ngay_sinh = clean_text(row[2].value)
            dia_chi = clean_text(row[3].value)
            xe_gv_sdt = row[4].value
            ghi_chu = clean_text(row[5].value)

            if xe_gv_sdt and str(xe_gv_sdt).strip():
                lines = [clean_text(x) for x in str(xe_gv_sdt).split("\n")]
                lines = [x for x in lines if x]
                giao_vien = lines[0] if len(lines) > 0 else ""
                xe = lines[1] if len(lines) > 1 else ""
                sdt = lines[2] if len(lines) > 2 else ""
                current_group = {
                    "giao_vien": giao_vien,
                    "xe": xe,
                    "sdt": sdt,
                    "hoc_vien": [],
                }
                current["groups"].append(current_group)

            if current_group is not None:
                current_group["hoc_vien"].append(
                    {
                        "stt": stt,
                        "ho_ten": ho_ten,
                        "ngay_sinh": ngay_sinh,
                        "dia_chi": dia_chi,
                        "ghi_chu": ghi_chu,
                    }
                )

    return courses


def parse_lich_hoc(ws):
    """Trả về dict: ma_khoa -> {lop, hv_per_xe, lich_hoc: [...]}"""
    courses = {}
    current = None

    title_re = re.compile(r"KHÓA\s+(\S+)\s*\(([^)]+)\)(?:\s*\((\d+)hv/xe\))?", re.UNICODE)

    all_rows = {}
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=ws.max_column):
        r = row[0].row
        all_rows[r] = {get_column_letter(cell.column): cell.value for cell in row}

    for r in sorted(all_rows):
        cells = all_rows[r]
        a_val = cells.get("A")
        a_str = str(a_val).strip() if a_val is not None else ""

        if a_str.startswith("LỊCH HỌC THỰC HÀNH KHÓA"):
            m = title_re.search(a_str)
            if m:
                ma_khoa, lop, hv_per_xe = m.groups()
                ma_khoa, lop = ma_khoa.strip(), lop.strip()
                hv_per_xe = int(hv_per_xe) if hv_per_xe else None
            else:
                ma_khoa, lop, hv_per_xe = a_str, "", None
            current = courses.setdefault(
                ma_khoa, {"ma_khoa": ma_khoa, "lop": lop, "hv_per_xe": hv_per_xe, "lich_hoc": []}
            )
            continue

        if "Thứ" in a_str and "Ngày" in a_str and current is not None:
            header = cells
            labels = all_rows.get(r + 1, {})
            dates = all_rows.get(r + 2, {})
            sang = all_rows.get(r + 3, {})
            chieu = all_rows.get(r + 4, {})
            toi = all_rows.get(r + 5, {})

            for col in DAY_COLS:
                date_val = dates.get(col)
                if date_val in (None, ""):
                    continue
                if isinstance(date_val, datetime):
                    date_iso = date_val.strftime("%Y-%m-%d")
                else:
                    date_iso = str(date_val)
                current["lich_hoc"].append(
                    {
                        "date": date_iso,
                        "thu": clean_text(header.get(col)),
                        "label": clean_text(labels.get(col)),
                        "sang": clean_text(sang.get(col)),
                        "chieu": clean_text(chieu.get(col)),
                        "toi": clean_text(toi.get(col)),
                    }
                )

    return courses


def merge(phan_xe_courses, lich_hoc_courses):
    result = []
    all_ma_khoa = set(phan_xe_courses) | set(lich_hoc_courses)
    for ma_khoa in sorted(all_ma_khoa):
        px = phan_xe_courses.get(ma_khoa, {})
        lh = lich_hoc_courses.get(ma_khoa, {})
        lop = px.get("lop") or lh.get("lop") or ""
        groups = px.get("groups", [])
        so_hoc_vien = sum(len(g["hoc_vien"]) for g in groups)
        result.append(
            {
                "ma_khoa": ma_khoa,
                "lop": lop,
                "tu_ngay": px.get("tu_ngay", ""),
                "den_ngay": px.get("den_ngay", ""),
                "hv_per_xe": lh.get("hv_per_xe"),
                "so_hoc_vien": so_hoc_vien,
                "groups": groups,
                "lich_hoc": sorted(lh.get("lich_hoc", []), key=lambda d: d["date"]),
            }
        )
    return result


def main():
    excel_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(EXCEL_FILE)
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(OUTPUT_FILE)

    wb = openpyxl.load_workbook(excel_path, data_only=True)
    phan_xe_courses = parse_phan_xe(wb["PHÂN XE"])
    lich_hoc_courses = parse_lich_hoc(wb["LỊCH HỌC"])
    courses = merge(phan_xe_courses, lich_hoc_courses)

    data = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_file": excel_path.name,
        "courses": courses,
    }

    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: exported {len(courses)} khoa -> {output_path}")


if __name__ == "__main__":
    main()
