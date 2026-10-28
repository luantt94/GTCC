"""Tab CẬP NHẬT WEB: 1 nút để đẩy số liệu giáo viên lên trang web (GitHub Pages).

Người dùng chỉ cần: mở & lưu file Excel như bình thường, rồi bấm nút này.
Toàn bộ convert Excel -> JSON công khai -> git commit/push chạy ngầm,
không cần biết gì về git.
"""
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
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

    def run(self):
        try:
            result = publish_data.run_pipeline()
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

    def _build_ui(self):
        outer = QVBoxLayout(self)

        box = QGroupBox("Đăng số liệu giáo viên lên trang web")
        box_layout = QVBoxLayout(box)

        box_layout.addWidget(
            QLabel(
                "Sau khi đã cập nhật file Excel, bấm nút dưới đây để đăng số liệu\n"
                "mới nhất (tên giáo viên + số học viên đang dạy) lên trang web.\n"
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

    def _on_publish_clicked(self):
        self.btn_publish.setEnabled(False)
        self.btn_publish.setText("Đang cập nhật...")
        self.log.append("Đang xử lý, vui lòng chờ...")

        self.worker = _PublishWorker()
        self.worker.finished_ok.connect(self._on_done)
        self.worker.finished_err.connect(self._on_error)
        self.worker.start()

    def _on_done(self, result):
        self.btn_publish.setEnabled(True)
        self.btn_publish.setText("Cập nhật && Đăng lên web")

        lines = [f"Đã xử lý xong lúc {result['generated_at']}."]
        lines.append(f"Tổng số giáo viên: {result['so_giao_vien']}.")
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
