# pack-frontend-react — Coding Rules

## Component Structure

- One component per file, named after file. Default export cho top-level component.
- Container/Presenter split khi component có cả data fetching + complex render.
- Compound components cho UI có sub-parts có quan hệ (`<Tabs><Tabs.Item/></Tabs>`).

## Props & Types

- TypeScript: `interface Props {}` hoặc `type Props =`. Avoid `any` and `React.FC<>` (loses children typing).
- Optional props với default qua destructuring `({ size = "md" }: Props)`, không qua `defaultProps`.
- Don't spread arbitrary `{...props}` xuống DOM element — explicit pass.

## Data Fetching

- TanStack Query / SWR cho client-side data fetching.
- Next.js: prefer Server Component fetch hoặc server action; client fetch chỉ khi cần real-time / mutation flow.
- Always handle 3 states: loading / error / data. Default empty state too.

## Forms

- Controlled inputs với React Hook Form (RHF) hoặc state-driven controlled component.
- Validate qua Zod / Yup schema, share schema giữa client + server (single source of truth).
- Submit handler async + disable button while pending.

## Styling

- Avoid inline `style={{...}}` cho static value — dùng class (CSS Modules, Tailwind, styled-components, vanilla-extract).
- Inline style chấp nhận khi value dynamic per-instance (vd `style={{ width: progress + "%" }}`).

## Error Boundary

- Top-level `ErrorBoundary` quanh route/page, hiển thị fallback thay vì white screen.
- Suspense boundary quanh data fetching để tránh suspending toàn page.

## Testing

- React Testing Library (RTL) — query by role/label, không by class/id (test what user sees).
- Mock external boundary (fetch, router) — không mock implementation detail (useState).
