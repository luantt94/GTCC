"""Tab CẬP NHẬT WEB: chọn 1 hoặc nhiều file Excel rồi bấm 1 nút để đẩy số liệu
giáo viên lên trang web (GitHub Pages).

Người dùng chỉ cần: chọn file Excel (nhớ lựa chọn cho lần sau), rồi bấm nút.
Toàn bộ convert Excel -> JSON công khai -> git commit/push chạy ngầm,
không cần biết gì về git.
"""
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import publish_data
import git_publish


class _PublishWorker(QThread):
    finished_ok = Signal(dict)
    finished_err = Signal(str)

    def __init__(self, excel_paths, parent=None):
        super().__init__(parent)
        self.excel_paths = excel_paths

    def run(self):
        try:
            result = publish_data.run_pipeline(self.excel_paths)
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
        self.excel_paths = publish_data.load_selected_excel_files()
        self._build_ui()
        self._refresh_file_list()

    def _build_ui(self):
        outer = QVBoxLayout(self)

        file_box = QGroupBox("File Excel nguồn (có thể chọn nhiều file, sẽ được gộp chung)")
        file_layout = QVBoxLayout(file_box)

        self.lst_files = QListWidget()
        self.lst_files.setFixedHeight(90)
        file_layout.addWidget(self.lst_files)

        btn_row = QHBoxLayout()
        btn_choose = QPushButton("Chọn file Excel...")
        btn_choose.clicked.connect(self._on_choose_files)
        btn_row.addWidget(btn_choose)
        btn_row.addStretch(1)
        file_layout.addLayout(btn_row)

        outer.addWidget(file_box)

        box = QGroupBox("Đăng số liệu giáo viên lên trang web")
        box_layout = QVBoxLayout(box)

        box_layout.addWidget(
            QLabel(
                "Sau khi đã chọn đúng file Excel và lưu dữ liệu mới nhất, bấm nút\n"
                "dưới đây để đăng số liệu lên trang web.\n"
                "Mã QR của giáo viên không đổi, chỉ nội dung trang được cập nhật."
            )
        )

        self.btn_publish = QPushButton("Cập nhật && Đăng lên web")
        self.btn_publish.clicked.connect(self._on_publish_clicked)
        box_layout.addWidget(self.btn_publish)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(160)
        box_layout.addWidget(self.log)

        outer.addWidget(box)
        outer.addStretch(1)

    def _refresh_file_list(self):
        self.lst_files.clear()
        if not self.excel_paths:
            self.lst_files.addItem("(Chưa chọn file nào)")
            return
        for p in self.excel_paths:
            self.lst_files.addItem(Path(p).name)

    def _on_choose_files(self):
        start_dir = str(Path(self.excel_paths[0]).parent) if self.excel_paths else ""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Chọn file Excel", start_dir, "Excel Files (*.xlsx)"
        )
        if not files:
            return
        self.excel_paths = files
        publish_data.save_selected_excel_files(files)
        self._refresh_file_list()

    def _on_publish_clicked(self):
        if not self.excel_paths:
            QMessageBox.warning(
                self, "Chưa chọn file", "Hãy bấm 'Chọn file Excel...' trước."
            )
            return

        self.btn_publish.setEnabled(False)
        self.btn_publish.setText("Đang cập nhật...")
        self.log.append("Đang xử lý, vui lòng chờ...")

        self.worker = _PublishWorker(self.excel_paths)
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
        if result["giao_vien_moi"]:
            lines.append("Giáo viên MỚI (đã tạo mã QR trong thư mục qr_codes/):")
            for name, tid in result["giao_vien_moi"]:
                lines.append(f"  - {name} ({tid}.png)")
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
