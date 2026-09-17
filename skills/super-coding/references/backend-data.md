# BACKEND, APIs & DATA: contracts that are hard to misuse

Anything touching input, auth, sessions, secrets, payments, uploads, webhooks or personal data also follows **`security-and-hardening`**, every time.

## 1. Interfaces and APIs

- **Contract first:** write the types or schemas (TypeScript types, Zod or Pydantic, OpenAPI) before the implementation. Keep **input types** (what callers send) separate from **output types** (including server-generated fields).
- **One error shape everywhere:** `{ "error": { "code": "VALIDATION_ERROR", "message": "…", "details": … } }`. Status codes: 400 bad input · 401 not signed in · 403 not allowed · 404 not found · 409 conflict · 422 invalid content · 500 server error (never exposes internals).
- **Validate at boundaries only:** request handlers, form handlers, environment variables at startup, and **third-party API responses** (always untrusted). Internal code trusts validated types.
- **Change by adding:** new fields are optional, and existing fields never change type or disappear. **Hyrum's law:** every observable behavior (error text, ordering, timing) becomes something someone depends on, so expose deliberately.
- **Predictable REST:** plural nouns, no verbs (`GET/POST /api/bookings`, `PATCH /api/bookings/:id`), camelCase fields, `is/has/can` for booleans, **pagination on every list endpoint**, filters as query parameters, PATCH for partial updates.
- Use discriminated unions for variants (`{type:'paid', paidAt}` / `{type:'refunded', reason}`) and branded ID types where mixing IDs would be costly.

## 2. Money and side effects: idempotency

For endpoints that charge, send, create orders or trigger external effects:
- **Derive the key from the intent, not the attempt:** the client sends an `Idempotency-Key` generated once and reused on retry, or the key is derived from an immutable ID (`charge:v1:<orderId>`). Never use a random UUID per attempt, and never use a timestamp.
- **Claim atomically:** insert the key under a **unique constraint** before acting; a duplicate-key error means replay the stored result or reject. Check-then-insert is a race.
- **Same key with a different payload → 422.** **Duplicate while the first is still running → 409.**
- **Three outcomes: success, failure, unknown.** Record the intent before calling the external service, so a crash leaves evidence to reconcile.
- **Keep keys longer than the longest retry path** (queues, dead letters, provider dispute windows).

## 3. Data integrity and concurrency

- Parameterized queries or the ORM only; never build SQL from strings.
- **Find-or-create needs a unique index** plus handling of the duplicate-key error.
- **Status transitions are atomic:** `UPDATE … SET status='paid' WHERE id=? AND status='pending'`, then check the affected row count.
- Multi-step writes that must succeed together go in a **transaction**.
- Add indexes for real query patterns. Avoid N+1 queries by eager-loading relations used in loops. Paginate large reads.
- **Time:** store UTC and convert only for display. Make day and period boundaries explicit.

## 4. Schema migrations: expand → migrate → contract

The database is the one thing a code rollback can't undo.
1. **Expand:** add the new column or table as nullable or additive, and deploy. Old code still works.
2. **Dual-write:** the app writes both the old and new shape, and you deploy.
3. **Backfill** existing rows **in batches**, throttled and off peak, so tables don't lock.
4. **Switch reads** to the new shape, still writing both; deploy and let it run.
5. **Contract:** stop writing the old shape, then drop it in a **separate, later deploy**.

Rules: never rename or drop in place · never ship a schema change and the code that needs it in one deploy · **every migration has a tested down path** · build large indexes without blocking writes (for example `CREATE INDEX CONCURRENTLY`) · back up production data before destructive steps, with the owner's yes.

## 5. Background jobs, queues, webhooks

- Delivery is **at least once**, so every handler must be idempotent (§2).
- Verify webhook signatures and reject stale timestamps. Return 2xx quickly and do slow work in a job.
- Retry with exponential backoff and a cap. After the final failure, send to a dead-letter queue and log it.
- Name each entry point (scheduler, webhook, manual run) in the logs, alongside the correlation ID.

## 6. Configuration and secrets

Environment variables, validated at startup (fail fast with a clear message) · every variable documented in `.env.example` · secrets never logged, returned in responses or committed · separate keys for development, test and production · least-privilege API keys.

## 7. AI and LLM features

Invoke **`claude-api`** before writing that code (current models, SDK usage, prompt caching, streaming, tool use).
- **Model output is untrusted input:** validate structure against a schema before it reaches the database, email, redirects or `fetch` (allowlist URLs to prevent SSRF). Never `eval` generated code outside a sandbox.
- User content and stored documents can carry **prompt injection**: keep instructions and data separated, and don't give the model tools that can do more than the user is allowed to do.
- Set timeouts, retries and cost limits, and handle refusals and empty output gracefully.

## 8. Deprecating or replacing old code and systems

- Build and **prove the replacement** before deprecating the old one. Code is a liability; removing it is an achievement.
- **Advisory** deprecation (warnings, docs) by default; **compulsory** (a hard date) only for security or unsustainable cost, and only with migration tooling.
- Migrate consumers **one at a time**, using the strangler pattern (route traffic gradually), adapters (old interface over the new implementation) or feature flags.
- Remove the old system only after **verified zero usage** (logs or metrics), together with its tests, docs and config.
- Code nobody owns but everyone depends on gets an owner or a removal plan. It can't stay in limbo.
