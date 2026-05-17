# NeevFinance — Frontend Architecture

> **Senior Frontend Architect Reference**
> Stack: Next.js 14 (App Router) · TypeScript · Tailwind · shadcn/ui · Framer Motion · D3.js · Recharts · React Query · Zustand · Axios · Sonner

---

## Folder Tree

```
frontend/
│
├── app/                          # Next.js 14 App Router — routing ONLY
│   ├── layout.tsx                # Root HTML shell, providers, fonts
│   ├── page.tsx                  # Root redirect → /dashboard
│   ├── globals.css               # Tailwind base + CSS variables
│   ├── not-found.tsx             # 404 page
│   ├── error.tsx                 # Root error boundary
│   ├── loading.tsx               # Root suspense fallback
│   │
│   ├── (auth)/                   # Route group — unauthenticated
│   │   ├── layout.tsx            # Auth shell (centered card layout)
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   │
│   ├── (dashboard)/              # Route group — protected, sidebar layout
│   │   ├── layout.tsx            # Auth guard + Sidebar + Topbar
│   │   ├── dashboard/
│   │   │   ├── page.tsx          # Compose dashboard feature components
│   │   │   ├── loading.tsx       # Skeleton state
│   │   │   └── error.tsx         # Error state
│   │   ├── cashflow/
│   │   ├── loan/
│   │   ├── watchlist/
│   │   ├── company/[bseCode]/    # Dynamic route — company deep-dive
│   │   └── settings/
│   │
│   └── api/health/route.ts       # Internal Next.js health check
│
├── components/                   # ALL visual components
│   │
│   ├── ui/                       # shadcn/ui primitives (NEVER add business logic)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── badge.tsx
│   │   ├── dialog.tsx
│   │   ├── sheet.tsx
│   │   ├── skeleton.tsx
│   │   ├── tooltip.tsx
│   │   ├── progress.tsx
│   │   ├── tabs.tsx
│   │   ├── input.tsx
│   │   ├── slider.tsx
│   │   ├── select.tsx
│   │   └── alert.tsx
│   │
│   ├── shared/                   # Cross-feature reusable components
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx       # Nav sidebar with route awareness
│   │   │   ├── Topbar.tsx        # Top bar — business selector, alerts bell
│   │   │   ├── PageHeader.tsx    # Title + breadcrumb + actions slot
│   │   │   └── PageShell.tsx     # Page padding/max-width wrapper
│   │   ├── feedback/
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   ├── SkeletonCard.tsx
│   │   │   └── FullPageLoader.tsx
│   │   └── navigation/
│   │       ├── NavItem.tsx
│   │       └── Breadcrumb.tsx
│   │
│   ├── charts/                   # ALL chart components (zero business logic)
│   │   ├── d3/                   # Custom D3 — complex interactive charts
│   │   │   ├── GraphNetwork.tsx  # Force-directed company/director graph
│   │   │   ├── PledgeTimeline.tsx# Pledge % over time with threshold line
│   │   │   ├── AnomalyHeatmap.tsx# Quarter × signal heatmap
│   │   │   └── useD3.ts          # D3 SVG ref management hook
│   │   ├── recharts/             # Standard Recharts — data charts
│   │   │   ├── CashFlowAreaChart.tsx
│   │   │   ├── ForecastBandChart.tsx  # p10/median/p90 confidence band
│   │   │   ├── RevenueBarChart.tsx
│   │   │   ├── ClientConcentrationPie.tsx
│   │   │   ├── LoanWaterfallChart.tsx # SHAP waterfall
│   │   │   └── AnomalyScoreLineChart.tsx
│   │   └── shared/               # Chart primitives shared across both libs
│   │       ├── ChartTooltip.tsx
│   │       ├── ChartLegend.tsx
│   │       ├── ChartSkeleton.tsx
│   │       └── chartColors.ts    # Design-system color tokens for charts
│   │
│   ├── dashboard/                # Dashboard feature components
│   │   ├── SummaryCard.tsx
│   │   ├── DangerZoneBanner.tsx
│   │   ├── LoanReadinessWidget.tsx
│   │   ├── ClientRiskPreview.tsx
│   │   ├── DataQualityMeter.tsx
│   │   ├── AlertsFeed.tsx
│   │   └── QuickUploadCard.tsx
│   │
│   ├── cashflow/
│   │   ├── ForecastChart.tsx
│   │   ├── DangerZoneList.tsx
│   │   ├── ScenarioPlannerPanel.tsx
│   │   ├── ClientDelaySlider.tsx
│   │   ├── ForecastAccuracyBadge.tsx
│   │   └── ModelInfoTooltip.tsx
│   │
│   ├── loan/
│   │   ├── EligibilityScoreCard.tsx
│   │   ├── LenderComparisonTable.tsx
│   │   ├── ShapWaterfallChart.tsx
│   │   ├── WhatIfPanel.tsx
│   │   ├── FeatureSlider.tsx
│   │   ├── ActionItemCard.tsx
│   │   └── LoanCtaBanner.tsx
│   │
│   ├── watchlist/
│   │   ├── WatchlistTable.tsx
│   │   ├── CompanyAnomalyBadge.tsx
│   │   ├── AddCompanyDialog.tsx
│   │   ├── FilingFeed.tsx
│   │   ├── RealTimeIndicator.tsx
│   │   └── SeverityFilter.tsx
│   │
│   ├── company/
│   │   ├── CompanyHeader.tsx
│   │   ├── AnomalyTimeline.tsx
│   │   ├── PledgeTrendChart.tsx
│   │   ├── AuditorOpinionBadge.tsx
│   │   ├── DirectorGraph.tsx
│   │   └── FilingHistoryTable.tsx
│   │
│   └── upload/
│       ├── UploadDropzone.tsx
│       ├── UploadProgressCard.tsx
│       ├── DataSourceCard.tsx
│       └── ParseStatusBadge.tsx
│
├── services/                     # ALL external communication (no JSX)
│   ├── api/
│   │   ├── client.ts             # Axios instance — baseURL, interceptors, token attach
│   │   ├── endpoints.ts          # Enum/const of every API path
│   │   ├── forecast.ts           # getForecast(), getScenario()
│   │   ├── loan.ts               # getLoanEligibility(), postWhatIf()
│   │   ├── clients.ts            # getClientRisk()
│   │   ├── watchlist.ts          # getWatchlist(), addCompany(), removeCompany()
│   │   ├── graph.ts              # getGraphNeighbors(), getAnomalyTimeline()
│   │   ├── data.ts               # uploadFile(), getUploadStatus()
│   │   ├── dashboard.ts          # getDashboardSummary()
│   │   └── health.ts             # getHealth()
│   ├── websocket/
│   │   ├── socket.ts             # WebSocket class — connect/send/close
│   │   ├── events.ts             # Typed event union (FilingEvent, AlertEvent)
│   │   └── reconnect.ts          # Exponential backoff reconnect strategy
│   └── queries/
│       ├── queryClient.ts        # React Query client config (staleTime, retry)
│       ├── forecastQueries.ts    # useQuery/useMutation factories for forecast
│       ├── loanQueries.ts
│       ├── clientQueries.ts
│       ├── watchlistQueries.ts
│       └── dashboardQueries.ts
│
├── hooks/                        # Custom React hooks
│   ├── auth/
│   │   ├── useAuth.ts            # Auth state + login/logout actions
│   │   ├── useSession.ts         # Current session token management
│   │   └── usePermissions.ts     # Role-based access checks
│   ├── data/                     # Data-fetching hooks (thin wrappers over queries/)
│   │   ├── useForecast.ts
│   │   ├── useLoanEligibility.ts
│   │   ├── useClientRisk.ts
│   │   ├── useWatchlist.ts
│   │   ├── useDashboardSummary.ts
│   │   ├── useScenarioPlanner.ts
│   │   ├── useWhatIf.ts
│   │   ├── useCompanyDeepDive.ts
│   │   └── useUpload.ts
│   ├── ui/                       # Generic UI behaviour hooks
│   │   ├── useDebounce.ts        # Debounce value for sliders/search
│   │   ├── useLocalStorage.ts
│   │   ├── useMediaQuery.ts
│   │   ├── useSidebar.ts
│   │   └── useToast.ts
│   └── websocket/
│       ├── useFilingStream.ts    # WS connection for filing alerts
│       └── useAlertStream.ts     # WS connection for danger zone alerts
│
├── types/                        # TypeScript types only — no logic
│   ├── api/                      # Mirror of backend Pydantic response models
│   │   ├── forecast.ts           # ForecastResponse, DailyForecast, DangerZone
│   │   ├── loan.ts               # LoanEligibilityResponse, ShapBreakdown
│   │   ├── clients.ts            # ClientRiskResponse, PaymentAnomaly
│   │   ├── watchlist.ts          # WatchlistItem, FilingFeedItem
│   │   ├── graph.ts              # GraphNode, GraphLink, AnomalyTimeline
│   │   ├── dashboard.ts          # DashboardSummary, LoanReadiness
│   │   ├── upload.ts             # UploadTask, ParseStatus
│   │   ├── common.ts             # PaginatedResponse<T>, ApiError
│   │   └── index.ts              # Re-exports all API types
│   ├── domain/                   # Business domain models
│   │   ├── business.ts           # Business, DataSource
│   │   ├── transaction.ts        # Transaction, Direction
│   │   ├── invoice.ts            # Invoice, InvoiceStatus
│   │   └── index.ts
│   └── ui/                       # Component prop types
│       ├── chart.ts              # ChartDataPoint, BandData
│       ├── table.ts              # ColumnDef, SortState
│       ├── form.ts               # FormField, ValidationRule
│       └── index.ts
│
├── lib/                          # Pure utility functions (no React, no side-effects)
│   ├── utils/
│   │   ├── cn.ts                 # clsx + tailwind-merge helper
│   │   ├── format.ts             # formatNumber, formatPercent
│   │   ├── date.ts               # formatDate, daysBetween
│   │   ├── currency.ts           # formatINR, formatLakhs, formatCrores
│   │   └── validation.ts        # GSTIN validator, PAN validator
│   ├── constants/
│   │   ├── routes.ts             # ROUTES object — single source of truth
│   │   ├── api.ts                # API_BASE_URL, WEBSOCKET_URL
│   │   ├── chart.ts              # Chart breakpoints, animation durations
│   │   └── severity.ts          # SEVERITY_COLORS, SEVERITY_LABELS
│   ├── auth/
│   │   ├── middleware.ts         # Next.js middleware — route protection
│   │   └── session.ts           # JWT decode, expiry check
│   └── d3/
│       ├── scales.ts             # D3 scale factories (color, linear, time)
│       ├── axes.ts               # D3 axis helpers
│       └── simulation.ts        # Force simulation config for graph
│
├── store/                        # Zustand global state
│   ├── index.ts                  # Combine and export all slices
│   └── slices/
│       ├── uiSlice.ts            # Sidebar open/close, theme, modal state
│       ├── authSlice.ts          # User identity, token
│       ├── businessSlice.ts      # Active business_id selection
│       └── alertsSlice.ts        # Unread alert count, alert list
│
├── mock/                         # Dev-only mock data (MSW or direct import)
│   ├── fixtures/
│   │   ├── forecast.ts
│   │   ├── loan.ts
│   │   ├── clients.ts
│   │   ├── watchlist.ts
│   │   └── dashboard.ts
│   └── index.ts                  # Exports all mocks, gated by NODE_ENV
│
├── styles/
│   ├── chart-themes.css          # CSS custom props for chart color themes
│   ├── animations.css            # Framer Motion keyframe helpers
│   └── typography.css            # Custom heading/body scale
│
├── config/
│   ├── env.ts                    # Validated env var access (NEXT_PUBLIC_*)
│   └── features.ts               # Feature flags (ENABLE_LOAN, ENABLE_GRAPH)
│
├── middleware.ts                 # Next.js route guard (auth redirect)
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── package.json
├── components.json               # shadcn/ui registry config
└── .env.local.example
```

---

## Folder Responsibilities

### `app/` — Routing Only
Pages are **thin orchestrators**. They import feature components, pass route params, and wrap with Suspense/Error boundaries. **No business logic, no data fetching logic, no inline styles.**

### `components/ui/` — Design System Primitives
Pure shadcn/ui wrappers. Accepts props only. **NEVER import from services/, hooks/data/, or store/.** Reusable across any project.

### `components/shared/` — Cross-feature Patterns
Layout shells, loading states, error boundaries. Reusable across all feature modules. **No feature-specific logic.**

### `components/charts/` — Visualisation Only
Charts receive `data: ChartDataPoint[]` as props. They never fetch data, never import from services. D3 charts live in `d3/`, Recharts in `recharts/`. D3 charts use the `useD3` hook to manage SVG refs.

### `components/{feature}/` — Feature Components
Composed from `ui/`, `shared/`, and `charts/`. May use `hooks/data/` hooks. **Never import from another feature's component folder** — cross-feature data goes through the store or is passed as props from the page.

### `services/api/` — HTTP Layer
One file per API domain. All Axios calls live here. **No JSX, no React imports.** `client.ts` handles auth token injection via interceptors.

### `services/queries/` — React Query Factories
Define `queryKey` arrays and `queryFn` factories. Components call `useQuery` / `useMutation` from here via the `hooks/data/` layer.

### `services/websocket/` — WebSocket Architecture
`socket.ts` is a class-based singleton. `events.ts` defines typed event discriminated unions. `reconnect.ts` implements exponential backoff.

### `hooks/data/` — Data Hooks
Thin wrappers over React Query — one hook per API resource. Components call these, never `services/queries/` directly.

### `hooks/ui/` — Behavioural Hooks
Generic hooks with zero business knowledge: `useDebounce`, `useMediaQuery`, etc. Fully reusable.

### `types/api/` — Backend Contract Mirror
Every interface here mirrors a backend Pydantic model. When the backend schema changes, update here first.

### `lib/` — Pure Utilities
Zero React. Zero side-effects. All `lib/utils/` functions are pure functions. `lib/constants/` is read-only data.

### `store/` — Global Client State
Only for state that genuinely needs to be global: active business ID, sidebar state, unread alert count, auth token. **Server data (API responses) stays in React Query cache, not Zustand.**

### `mock/` — Development Only
Never imported in production code. Gated by `NODE_ENV !== 'production'` in `mock/index.ts`.

---

## Naming Conventions

| Pattern | Rule | Example |
|---|---|---|
| Pages | `page.tsx` (Next.js convention) | `app/(dashboard)/cashflow/page.tsx` |
| Components | `PascalCase.tsx` | `ForecastBandChart.tsx` |
| Hooks | `camelCase` starting with `use` | `useForecast.ts` |
| Services | `camelCase` noun | `forecast.ts` |
| Types | `PascalCase` interfaces | `ForecastResponse` |
| Constants | `SCREAMING_SNAKE_CASE` | `ROUTES.CASHFLOW` |
| Utils | `camelCase` verb | `formatINR()` |
| CSS vars | `--color-danger-zone` | kebab-case |
| Query keys | `['forecast', businessId]` | array tuple |

---

## Architecture Rules

### Folders that MUST NEVER contain business logic
- `components/ui/` — primitives only
- `components/charts/` — data-in, SVG-out
- `components/shared/` — layout/feedback only
- `lib/` — pure functions only
- `types/` — types only, zero runtime code
- `mock/` — static fixture data only

### Folders that MUST remain reusable (no NeevFinance-specific imports)
- `components/ui/`
- `components/charts/shared/`
- `hooks/ui/`
- `lib/utils/`
- `lib/constants/` (except `api.ts`)

### Folders that are feature-specific (coupling is acceptable)
- `components/dashboard/`
- `components/cashflow/`
- `components/loan/`
- `components/watchlist/`
- `components/company/`
- `hooks/data/`
- `services/api/` (per domain)

---

## Scalability Rules

1. **Pages never contain JSX below the fold.** Extract any repeated block into a named component immediately.
2. **One query key per resource.** Define all query keys in `services/queries/` — never inline `useQuery(['forecast'])` in a component.
3. **D3 only touches the DOM inside `useEffect`.** Never render D3 output as JSX. The `useD3` hook enforces this pattern.
4. **WebSocket events are typed.** Every message dispatched from `socket.ts` is a discriminated union defined in `events.ts`. No `any`.
5. **Feature flags gate new modules.** Add entries to `config/features.ts` before building a new feature. Conditional rendering uses the flag — never delete-and-rewrite.
6. **The `mock/` folder is the only place for fake data.** If you're hardcoding data in a component, move it to `mock/fixtures/`.
7. **Types before implementation.** Define the API type in `types/api/` before writing the service function.

---

## API ↔ Frontend Connection Map

| Backend Endpoint | Service File | Query Hook | Component |
|---|---|---|---|
| `GET /api/dashboard/summary` | `services/api/dashboard.ts` | `dashboardQueries.ts` | `components/dashboard/*` |
| `GET /api/forecast/{id}` | `services/api/forecast.ts` | `forecastQueries.ts` | `components/cashflow/ForecastChart.tsx` |
| `GET /api/forecast/scenario` | `services/api/forecast.ts` | `forecastQueries.ts` | `components/cashflow/ScenarioPlannerPanel.tsx` |
| `POST /api/loan/eligibility` | `services/api/loan.ts` | `loanQueries.ts` | `components/loan/EligibilityScoreCard.tsx` |
| `POST /api/loan/whatif` | `services/api/loan.ts` | `loanQueries.ts` | `components/loan/WhatIfPanel.tsx` |
| `GET /api/clients/{id}/risk` | `services/api/clients.ts` | `clientQueries.ts` | `components/dashboard/ClientRiskPreview.tsx` |
| `GET /api/graph/{code}/neighbors` | `services/api/graph.ts` | `watchlistQueries.ts` | `components/company/DirectorGraph.tsx` |
| `WS /ws/filings/{id}` | `services/websocket/socket.ts` | `hooks/websocket/useFilingStream.ts` | `components/watchlist/FilingFeed.tsx` |
| `POST /api/data/upload` | `services/api/data.ts` | — (mutation) | `components/upload/UploadDropzone.tsx` |
