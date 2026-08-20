# API Specification
## AI-Based Business Report Generation and Analytics System

Base URL: `/api/v1`
Auth: `Authorization: Bearer <access_token>` (JWT) on all routes except `/auth/*`.
All responses: `application/json` unless exporting a file.
Errors: `{ "error": { "code": "string", "message": "string" } }` with appropriate HTTP status.
Pagination: `?page=1&page_size=20` → response includes `{ items: [...], total, page, page_size }`.

---

## Auth

**POST `/auth/register`**
Body: `{ email, password, full_name, org_name }`
→ Creates org + first user (role `owner`). Returns `{ user, access_token, refresh_token }`.

**POST `/auth/login`**
Body: `{ email, password }` → `{ user, access_token, refresh_token }`

**POST `/auth/refresh`**
Body: `{ refresh_token }` → `{ access_token }`

**POST `/auth/logout`**
→ Invalidates refresh token.

---

## Organizations

**GET `/orgs/me`** → current org details + plan.

**GET `/orgs/me/members`** → list of org users.

**POST `/orgs/me/invite`**
Body: `{ email, role }` → sends invite (post-MVP: email; MVP: return an invite link/token).

**PATCH `/orgs/me/members/{user_id}`**
Body: `{ role }` → update a member's role. Owner/admin only.

---

## Datasets

**POST `/datasets/upload`** (multipart/form-data: `file`, `name`)
→ Uploads CSV/XLSX, kicks off async parsing job. Returns `{ dataset_id, status: "processing" }`.

**GET `/datasets`** → paginated list for current org.

**GET `/datasets/{id}`**
→ `{ id, name, source_type, schema_json, row_count, status, created_at }`

**GET `/datasets/{id}/preview`**
→ First ~50 rows for UI preview table.

**PATCH `/datasets/{id}`**
Body: `{ name?, column_type_overrides? }`

**DELETE `/datasets/{id}`**

---

## Reports

**POST `/reports/generate`**
Body: `{ dataset_id, report_type: "auto_summary" | "custom", custom_prompt?: string }`
→ Enqueues generation job. Returns `{ report_id, status: "queued" }`.

**GET `/reports/{id}`**
→ `{ id, title, status, narrative_text, charts_json, computed_stats_json, created_at, generated_at }`
While `status: "generating"`, frontend polls this endpoint (or subscribes via SSE — see `/reports/{id}/stream`).

**GET `/reports/{id}/stream`** (Server-Sent Events, optional nicety)
→ Streams status updates / narrative tokens as they're generated.

**GET `/reports`** → paginated list for current org, filterable by `dataset_id`.

**GET `/reports/{id}/export?format=pdf|docx`**
→ Returns the file (binary) or a signed download URL.

**DELETE `/reports/{id}`**

---

## Chat

**POST `/chat/sessions`**
Body: `{ dataset_id }` → `{ session_id }`

**GET `/chat/sessions`** → list sessions for current org (filterable by `dataset_id`).

**GET `/chat/sessions/{id}/messages`** → ordered message history.

**POST `/chat/sessions/{id}/messages`**
Body: `{ content }`
→ Runs the NL→query→execute→answer pipeline (see Architecture §8). Returns:
```json
{
  "message": {
    "role": "assistant",
    "content": "Revenue grew 12% quarter over quarter, led by...",
    "chart_data_json": { "type": "line", "data": [...] },
    "query_executed": "GROUP BY month, SUM(revenue) WHERE region='APAC'"
  }
}
```

---

## Forecasts

**POST `/forecast/run`**
Body: `{ dataset_id, target_column, date_column, horizon_periods, model_type? }`
→ Enqueues job. Returns `{ forecast_id, status: "queued" }`.

**GET `/forecast/{id}`**
→ `{ id, status, result_json: { points: [{date, value, lower_bound, upper_bound}], summary_text }, ... }`

---

## Dashboard

**GET `/dashboard/summary`**
→ `{ dataset_count, report_count, recent_reports: [...], recent_chats: [...] }` — powers the home screen.

---

## Scheduled Reports (post-MVP, spec now for forward compatibility)

**POST `/scheduled-reports`**
Body: `{ report_config_json, frequency, recipients }`

**GET `/scheduled-reports`** / **PATCH `/scheduled-reports/{id}`** / **DELETE `/scheduled-reports/{id}`**

---

## Error Codes (reference)

| Code | Meaning |
|---|---|
| `AUTH_INVALID_CREDENTIALS` | Login failed |
| `AUTH_TOKEN_EXPIRED` | Refresh required |
| `DATASET_INVALID_FORMAT` | Upload rejected (wrong type/too large) |
| `DATASET_NOT_READY` | Report/chat/forecast requested before parsing finished |
| `QUERY_NOT_ALLOWED` | Chat query fell outside the safe whitelist — ask a different question |
| `PERMISSION_DENIED` | Role doesn't allow this action |
| `PLAN_LIMIT_REACHED` | Free-tier usage cap hit |
