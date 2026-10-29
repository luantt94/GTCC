"""Sinh ảnh/PDF "Phù hiệu giáo viên dạy lái xe" theo đúng Mẫu số 01 (quy
cách chính thức do người dùng cung cấp):

- Kích thước: 50 mm x 85 mm.
- In trên giấy trắng chất lượng tốt, ép plastic kẹp trong mica, đeo ở phía
  ngực trái hoặc ở cổ (việc in ấn/ép plastic/đeo thẻ nằm ngoài phạm vi phần
  mềm - chỉ ghi chú lại đây để người in nhớ làm đúng).
- Phía trên: tên cơ quan quản lý cấp trên trực tiếp + tên cơ sở đào tạo -
  Times New Roman in hoa, cỡ chữ 10.
- Phía dưới bên trái: ảnh màu 3 cm x 4 cm (có đóng dấu giáp lai của cơ sở
  đào tạo - phần mềm KHÔNG tự vẽ dấu giáp lai, đây là con dấu đóng tay thật
  sau khi in, ngoài phạm vi phần mềm).
- Phía dưới bên phải:
  - "GIÁO VIÊN DẠY LÁI XE" - Times New Roman in hoa, đậm, cỡ chữ 13.
  - Họ tên giáo viên - Times New Roman in hoa, đậm, cỡ chữ 14.
  - Hạng giấy phép lái xe dạy lái - Times New Roman in hoa, đậm, cỡ chữ 14.
- Mã QR tra cứu thông tin (bổ sung theo yêu cầu, không nằm trong Mẫu số 01
  gốc) đặt trong khung riêng, có chú thích "QUÉT QR TRA CỨU THÔNG TIN",
  dùng chung link với mã QR đã phát cho giáo viên.
- Xuất PDF tối đa 8 thẻ/trang giấy (xem CARDS_PER_PAGE).

Dữ liệu ảnh + hạng lái xe dạy lấy từ giao_vien_extra.json / anh_gv/ (xem
publish_data.py) - tách riêng khỏi DSGV/DSXTL để không mất khi đổi file XML.
"""
import os
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

APP_DIR = Path(__file__).resolve().parent
BG_PATH = APP_DIR / "data" / "khunganhnen.jpg"  # ảnh nền thẻ đã thiết kế sẵn (nếu có)

DPI = 300
_MM_TO_PX = DPI / 25.4
_PT_TO_PX = DPI / 72

CARD_W_MM, CARD_H_MM = 85, 50
PHOTO_W_MM, PHOTO_H_MM = 30, 40
PAGE_W_MM, PAGE_H_MM = 210, 297  # A4 dọc
GRID_COLS, GRID_ROWS = 2, 4
CARDS_PER_PAGE = GRID_COLS * GRID_ROWS

# Cỡ chữ (pt) đúng theo quy cách Mẫu số 01 - dùng khi KHÔNG có ảnh nền
# (xem _generate_card_image_procedural).
FONT_PT_HEADER = 10  # tên cơ quan/cơ sở đào tạo
FONT_PT_ROLE = 13  # "GIÁO VIÊN DẠY LÁI XE"
FONT_PT_NAME = 14  # họ tên giáo viên
FONT_PT_HANG = 14  # hạng lái xe dạy

# Toạ độ (px) các vùng trống trên ảnh nền data/khunganhnen.jpg (1280x768),
# đo trực tiếp trên ảnh - chỉ đúng với ảnh nền này, phải đo lại nếu đổi ảnh.
_BG_PHOTO_BOX = (48, 223, 378, 718)  # x0,y0,x1,y1 - khung ảnh giáo viên
_BG_QR_BOX = (1068, 506, 1222, 638)  # khung mã QR
_BG_HANG_VALUE_X = 850  # bắt đầu vẽ giá trị hạng, ngay sau chữ "Dạy lái xe hạng:"
_BG_HANG_VALUE_Y = (598, 658)
_BG_HANG_RIGHT = 1250
# Khoảng trống dưới tiêu đề "GIÁO VIÊN DẠY LÁI XE" để ghi Họ và tên / Ngày
# sinh / Địa chỉ (x1 chừa chỗ cho khung QR bên phải, không lấy hết x=1236
# như trước để tránh đè lên khung QR).
_BG_FIELDS_AREA = (418, 352, 1048, 596)
_BG_FIELDS_COLOR = "black"
_BG_HANG_COLOR = "#0a1450"
# Băng chữ trắng trên nền xanh ở đầu thẻ (tên cơ quan/cơ sở đào tạo) - đã có
# sẵn trong ảnh nền, vẽ đè thêm bằng org_line1/org_line2 để luôn khớp với
# cài đặt trong app (phòng khi sau này đổi ảnh nền/đổi tên cơ quan).
_BG_HEADER_X = (40, 1240)
_BG_HEADER_LINE_BANDS = [(44, 98), (100, 164)]
_BG_HEADER_COLOR = "white"
_BG_HEADER_FILL_RECT = (30, 26, 1250, 182)  # vùng tô lại nền xanh trước khi ghi đè chữ
_BG_HEADER_FILL_COLOR = "#0556b0"


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
    ngay_sinh: str = ""
    dia_chi: str = ""


def _font_times_px(size_px, bold=False):
    windir = os.environ.get("WINDIR", "C:\\Windows")
    names = ["timesbd.ttf", "times.ttf"] if bold else ["times.ttf"]
    size_px = max(round(size_px), 8)
    for name in names:
        path = os.path.join(windir, "Fonts", name)
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size_px)
            except OSError:
                continue
    return ImageFont.load_default()


def _font_times(size_pt, bold=False):
    return _font_times_px(size_pt * _PT_TO_PX, bold=bold)


def _line_advance(font):
    """Khoảng cách dọc chuẩn giữa các dòng (ascent+descent) - dùng thay cho
    textbbox height vì bbox phụ thuộc ký tự cụ thể của từng dòng (dấu tiếng
    Việt cao/thấp khác nhau), cộng dồn sai số nếu dùng để xếp nhiều dòng."""
    ascent, descent = font.getmetrics()
    return ascent + descent


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


_LINE_GAP = _mm(0.6)
_BLOCK_GAP = _mm(1)


def _total_height(rendered):
    """Tổng chiều cao thật sự của kết quả _measure_blocks/_fit_blocks."""
    total_h = 0
    started = False
    for lines, font, lh in rendered:
        if not lines:
            continue
        if started:
            total_h += _BLOCK_GAP
        started = True
        total_h += len(lines) * lh + max(len(lines) - 1, 0) * _LINE_GAP
    return total_h


def _measure_blocks(draw, blocks, max_w, scale, font_for=None):
    """blocks: list (text, cỡ_chữ_gốc, bold). `font_for(base_size, scale,
    bold)` quyết định font thật sự dùng (mặc định: cỡ chữ pt theo quy cách
    Mẫu số 01). Trả về (tổng chiều cao, [(lines, font, line_advance), ...])
    ở mức thu nhỏ `scale` (1.0 = đúng cỡ chữ gốc)."""
    if font_for is None:
        font_for = lambda base_size, scale, bold: _font_times(base_size * scale, bold=bold)

    rendered = []
    for text, base_size, bold in blocks:
        font = font_for(base_size, scale, bold)
        lines = _wrap_lines(draw, text, max_w, font) if text else []
        rendered.append((lines, font, _line_advance(font)))

    return _total_height(rendered), rendered


def _fit_blocks(draw, blocks, max_w, max_h, font_for=None, min_scale=0.45, step=0.05):
    """Thử cỡ chữ gốc trước; nếu không vừa khung (tên cơ quan/họ tên quá
    dài) thì thu nhỏ dần (đều cho mọi khối) tới khi vừa, để không bao giờ
    tràn ra ngoài thẻ."""
    scale = 1.0
    rendered = None
    while True:
        total_h, rendered = _measure_blocks(draw, blocks, max_w, scale, font_for=font_for)
        if total_h <= max_h or scale <= min_scale:
            return rendered
        scale = max(scale - step, min_scale)


def _draw_rendered_blocks(draw, rendered, y, x=None, cx=None, fill="black"):
    """Vẽ kết quả _fit_blocks/_measure_blocks, căn trái (x) hoặc căn giữa (cx)."""
    ty = y
    started = False
    for lines, font, lh in rendered:
        if not lines:
            continue
        if started:
            ty += _BLOCK_GAP
        started = True
        for i, line in enumerate(lines):
            if i > 0:
                ty += _LINE_GAP
            if cx is not None:
                bbox = draw.textbbox((0, 0), line, font=font)
                lw = bbox[2] - bbox[0]
                draw.text((cx - lw / 2, ty), line, font=font, fill=fill)
            else:
                draw.text((x, ty), line, font=font, fill=fill)
            ty += lh
    return ty - y


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


def _generate_card_image_from_background(data: CardData) -> Image.Image:
    """Dùng ảnh nền đã thiết kế sẵn (data/khunganhnen.jpg) làm thẻ, chỉ dán
    đè ảnh giáo viên + mã QR + ghi họ tên/ngày sinh/địa chỉ/hạng vào đúng
    các vùng trống có sẵn trên ảnh (xem _BG_* ở đầu file). Trả về ảnh đã
    resize về đúng khổ thẻ chuẩn (CARD_W_MM x CARD_H_MM) để ghép trang PDF
    như bình thường."""
    img = Image.open(BG_PATH).convert("RGB").copy()
    draw = ImageDraw.Draw(img)
    _px_font_for = lambda base_size, scale, bold: _font_times_px(base_size * scale, bold=bold)

    # Băng tên cơ quan/cơ sở đào tạo - tô lại nền xanh (tránh chồng/bóng mờ
    # lên chữ có sẵn trong ảnh) rồi ghi đè đúng nội dung từ cài đặt trong
    # app (ô "Thông tin in trên thẻ giáo viên").
    draw.rectangle(_BG_HEADER_FILL_RECT, fill=_BG_HEADER_FILL_COLOR)
    hx0, hx1 = _BG_HEADER_X
    for line, (by0, by1) in zip((data.org_line1, data.org_line2), _BG_HEADER_LINE_BANDS):
        if not line:
            continue
        rendered = _fit_blocks(
            draw, [(line.upper(), 46, True)], hx1 - hx0, by1 - by0, font_for=_px_font_for
        )
        ly = by0 + max((by1 - by0 - _total_height(rendered)) / 2, 0)
        _draw_rendered_blocks(draw, rendered, ly, cx=(hx0 + hx1) / 2, fill=_BG_HEADER_COLOR)

    px0, py0, px1, py1 = _BG_PHOTO_BOX
    if data.photo_path and Path(data.photo_path).exists():
        img.paste(_fit_photo(data.photo_path, px1 - px0, py1 - py0), (px0, py0))

    qx0, qy0, qx1, qy1 = _BG_QR_BOX
    qr_size = min(qx1 - qx0, qy1 - qy0) - _mm(0.8)
    qr_x = qx0 + (qx1 - qx0 - qr_size) // 2
    qr_y = qy0 + (qy1 - qy0 - qr_size) // 2
    img.paste(_make_qr(data.url, qr_size), (qr_x, qr_y))

    if data.hang:
        hang_w = _BG_HANG_RIGHT - _BG_HANG_VALUE_X
        hang_h = _BG_HANG_VALUE_Y[1] - _BG_HANG_VALUE_Y[0]
        hang_rendered = _fit_blocks(
            draw, [(data.hang.upper(), 50, True)], hang_w, hang_h, font_for=_px_font_for
        )
        hang_y = _BG_HANG_VALUE_Y[0] + max((hang_h - _total_height(hang_rendered)) / 2, 0)
        _draw_rendered_blocks(
            draw, hang_rendered, hang_y, x=_BG_HANG_VALUE_X, fill=_BG_HANG_COLOR
        )

    # Họ và tên / Ngày tháng năm sinh / Địa chỉ thường trú - tự thu nhỏ
    # chung (xem _fit_blocks) nếu địa chỉ dài, để không đè lên khung QR hay
    # dòng "Dạy lái xe hạng:" đã in sẵn bên dưới.
    fx0, fy0, fx1, fy1 = _BG_FIELDS_AREA
    field_blocks = [
        (f"Họ và tên: {data.ten}".upper(), 40, True),
        (f"Ngày, tháng, năm sinh: {data.ngay_sinh}".upper() if data.ngay_sinh else "", 36, True),
        (f"Địa chỉ thường trú: {data.dia_chi}".upper() if data.dia_chi else "", 36, True),
    ]
    fields_rendered = _fit_blocks(draw, field_blocks, fx1 - fx0, fy1 - fy0, font_for=_px_font_for)
    _draw_rendered_blocks(draw, fields_rendered, fy0, x=fx0, fill=_BG_FIELDS_COLOR)

    card_w, card_h = _mm(CARD_W_MM), _mm(CARD_H_MM)
    return img.resize((card_w, card_h), Image.LANCZOS)


def _generate_card_image_procedural(data: CardData) -> Image.Image:
    """Dùng khi KHÔNG có ảnh nền thiết kế sẵn (data/khunganhnen.jpg) - tự vẽ
    thẻ theo đúng quy cách Mẫu số 01 (10/13/14pt); tên cơ quan/họ tên quá
    dài thì tự thu nhỏ đều (xem _fit_blocks) để không tràn ra ngoài thẻ."""
    w, h = _mm(CARD_W_MM), _mm(CARD_H_MM)
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w - 1, h - 1], outline="black", width=2)

    pad = _mm(2)
    header_w = w - 2 * pad
    header_blocks = [
        (data.org_line1.upper() if data.org_line1 else "", FONT_PT_HEADER, True),
        (data.org_line2.upper() if data.org_line2 else "", FONT_PT_HEADER, True),
    ]
    header_rendered = _fit_blocks(draw, header_blocks, header_w, _mm(16))
    header_h = _draw_rendered_blocks(draw, header_rendered, pad, cx=w / 2)

    y = pad + header_h + _mm(0.5)
    draw.line([pad, y, w - pad, y], fill="black", width=1)
    content_top = y + _mm(1.5)

    photo_w, photo_h = _mm(PHOTO_W_MM), _mm(PHOTO_H_MM)
    photo_x = pad
    photo_y = h - pad - photo_h
    if data.photo_path and Path(data.photo_path).exists():
        img.paste(_fit_photo(data.photo_path, photo_w, photo_h), (photo_x, photo_y))
    else:
        font_ph = _font_times(9)
        msg = "ẢNH 3x4"
        bbox = draw.textbbox((0, 0), msg, font=font_ph)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(
            (photo_x + (photo_w - tw) / 2, photo_y + (photo_h - th) / 2),
            msg, font=font_ph, fill="#999999",
        )
    draw.rectangle(
        [photo_x, photo_y, photo_x + photo_w, photo_y + photo_h], outline="black", width=1
    )

    # Khung "QR tra cứu" - mã QR nằm TRONG khung, chú thích đầy đủ bên dưới
    # (bổ sung theo yêu cầu, không thuộc Mẫu số 01 gốc).
    qr_pad = _mm(1.2)
    qr_size = _mm(15)
    qr_cap_max_h = max((h - pad) - (content_top + qr_pad + qr_size + _mm(0.8) + qr_pad), _mm(4))
    qr_cap_blocks = [("QUÉT QR TRA CỨU THÔNG TIN", 6.5, False)]
    qr_cap_rendered = _fit_blocks(draw, qr_cap_blocks, qr_size, qr_cap_max_h)

    qr_box_w = qr_size + 2 * qr_pad
    qr_box_x = w - pad - qr_box_w
    qr_box_y = content_top
    qr_x = qr_box_x + qr_pad
    qr_y = qr_box_y + qr_pad
    img.paste(_make_qr(data.url, qr_size), (qr_x, qr_y))
    cap_y = qr_y + qr_size + _mm(0.8)
    cap_h = _draw_rendered_blocks(draw, qr_cap_rendered, cap_y, cx=qr_box_x + qr_box_w / 2)
    qr_box_h = qr_pad + qr_size + _mm(0.8) + cap_h + qr_pad
    draw.rectangle(
        [qr_box_x, qr_box_y, qr_box_x + qr_box_w, qr_box_y + qr_box_h], outline="black", width=1
    )

    text_x = photo_x + photo_w + _mm(2)
    text_right = qr_box_x - _mm(2)
    text_w = max(text_right - text_x, _mm(10))
    text_max_h = max((h - pad) - content_top, _mm(10))

    text_blocks = [
        ("GIÁO VIÊN DẠY LÁI XE", FONT_PT_ROLE, True),
        (data.ten.upper(), FONT_PT_NAME, True),
        (f"Hạng: {data.hang}".upper() if data.hang else "", FONT_PT_HANG, True),
    ]
    text_rendered = _fit_blocks(draw, text_blocks, text_w, text_max_h)
    _draw_rendered_blocks(draw, text_rendered, content_top, x=text_x)

    return img


def generate_card_image(data: CardData) -> Image.Image:
    """Dùng ảnh nền data/khunganhnen.jpg nếu có (xem
    _generate_card_image_from_background), nếu không thì tự vẽ thẻ theo quy
    cách Mẫu số 01 (xem _generate_card_image_procedural)."""
    if BG_PATH.exists():
        return _generate_card_image_from_background(data)
    return _generate_card_image_procedural(data)


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
