# Thông Tin Deploy - Checkpoint 5

## Thông Tin Học Viên

| Mục | Nội dung |
|-----|----------|
| Họ và tên | CapVietAnh |
| Mã học viên | 01270 |
| Repo | K4-DAY12-01270-CapVietAnh |

## Service

| Mục | Nội dung |
|-----|----------|
| Public URL | local fallback qua Docker Compose tại http://localhost:8000 |
| Platform | Local fallback với Docker Compose, không deploy Railway |
| Ngày deploy | 2026-08-10 |

## Biến Môi Trường Đã Set Trên Cloud

Không dùng cloud cho bài nộp này. Service được kiểm tra bằng phương án dự phòng ở máy local.

| Biến | Đã set | Ghi chú |
|------|--------|---------|
| `PORT` | yes | docker compose map cổng 8000 |
| `API_TOKEN` | yes | đặt trong `.env`, không ghi giá trị vào tài liệu |
| `REDIS_URL` | yes | `redis://redis:6379/0` trong compose |
| `BUCKET_CAPACITY` | yes | 10 |
| `REFILL_PER_MINUTE` | yes | 10 |
| `DAILY_BUDGET_USD` | yes | 1.0 |
| `LOG_LEVEL` | yes | INFO |

## Lệnh Kiểm Tra

```bash
curl -i http://localhost:8000/healthz
curl -i http://localhost:8000/readyz
curl -i -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message":"Hello"}'
docker compose ps
```

## Kết Quả Chạy Thật

Đã xác nhận local fallback bằng `docker compose up -d`, `docker compose ps`,
`GET /healthz`, `GET /readyz`, và `POST /chat` không kèm token trả 401.

## Ảnh Chụp Màn Hình

Đặt ảnh trong thư mục `screenshots/`:

- `screenshots/local-fallback.png`

## Nếu Dùng Phương Án Dự Phòng

Lý do dùng fallback: hoàn tất checkpoint trong môi trường local bằng Docker Compose
và Redis, không phụ thuộc vào tài khoản cloud trong lúc làm bài.
