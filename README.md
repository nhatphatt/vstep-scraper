# VSTEP Exam Scraper

Cào đề thi VSTEP từ luyenthivstep.vn kèm đáp án.

## Cài đặt

```bash
# Clone và cài đặt
git clone https://github.com/nhatphatt/vstep-scraper.git
cd vstep-scraper
python -m venv venv
.\venv\Scripts\activate      # Windows
pip install -r requirements.txt
playwright install chromium
```

## Cấu hình

```bash
# Copy file mẫu
cp .env.example .env
```

Mở `.env` và điền thông tin:

```env
VSTEP_USERNAME=your_username
VSTEP_PASSWORD=your_password
```

## Sử dụng

```bash
# Cào 1 loại đề
python main.py --type listening --start 1 --end 100
python main.py --type reading --start 1 --end 100
python main.py --type writing --start 1 --end 100
python main.py --type speaking --start 1 --end 100

# Cào tất cả và xóa trùng lặp
python main.py --type all --cleanup

# Hiện browser khi cào
python main.py --type listening --visible
```

## Lưu ý

- **Tài khoản VIP**: Cào được tất cả đề
- **Tài khoản thường**: Đề VIP bị bỏ qua
