from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import attach_files
import publish_data
import roster_xml
from style import icon as _icon

HISTORY_COLUMNS = ["Mã khóa", "Lớp", "Giáo viên", "SĐT", "Thời gian học", "Số HV", "Tình trạng"]


class TraCuuXeTab(QWidget):
    """Tab DANH SÁCH XE: danh sách toàn bộ xe tập lái (từ DSXTL) hiện sẵn
    bên trái để chọn nhanh; bấm vào 1 xe là xem nhãn hiệu/loại xe, toàn bộ
    lịch sử giáo viên/khóa đã dùng xe này, nội dung giấy tờ xe cục bộ (nếu
    có), và nhập/sửa link giấy tờ xe hiện công khai trên trang web."""

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
        self._load_list()

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
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(main_splitter, 1)

        # Danh sách xe hiện sẵn toàn bộ bên trái (thay vì giấu trong dropdown)
        # để chọn nhanh - giống cách làm ở tab DANH SÁCH GIÁO VIÊN.
        self.list_widget = QListWidget()
        self.list_widget.setMinimumWidth(220)
        self.list_widget.setMaximumWidth(320)
        self.list_widget.currentItemChanged.connect(self._on_xe_changed)
        main_splitter.addWidget(self.list_widget)

        right = QWidget()
        right_layout = QVBoxLayout(right)

        top = QHBoxLayout()
        self.lbl_info = QLabel("")
        top.addWidget(self.lbl_info, 1)
        self.btn_open_doc = QPushButton("Mở giấy tờ xe...")
        self.btn_open_doc.setEnabled(False)
        self.btn_open_doc.clicked.connect(self._open_doc_external)
        top.addWidget(self.btn_open_doc)
        right_layout.addLayout(top)

        link_row = QHBoxLayout()
        link_row.addWidget(QLabel("Link giấy tờ xe (hiện trên trang web):"))
        self.txt_xe_link = QLineEdit()
        self.txt_xe_link.setPlaceholderText("https://... (vd trang tra cứu xe của Sở)")
        link_row.addWidget(self.txt_xe_link, 1)
        self.btn_save_xe_link = QPushButton(
            _icon(self, QStyle.StandardPixmap.SP_DialogSaveButton), "Lưu link"
        )
        self.btn_save_xe_link.clicked.connect(self._on_save_xe_link)
        link_row.addWidget(self.btn_save_xe_link)
        right_layout.addLayout(link_row)

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
        right_layout.addWidget(splitter, 1)

        main_splitter.addWidget(right)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 3)

    def _load_list(self):
        self.list_widget.clear()
        for plate, v in self.vehicles.items():
            label = v["bien_so"] if v["in_dsxtl"] else f"{v['bien_so']} (chưa có trong DSXTL)"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, plate)
            self.list_widget.addItem(item)
        if not self.vehicles:
            self.lbl_info.setText(
                "Chưa có danh sách xe - chọn file DSXTL_*.xml ở tab CẬP NHẬT WEB "
                "rồi khởi động lại app."
            )

    def _on_xe_changed(self, current, _previous=None):
        plate = current.data(Qt.ItemDataRole.UserRole) if current else None
        v = self.vehicles.get(plate)
        if not v:
            self.lbl_info.setText("")
            self.txt_xe_link.setText("")
            self.btn_save_xe_link.setEnabled(False)
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

        self.btn_save_xe_link.setEnabled(True)
        self.txt_xe_link.setText(publish_data.get_xe_link(plate))

        self._render_history(plate)

        doc_path = attach_files.find_xe_doc(v["bien_so"], self.xe_folder)
        self._show_doc(doc_path)

    def _on_save_xe_link(self):
        current = self.list_widget.currentItem()
        plate = current.data(Qt.ItemDataRole.UserRole) if current else None
        if not plate:
            return
        publish_data.set_xe_link(plate, self.txt_xe_link.text())
        QMessageBox.information(
            self, "Đã lưu",
            "Đã lưu link giấy tờ xe. Bấm 'Cập nhật && Đăng lên web' ở tab CẬP NHẬT WEB "
            "để áp dụng lên trang web.",
        )

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
