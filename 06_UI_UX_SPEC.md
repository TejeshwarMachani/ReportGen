# UI/UX Specification
## AI-Based Business Report Generation and Analytics System

---

## 1. Design Principles

- **Trustworthy over flashy.** This tool touches real business numbers — favor clarity, whitespace, and restraint over heavy gradients/animation. Think "a report a CFO would trust," not a consumer AI toy.
- **Data-dense but readable.** Dashboards should surface a lot of information without feeling cluttered — use card grouping, clear hierarchy, generous line-height on numbers.
- **Progress over spinners.** Report generation and forecasting take real time — always show meaningful status ("Analyzing 12,400 rows...", "Drafting summary...") instead of a bare spinner.
- **Transparency by default.** Anywhere the AI produces an answer (chat, reports), show the underlying computed data/query nearby — never a black-box number.

## 2. Design Tokens

**Color palette**
| Token | Hex | Use |
|---|---|---|
| `primary` | `#4F46E5` (indigo-600) | Primary actions, active states |
| `primary-foreground` | `#FFFFFF` | Text on primary |
| `neutral-900` → `neutral-50` | slate scale | Text, backgrounds, borders |
| `success` | `#059669` (emerald-600) | Positive metric changes |
| `danger` | `#DC2626` (red-600) | Negative metric changes, errors |
| `warning` | `#D97706` (amber-600) | Data quality warnings |
| `accent-chart` palette | indigo/emerald/amber/sky/violet | Chart series colors, consistent across the app |

**Typography**
- UI + body: **Inter**
- Numeric/report headline figures: **Inter, tabular-nums** (so numbers align in tables)
- Query/code snippets (chat's `query_executed`): **JetBrains Mono**

**Spacing/radius**
- 4px base spacing scale (4/8/12/16/24/32/48)
- Card radius: 12px · Button radius: 8px

## 3. Screen Inventory

| Screen | Purpose | Key components |
|---|---|---|
| **Login / Register** | Auth entry | Form, org-name field on register |
| **Onboarding** | First dataset upload, guided | Upload dropzone, progress stepper |
| **Dashboard Home** | Overview on login | Summary cards (datasets, reports, recent activity), quick actions ("New Report", "Upload Data", "Ask a question") |
| **Data Sources** | List/manage datasets | Data table (name, rows, status, date), upload button |
| **Dataset Detail** | Inspect one dataset | Schema table with types, data quality summary, preview table, "Generate Report" / "Chat" / "Forecast" actions |
| **Report Generator (config)** | Configure a new report | Dataset selector, report-type selector, optional custom prompt field |
| **Report Viewer** | View a generated report | Narrative sections, embedded charts, export buttons (PDF/DOCX), "regenerate" |
| **Reports Library** | Browse past reports | Searchable/filterable data table |
| **Chat With Data** | Conversational analytics | Dataset selector sidebar, message thread, inline charts, visible query per answer, input box |
| **Forecasting** | Configure + view forecast | Column pickers, horizon selector, forecast chart w/ confidence band, summary text |
| **Settings — Team** | Manage members/roles | Member list, invite form, role dropdown |
| **Settings — Org/Billing** | Org info, plan | Org name, plan display, (post-MVP) upgrade CTA |

## 4. Key User Flows

**Onboarding → first report**
`Signup form → Org auto-created → Upload dropzone → Parsing progress → Dataset preview/confirm → "Generate my first report" CTA → Report viewer`

**Chat flow**
`Select dataset → type question → loading state ("Running your query...") → answer + chart + query shown → follow-up question in same thread`

**Forecast flow**
`Dataset detail → "Forecast a metric" → pick target/date column + horizon → loading state → forecast chart + summary`

## 5. Component Inventory (build these once, reuse everywhere)

- `<DataTable>` — sortable, paginated, used for datasets list, reports list, team members.
- `<UploadDropzone>` — drag/drop + click, shows upload progress.
- `<StatCard>` — headline metric + delta indicator (▲/▼ with success/danger color).
- `<ChartWrapper>` — wraps Recharts, consistent tooltip/legend/color styling across line/bar/area charts.
- `<ChatBubble>` — user vs. assistant styling, optional embedded `<ChartWrapper>` and collapsible `query_executed` snippet.
- `<StatusBadge>` — for dataset/report/job status (`processing`, `ready`, `failed`, etc.), color-coded.
- `<ProgressState>` — for long-running jobs, shows a message + indeterminate or step progress.
- `<RoleBadge>` — owner/admin/member/viewer pill.
- `<EmptyState>` — consistent "no reports yet" / "no datasets yet" pattern with a CTA.

## 6. Responsive Notes

MVP targets desktop-first (this is a work tool used at a desk) but must be usable on tablet width (≥768px) without horizontal scroll breaking. Mobile phone support is not a launch requirement — degrade gracefully, don't crash.
