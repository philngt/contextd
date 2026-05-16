# Recipe: Scheduled Recurring Task

Tool tự động chạy định kỳ (mỗi ngày, mỗi giờ, mỗi tuần). Vd: backup data, check email mới, sync API, gửi report.

## When to use

Task signals:
- "Mỗi sáng tự pull data từ API và lưu file"
- "Hằng tuần backup folder X sang nơi Y"
- "Mỗi giờ check website giá có đổi không"
- "Daily report gửi email lúc 8AM"

Không phải:
- Chạy 1 lần khi user gõ command → các recipe khác phù hợp hơn
- Cần GUI điều khiển → `daily-form-with-history` + cron riêng

## Tech Stack

Recipe này = wrapper trên recipe khác (`bulk-file-processing`, `api-data-fetcher`, ...) + scheduler.

| Scheduler | Linux/macOS | Windows native | Docker (cross-platform) |
|-----------|-------------|----------------|-------------------------|
| Đơn giản | `cron` | Task Scheduler (GUI) | Docker container với restart-policy + Python `schedule` |
| Phức tạp | `systemd timer` | Task Scheduler XML | `cron` trong container |

### Linux/macOS — cron

Edit crontab:
```bash
crontab -e
```

Thêm dòng (chạy mỗi ngày 8:00 AM):
```cron
0 8 * * * /home/user/myapp/.venv/bin/python /home/user/myapp/tool.py >> /home/user/myapp/log.txt 2>&1
```

Cron syntax: `phút giờ ngày tháng thứ` — `0 8 * * *` = 8h0' mọi ngày.

### Windows native — Task Scheduler

GUI:
1. Mở "Task Scheduler" → Create Task
2. Triggers → Daily, 8:00 AM
3. Actions → Start a program
   - Program: `D:\myapp\.venv\Scripts\python.exe`
   - Arguments: `D:\myapp\tool.py`
   - Start in: `D:\myapp`
4. Settings → tick "Run whether user is logged on or not"

### Windows + Docker (recommend — đồng nhất với Linux)

`docker-compose.yml`:
```yaml
services:
  scheduled-tool:
    image: python:3.11-slim
    working_dir: /app
    volumes: [".:/app", "./output:/output"]
    command: bash -c "pip install -q -r requirements.txt && python scheduler.py"
    restart: unless-stopped
```

`scheduler.py` — Python in-process scheduler:
```python
import schedule
import time
import subprocess

def run_task():
    print("[scheduler] Running tool.py")
    subprocess.run(["python", "tool.py"], check=False)

schedule.every().day.at("08:00").do(run_task)
# Hoặc: schedule.every().hour.do(run_task)
# Hoặc: schedule.every().monday.at("09:30").do(run_task)

print("[scheduler] Started — waiting for triggers")
while True:
    schedule.run_pending()
    time.sleep(30)
```

`requirements.txt`:
```
schedule
# + dependencies của tool.py
```

```bash
docker compose up -d
docker compose logs -f
```

## Trade-offs

**Vì sao Docker container + Python `schedule`** (cho cross-platform):
- Đồng nhất Linux/Windows — 1 cách deploy
- Container restart-policy = tool tự chạy lại nếu máy reboot
- Không phải nhớ "máy này dùng cron, máy kia dùng Task Scheduler"

**Vì sao KHÔNG**:
- **Cron-only Linux**: tốt nhưng không cross-platform.
- **Task Scheduler Windows GUI**: GUI dễ click nhầm, khó version-control config.
- **Airflow / Prefect**: enterprise scheduler, overkill cho 1 task chạy daily.
- **AWS Lambda / Cloud Functions**: cloud lock-in, cost, học cloud setup.

## Skeleton — full Docker setup

Folder structure:
```
my-scheduled-tool/
├── docker-compose.yml
├── scheduler.py
├── tool.py            # logic thực — pull API, process file, etc
├── requirements.txt
└── output/            # output ghi ra đây, persist ở host
```

`tool.py`:
```python
# Logic thực — không cần biết về scheduler
from datetime import datetime
from pathlib import Path

def main():
    print(f"[tool] Run at {datetime.now().isoformat()}")
    # Logic pull data / process file / ...
    Path("output").mkdir(exist_ok=True)
    Path(f"output/run-{datetime.now():%Y%m%d-%H%M}.txt").write_text("Done")

if __name__ == "__main__":
    main()
```

Test ngay không scheduler:
```bash
docker compose run --rm scheduled-tool python tool.py
```

Run scheduled (background):
```bash
docker compose up -d
```

Check log:
```bash
docker compose logs -f
```

Stop:
```bash
docker compose down
```

## Decision tree

✅ **Match recipe này KHI**:
- Tool đã hoạt động khi chạy thủ công, giờ cần tự động
- Task chạy ≤ vài giờ
- 1 máy chạy là đủ (không cần distributed)

❌ **KHÔNG match KHI**:
- Cần trigger event-based (vd file mới upload thì chạy) → cân nhắc file watcher (`watchdog`)
- Cần distributed → ngoài scope solo builder
- Task chạy giờ-ngày liên tục → cân nhắc dedicated server / cloud

## Note quan trọng

- **Log mọi run** ra file/output — nếu cron chạy ngầm và lỗi không log, bạn không biết tool đã fail.
- **Tool phải idempotent** — chạy 2 lần vẫn safe. Vì cron có thể trigger overlap nếu run trước chưa xong.
- **Test thủ công TRƯỚC khi đặt scheduler** — confirm tool.py chạy chuẩn rồi mới schedule.
