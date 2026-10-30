"""Tab NGUỒN DỮ LIỆU & CẬP NHẬT WEB: khai báo tất cả nguồn dữ liệu rồi bấm 1
nút để đẩy lên trang web (GitHub Pages).

Nguồn dữ liệu gồm:
- File Excel "BIÊN CHẾ XE KHÓA xxxx.xlsx" (mỗi khóa 1 file, thêm/xóa được)
- File PDF "LICH HOC THUC HANH xxxx.pdf" (mỗi khóa 1 file, thêm/xóa được)
- File DSGV_*.xml: danh sách TOÀN BỘ giáo viên (nguồn mã QR chính thức)
- File DSXTL_*.xml: danh sách xe tập lái (đối chiếu biển số)
- Thư mục hồ sơ cá nhân giáo viên (.pdf theo tên)

Ảnh đại diện, hạng lái xe dạy, xuất thẻ giáo viên: xem tab DANH SÁCH GIÁO
VIÊN (tab_danh_sach_gv.py). Link giấy tờ xe: xem tab DANH SÁCH XE
(tab_tra_cuu_xe.py).

Người dùng không cần biết git: toàn bộ convert -> JSON công khai ->
git commit/push chạy ngầm khi bấm nút "Cập nhật && Đăng lên web".
"""
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import publish_data
import git_publish
from style import icon as _icon


class _FileListPicker(QGroupBox):
    """Khung: danh sách nhiều file + nút Thêm / Xóa mục chọn."""

    def __init__(self, title, file_filter, parent=None):
        super().__init__(title, parent)
        self.file_filter = file_filter
        layout = QVBoxLayout(self)

        self.lst = QListWidget()
        self.lst.setFixedHeight(90)
        self.lst.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.lst)

        btn_row = QHBoxLayout()
        btn_add = QPushButton(_icon(self, QStyle.StandardPixmap.SP_FileIcon), "Thêm...")
        btn_add.clicked.connect(self._on_add)
        btn_row.addWidget(btn_add)
        btn_remove = QPushButton(_icon(self, QStyle.StandardPixmap.SP_TrashIcon), "Xóa")
        btn_remove.clicked.connect(self._on_remove)
        btn_row.addWidget(btn_remove)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

    def _on_add(self):
        existing = self.paths()
        start_dir = str(Path(existing[0]).parent) if existing else ""
        files, _ = QFileDialog.getOpenFileNames(
            self, f"Chọn file - {self.title()}", start_dir, self.file_filter
        )
        if not files:
            return
        existing_set = set(existing)
        for f in files:
            if f not in existing_set:
                self.lst.addItem(f)

    def _on_remove(self):
        items = self.lst.selectedItems()
        if not items:
            return
        ten_file = "\n".join(f"- {Path(i.text()).name}" for i in items)
        confirm = QMessageBox.question(
            self, "Xác nhận",
            f"Bỏ {len(items)} file khỏi danh sách này?\n{ten_file}\n\n"
            "(Chỉ bỏ khỏi danh sách đang chọn trong app, không xóa file gốc trên máy.)",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        for item in items:
            self.lst.takeItem(self.lst.row(item))

    def paths(self):
        return [self.lst.item(i).text() for i in range(self.lst.count())]

    def set_paths(self, paths):
        self.lst.clear()
        for p in paths:
            self.lst.addItem(str(p))


class _SinglePathPicker(QGroupBox):
    """Khung: 1 đường dẫn (file hoặc thư mục) + nút Chọn."""

    def __init__(self, title, mode="file", file_filter="", parent=None):
        super().__init__(title, parent)
        self.mode = mode
        self.file_filter = file_filter
        layout = QHBoxLayout(self)
        self.txt = QLineEdit()
        self.txt.setReadOnly(True)
        layout.addWidget(self.txt, 1)
        btn = QPushButton(_icon(self, QStyle.StandardPixmap.SP_DirOpenIcon), "Chọn...")
        btn.clicked.connect(self._on_choose)
        layout.addWidget(btn)

    def _on_choose(self):
        if self.mode == "file":
            start_dir = str(Path(self.txt.text()).parent) if self.txt.text() else ""
            path, _ = QFileDialog.getOpenFileName(
                self, f"Chọn file - {self.title()}", start_dir, self.file_filter
            )
        else:
            start_dir = self.txt.text() or ""
            path = QFileDialog.getExistingDirectory(
                self, f"Chọn thư mục - {self.title()}", start_dir
            )
        if path:
            self.txt.setText(path)

    def path(self):
        return self.txt.text().strip()

    def set_path(self, path):
        self.txt.setText(str(path) if path else "")


class _PublishWorker(QThread):
    finished_ok = Signal(dict)
    finished_err = Signal(str)

    def __init__(self, sources, parent=None):
        super().__init__(parent)
        self.sources = sources

    def run(self):
        try:
            result = publish_data.run_pipeline(self.sources)
            ok, message = git_publish.push_public_data(
                f"Cập nhật số liệu giáo viên ({result['generated_at']})"
            )
            result["git_ok"] = ok
            result["git_message"] = message
            self.finished_ok.emit(result)
        except Exception as exc:  # báo lỗi rõ ràng, không để app crash
            self.finished_err.emit(str(exc))


class CapNhatWebTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self._build_ui()
        self._load_sources()

    def _build_ui(self):
        # Nội dung tab ngày càng dài (nhiều khung cài đặt) nên bọc trong
        # QScrollArea - tránh bị tràn/đè lên nhau khi cửa sổ không đủ cao.
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        outer = QVBoxLayout(content)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(10)

        self.pick_bien_che = _FileListPicker(
            'File Excel "BIÊN CHẾ XE KHÓA ..." (mỗi khóa 1 file)',
            "Excel Files (*.xlsx)",
        )
        outer.addWidget(self.pick_bien_che)

        self.pick_lich_hoc = _FileListPicker(
            'File PDF "LICH HOC THUC HANH ..." (mỗi khóa 1 file)',
            "PDF Files (*.pdf)",
        )
        outer.addWidget(self.pick_lich_hoc)

        row1 = QHBoxLayout()
        self.pick_dsgv = _SinglePathPicker(
            "Danh sách giáo viên (DSGV_*.xml)", mode="file", file_filter="XML Files (*.xml)"
        )
        row1.addWidget(self.pick_dsgv)
        self.pick_dsxtl = _SinglePathPicker(
            "Danh sách xe tập lái (DSXTL_*.xml)", mode="file", file_filter="XML Files (*.xml)"
        )
        row1.addWidget(self.pick_dsxtl)
        outer.addLayout(row1)

        self.pick_ho_so_folder = _SinglePathPicker(
            "Thư mục hồ sơ cá nhân giáo viên", mode="folder"
        )
        outer.addWidget(self.pick_ho_so_folder)

        pass_box = QGroupBox(
            "Mật khẩu xem hồ sơ cá nhân giáo viên (áp dụng cho mọi giáo viên)"
        )
        pass_layout = QHBoxLayout(pass_box)
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setPlaceholderText(
            "Để trống = ẩn hoàn toàn mục hồ sơ cá nhân trên trang web"
        )
        settings = publish_data.load_app_settings()
        self.txt_password.setText(settings.get("ho_so_password", ""))
        pass_layout.addWidget(self.txt_password)
        self.chk_show_password = QCheckBox("Hiện mật khẩu")
        self.chk_show_password.setChecked(False)
        self.chk_show_password.toggled.connect(self._on_toggle_show_password)
        pass_layout.addWidget(self.chk_show_password)
        btn_save_password = QPushButton(_icon(self, QStyle.StandardPixmap.SP_DialogSaveButton), "Lưu")
        btn_save_password.clicked.connect(self._on_save_password)
        pass_layout.addWidget(btn_save_password)
        outer.addWidget(pass_box)

        box = QGroupBox("Đăng số liệu giáo viên lên trang web")
        box_layout = QVBoxLayout(box)
        box_layout.addWidget(
            QLabel(
                "Kiểm tra lại các nguồn dữ liệu ở trên rồi bấm nút dưới đây để\n"
                "đăng số liệu lên trang web. Mã QR của mỗi giáo viên cố định\n"
                "theo mã GV chính thức (DSGV), không đổi giữa các lần cập nhật."
            )
        )
        self.btn_publish = QPushButton(
            _icon(self, QStyle.StandardPixmap.SP_ArrowUp), "Cập nhật && Đăng lên web"
        )
        self.btn_publish.setObjectName("primary")
        self.btn_publish.clicked.connect(self._on_publish_clicked)
        box_layout.addWidget(self.btn_publish)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(160)
        box_layout.addWidget(self.log)

        outer.addWidget(box)
        outer.addStretch(1)

    def _load_sources(self):
        sources = publish_data.load_data_sources()
        self.pick_bien_che.set_paths(sources.get("bien_che_files", []))
        self.pick_lich_hoc.set_paths(sources.get("lich_hoc_files", []))
        self.pick_dsgv.set_path(sources.get("dsgv_file", ""))
        self.pick_dsxtl.set_path(sources.get("dsxtl_file", ""))
        self.pick_ho_so_folder.set_path(sources.get("ho_so_folder", ""))

    def _current_sources(self):
        return {
            "bien_che_files": self.pick_bien_che.paths(),
            "lich_hoc_files": self.pick_lich_hoc.paths(),
            "dsgv_file": self.pick_dsgv.path(),
            "dsxtl_file": self.pick_dsxtl.path(),
            "ho_so_folder": self.pick_ho_so_folder.path(),
        }

    def _on_toggle_show_password(self, checked):
        self.txt_password.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )

    def _on_save_password(self):
        settings = publish_data.load_app_settings()
        settings["ho_so_password"] = self.txt_password.text().strip()
        publish_data.save_app_settings(settings)
        QMessageBox.information(
            self,
            "Đã lưu",
            "Đã lưu mật khẩu. Bấm 'Cập nhật && Đăng lên web' để áp dụng lên trang web.",
        )

    def _on_publish_clicked(self):
        sources = self._current_sources()
        if not sources["bien_che_files"]:
            QMessageBox.warning(
                self, "Thiếu dữ liệu", "Hãy thêm ít nhất 1 file 'BIÊN CHẾ XE KHÓA ...'."
            )
            return
        if not sources["dsgv_file"]:
            QMessageBox.warning(
                self, "Thiếu dữ liệu", "Hãy chọn file danh sách giáo viên (DSGV_*.xml)."
            )
            return

        publish_data.save_data_sources(sources)

        self.btn_publish.setEnabled(False)
        self.btn_publish.setText("Đang cập nhật...")
        self.log.append("Đang xử lý, vui lòng chờ...")

        self.worker = _PublishWorker(sources)
        self.worker.finished_ok.connect(self._on_done)
        self.worker.finished_err.connect(self._on_error)
        self.worker.start()

    def _on_done(self, result):
        self.btn_publish.setEnabled(True)
        self.btn_publish.setText("Cập nhật && Đăng lên web")

        lines = [
            f"Đã xử lý xong lúc {result['generated_at']} "
            f"(từ {result['so_file_excel']} file Excel)."
        ]
        lines.append(f"Tổng số giáo viên: {result['so_giao_vien']}.")
        if result["ma_khoa_trung"]:
            lines.append(
                "CẢNH BÁO: các mã khóa bị trùng giữa các file (lấy dữ liệu file sau cùng): "
                + ", ".join(result["ma_khoa_trung"])
            )
        if result.get("canh_bao"):
            lines.append("CẢNH BÁO dữ liệu (kiểm tra lại nguồn):")
            for w in result["canh_bao"]:
                lines.append("  - " + w)
        if result["giao_vien_moi"]:
            lines.append("Giáo viên MỚI (đã tạo mã QR trong thư mục qr_codes/):")
            for name, tid in result["giao_vien_moi"]:
                lines.append(f"  - {name} ({tid}.png)")
        if result.get("giao_vien_doi_ten"):
            lines.append("Đã cập nhật lại tên in trên mã QR (link/mã QR không đổi):")
            for ten_cu, ten_moi, tid in result["giao_vien_doi_ten"]:
                lines.append(f"  - {tid}: '{ten_cu}' -> '{ten_moi}'")
        lines.append(result["git_message"])
        self.log.append("\n".join(lines))

        if result["git_ok"]:
            QMessageBox.information(self, "Hoàn tất", "\n".join(lines))
        else:
            QMessageBox.warning(self, "Chưa đăng lên web được", result["git_message"])

    def _on_error(self, message):
        self.btn_publish.setEnabled(True)
        self.btn_publish.setText("Cập nhật && Đăng lên web")
        self.log.append(f"LỖI: {message}")
        QMessageBox.critical(self, "Lỗi", message)
