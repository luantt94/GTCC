from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

COLUMNS = ["Ngày", "Thứ", "Buổi sáng", "Buổi chiều", "Buổi tối"]


class LichHocTab(QWidget):
    """Tab LỊCH HỌC: chọn khóa, xem lịch học thực hành theo từng ngày."""

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self._build_ui()
        self._load_courses()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Chọn khóa:"))
        self.cbo_course = QComboBox()
        self.cbo_course.currentIndexChanged.connect(self._on_course_changed)
        top.addWidget(self.cbo_course, 1)

        top.addWidget(QLabel("Tháng:"))
        self.cbo_month = QComboBox()
        self.cbo_month.addItem("Tất cả", None)
        self.cbo_month.currentIndexChanged.connect(self._render_table)
        top.addWidget(self.cbo_month)
        layout.addLayout(top)

        self.lbl_summary = QLabel("")
        layout.addWidget(self.lbl_summary)

        self.table = QTableWidget()
        self.table.setColumnCount(len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

    def _load_courses(self):
        self.cbo_course.clear()
        for c in self.model.all_courses():
            label = f"{c['ma_khoa']} ({c['lop']})"
            self.cbo_course.addItem(label, c["ma_khoa"])

    def _on_course_changed(self, _index):
        ma_khoa = self.cbo_course.currentData()
        course = self.model.find_course(ma_khoa)
        self.cbo_month.blockSignals(True)
        self.cbo_month.clear()
        self.cbo_month.addItem("Tất cả", None)
        if course:
            months = sorted({d["date"][:7] for d in course.get("lich_hoc", [])})
            for m in months:
                year, month = m.split("-")
                self.cbo_month.addItem(f"Tháng {int(month)}/{year}", m)
        self.cbo_month.blockSignals(False)
        self._render_table()

    def _render_table(self, *_args):
        ma_khoa = self.cbo_course.currentData()
        course = self.model.find_course(ma_khoa)
        self.table.setRowCount(0)
        if not course:
            self.lbl_summary.setText("")
            return

        month_filter = self.cbo_month.currentData()
        days = course.get("lich_hoc", [])
        if month_filter:
            days = [d for d in days if d["date"].startswith(month_filter)]

        self.lbl_summary.setText(
            f"Lớp {course['lop']} | Thời gian: {course['tu_ngay']} → {course['den_ngay']} | "
            f"Số buổi học ghi nhận: {sum(1 for d in days if d['sang'] or d['chieu'] or d['toi'])}/{len(days)} ngày"
        )

        self.table.setRowCount(len(days))
        for row, d in enumerate(days):
            values = [
                f"{d['label']} ({d['date']})" if d["label"] else d["date"],
                d["thu"],
                d["sang"],
                d["chieu"],
                d["toi"],
            ]
            has_session = bool(d["sang"] or d["chieu"] or d["toi"])
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                if not has_session:
                    item.setForeground(Qt.gray)
                self.table.setItem(row, col, item)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
