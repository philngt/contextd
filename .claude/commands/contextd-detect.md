# Wiki Detect

Skill này chạy tự động khi `/contextd-use` không tìm thấy `.claude/wiki.json` của codebase, hoặc gọi trực tiếp để kiểm tra trạng thái tích hợp wiki của dự án hiện tại.

> Wiki giờ tổ chức theo workspace. Mọi path scan/validate đều scope trong `{wiki_root}/workspaces/{workspace}/` — KHÔNG cross-workspace.

---

## Bước 1 — Kiểm tra local config

Tìm file `.claude/wiki.json` trong thư mục gốc của dự án (codebase) hiện tại.

### Nếu file tồn tại → Validate config

Đọc file và kiểm tra từng field:

| Kiểm tra | Hành động nếu lỗi |
|----------|------------------|
| `project` có giá trị | Báo lỗi: thiếu tên project |
| `workspace` có giá trị | Báo lỗi: thiếu workspace; gợi ý chạy `/contextd-setup` |
| `wiki_root` resolve được (hoặc null → fallback `~/.claude/wiki-global.json`) | Nếu không resolve → báo path sai |
| `{wiki_root}/workspaces/{workspace}/` tồn tại | Nếu không → báo workspace không tồn tại; liệt kê workspaces có sẵn |
| `knowledge_map` resolve trong `{wiki_root}/workspaces/{workspace}/` | Nếu không tồn tại → báo file không tìm thấy |
| `domain` có trong `{wiki_root}/workspaces/{workspace}/domains/` | Nếu không tồn tại → cảnh báo |
| `patterns` đều có trong `{wiki_root}/workspaces/{workspace}/patterns-index.md` | Liệt kê pattern không nhận ra |
| `contracts` đều có trong `{wiki_root}/workspaces/{workspace}/platform/contracts/` | Liệt kê contract không tìm thấy |
| `services` đều resolve trong `{wiki_root}/workspaces/{workspace}/projects/{project}/services/` | Liệt kê service doc không tìm thấy |

Hiển thị kết quả:
```
✅ Wiki config hợp lệ
   Workspace: {workspace}
   Project  : {project}
   Wiki root: {resolved_path}
   Domain   : {domain}
   Patterns : {danh sách}
   Contracts: {danh sách}
   Services : {danh sách}
```

Hoặc nếu có lỗi:
```
⚠️  Wiki config có vấn đề
   [ERROR] workspace 'foo' không tồn tại trong {wiki_root}/workspaces/
           Có sẵn: example-surgery, company-b, ...
   [ERROR] knowledge_map không tìm thấy: workspaces/{ws}/projects/xyz/knowledge-map.md
   [WARN]  domain 'surgery' không có trong workspaces/{ws}/domains/
   → Chạy /contextd-setup để sửa
```

---

### Nếu file KHÔNG tồn tại → Scan dự án và đề xuất

#### Bước 1a — Đọc global config

Đọc `~/.claude/wiki-global.json` để lấy `wiki_root` (và optional `default_workspace`).

Nếu file không tồn tại:
```
⚠️  Chưa cấu hình wiki global.

Để bắt đầu:
1. Copy file templates/wiki-global.json từ wiki-template vào ~/.claude/wiki-global.json
2. Điền đường dẫn thực tế vào "wiki_root"
3. (Optional) Điền "default_workspace" để skip bước chọn workspace ở /contextd-setup
4. Chạy lại /contextd-detect
```
Dừng tại đây nếu không có global config.

#### Bước 1b — Xác định candidate workspace

Thứ tự ưu tiên:
1. `default_workspace` trong `~/.claude/wiki-global.json` (nếu có).
2. Nếu chỉ có 1 workspace trong `{wiki_root}/workspaces/` → dùng nó.
3. Để trống → user phải chọn ở `/contextd-setup`.

#### Bước 1c — Scan project signals

Tìm các dấu hiệu trong dự án hiện tại:

**Scan dependency files** (`pom.xml`, `build.gradle`, `package.json`, `requirements.txt`):

| Tìm thấy | Đề xuất pattern/contract |
|----------|--------------------------|
| `spring-kafka` hoặc `kafka-clients` | `kafka-event-processing` |
| `eclipse-paho` hoặc `hivemq-mqtt-client` hoặc `mqtt` | `mqtt-routing`, `mqtt-topic-contract` |
| `spring-batch` | ghi chú: xem section Batch trong `kafka-event-processing` |
| `spring-web` hoặc `feign` hoặc `axios` | component: `http` |
| `spring-data` hoặc `jpa` hoặc `sequelize` | component: `db` |

> Pattern/contract đề xuất phải tồn tại trong workspace candidate. Nếu workspace candidate chưa có → đánh dấu "(missing in workspace {ws})" và gợi ý tạo bằng `/contextd-update` sau.

**Scan package names / file paths** để detect domain:

Tìm các thư mục hoặc package có tên trùng với domain trong `{wiki_root}/workspaces/{ws}/domains/`:
- Ví dụ: thư mục `surgery/`, `patient/`, `finance/` → map sang domain tương ứng trong workspace

**Scan tên dự án** (từ `pom.xml` `<artifactId>`, `package.json` `name`, hoặc tên thư mục):
- Tìm project tương ứng trong `{wiki_root}/workspaces/{ws}/projects/`

#### Bước 1d — Hiển thị đề xuất

```
📋 Wiki chưa được cấu hình cho dự án này.

Workspace candidate: {ws}    (lý do: default_workspace | only one | n/a)

Phát hiện từ codebase:
  Kafka consumer        → pattern: kafka-event-processing
  MQTT publisher        → pattern: mqtt-routing
                           contract: mqtt-topic-contract
  Package: com.example.surgery → domain: surgery

Wiki phù hợp (trong workspace {ws}):
  knowledge_map: projects/surgery-service/knowledge-map.md
  domain       : surgery
  patterns     : ["kafka-event-processing", "mqtt-routing"]
  contracts    : ["mqtt-topic-contract"]

→ Chạy /contextd-setup để tạo .claude/wiki.json tự động với các giá trị trên
→ Hoặc copy templates/wiki-local.json vào .claude/wiki.json và điền thủ công (nhớ điền field "workspace")
```

Nếu không detect được gì:
```
📋 Wiki chưa được cấu hình. Không phát hiện component quen thuộc.

→ Chạy /contextd-setup để cấu hình thủ công (sẽ hỏi workspace)
→ Hoặc copy templates/wiki-local.json vào .claude/wiki.json
```

---

## Khi nào nên chạy

- Tự động: được gọi bởi `/contextd-use` khi không tìm thấy `.claude/wiki.json` của codebase
- Thủ công: khi muốn kiểm tra config wiki của dự án hiện tại
- Sau khi thêm dependency mới vào dự án (để check đề xuất pattern mới)
- Sau khi thêm/đổi workspace trong wiki-template (xác nhận project vẫn trỏ đúng workspace)
