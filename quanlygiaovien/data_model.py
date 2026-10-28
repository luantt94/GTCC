"""Nạp data.json (xuất từ Excel) và cung cấp các hàm tra cứu cho app."""
import json
from datetime import datetime
from pathlib import Path


def _parse_date(text):
    text = (text or "").strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


class DataModel:
    def __init__(self, json_path):
        self.json_path = Path(json_path)
        raw = json.loads(self.json_path.read_text(encoding="utf-8"))
        self.generated_at = raw.get("generated_at", "")
        self.source_files = raw.get("source_files", [])
        self.courses = raw.get("courses", [])

    # ---- truy cập cơ bản ----
    def all_courses(self):
        return self.courses

    def course_codes(self):
        return [c["ma_khoa"] for c in self.courses]

    def find_course(self, ma_khoa):
        for c in self.courses:
            if c["ma_khoa"] == ma_khoa:
                return c
        return None

    def all_teachers(self):
        """Danh sách tên giáo viên duy nhất, đã sắp xếp."""
        names = set()
        for c in self.courses:
            for g in c.get("groups", []):
                if g.get("giao_vien"):
                    names.add(g["giao_vien"])
        return sorted(names)

    def status_of(self, course):
        today = datetime.now()
        start = _parse_date(course.get("tu_ngay", ""))
        end = _parse_date(course.get("den_ngay", ""))
        if end and today > end:
            return "Đã đào tạo"
        if start and today < start:
            return "Chưa đào tạo"
        return "Đang đào tạo"

    # ---- tra cứu ----
    def search_by_teacher(self, name):
        """Trả về list các dòng (mỗi dòng = 1 khóa mà giáo viên này tham gia)."""
        name = (name or "").strip().lower()
        rows = []
        for c in self.courses:
            for g in c.get("groups", []):
                if name and name not in g.get("giao_vien", "").lower():
                    continue
                if not name:
                    continue
                rows.append(
                    {
                        "giao_vien": g["giao_vien"],
                        "ma_khoa": c["ma_khoa"],
                        "lop": c["lop"],
                        "xe": g["xe"],
                        "sdt": g.get("sdt", ""),
                        "so_hoc_vien": len(g.get("hoc_vien", [])),
                        "tu_ngay": c.get("tu_ngay", ""),
                        "den_ngay": c.get("den_ngay", ""),
                        "status": self.status_of(c),
                        "course": c,
                        "group": g,
                    }
                )
        return rows

    def search_by_course(self, ma_khoa):
        """Trả về list các dòng (mỗi dòng = 1 giáo viên/xe trong khóa đó)."""
        c = self.find_course(ma_khoa)
        if not c:
            return []
        rows = []
        for g in c.get("groups", []):
            rows.append(
                {
                    "giao_vien": g["giao_vien"],
                    "ma_khoa": c["ma_khoa"],
                    "lop": c["lop"],
                    "xe": g["xe"],
                    "sdt": g.get("sdt", ""),
                    "so_hoc_vien": len(g.get("hoc_vien", [])),
                    "tu_ngay": c.get("tu_ngay", ""),
                    "den_ngay": c.get("den_ngay", ""),
                    "status": self.status_of(c),
                    "course": c,
                    "group": g,
                }
            )
        return rows
