# Phiếu Phản Ánh — K4 Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: thay dòng `> *Câu trả lời của bạn*` bằng câu trả lời.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Cáp Việt Anh  Mã học viên: 01270

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `api_token` không có giá trị mặc định nên app chết ngay khi
khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà việc
"chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

> Ví dụ: một kỹ sư copy file `.env.example` sang môi trường staging nhưng quên
> điền `API_TOKEN` thật. Vì `api_token: str` trong `Settings` không có giá trị
> mặc định, Pydantic ném lỗi validation ngay khi `get_settings()` chạy lần đầu
> lúc khởi động — container không bao giờ vào trạng thái "đang chạy", healthcheck
> fail ngay, và người deploy biết lỗi trong vài giây. Nếu để mặc định
> `"changeme"`, app vẫn khởi động bình thường, healthz trả 200 OK, mọi thứ trông
> "ổn" — nhưng thực chất bất kỳ ai cũng gọi được `/chat` bằng token `"changeme"`.
> Lỗi cấu hình biến thành lỗ hổng bảo mật âm thầm, chỉ bị phát hiện khi có sự cố
> (log bất thường, chi phí tăng vọt) thay vì bị chặn ngay tại thời điểm deploy.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/chat` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

> Chạy `docker compose up -d --build` rồi gọi `POST /chat` với Bearer token hợp
> lệ (`curl -X POST http://localhost:8000/chat -H "Authorization: Bearer $API_TOKEN" -d '{"message":"xin chao"}'`),
> xem `docker compose logs chat`. Dòng log JSON thu được:
>
> `{"event": "chat_completed", "severity": "INFO", "ts": "2026-08-10T10:00:32.001204+00:00", "client_id": "demo", "prompt_tokens": 2, "completion_tokens": 34, "usd_cost": 2.07e-05}`
>
> Hai việc làm được với log JSON mà `print("đã trả lời xong")` không làm được:
> 1. **Truy vấn/lọc theo trường** — vì log là JSON có cấu trúc (`event`,
>    `client_id`, `usd_cost`...), công cụ như `jq`, Loki hay CloudWatch Insights
>    có thể lọc "tất cả request của `client_id=X` tốn hơn `$0.001`" mà không cần
>    parse chuỗi bằng regex.
> 2. **Tổng hợp/giám sát tự động** — có `ts` chuẩn ISO-8601 và số liệu
>    (`prompt_tokens`, `usd_cost`) nên có thể vẽ dashboard, tính tổng chi phí
>    theo giờ, hoặc set alert khi `usd_cost` trung bình tăng bất thường. Chuỗi
>    tiếng Việt tự do như "đã trả lời xong" không có trường nào để máy đọc và
>    tổng hợp được.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t chat:single .
docker build -t chat:multi .
docker images | grep chat
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | 1730 MB (1.73 GB) |
| Multi-stage | 270 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

> Số đo thật từ `docker images`: `chat:single` (build từ `Dockerfile.single`,
> nền `python:3.11` đầy đủ) = **1.73 GB**; `chat:multi` (build từ `Dockerfile`,
> multi-stage với `python:3.11-slim`) = **270 MB** — chênh lệch khoảng **1.46 GB**.
>
> Phần chênh lệch đó chủ yếu là:
> 1. **Base image**: `python:3.11` đầy đủ mang theo build toolchain (gcc, make,
>    headers...), nhiều thư viện hệ thống, docs, locale — trong khi
>    `python:3.11-slim` chỉ giữ runtime Python tối thiểu, nhẹ hơn nhiều trăm MB.
> 2. **Build-time artifacts bị giữ lại**: bản 1 stage chạy `RUN pip install`
>    ngay trong image cuối cùng, nên toàn bộ cache pip, wheel tạm, và các gói
>    build-dependency (nếu package nào cần compile) đều nằm lại trong layer
>    cuối. Bản multi-stage cài package ở stage `builder` riêng (dùng
>    `--prefix=/install`), rồi chỉ `COPY --from=builder /install /usr/local`
>    sang stage `runtime` — chỉ mang theo *kết quả* cài đặt, không mang theo
>    toolchain hay cache dùng để cài đặt.
> 3. **`.dockerignore`/COPY phạm vi**: `Dockerfile.single` dùng `COPY . .` nên
>    copy luôn cả những thứ không cần cho runtime (`.git`, `.venv`, `tests`,
>    `screenshots`...) nếu `.dockerignore` không chặn hết, trong khi
>    `Dockerfile` chỉ `COPY app ./app` và `COPY utils ./utils` — đúng những gì
>    cần chạy.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

> Với `Dockerfile` hiện tại (multi-stage), thứ tự là: `COPY requirements.txt .`
> → `RUN pip install ...` → `COPY app ./app` → `COPY utils ./utils`. Khi sửa một
> ký tự trong `app/main.py`, `requirements.txt` không đổi nên layer
> `COPY requirements.txt` và layer `RUN pip install` vẫn khớp cache (dùng lại
> nguyên vẹn, không tải lại package). Chỉ layer `COPY app ./app` trở đi (và mọi
> layer runtime phía sau nó: `chown`, `USER`...) phải build lại, vì Docker so
> khớp cache theo nội dung file được COPY.
>
> Nếu đặt `COPY . .` lên trước `RUN pip install -r requirements.txt` (giống
> `Dockerfile.single`): bất kỳ thay đổi nào trong code, kể cả một ký tự trong
> `app/main.py` không liên quan gì tới dependency, cũng làm layer `COPY . .`
> bị invalidate → layer `RUN pip install` phía sau nó luôn phải chạy lại, dù
> `requirements.txt` không đổi. Mỗi lần sửa code là một lần cài lại toàn bộ
> dependency từ đầu, build chậm hơn nhiều lần trong vòng lặp dev.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

> Chuỗi sự kiện nếu chạy root: (1) code Python có lỗ hổng, ví dụ deserialization
> không an toàn hoặc command injection trong một dependency; (2) kẻ tấn công gửi
> input khai thác lỗ hổng đó, đạt được khả năng thực thi lệnh tùy ý *bên trong*
> tiến trình; (3) vì tiến trình chạy bằng `root` (UID 0) trong container, lệnh
> đó thực thi với toàn quyền root — có thể ghi vào bất kỳ file nào trong
> container, cài backdoor, hoặc khai thác thêm lỗ hổng kernel/container runtime
> để "escape" ra ngoài; (4) nếu escape thành công, kẻ tấn công có UID 0 trên
> chính host, tức quyền cao nhất trên máy vật lý/VM đang chạy container đó.
>
> `Dockerfile` (multi-stage) cắt đứt chuỗi ở bước (3): dòng
> `RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app`
> và `USER appuser` khiến tiến trình `uvicorn` chạy với UID 10001, không phải
> root. Nếu code bị khai thác, kẻ tấn công chỉ có quyền của `appuser` — không
> ghi được ngoài `/app`, không cài được package hệ thống, và các kỹ thuật
> container-escape dựa vào quyền root bên trong container (ví dụ mount
> `/proc`, truy cập Docker socket, khai thác capability) đều bị chặn hoặc khó
> hơn hẳn. `Dockerfile.single` không có `USER`, nên vẫn chạy root — thiếu hẳn
> lớp phòng thủ này.

---

### Câu 6 — Bearer token (CP3)

Vì sao 401 phải kèm header `WWW-Authenticate: Bearer`? Và vì sao ta trả **cùng
một** thông báo lỗi cho cả ba trường hợp (thiếu header, sai scheme, sai token)
thay vì nói rõ sai ở đâu cho người dùng dễ sửa?

> Header `WWW-Authenticate: Bearer` là một phần của chuẩn HTTP (RFC 6750/7235):
> khi trả 401, server phải cho client biết *cơ chế xác thực nào được chấp
> nhận* để client (hoặc thư viện HTTP) biết cách thử lại đúng cách — ví dụ gửi
> `Authorization: Bearer <token>` thay vì Basic Auth. Thiếu header này, client
> hợp lệ không có cách chuẩn để biết phải làm gì tiếp theo.
>
> Trả cùng một thông báo `"invalid or missing bearer token"` cho cả ba trường
> hợp (thiếu header, sai scheme, sai token) là vì lý do bảo mật: nếu thông báo
> khác nhau cho từng trường hợp, kẻ tấn công dò token có thể suy ra thêm thông
> tin — ví dụ "sai token" nghĩa là format đúng nhưng giá trị sai, giúp thu hẹp
> phạm vi brute-force, hoặc "sai scheme" tiết lộ rằng hệ thống *có* kiểm tra
> Bearer. Gộp lại một thông báo mơ hồ khiến kẻ tấn công không phân biệt được
> đang thất bại ở bước nào, làm chậm mọi nỗ lực dò/khai thác — đánh đổi một
> chút tiện lợi debug của người dùng hợp lệ để lấy an toàn cho hệ thống.

---

### Câu 7 — Token bucket (CP3)

Với `capacity=10`, `refill_per_minute=10`: một client im lặng 10 phút rồi gửi
liên tiếp. Nó gửi được bao nhiêu request trước khi bị 429? Nếu bỏ đoạn
`min(capacity, ...)` trong `available()` thì con số đó thành bao nhiêu, và tại sao?

> Với `capacity=10`, `refill_per_minute=10` (~0.1667 token/giây): sau 10 phút im
> lặng, `available()` tính `tokens = 0 + 600s * (10/60) = 100`, nhưng bị chặn
> bởi `min(capacity, tokens) = min(10, 100) = 10`. Client bắt đầu gửi liên tiếp:
> mỗi request tiêu 1 token (10 → 9 → ... → 0), 10 request đầu thành công, đến
> request thứ 11 `available()` ≈ 0 (< 1) nên bị 429. Vậy: **10 request** trước
> khi bị chặn — đúng bằng `capacity`, dù đã tích lũy đủ token cho 100 request
> nếu không giới hạn.
>
> Nếu bỏ `min(capacity, ...)`: `available()` trả thẳng 100 (không bị trần chặn
> lại). Client sẽ gửi được **100 request** liên tiếp trước khi bị 429, dùng hết
> toàn bộ số token đã "tích lũy" trong 10 phút im lặng. Đây chính là lý do
> `min()` tồn tại: nó biến bucket từ "tích điểm không giới hạn theo thời gian
> chờ" thành đúng nghĩa **rate limiting có trần burst** — capacity giới hạn độ
> lớn tối đa của một đợt burst, bất kể client đã im lặng bao lâu.

---

### Câu 8 — Ngân sách theo ngày (CP3)

So sánh hạn mức $30/tháng với hạn mức $1/ngày cho cùng một client. Giả sử có sự
cố khiến một client gọi liên tục từ 2h sáng. Với mỗi cách, thiệt hại tối đa là
bao nhiêu và service tự hồi phục khi nào?

> `CostGuard` khóa spend theo ngày UTC (`spend:{client_id}:{YYYY-MM-DD}`), nên
> hạn mức thực chất luôn là **theo ngày** — câu hỏi là đặt trần ở $30/tháng hay
> $1/ngày cho cùng một client gặp sự cố gọi liên tục từ 2h sáng.
>
> - **Hạn mức $30/tháng** (ví dụ chia đều $1/ngày nhưng cho phép "mượn" từ ngày
>   khác, hoặc kiểm tra tổng theo tháng): nếu sự cố không bị phát hiện ngay
>   (con người thường không giám sát 2h sáng), client có thể tiêu gần hết $30
>   trong một đêm trước khi budget tháng chặn lại — thiệt hại tối đa gần bằng
>   **toàn bộ $30**, và vì reset theo tháng, service chỉ tự hồi phục vào đầu
>   tháng sau (hoặc phải can thiệp thủ công).
> - **Hạn mức $1/ngày** (đúng như `CostGuard` hiện tại): thiệt hại tối đa trong
>   một ngày bị chặn ở đúng **$1**, bất kể sự cố kéo dài bao lâu trong ngày đó.
>   Vì key có `day` trong tên và không cộng dồn giữa các ngày, tại 00:00 UTC
>   ngày hôm sau, `spent()` cho ngày mới tự động là 0 — service **tự hồi phục
>   ngay lập tức khi sang ngày mới**, không cần ai can thiệp.
>
> Tóm lại: hạn mức theo ngày giới hạn "bán kính nổ" của một sự cố xuống còn một
> phần nhỏ, và tự phục hồi theo chu kỳ ngắn — trong khi hạn mức theo tháng để
> thiệt hại tích lũy lớn hơn nhiều lần trước khi bị chặn.

---

### Câu 9 — /healthz khác /readyz (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

> Hiện tại `/healthz` (liveness) chỉ kiểm tra `shutdown_guard.draining` — không
> đụng Redis; `/readyz` (readiness) mới gọi `store.ping()` để kiểm tra Redis.
> Nếu gộp làm một endpoint dùng cho cả liveness lẫn readiness và cho nó kiểm
> tra Redis, chuỗi sự kiện khi Redis mất kết nối 30 giây trên cụm 3 container:
>
> 1. Redis mất kết nối tại t=0s. Cả 3 container vẫn đang chạy bình thường,
>    process khỏe mạnh, chỉ là không gọi được Redis.
> 2. Orchestrator (k8s/Docker Swarm) tiếp tục polling endpoint gộp đó theo chu
>    kỳ (ví dụ mỗi 10s) cho cả 3 container cùng lúc. Vì `store.ping()` fail,
>    endpoint trả 503 cho cả liveness lẫn readiness.
> 3. Readiness fail → cả 3 container bị gỡ khỏi load balancer gần như đồng thời
>    → **toàn bộ traffic bị chặn, downtime hoàn toàn** dù process vẫn sống.
> 4. Liveness cũng fail → sau `failureThreshold` lần fail liên tiếp (thường
>    2-3 lần, tức trong khoảng 20-30s), orchestrator coi cả 3 container là
>    "chết" và **restart cả 3 gần như cùng lúc** — dù process không hề crash,
>    chỉ vì phụ thuộc ngoài (Redis) tạm thời không sẵn sàng.
> 5. Redis hồi phục ở t=30s, nhưng 3 container vừa bị kill đang trong quá trình
>    khởi động lại (tốn thêm vài giây), nên downtime kéo dài **lâu hơn** 30
>    giây thực tế của sự cố Redis.
>
> Nếu giữ tách biệt như hiện tại: chỉ `/readyz` fail → container bị gỡ khỏi
> load balancer (không nhận traffic mới) nhưng **không bị restart**, vì
> `/healthz` không đụng Redis nên liveness vẫn pass. Khi Redis hồi phục,
> `/readyz` pass lại ngay và traffic quay lại — không có restart, không mất
> trạng thái, downtime đúng bằng thời gian Redis thực sự mất kết nối.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

> **Câu này cần bạn tự deploy thật lên Railway/Render (xem `DEPLOYMENT.md`,
> `railway.toml`, `render.yaml`) và ghi lại lỗi thật bạn gặp** — không thể trả
> lời thay vì đề bài yêu cầu đúng trải nghiệm cá nhân của bạn. Gợi ý những chỗ
> hay gãy trong repo này để bạn để ý khi deploy:
> - `Dockerfile` dùng `CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]`
>   — nếu platform không set `$PORT` hoặc bạn tự set `PORT` sai kiểu (không phải
>   số), app có thể bind sai cổng và health check timeout.
> - `Settings.api_token` không có default (Câu 1) — quên set biến môi trường
>   `API_TOKEN` trên platform sẽ làm container crash-loop ngay khi khởi động.
> - `redis_url` mặc định là `redis://localhost:6379/0` — nếu deploy mà không
>   trỏ `REDIS_URL` tới Redis add-on thật của platform, `/readyz` sẽ trả 503
>   mãi mãi vì `store.ping()` luôn fail.
>
> Khi ghi câu trả lời, nêu rõ: (1) thông báo lỗi/log chính xác bạn thấy trong
> dashboard hoặc `docker logs`, (2) bước bạn dùng để xác định nguyên nhân (đọc
> log, so sánh biến môi trường, curl health endpoint...), (3) thay đổi cụ thể
> đã sửa (biến môi trường, dòng code, cấu hình platform).
