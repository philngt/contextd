# pack-dba — Constraints

- Mọi thay đổi schema PHẢI có rollback plan hoặc forward-fix strategy rõ ràng.
- Thay đổi có khả năng lock lớn PHẢI nêu maintenance strategy và impact scope.
- Query tuning recommendation PHẢI dựa trên evidence (plan/metrics), không tối ưu cảm tính.
- Backup policy PHẢI nêu rõ RPO/RTO và có restore verification định kỳ.
