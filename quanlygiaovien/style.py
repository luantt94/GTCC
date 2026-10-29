"""Giao diện chung cho toàn app - 1 stylesheet (QSS) áp dụng 1 lần lúc khởi
động (xem main.py: apply_style(app)), không cần sửa từng tab."""

APP_QSS = """
* {
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 10.5pt;
}

QWidget {
    background: #f4f5f7;
    color: #1f2328;
}

QTabWidget::pane {
    border: 1px solid #d9dce1;
    border-radius: 6px;
    background: #ffffff;
    top: -1px;
}

QTabBar::tab {
    background: #e7e9ee;
    color: #4a5160;
    padding: 9px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background: #ffffff;
    color: #1f2328;
    border: 1px solid #d9dce1;
    border-bottom: none;
}

QTabBar::tab:hover:!selected {
    background: #dde1e8;
}

QGroupBox {
    background: #ffffff;
    border: 1px solid #dde1e8;
    border-radius: 8px;
    margin-top: 14px;
    padding: 14px 10px 10px 10px;
    font-weight: 600;
    color: #2c3340;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 6px;
    color: #3457d5;
}

QLabel {
    background: transparent;
}

QLineEdit, QComboBox, QTextEdit, QListWidget, QTableWidget {
    background: #ffffff;
    border: 1px solid #d0d4db;
    border-radius: 5px;
    padding: 5px 8px;
    selection-background-color: #3457d5;
    selection-color: #ffffff;
}

QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
    border: 1px solid #3457d5;
}

QLineEdit:read-only {
    background: #f4f5f7;
    color: #5b6372;
}

QComboBox::drop-down {
    border: none;
    width: 22px;
}

QPushButton {
    background: #ffffff;
    border: 1px solid #c7ccd4;
    border-radius: 6px;
    padding: 6px 14px;
    color: #2c3340;
    font-weight: 600;
}

QPushButton:hover {
    background: #eef1f8;
    border-color: #a9b2c3;
}

QPushButton:pressed {
    background: #e2e6ef;
}

QPushButton:disabled {
    color: #a3a9b3;
    background: #f0f1f3;
    border-color: #e1e3e8;
}

QPushButton#primary {
    background: #2f6fed;
    border: 1px solid #2659c4;
    color: #ffffff;
    padding: 9px 18px;
    font-size: 11pt;
}

QPushButton#primary:hover {
    background: #4a82f0;
}

QPushButton#primary:pressed {
    background: #2659c4;
}

QPushButton#danger {
    color: #b3261e;
}

QTableWidget {
    gridline-color: #e7e9ee;
    alternate-background-color: #f7f8fa;
}

QHeaderView::section {
    background: #eef1f8;
    color: #2c3340;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #d9dce1;
    font-weight: 600;
}

QScrollBar:vertical {
    width: 11px;
    background: transparent;
}

QScrollBar::handle:vertical {
    background: #c7ccd4;
    border-radius: 5px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background: #a9b2c3;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


def apply_style(app):
    app.setStyleSheet(APP_QSS)
