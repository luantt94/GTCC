# Quản lý giáo viên / học viên — Trung tâm đào tạo lái xe

App desktop để tra cứu giáo viên/xe/lịch học, và đăng thông tin giáo viên
(dạng mã QR) lên một trang web công khai, cập nhật tự động mỗi khi bạn
bấm nút — không cần biết git hay lập trình.

## 1. Cách mở app

Bấm đúp vào file chạy app, hoặc mở terminal tại thư mục này và chạy:

```
python main.py
```

App có 5 tab:

| Tab | Dùng để |
|---|---|
| **CẬP NHẬT WEB** | Khai báo nguồn dữ liệu, quản lý ảnh đại diện giáo viên & đăng số liệu lên trang web (mã QR) |
| TRA CỨU | Tìm giáo viên / mã khóa, xem học viên, lịch học |
| PHÂN XE | Xem danh sách xe và giáo viên phụ trách |
| TRA CỨU XE | Xem chi tiết 1 xe (nhãn hiệu/loại xe, lịch sử giáo viên đã dùng, giấy tờ xe) |
| LỊCH HỌC | Xem trực tiếp nội dung file PDF lịch học thực hành theo khóa |

> **Lưu ý:** 4 tab TRA CỨU / PHÂN XE / TRA CỨU XE / LỊCH HỌC chỉ đọc dữ liệu
> nội bộ lúc **mở app**. Sau khi bấm "Cập nhật && Đăng lên web" ở tab đầu
> tiên, hãy **khởi động lại app** để các tab này thấy dữ liệu mới nhất.

## 2. Nguồn dữ liệu

Toàn bộ dữ liệu lấy từ thư mục `data/` (không còn dùng file Excel tổng hợp
cũ). Tab **CẬP NHẬT WEB** có 6 vùng khai báo, tự động quét sẵn từ `data/`
khi mở app lần đầu — bạn chỉ cần sửa khi có thay đổi:

| Vùng | Nội dung | Khi nào cần sửa |
|---|---|---|
| File Excel "BIÊN CHẾ XE KHÓA ..." | Mỗi khóa đào tạo 1 file `.xlsx` | Có khóa mới → bấm **Thêm...**; khóa đã xong → chọn dòng rồi **Xóa mục chọn** |
| File PDF "LICH HOC THUC HANH ..." | Mỗi khóa 1 file lịch học `.pdf` | Tương tự, thêm/xóa theo khóa |
| DSGV_*.xml | Danh sách **toàn bộ giáo viên** (nguồn chính thức, dùng để tạo mã QR) | Khi có bản DSGV mới xuất ra từ hệ thống |
| DSXTL_*.xml | Danh sách xe tập lái (đối chiếu biển số) | Khi có bản DSXTL mới |
| Thư mục giấy tờ xe tập lái | Chứa file `.docx`/`.pdf` giấy tờ từng xe (ghép theo biển số trong tên file) | Khi đổi chỗ lưu thư mục |
| Thư mục hồ sơ cá nhân giáo viên | Chứa file `.pdf` hồ sơ từng giáo viên (ghép theo tên trong tên file) | Khi đổi chỗ lưu thư mục |

App tự ghép file PDF/Word vào đúng khóa/xe/giáo viên bằng cách so khớp tên
file (biển số xe, mã khóa, tên giáo viên) — **không cần khai báo tay**.

### Mật khẩu xem hồ sơ cá nhân

Ô "Mật khẩu xem hồ sơ cá nhân giáo viên" dùng chung cho tất cả giáo viên.
**Mật khẩu mặc định: `gtcc2026`** (máy mới chưa từng lưu cài đặt riêng sẽ
tự điền sẵn mật khẩu này — đổi/xóa được bất cứ lúc nào ở ô này):
- Có đặt mật khẩu → trang web hiện mục "Hồ sơ cá nhân", người xem phải
  nhập đúng mật khẩu mới xem được (hồ sơ có CCCD/bằng lái nên cần hạn chế).
- Để **trống** → ẩn hoàn toàn mục hồ sơ cá nhân trên trang web.
- Bấm **Lưu mật khẩu**, sau đó bấm "Cập nhật && Đăng lên web" để áp dụng.

> **⚠️ Đây KHÔNG phải bảo mật thật sự, chỉ là lớp che tượng trưng.**
> Trang web chạy trên GitHub Pages (hosting tĩnh, không có server kiểm
> tra mật khẩu). Đường link PDF hồ sơ của **mọi** giáo viên vẫn nằm sẵn
> trong `docs/public_data.json` — ai mở DevTools (F12) → tab Network,
> hoặc tự tải file này bằng tay, đều xem/tải được hồ sơ **mà không cần
> biết mật khẩu**. Mật khẩu chỉ ngăn người dùng phổ thông bấm xem nhầm
> qua giao diện bình thường, không ngăn được người cố ý/biết kỹ thuật.
> Đây là lựa chọn đã cân nhắc (ưu tiên đơn giản, không cần thêm hạ tầng
> server) — nếu cần chặn thật, phải chuyển hồ sơ sang một dịch vụ có
> backend kiểm tra quyền truy cập, không thể làm được với GitHub Pages.

### Ảnh đại diện giáo viên

Ở khung "Ảnh đại diện & thẻ giáo viên dạy lái xe" (tab CẬP NHẬT WEB): chọn
giáo viên trong ô danh sách (bấm **Tải lại DS giáo viên** nếu vừa đổi file
DSGV), rồi bấm **Thêm/Đổi ảnh...** để chọn 1 file ảnh (.png/.jpg) hoặc
**Xóa ảnh** để gỡ. Ảnh được tự resize nhỏ lại rồi **đăng lên web ngay lập
tức** (không cần bấm "Cập nhật && Đăng lên web"), hiện ngay trên đầu trang
`gv.html` của giáo viên đó. Ảnh này **công khai, không cần mật khẩu** (khác
với "Hồ sơ cá nhân" ở mục trên). Cần Internet để bấm được 2 nút này.

### Thẻ (phù hiệu) giáo viên dạy lái xe

Cùng khung trên, mỗi giáo viên có thêm ô **"Dạy lái xe hạng"** (vd `B`,
`B2, C`) — nhập xong bấm **Lưu hạng**. Ảnh đại diện và hạng lái xe dạy được
lưu trong 2 file **riêng** (`anh_gv/` và `giao_vien_extra.json`, theo mã
GV) — **tách biệt khỏi DSGV_*.xml/DSXTL_*.xml**, nên khi sau này đổi sang
file DSGV/DSXTL mới (bản xuất lại từ Sở), 2 thông tin này **không bị mất**,
miễn mã GV của giáo viên đó giữ nguyên.

Khung **"Thông tin in trên thẻ giáo viên"** ở trên cùng dùng để nhập tên cơ
quan chủ quản + tên cơ sở đào tạo in ở đầu mỗi thẻ (bấm **Lưu**, dùng chung
cho mọi thẻ).

Bấm **"Xuất thẻ GV này (PDF)"** để xuất thẻ của 1 giáo viên đang chọn, hoặc
**"Xuất thẻ TẤT CẢ giáo viên (PDF)"** để xuất toàn bộ (tối đa 8 thẻ/trang
A4, tự ngắt trang). Đây là tính năng **in cục bộ, không đăng lên web** -
không cần Internet. Phần mềm không tự đóng dấu giáp lai lên ảnh thẻ, cần
đóng dấu tay sau khi in như quy định.

Nếu có file **`data/khunganhnen.jpg`** (ảnh nền thẻ đã thiết kế sẵn, đúng
logo/màu/bố cục của đơn vị), phần mềm sẽ dùng ảnh này làm nền và tự động
dán đè: ảnh giáo viên, mã QR, tên cơ quan/cơ sở đào tạo (ghi đè lên băng
xanh có sẵn, lấy đúng nội dung đã lưu ở khung "Thông tin in trên thẻ giáo
viên"), và **Họ và tên / Ngày, tháng, năm sinh / Địa chỉ thường trú / Dạy
lái xe hạng** - 3 trường ngày sinh/địa chỉ lấy thẳng từ file DSGV_*.xml
(trường NgaySinh/NoiCT - chỉ dùng để in thẻ cục bộ, không đưa lên web).
Không có file nền thì phần mềm tự vẽ thẻ theo đúng khổ/cỡ chữ quy định ở
Mẫu số 01 (85mm x 50mm, không có 3 trường ngày sinh/địa chỉ). File
`khunganhnen.jpg` nằm trong `data/` nên **không đưa lên git** (giống
Excel/XML) - máy nào cần ảnh nền riêng thì tự đặt file vào đúng đường dẫn
này.

## 3. Quy trình cập nhật web hàng ngày/hàng tuần

**Bước 1 — Cập nhật file Excel/PDF/XML** như bình thường (thêm học viên,
đổi lịch, đổi xe, xuất lại DSGV/DSXTL...), nhớ **Save** lại trong thư mục
`data/`.

**Bước 2 — Mở app**, vào tab **"CẬP NHẬT WEB"**, kiểm tra lại 6 vùng dữ
liệu ở trên (thêm/xóa nếu cần).

**Bước 3 — Bấm "Cập nhật && Đăng lên web"**. App sẽ tự động:
1. Đọc Excel/PDF/XML đã chọn, ghép đúng khóa/xe/giáo viên.
2. Tính số học viên đang học của từng giáo viên.
3. Nếu có **giáo viên mới** (có trong DSGV nhưng chưa từng đăng), tự tạo
   mã QR mới trong thư mục `qr_codes/` (app báo rõ tên file, ví dụ
   `48002017.png` — in ra và đưa cho giáo viên đó, **chỉ cần in 1 lần**).
4. Đăng dữ liệu mới nhất lên trang web (GitHub).

**Bước 4 — Đọc khung log** sau khi chạy xong. Nếu có dòng bắt đầu bằng
"CẢNH BÁO" (ví dụ tên giáo viên trong Excel không khớp với DSGV do viết
tắt, hoặc biển số không có trong DSXTL), hãy sửa lại cho đúng chính tả
trong file Excel rồi đăng lại — nếu không sửa, giáo viên/xe đó sẽ bị thiếu
thông tin trên trang web.

Vài giây đến vài phút sau, quét lại mã QR cũ của bất kỳ giáo viên nào cũng
sẽ thấy số liệu mới — **mã QR không cần tạo lại**.

> Máy chạy app cần có **kết nối Internet** ở Bước 3. Nếu mất mạng, app báo
> lỗi rõ ràng, bạn chỉ cần bấm lại nút khi có mạng.

## 4. Mã QR giáo viên

Mỗi giáo viên có 1 file ảnh QR trong thư mục `qr_codes/`, đặt tên theo
**mã giáo viên chính thức (MaGV trong DSGV)**, ví dụ `48002017.png`, có in
tên giáo viên ngay bên dưới mã QR để dễ phân biệt khi in/dán. In mã này ra
và phát cho giáo viên — quét bằng camera điện thoại sẽ mở trang hiển thị:

- Các khóa giáo viên đang dạy (mã khóa, lớp, thời gian đào tạo).
- Xe tập lái phụ trách (bấm vào để xem SĐT + giấy tờ xe).
- Số lượng học viên (bấm vào để xem danh sách tên).
- Lịch học (bấm vào để xem bảng lịch chi tiết + file PDF gốc).
- Hồ sơ cá nhân (nếu đã đặt mật khẩu) — cần nhập đúng mật khẩu mới xem.

Mã QR này **cố định vĩnh viễn** theo MaGV — in ra 1 lần dùng mãi, các lần
cập nhật sau không đổi link/mã QR của giáo viên cũ, chỉ sinh thêm mã mới
cho giáo viên mới xuất hiện trong DSGV. Nếu DSGV sửa lại tên 1 giáo viên
đã có mã QR (ví dụ sửa chính tả), app tự nhận ra và **vẽ lại ảnh QR với
tên mới** ở lần đăng web kế tiếp — link/mã QR vẫn giữ nguyên, không cần
in lại, không cần xóa file tay.

## 5. Thông tin bảo mật

Trang web là **công khai trên Internet** (ai có link đều xem được). Những
gì **lên web**: tên giáo viên, SĐT, mã khóa/lớp, thời gian học, xe + giấy
tờ xe, **tên** học viên, lịch học (kèm file PDF gốc), và hồ sơ cá nhân giáo
viên **nếu** có đặt mật khẩu xem (xem mục 2).

Những gì **KHÔNG BAO GIỜ** lên web, kể cả khi đã đặt mật khẩu hồ sơ cá
nhân — app chủ động không đọc các trường này từ DSGV/DSXTL:
- Ảnh chân dung (AnhCD) và số CMT/CCCD (SoCMT) trong file DSGV.
- File Excel/XML gốc, và toàn bộ thư mục `data/` (chỉ những file được app
  copy sang `docs/files/` theo đúng giáo viên/xe/khóa mới public).
- Mật khẩu hồ sơ cá nhân ở dạng gốc (chỉ lưu bản băm SHA-256 trên web).
- Ngày sinh (NgaySinh) và địa chỉ (NoiCT) trong file DSGV - chỉ đọc để in
  lên thẻ giáo viên cục bộ (mục "Thẻ (phù hiệu) giáo viên dạy lái xe" ở
  trên), không có trong `docs/public_data.json`.

## 6. Cài đặt lần đầu (dành cho máy mới)

```
pip install -r requirements.txt
```

Nếu đây là máy mới hoàn toàn chưa từng đăng nhập GitHub, lần đầu bấm
"Cập nhật && Đăng lên web" có thể hiện cửa sổ đăng nhập GitHub — đăng nhập
1 lần, các lần sau không cần nhập lại.

### Bật GitHub Pages (chỉ làm 1 lần cho repo)

1. Vào `https://github.com/luantt94/GTCC/settings/pages`
2. **Source**: "Deploy from a branch" → Branch: `main`, thư mục `/docs` → **Save**.
3. Sau 1–2 phút, trang chạy tại: `https://luantt94.github.io/GTCC/gv.html?id=<mã GV>`

## 7. Xử lý sự cố thường gặp

| Vấn đề | Cách xử lý |
|---|---|
| "Hãy thêm ít nhất 1 file 'BIÊN CHẾ XE KHÓA ...'" | Vào tab CẬP NHẬT WEB, bấm "Thêm..." ở vùng Excel |
| "Hãy chọn file danh sách giáo viên (DSGV_*.xml)" | Chọn file DSGV ở vùng tương ứng |
| Đã lưu ở máy nhưng chưa đăng được lên web | Kiểm tra Internet, bấm lại nút "Cập nhật && Đăng lên web" |
| Cảnh báo "trùng mã khóa" | Hai file Excel đang chọn có cùng 1 mã khóa — kiểm tra lại có chọn nhầm file không |
| Cảnh báo "không khớp được giáo viên" / "biển số không có trong DSXTL" | Tên/biển số viết tắt hoặc sai chính tả trong Excel so với DSGV/DSXTL — sửa lại cho khớp rồi đăng lại |
| Quét QR báo "Không tìm thấy mã giáo viên" | Chưa bật GitHub Pages, hoặc mới đăng xong cần đợi vài phút |
| Tab TRA CỨU/PHÂN XE/LỊCH HỌC chưa thấy dữ liệu mới | Khởi động lại app sau khi đăng web xong |
