# Quản lý giáo viên / học viên — Trung tâm đào tạo lái xe

App desktop để tra cứu giáo viên/xe/lịch học, và đăng thông tin giáo viên
(dạng mã QR) lên một trang web công khai, cập nhật tự động mỗi khi bạn
bấm nút — không cần biết git hay lập trình.

## 1. Cách mở app

Bấm đúp vào file chạy app, hoặc mở terminal tại thư mục này và chạy:

```
python main.py
```

App có 4 tab:

| Tab | Dùng để |
|---|---|
| TRA CỨU | Tìm giáo viên / mã khóa, xem học viên, lịch học |
| PHÂN XE | Xem danh sách xe và giáo viên phụ trách |
| LỊCH HỌC | Xem lịch học theo khóa |
| **CẬP NHẬT WEB** | Đăng số liệu giáo viên lên trang web (mã QR) |

## 2. Quy trình cập nhật web hàng ngày/hàng tuần

**Bước 1 — Cập nhật file Excel** như bình thường (thêm học viên, đổi lịch,
đổi xe...), nhớ **Save** lại.

**Bước 2 — Mở app**, vào tab **"CẬP NHẬT WEB"**.

**Bước 3 — Chọn file Excel** (chỉ cần làm lần đầu, hoặc khi bạn đổi tên/vị
trí file, hoặc có thêm file mới):
- Bấm **"Chọn file Excel..."**
- Nếu dữ liệu nằm trong **nhiều file** (ví dụ mỗi khóa 1 file), giữ phím
  `Ctrl` để chọn nhiều file cùng lúc. App sẽ tự gộp lại theo mã khóa.
- App nhớ lựa chọn này cho những lần mở sau, không cần chọn lại.

**Bước 4 — Bấm "Cập nhật & Đăng lên web"**. App sẽ tự động:
1. Đọc (các) file Excel đã chọn.
2. Tính số học viên đang học của từng giáo viên.
3. Nếu có **giáo viên mới**, tự tạo mã QR mới trong thư mục `qr_codes/`
   (app sẽ báo rõ tên file, ví dụ `GV011.png` — in ra và đưa cho giáo viên
   đó, **chỉ cần in 1 lần**).
4. Đăng dữ liệu mới nhất lên trang web (GitHub).

Vài giây đến vài phút sau, quét lại mã QR cũ của bất kỳ giáo viên nào cũng
sẽ thấy số liệu mới — **mã QR không cần tạo lại**.

> Máy chạy app cần có **kết nối Internet** ở Bước 4. Nếu mất mạng, app báo
> lỗi rõ ràng, bạn chỉ cần bấm lại nút khi có mạng.

## 3. Mã QR giáo viên

Mỗi giáo viên có 1 file ảnh QR trong thư mục `qr_codes/`, đặt tên theo mã
giáo viên (`GV001.png`, `GV002.png`, ...). In mã này ra và dán/phát cho
giáo viên — quét bằng camera điện thoại sẽ mở trang hiển thị:

- Các khóa giáo viên đang dạy (mã khóa, lớp, thời gian đào tạo)
- Xe tập lái phụ trách (bấm vào để xem thêm SĐT)
- Số lượng học viên (bấm vào để xem danh sách tên)
- Lịch học (bấm vào để xem bảng lịch chi tiết)

Danh sách tên giáo viên ↔ mã QR được lưu trong `teacher_ids.json` — **không
xoá file này**, vì mã QR đã in ra sẽ dùng mãi theo mã đó.

## 4. Thông tin bảo mật

Trang web là **công khai trên Internet** (ai có link đều xem được). Những
gì **lên web**: tên giáo viên, mã khóa/lớp, thời gian học, xe, SĐT, **tên**
học viên, lịch học.

Những gì **KHÔNG BAO GIỜ** lên web (chỉ nằm trên máy bạn):
- File Excel gốc
- Ngày sinh, địa chỉ học viên
- Thư mục `data/` (hồ sơ giáo viên, file PDF có chữ ký...)

## 5. Cài đặt lần đầu (dành cho máy mới)

```
pip install -r requirements.txt
```

Nếu đây là máy mới hoàn toàn chưa từng đăng nhập GitHub, lần đầu bấm
"Cập nhật & Đăng lên web" có thể hiện cửa sổ đăng nhập GitHub — đăng nhập
1 lần, các lần sau không cần nhập lại.

### Bật GitHub Pages (chỉ làm 1 lần cho repo)

1. Vào `https://github.com/luantt94/GTCC/settings/pages`
2. **Source**: "Deploy from a branch" → Branch: `main`, thư mục `/docs` → **Save**.
3. Sau 1–2 phút, trang chạy tại: `https://luantt94.github.io/GTCC/gv.html?id=<mã GV>`

## 6. Xử lý sự cố thường gặp

| Vấn đề | Cách xử lý |
|---|---|
| "Chưa chọn file Excel nào" | Vào tab CẬP NHẬT WEB, bấm "Chọn file Excel..." |
| Đã lưu ở máy nhưng chưa đăng được lên web | Kiểm tra Internet, bấm lại nút "Cập nhật & Đăng lên web" |
| Cảnh báo "trùng mã khóa" | Hai file Excel đang chọn có cùng 1 mã khóa — kiểm tra lại có chọn nhầm file không |
| Quét QR báo "Không tìm thấy mã giáo viên" | Chưa bật GitHub Pages, hoặc mới đăng xong cần đợi vài phút |
