import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTabWidget

from data_model import DataModel
from tab_cap_nhat_web import CapNhatWebTab
from tab_lich_hoc import LichHocTab
from tab_phan_xe import PhanXeTab
from tab_tra_cuu import TraCuuTab

APP_DIR = Path(__file__).resolve().parent
DATA_JSON = APP_DIR / "data.json"


class MainWindow(QMainWindow):
    def __init__(self, model):
        super().__init__()
        self.setWindowTitle("Quản lý đào tạo lái xe - Tra cứu giáo viên / xe / lịch học")
        self.resize(1200, 750)

        tabs = QTabWidget()
        tabs.addTab(TraCuuTab(model), "TRA CỨU")
        tabs.addTab(PhanXeTab(model), "PHÂN XE")
        tabs.addTab(LichHocTab(model), "LỊCH HỌC")
        tabs.addTab(CapNhatWebTab(), "CẬP NHẬT WEB")
        self.setCentralWidget(tabs)


def main():
    app = QApplication(sys.argv)

    if not DATA_JSON.exists():
        QMessageBox.critical(
            None,
            "Thiếu dữ liệu",
            f"Không tìm thấy {DATA_JSON.name}.\n"
            "Hãy chạy trước: python convert_excel_to_json.py",
        )
        sys.exit(1)

    model = DataModel(DATA_JSON)
    window = MainWindow(model)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
