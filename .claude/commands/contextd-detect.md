# /contextd-detect — Detect contextd Config

Skill này chạy tự động khi `/use-contextd` không resolve được config của codebase, hoặc gọi trực tiếp để kiểm tra trạng thái tích hợp contextd của dự án hiện tại.

> Knowledge giờ tổ chức theo workspace. Mọi path scan/validate đều scope trong `{knowledge_root}/workspaces/{workspace}/` — KHÔNG cross-workspace.

---

## Bước 1 — Kiểm tra local config

Tìm file `.contextd/config.json` trong thư mục gốc của dự án (codebase) hiện tại.

### Nếu file tồn tại → Validate config

Đọc file và kiểm tra từng field:

| Kiểm tra | Hành động nếu lỗi |
|----------|------------------|
| `project` có giá trị | Báo lỗi: thiếu tên project |
| `workspace` có giá trị | Báo lỗi: thiếu workspace; gợi ý chạy `/contextd-setup` |
| `knowledge_root` resolve được (hoặc null → fallback `~/.contextd/config.json`) | Nếu không resolve → báo path sai |
| `{knowledge_root}/workspaces/{workspace}/` tồn tại | Nếu không → báo workspace không tồn tại; liệt kê workspaces có sẵn |
| `knowledge_map` resolve trong `{knowledge_root}/workspaces/{workspace}/` | Nếu không tồn tại → báo file không tìm thấy |
| `domain` có trong `{knowledge_root}/workspaces/{workspace}/domains/` | Nếu không tồn tại → cảnh báo |
| `patterns` đều có trong `{knowledge_root}/workspaces/{workspace}/patterns-index.md` | Liệt kê pattern không nhận ra |
| `contracts` đều có trong `{knowledge_root}/workspaces/{workspace}/platform/contracts/` | Liệt kê contract không tìm thấy |
| `services` đều resolve trong `{knowledge_root}/workspaces/{workspace}/projects/{project}/services/` | Liệt kê service doc không tìm thấy |

Hiển thị kết quả:
```
✅ contextd config hợp lệ
   Workspace: {workspace}
   Project  : {project}
   Knowledge root: {resolved_path}
   Domain   : {domain}
   Patterns : {danh sách}
   Contracts: {danh sách}
   Services : {danh sách}
```

Hoặc nếu có lỗi:
```
⚠️  contextd config có vấn đề
   [ERROR] workspace 'foo' không tồn tại trong {knowledge_root}/workspaces/
           Có sẵn: example-surgery, company-b, ...
   [ERROR] knowledge_map không tìm thấy: workspaces/{ws}/projects/xyz/knowledge-map.md
   [WARN]  domain 'surgery' không có trong workspaces/{ws}/domains/
   → Chạy /contextd-setup để sửa
```

---

### Nếu file KHÔNG tồn tại → Scan dự án và đề xuất

#### Bước 1a — Đọc global config

Đọc `~/.contextd/config.json` để lấy `knowledge_root` (và optional `default_workspace`).

Nếu file không tồn tại:
```
⚠️  Chưa cấu hình contextd global.

Để bắt đầu:
1. Copy file templates/contextd-config.json từ contextd repo vào ~/.contextd/config.json
2. Điền đường dẫn thực tế vào "knowledge_root"
3. (Optional) Điền "default_workspace" để skip bước chọn workspace ở /contextd-setup
4. Chạy lại /contextd-detect
```
Dừng tại đây nếu không có global config.

#### Bước 1b — Xác định candidate workspace

Thứ tự ưu tiên:
1. `default_workspace` trong `~/.contextd/config.json` (nếu có).
2. Nếu chỉ có 1 workspace trong `{knowledge_root}/workspaces/` → dùng nó.
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

> Pattern/contract đề xuất phải tồn tại trong workspace candidate. Nếu workspace candidate chưa có → đánh dấu "(missing in workspace {ws})" và gợi ý tạo bằng `/update-contextd` sau.

**Scan package names / file paths** để detect domain:

Tìm các thư mục hoặc package có tên trùng với domain trong `{knowledge_root}/workspaces/{ws}/domains/`:
- Ví dụ: thư mục `surgery/`, `patient/`, `finance/` → map sang domain tương ứng trong workspace

**Scan tên dự án** (từ `pom.xml` `<artifactId>`, `package.json` `name`, hoặc tên thư mục):
- Tìm project tương ứng trong `{knowledge_root}/workspaces/{ws}/projects/`

#### Bước 1d — Hiển thị đề xuất

```
📋 contextd chưa được cấu hình cho dự án này.

Workspace candidate: {ws}    (lý do: default_workspace | only one | n/a)

Phát hiện từ codebase:
  Kafka consumer        → pattern: kafka-event-processing
  MQTT publisher        → pattern: mqtt-routing
                           contract: mqtt-topic-contract
  Package: com.example.surgery → domain: surgery

Knowledge phù hợp (trong workspace {ws}):
  knowledge_map: projects/surgery-service/knowledge-map.md
  domain       : surgery
  patterns     : ["kafka-event-processing", "mqtt-routing"]
  contracts    : ["mqtt-topic-contract"]

→ Chạy /contextd-setup để tạo .contextd/config.json tự động với các giá trị trên
→ Hoặc copy templates/contextd-config.json vào .contextd/config.json và điền thủ công (nhớ điền field "workspace")
```

Nếu không detect được gì:
```
📋 contextd chưa được cấu hình. Không phát hiện component quen thuộc.

→ Chạy /contextd-setup để cấu hình thủ công (sẽ hỏi workspace)
→ Hoặc copy templates/contextd-config.json vào .contextd/config.json
```

---

## Khi nào nên chạy

- Tự động: được gọi bởi `/use-contextd` khi không tìm thấy `.contextd/config.json` của codebase
- Thủ công: khi muốn kiểm tra config contextd của dự án hiện tại
- Sau khi thêm dependency mới vào dự án (để check đề xuất pattern mới)
- Sau khi thêm/đổi workspace trong knowledge repo (xác nhận project vẫn trỏ đúng workspace)

## Compatibility

Nếu canonical `.contextd/config.json` chưa có, resolver vẫn có thể đọc legacy `.claude/wiki.json`, `.Codex/wiki.json`, và legacy globals. Khi detect thấy legacy config, output phải khuyến nghị `contextd migrate-config` thay vì coi legacy file là source of truth.
