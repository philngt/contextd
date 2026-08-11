# 08 — Knowledge Gaps (vs workspace `default`)

## Blocking gaps (must resolve before apply)

1. **Chưa chạy QA end-to-end trên evidence set thật** — templates có frontmatter chưa được render thành file thật trong pipeline (fixture này sinh ra để lấp gap này). Apply lên wiki nên chờ sau khi QA verified.

## Nice-to-have gaps

1. **C8 recommendations chưa chạy với source_type=code** — `recommendations.md` chỉ được sinh khi `source_type=code`; fixture dùng `paste` nên Bước 3.5 skip. Không block — code evidence chạy độc lập.

## Missing source types

- Không có source type nào thiếu — paste evidence đủ để verify QA templates.
