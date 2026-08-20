# pack-frontend-react — Coding Rules

## Component Structure

- Tách file theo cohesion và ownership; không bắt buộc “one component per file” khi helper nhỏ chỉ phục vụ một component.
- Tách data/loading/error boundary khỏi presentation khi điều đó làm contract dễ test, không áp Container/Presenter máy móc.
- Compound components cho UI có sub-parts có quan hệ (`<Tabs><Tabs.Item/></Tabs>`).

## Props & Types

- TypeScript: dùng `interface` hoặc `type` theo local convention; type `children`/callback/ref rõ và tránh `any` không kiểm soát.
- Optional props với default qua destructuring `({ size = "md" }: Props)`, không qua `defaultProps`.
- Don't spread arbitrary `{...props}` xuống DOM element — explicit pass.

## Data Fetching

- Client-side data fetching dùng workspace-approved cache/data layer khi cần dedupe, retry hoặc invalidation.
- Next.js: chọn Server Component, route handler/action, hoặc client fetch theo pinned router/version, auth boundary và freshness contract.
- Model các state thực sự có thể xảy ra (loading/pending, error, empty, stale/refresh, success) theo data contract; không ép boilerplate state không reachable.

## Forms

- Chọn controlled/uncontrolled form theo UX và performance; library không bắt buộc nếu native form primitives đủ.
- Validate client để hỗ trợ UX và luôn validate lại ở trusted server boundary; share schema khi semantics/runtime tương thích.
- Pending submit phải ngăn duplicate effect theo interaction contract; disable, idempotency key hoặc alternate feedback được chọn theo accessibility/UX.

## Styling

- Avoid inline `style={{...}}` cho static value — dùng class (CSS Modules, Tailwind, styled-components, vanilla-extract).
- Inline style chấp nhận khi value dynamic per-instance (vd `style={{ width: progress + "%" }}`).

## Error Boundary

- Đặt error boundary tại recovery/ownership boundary phù hợp; route-level fallback là baseline khi không có boundary hẹp hơn.
- Đặt Suspense boundary theo reveal/streaming UX của router đã pin, không bọc máy móc mọi fetch.

## Testing

- React Testing Library (RTL) — query by role/label, không by class/id (test what user sees).
- Mock external boundary (fetch, router) — không mock implementation detail (useState).
