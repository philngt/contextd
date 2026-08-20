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

| Target | Preferred owner | Notes |
|--------|-----------------|-------|
| Linux host | `systemd timer` hoặc managed cron | One-shot process, logs/exit status, overlap policy |
| macOS host | `launchd` (cron only when already governed) | Explicit environment, working directory and timezone |
| Windows host | Task Scheduler | Export/version task definition; set account/credential policy |
| Container/platform | Platform scheduler; persistent in-process scheduler only with owner | Container restart policy is not a schedule |

### Cron example (only on a host where cron is the approved scheduler)

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

### Persistent container option (only when an always-on scheduler process is justified)

`compose.yaml`:
```yaml
services:
  scheduled-tool:
    build:
      context: .
      args:
        PYTHON_BASE: ${PYTHON_IMAGE:?set a tested Python image tag or digest}
    working_dir: /app
    volumes: ["./output:/app/output"]
    command: python scheduler.py
    restart: unless-stopped
```

```dockerfile
# Dockerfile
ARG PYTHON_BASE
FROM ${PYTHON_BASE}
WORKDIR /app
COPY requirements.lock .
RUN python -m pip install --no-cache-dir -r requirements.lock
COPY scheduler.py tool.py ./
CMD ["python", "scheduler.py"]
```

`scheduler.py` — Python in-process scheduler:
```python
import schedule
import time
import subprocess
import sys

def run_task():
    print("[scheduler] Running tool.py")
    completed = subprocess.run(["python", "tool.py"], check=False)
    if completed.returncode != 0:
        # Report the failed run without killing the scheduler loop. Production
        # code should also persist run status and alert on this event.
        print(
            f"[scheduler] tool.py failed with exit code {completed.returncode}",
            file=sys.stderr,
        )

schedule.every().day.at("08:00").do(run_task)
# Hoặc: schedule.every().hour.do(run_task)
# Hoặc: schedule.every().monday.at("09:30").do(run_task)

print("[scheduler] Started — waiting for triggers")
while True:
    schedule.run_pending()
    time.sleep(30)
```

`requirements.lock` (pin the tested scheduler/runtime versions):
```
schedule
# + dependencies của tool.py
```

```bash
docker compose up -d
docker compose logs -f
```

## Trade-offs

**Khi nào container + in-process scheduler hợp lý**:
- Target đã vận hành container continuously và có owner cho restart/log/upgrade.
- Runtime/dependencies cần pin giống nhau giữa hosts.
- Misfire, timezone/DST, duplicate instance và overlap semantics đã được chốt/test.

**Vì sao KHÔNG**:
- **Native scheduler**: thường ít moving parts nhất cho một host; khác config giữa OS nhưng process chỉ chạy khi đến lịch.
- **Workflow orchestrator/managed scheduler**: hợp khi cần dependency graph, distributed execution, retries/audit/SLA; thêm vận hành cho task local nhỏ.
- **Cloud scheduler/function**: đánh giá theo data residency, networking, cost và existing platform ownership; không loại chỉ vì cloud.

## Skeleton — full Docker setup

Folder structure:
```
my-scheduled-tool/
├── compose.yaml
├── Dockerfile
├── scheduler.py
├── tool.py            # logic thực — pull API, process file, etc
├── requirements.lock
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
- Task duration/timeout nhỏ hơn interval hoặc có explicit overlap/queue policy
- 1 máy chạy là đủ (không cần distributed)

❌ **KHÔNG match KHI**:
- Cần trigger event-based (vd file mới upload thì chạy) → cân nhắc file watcher (`watchdog`)
- Cần distributed → ngoài scope solo builder
- Task long-running/continuous → dùng service supervision hoặc platform phù hợp, không giả scheduler là worker

## Note quan trọng

- **Mỗi run có run ID, start/end/status/duration và durable output/error destination**; monitoring phải phát hiện cả “không chạy”.
- **Chốt delivery semantics**: idempotent/re-entrant hoặc lock/dedupe/transaction; document misfire, retry và overlap behavior.
- **Timezone/DST explicit**; test clock changes và máy sleep/reboot nếu relevant.
- **Test thủ công TRƯỚC khi đặt scheduler** — confirm tool.py chạy chuẩn rồi mới schedule.
