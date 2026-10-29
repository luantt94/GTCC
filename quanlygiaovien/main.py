import json
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

from data_model import DataModel
from tab_cap_nhat_web import CapNhatWebTab
from tab_lich_hoc import LichHocTab
from tab_phan_xe import PhanXeTab
from tab_tra_cuu import TraCuuTab
from tab_tra_cuu_xe import TraCuuXeTab

APP_DIR = Path(__file__).resolve().parent
DATA_JSON = APP_DIR / "data.json"


class MainWindow(QMainWindow):
    def __init__(self, model):
        super().__init__()
        self.setWindowTitle("Quản lý đào tạo lái xe - Tra cứu giáo viên / xe / lịch học")
        self.resize(1200, 750)

        tabs = QTabWidget()
        tabs.addTab(CapNhatWebTab(), "CẬP NHẬT WEB")
        tabs.addTab(TraCuuTab(model), "TRA CỨU")
        tabs.addTab(PhanXeTab(model), "PHÂN XE")
        tabs.addTab(TraCuuXeTab(model), "TRA CỨU XE")
        tabs.addTab(LichHocTab(model), "LỊCH HỌC")
        self.setCentralWidget(tabs)


def main():
    app = QApplication(sys.argv)

    if not DATA_JSON.exists():
        # Chưa đăng dữ liệu lần nào - tạo file rỗng để mở app được, người
        # dùng vào tab "CẬP NHẬT WEB" chọn nguồn dữ liệu rồi bấm đăng.
        DATA_JSON.write_text(
            json.dumps(
                {"generated_at": "", "source_files": [], "courses": []},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    model = DataModel(DATA_JSON)
    window = MainWindow(model)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
