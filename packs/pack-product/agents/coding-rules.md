# pack-product — Writing Rules

> "Coding rules" trong pack này nghĩa là **writing rules** cho product documentation. Pack-product không sinh code — nó sinh artifacts: briefs, OKRs, personas, journeys.

## Brief Writing

- **Lead with the problem, not the solution**. Section đầu tiên là `## Problem`, không phải `## Feature description`.
- **Quantify the problem**: "30% of new users abandon onboarding at step 3" beats "users find onboarding hard".
- **One brief = one coherent outcome/initiative**. Split khi phần có owner, metric, rollout hoặc acceptance lifecycle độc lập; không split chỉ vì số bullet.
- **Use active voice**: "User uploads CSV" beats "CSV file is uploaded by user".

## OKR Writing

- **Objective = qualitative, inspirational, time-bound**. Vd: "Make first-week activation effortless by Q2".
- **Key Result = quantitative, measurable, ambitious**. Vd: "Increase D7 retention from 22% → 35%".
- Giữ tập Key Result nhỏ và đủ để chứng minh Objective; số lượng do outcome model/governance quyết định, không theo quota chung.
- **KR is an outcome, not an output**. "Ship feature X" is output (binary done/undone). "X% of users adopt feature X within 14 days" is outcome.

## Persona Writing

- Header ưu tiên role/context/JTBD; name/photo/demographic chỉ dùng khi research cần và privacy policy cho phép, không dùng ảnh/chi tiết hư cấu để tăng cảm giác “thật”.
- Sections: **Goals**, **Constraints/Frictions**, **Observed Behaviors**, **Context**, **Evidence base** (method, sample, source IDs, date, confidence).
- Quote chỉ dùng excerpt đã consent/redact và gắn source ID; paraphrase phải được label để không biến thành lời người dùng.

## Customer Journey Writing

- Format table: `Stage | User Action | Touchpoint | Emotion | Pain Point | Opportunity`
- Mỗi stage có **Drop-off rate** column nếu có data analytics.
- **Annotate moments of truth** — nơi user quyết định stay/leave.

## Roadmap Writing

- Format theo planning cadence của workspace; giới hạn WIP/capacity phải lấy từ planning policy thay vì quota cố định trong pack.
- Mỗi item: link → brief + status (`committed` / `exploring` / `shipped` / `cut`).
- **Date format**: `YYYY-Qx` cho quarter, `YYYY-MM` cho month milestone, không dùng "soon" / "next sprint".

## Metrics Writing

- Xác định một primary outcome metric cho mỗi product/scope khi mô hình phù hợp; portfolio workspace có thể có nhiều scoped primary metrics nhưng phải nêu hierarchy/trade-off.
- Supporting metrics organized in tree: NSM → input metrics → leading indicators.
- Mỗi metric: **definition** (formula), **owner** (team/role), **measurement cadence** (daily/weekly), **dashboard link** (nếu có).

## Translation from Engineering (cho `/business-view`)

Khi dịch service/contract sang business view, áp dụng mapping:

| Engineering term | Business view |
|---|---|
| Endpoint / API | Capability the system offers |
| Schema / DTO | Information shape we exchange |
| Service | Component that does X for users |
| Deployment / container | Where it runs (cloud / region / device) |
| Migration | One-time data update |
| Refactor | Internal cleanup, no user-visible change |
| Latency p99 | "99% of users see response within Xms" |
| Throughput | How many requests we can handle per second/minute |

Output `/business-view` PHẢI: (1) không có jargon trong main body, (2) kèm "Technical reference" footnote link tới source doc.
