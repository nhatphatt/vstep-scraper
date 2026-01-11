# VSTEP Exam Scraper

Công cụ cào đề thi VSTEP từ luyenthivstep.vn, bao gồm cả đáp án đúng.

## 📊 Dữ liệu đã cào

| Loại đề | Số lượng | Ghi chú |
|---------|----------|---------|
| Listening | 9 đề | Có đáp án đúng |
| Reading | 12 đề | Có đáp án đúng |
| Writing | 7 đề | Có đề bài, word limit |
| Speaking | 9 đề | Có topic, follow-up questions |
| **Tổng** | **37 đề** | |

## 🚀 Cài đặt

```bash
# Clone repo
git clone <repo-url>
cd vstep_scraper

# Tạo virtual environment
python -m venv venv

# Kích hoạt venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt

# Cài đặt Playwright browser
playwright install chromium
```

## 📖 Sử dụng

### Cào một loại đề

```bash
# Cào Listening (đề 1-100)
python main.py --type listening --start 1 --end 100

# Cào Reading
python main.py --type reading --start 1 --end 100

# Cào Writing
python main.py --type writing --start 1 --end 100

# Cào Speaking
python main.py --type speaking --start 1 --end 100
```

### Cào tất cả loại đề

```bash
python main.py --type all --start 1 --end 100
```

### Tùy chọn

| Option | Mô tả |
|--------|-------|
| `--type` | Loại đề: listening, reading, writing, speaking, all |
| `--start` | ID đề bắt đầu (mặc định: 1) |
| `--end` | ID đề kết thúc (mặc định: 100) |
| `--visible` | Hiển thị browser khi chạy |
| `--cleanup` | Xóa đề trùng lặp sau khi cào |

### Ví dụ

```bash
# Cào Listening đề 1-50 với browser hiển thị
python main.py --type listening --start 1 --end 50 --visible

# Cào tất cả và xóa trùng lặp
python main.py --type all --cleanup
```

## 📁 Cấu trúc thư mục

```
vstep_scraper/
├── main.py              # Script chính
├── requirements.txt     # Dependencies
├── README.md           
└── data/               
    ├── listening/       # Đề Listening (*.json)
    ├── reading/         # Đề Reading (*.json)
    ├── writing/         # Đề Writing (*.json)
    └── speaking/        # Đề Speaking (*.json)
```

## 📝 Cấu trúc dữ liệu

### Listening/Reading
```json
{
  "exam_type": "listening",
  "exam_id": "1",
  "audio_url": "https://...",
  "questions": [
    {
      "question_number": 1,
      "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
      "correct_answer": "A"
    }
  ]
}
```

### Writing
```json
{
  "exam_type": "writing",
  "exam_id": "1",
  "tasks": [
    {
      "task_number": 1,
      "prompt": "Write an email...",
      "word_limit": 120
    }
  ]
}
```

### Speaking
```json
{
  "exam_type": "speaking",
  "exam_id": "69",
  "parts": [
    {
      "part_number": 1,
      "topic": "Traditional festivals...",
      "instructions": "...",
      "follow_up_questions": ["1. ...", "2. ...", "3. ..."],
      "speaking_time": 4
    }
  ]
}
```

## ⚠️ Lưu ý

- **Tài khoản VIP**: Cào được tất cả đề (kể cả đề VIP)
- **Tài khoản thường**: Đề VIP sẽ tự động bị bỏ qua
- Cần có tài khoản luyenthivstep.vn để cào
- Đề trùng lặp sẽ tự động được phát hiện và xóa khi dùng `--cleanup`

## 🔧 Cấu hình tài khoản

Mở file `main.py` và thay đổi thông tin đăng nhập:

```python
USERNAME = "your_username"
PASSWORD = "your_password"
```
