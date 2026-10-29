"""Sinh ảnh/PDF "Phù hiệu giáo viên dạy lái xe" (Mẫu số 01): thẻ 85mm x
50mm có ảnh thẻ 3x4cm, tên cơ quan/cơ sở đào tạo, họ tên, hạng lái xe dạy,
và mã QR tra cứu thông tin (cùng link với mã QR phát cho giáo viên).

Phần mềm KHÔNG tự vẽ dấu giáp lai (con dấu đóng đè lên ảnh thẻ) - đây là
thao tác đóng dấu thật sau khi in, ngoài phạm vi phần mềm.

Dữ liệu ảnh + hạng lái xe dạy lấy từ giao_vien_extra.json / anh_gv/ (xem
publish_data.py) - tách riêng khỏi DSGV/DSXTL để không mất khi đổi file XML.
"""
import os
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DPI = 300
_MM_TO_PX = DPI / 25.4

CARD_W_MM, CARD_H_MM = 85, 50
PHOTO_W_MM, PHOTO_H_MM = 30, 40
PAGE_W_MM, PAGE_H_MM = 210, 297  # A4 dọc
GRID_COLS, GRID_ROWS = 2, 4
CARDS_PER_PAGE = GRID_COLS * GRID_ROWS


def _mm(value):
    return round(value * _MM_TO_PX)


@dataclass
class CardData:
    ma_gv: str
    ten: str
    hang: str
    photo_path: "Path | None"
    org_line1: str
    org_line2: str
    url: str


def _font_times(size_mm, bold=False):
    windir = os.environ.get("WINDIR", "C:\\Windows")
    names = ["timesbd.ttf", "times.ttf"] if bold else ["times.ttf"]
    size_px = max(_mm(size_mm), 8)
    for name in names:
        path = os.path.join(windir, "Fonts", name)
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size_px)
            except OSError:
                continue
    return ImageFont.load_default()


def _line_advance(font):
    """Khoảng cách dọc chuẩn giữa các dòng (ascent+descent) - dùng thay cho
    textbbox height vì bbox phụ thuộc ký tự cụ thể của từng dòng (dấu tiếng
    Việt cao/thấp khác nhau), cộng dồn sai số nếu dùng để xếp nhiều dòng."""
    ascent, descent = font.getmetrics()
    return ascent + descent


def _draw_centered(draw, text, cx, y, font, fill="black"):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text((cx - w / 2, y), text, font=font, fill=fill)
    return _line_advance(font)


def _wrap_lines(draw, text, max_w, font):
    """Xuống dòng nếu quá rộng (naive, theo từ)."""
    words = text.split()
    lines = []
    cur = ""
    for word in words:
        trial = f"{cur} {word}".strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _wrap_and_draw(draw, text, x, y, max_w, font, fill="black"):
    """Xuống dòng (căn trái) nếu quá rộng. Trả về chiều cao đã vẽ."""
    line_gap = _mm(0.6)
    lh = _line_advance(font)
    total_h = 0
    for line in _wrap_lines(draw, text, max_w, font):
        draw.text((x, y + total_h), line, font=font, fill=fill)
        total_h += lh + line_gap
    return total_h


def _wrap_and_draw_centered(draw, text, cx, y, max_w, font, fill="black"):
    """Xuống dòng (căn giữa) nếu quá rộng. Trả về chiều cao đã vẽ."""
    line_gap = _mm(0.6)
    lh = _line_advance(font)
    total_h = 0
    for line in _wrap_lines(draw, text, max_w, font):
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        draw.text((cx - w / 2, y + total_h), line, font=font, fill=fill)
        total_h += lh + line_gap
    return total_h


def _make_qr(url, size_px):
    import qrcode

    img = qrcode.make(url).convert("RGB")
    return img.resize((size_px, size_px), Image.NEAREST)


def _fit_photo(photo_path, box_w, box_h):
    photo = Image.open(photo_path).convert("RGB")
    ratio = box_w / box_h
    pw, ph = photo.size
    if pw / ph > ratio:
        new_w = int(ph * ratio)
        x0 = (pw - new_w) // 2
        photo = photo.crop((x0, 0, x0 + new_w, ph))
    else:
        new_h = int(pw / ratio)
        y0 = (ph - new_h) // 2
        photo = photo.crop((0, y0, pw, y0 + new_h))
    return photo.resize((box_w, box_h), Image.LANCZOS)


def generate_card_image(data: CardData) -> Image.Image:
    w, h = _mm(CARD_W_MM), _mm(CARD_H_MM)
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w - 1, h - 1], outline="black", width=2)

    pad = _mm(2)
    y = pad
    font_header = _font_times(2.6, bold=True)
    header_w = w - 2 * pad
    for line in (data.org_line1, data.org_line2):
        if line:
            y += _wrap_and_draw_centered(draw, line.upper(), w / 2, y, header_w, font_header)
    y += _mm(0.5)
    draw.line([pad, y, w - pad, y], fill="black", width=1)
    content_top = y + _mm(1.5)

    photo_w, photo_h = _mm(PHOTO_W_MM), _mm(PHOTO_H_MM)
    photo_x = pad
    photo_y = h - pad - photo_h
    draw.rectangle(
        [photo_x, photo_y, photo_x + photo_w, photo_y + photo_h], outline="black", width=1
    )
    if data.photo_path and Path(data.photo_path).exists():
        img.paste(_fit_photo(data.photo_path, photo_w, photo_h), (photo_x, photo_y))
        draw.rectangle(
            [photo_x, photo_y, photo_x + photo_w, photo_y + photo_h], outline="black", width=1
        )
    else:
        font_ph = _font_times(3)
        msg = "ẢNH 3x4"
        bbox = draw.textbbox((0, 0), msg, font=font_ph)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(
            (photo_x + (photo_w - tw) / 2, photo_y + (photo_h - th) / 2),
            msg, font=font_ph, fill="#999999",
        )

    qr_size = _mm(16)
    qr_x = w - pad - qr_size
    qr_y = content_top
    img.paste(_make_qr(data.url, qr_size), (qr_x, qr_y))
    font_qr_cap = _font_times(2)
    _draw_centered(draw, "QUÉT QR TRA CỨU", qr_x + qr_size / 2, qr_y + qr_size + _mm(0.3), font_qr_cap)

    text_x = photo_x + photo_w + _mm(2)
    text_right = qr_x - _mm(2)
    text_w = max(text_right - text_x, _mm(10))

    ty = content_top
    f_role = _font_times(3.6, bold=True)
    ty += _wrap_and_draw(draw, "GIÁO VIÊN DẠY LÁI XE", text_x, ty, text_w, f_role) + _mm(1)
    f_name = _font_times(3.9, bold=True)
    ty += _wrap_and_draw(draw, data.ten.upper(), text_x, ty, text_w, f_name) + _mm(1)
    if data.hang:
        f_hang = _font_times(3.9, bold=True)
        _wrap_and_draw(draw, f"Dạy lái xe hạng: {data.hang}".upper(), text_x, ty, text_w, f_hang)

    return img


def generate_cards_pdf(items, output_path):
    """items: list CardData. Xuất 1 file PDF, tối đa CARDS_PER_PAGE thẻ/trang.
    Trả về số trang đã xuất."""
    if not items:
        raise ValueError("Không có giáo viên nào để xuất thẻ.")

    page_w, page_h = _mm(PAGE_W_MM), _mm(PAGE_H_MM)
    card_w, card_h = _mm(CARD_W_MM), _mm(CARD_H_MM)
    gap_x = (page_w - GRID_COLS * card_w) // (GRID_COLS + 1)
    gap_y = (page_h - GRID_ROWS * card_h) // (GRID_ROWS + 1)

    pages = []
    page_img = None
    for i, data in enumerate(items):
        slot = i % CARDS_PER_PAGE
        if slot == 0:
            page_img = Image.new("RGB", (page_w, page_h), "white")
            pages.append(page_img)
        row, col = divmod(slot, GRID_COLS)
        x = gap_x + col * (card_w + gap_x)
        y = gap_y + row * (card_h + gap_y)
        page_img.paste(generate_card_image(data), (x, y))

    output_path = Path(output_path)
    pages[0].save(output_path, save_all=True, append_images=pages[1:], resolution=DPI)
    return len(pages)
