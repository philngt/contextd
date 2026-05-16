# Code Snapshot — {evid-id}

> Source: codebase tại `{repo-path}` @ git SHA `{git_sha}` (branch: `{git_branch}`)
> Snapshotted at: {ISO timestamp}
> Scope: {paths/globs included}
>
> Đây là snapshot METADATA, KHÔNG phải bản sao source code. Mọi citation `(file:line)` trỏ về code thật trong repo (immutable tại git SHA trên).

---

## Section 1 — Project metadata

- **Project name**: {từ pom.xml#artifactId / package.json#name / dir name}
- **Version**: {từ pom.xml#version / package.json#version}
- **Build tool**: {maven | gradle | npm | pnpm | poetry | cargo | go-mod}
- **Language(s)**: {Java 21 | TypeScript 5.x | ...}
- **Top-level dirs**: {liệt kê 1 cấp đầu, kèm 1-line mô tả mỗi dir nếu rõ}
- **README excerpt**: {≤ 200 ký tự nếu có README.md}

---

## Section 2 — Dependencies

### Production
| Group | Artifact | Version | Purpose (heuristic) |
|-------|----------|---------|---------------------|
| {group} | {artifact} | {ver} | {purpose} |

### Test
{tương tự}

### Build/dev
{tương tự}

> Citation: `(pom.xml:L<start>-L<end>)` hoặc `(package.json:L..-L..)`

---

## Section 3 — Configs

### `{config-file-1}`
```yaml
# Đã redact: tokens, passwords, internal hostnames có credential
{nội dung config với placeholders}
```
Citation: `({path}:L..-L..)`

### `{config-file-2}`
{tương tự}

---

## Section 4 — REST endpoints

| Method | Path | Handler class:method | Auth | Citation |
|--------|------|----------------------|------|----------|
| GET    | /api/x/{id} | `XController.getX` | {required/none} | `({path}:L..-L..)` |

---

## Section 5 — Message consumers

### Kafka
| Topic | Group ID | Consumer class:method | Citation |
|-------|----------|------------------------|----------|
| {topic} | {group} | `KafkaXListener.onMessage` | `({path}:L..)` |

### MQTT / RabbitMQ / SQS / ...
{tương tự}

---

## Section 6 — Services & components

| Class | Stereotype | Responsibility (1 line) | Citation |
|-------|------------|--------------------------|----------|
| {FQN} | @Service / @Component / @Repository | {summary} | `({path}:L..)` |

---

## Section 7 — DB schema

### Entities
| Class | Table | Key fields | Citation |
|-------|-------|------------|----------|
| {Entity} | {table} | {pk, important fk} | `({path}:L..)` |

### Migrations
{liệt kê file migration theo thứ tự version}

---

## Section 8 — Public APIs

> Class signatures cho package-level public API (interfaces, public classes có @PublicApi hoặc tương đương).

```java
public interface FooService {
    Foo create(CreateFooCommand cmd);
    Optional<Foo> findById(FooId id);
}
```
Citation: `(src/main/java/.../FooService.java:L..-L..)`

---

## Section 9 — Git summary

### Last 50 commits (oneline)
```
{sha7} {date} {author} — {subject}
...
```

### Top contributors (by commit count, last 1 year)
| Author | Commits |
|--------|---------|
| {name} | {N} |

### Notable commits (mention "decision", "chose", "switch to", "deprecate")
| SHA | Date | Subject |
|-----|------|---------|
| {sha7} | {date} | {subject} |

---

## Section 10 — Notes

{Bất cứ điều gì surprising mà extractor phát hiện — vd 2 framework cùng level (Spring + Quarkus), config file conflict, deprecated API vẫn được dùng. KHÔNG đoán; chỉ ghi observation kèm citation.}
