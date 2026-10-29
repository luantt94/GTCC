from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import attach_files
import publish_data
import roster_xml

HISTORY_COLUMNS = ["Mã khóa", "Lớp", "Giáo viên", "SĐT", "Thời gian học", "Số HV", "Tình trạng"]


class TraCuuXeTab(QWidget):
    """Tab TRA CỨU XE: chọn 1 xe tập lái, xem nhãn hiệu/loại xe (theo DSXTL),
    toàn bộ lịch sử giáo viên/khóa đã dùng xe này, và nội dung giấy tờ xe."""

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        sources = publish_data.load_data_sources()
        self.xe_folder = sources.get("xe_folder", "")
        dsxtl_file = sources.get("dsxtl_file", "")
        self.dsxtl = (
            roster_xml.parse_dsxtl(dsxtl_file)
            if dsxtl_file and Path(dsxtl_file).exists()
            else {}
        )
        self.vehicles = self._build_vehicle_list()
        self.current_doc_path = None
        self._build_ui()
        self._load_combo()

    def _build_vehicle_list(self):
        """Gộp danh sách xe từ DSXTL (nguồn chính thức) với mọi biển số xuất
        hiện trong các khóa (phòng khi biển số chưa kịp cập nhật vào DSXTL)."""
        vehicles = {}
        for bien_so, info in self.dsxtl.items():
            plate = attach_files.normalize_plate(bien_so)
            vehicles[plate] = {
                "bien_so": bien_so,
                "nhan_hieu": info.get("nhan_hieu", ""),
                "loai_xe": info.get("loai_xe", ""),
                "in_dsxtl": True,
            }
        for c in self.model.all_courses():
            for g in c.get("groups", []):
                xe = g.get("xe", "")
                if not xe:
                    continue
                plate = attach_files.normalize_plate(xe)
                if plate and plate not in vehicles:
                    vehicles[plate] = {
                        "bien_so": xe,
                        "nhan_hieu": "",
                        "loai_xe": "",
                        "in_dsxtl": False,
                    }
        return dict(sorted(vehicles.items(), key=lambda kv: kv[1]["bien_so"]))

    def _build_ui(self):
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Chọn xe (biển số):"))
        self.cbo_xe = QComboBox()
        self.cbo_xe.setEditable(True)
        self.cbo_xe.setInsertPolicy(QComboBox.NoInsert)
        self.cbo_xe.currentIndexChanged.connect(self._on_xe_changed)
        top.addWidget(self.cbo_xe, 1)
        self.btn_open_doc = QPushButton("Mở giấy tờ xe...")
        self.btn_open_doc.setEnabled(False)
        self.btn_open_doc.clicked.connect(self._open_doc_external)
        top.addWidget(self.btn_open_doc)
        layout.addLayout(top)

        self.lbl_info = QLabel("")
        layout.addWidget(self.lbl_info)

        splitter = QSplitter(Qt.Vertical)

        self.table = QTableWidget()
        self.table.setColumnCount(len(HISTORY_COLUMNS))
        self.table.setHorizontalHeaderLabels(HISTORY_COLUMNS)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        splitter.addWidget(self.table)

        self.doc_stack = QStackedWidget()

        self.lbl_no_doc = QLabel("Chưa có file giấy tờ xe khớp với biển số này.")
        self.lbl_no_doc.setAlignment(Qt.AlignCenter)
        self.doc_stack.addWidget(self.lbl_no_doc)

        self.pdf_doc = QPdfDocument(self)
        self.pdf_view = QPdfView()
        self.pdf_view.setDocument(self.pdf_doc)
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        self.doc_stack.addWidget(self.pdf_view)

        self.lbl_doc_external = QLabel("")
        self.lbl_doc_external.setAlignment(Qt.AlignCenter)
        self.doc_stack.addWidget(self.lbl_doc_external)

        splitter.addWidget(self.doc_stack)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, 1)

    def _load_combo(self):
        self.cbo_xe.clear()
        for plate, v in self.vehicles.items():
            label = v["bien_so"] if v["in_dsxtl"] else f"{v['bien_so']} (chưa có trong DSXTL)"
            self.cbo_xe.addItem(label, plate)

    def _on_xe_changed(self, _index):
        plate = self.cbo_xe.currentData()
        v = self.vehicles.get(plate)
        if not v:
            self.lbl_info.setText("")
            self._render_history(None)
            self._show_doc(None)
            return

        if v["in_dsxtl"]:
            self.lbl_info.setText(f"Nhãn hiệu: {v['nhan_hieu']}  |  Loại xe: {v['loai_xe']}")
        else:
            self.lbl_info.setText(
                "CẢNH BÁO: biển số này không có trong DSXTL "
                "(kiểm tra lại chính tả biển số trong Excel)."
            )

        self._render_history(plate)

        doc_path = attach_files.find_xe_doc(v["bien_so"], self.xe_folder)
        self._show_doc(doc_path)

    def _render_history(self, plate):
        rows = []
        if plate:
            for c in self.model.all_courses():
                for g in c.get("groups", []):
                    if attach_files.normalize_plate(g.get("xe", "")) != plate:
                        continue
                    rows.append(
                        {
                            "ma_khoa": c["ma_khoa"],
                            "lop": c.get("lop", ""),
                            "giao_vien": g.get("giao_vien", ""),
                            "sdt": g.get("sdt", ""),
                            "thoi_gian": f"{c.get('tu_ngay', '')} → {c.get('den_ngay', '')}",
                            "so_hoc_vien": str(len(g.get("hoc_vien", []))),
                            "status": self.model.status_of(c),
                        }
                    )

        self.table.setRowCount(len(rows))
        for row_idx, r in enumerate(rows):
            values = [
                r["ma_khoa"],
                r["lop"],
                r["giao_vien"],
                r["sdt"],
                r["thoi_gian"],
                r["so_hoc_vien"],
                r["status"],
            ]
            for col, val in enumerate(values):
                self.table.setItem(row_idx, col, QTableWidgetItem(val))
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def _show_doc(self, doc_path):
        self.current_doc_path = doc_path
        self.btn_open_doc.setEnabled(doc_path is not None)
        if doc_path is None:
            self.doc_stack.setCurrentWidget(self.lbl_no_doc)
            return
        if doc_path.suffix.lower() == ".pdf":
            self.pdf_doc.load(str(doc_path))
            self.doc_stack.setCurrentWidget(self.pdf_view)
        else:
            self.lbl_doc_external.setText(
                f"Giấy tờ xe: {doc_path.name}\n(bấm \"Mở giấy tờ xe...\" để mở bằng Word)"
            )
            self.doc_stack.setCurrentWidget(self.lbl_doc_external)

    def _open_doc_external(self):
        if self.current_doc_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.current_doc_path)))
