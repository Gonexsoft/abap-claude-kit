# Analysis Patterns

Load this file when interpreting `abap_review_scan.py` output, or when a
human asks why a specific finding was raised (or not raised). Every rule
here is a lexical heuristic over ABAP source text, not a parser and not a
substitute for ABAP Test Cockpit (`atc-check` in `sap-adt-commands`). State
findings as "the scanner flagged this because ..." not as proven defects.

## How the scanner reads ABAP

- Comments are stripped per physical line: a line whose first non-blank
  character is `*` is a full-line comment; a `"` outside a string literal
  starts a trailing comment. This is safe because ABAP has exactly one
  string delimiter (`'`) and a string literal cannot span multiple physical
  lines — so per-line comment/string handling is exact, not approximate.
- Statements are grouped by scanning for a bare `.` (outside a string) as
  the terminator, joining continuation lines until one is found. If two
  statements share one physical line (`a = 1. b = 2.`), the scanner still
  finds the first terminator correctly; only extreme same-line chaining of
  three or more statements risks folding a later one into the wrong group,
  which is rare in real code.
- Everything else (nesting depth, nested structures, nested SELECT
  subqueries, nested internal-table types) is intentionally out of scope.

## Performance findings (`category: performance`, `kind: issue`)

| id | Severity | Trigger | Notes |
|----|----------|---------|-------|
| `select-in-loop` | high | Any `SELECT` statement between an open `LOOP AT` and its `ENDLOOP` | Classic N+1: one DB round trip per loop iteration. Fix by moving the SELECT outside the loop (`FOR ALL ENTRIES`, a JOIN, or a bulk SELECT into a hashed table used for lookups inside the loop). |
| `select-endselect-loop` | medium | A `SELECT ... .` statement (without `INTO TABLE`/`INTO CORRESPONDING FIELDS OF TABLE`) later matched to an `ENDSELECT.` | Row-by-row DB cursor fetch. Fix by using `SELECT ... INTO TABLE` (or `APPENDING TABLE`) and looping over the resulting internal table. |
| `select-star` | low | `SELECT *`, `SELECT SINGLE *`, or `SELECT DISTINCT *` | Reads every column even when only a few are used. Lower severity than the others — sometimes intentional (dynamic tools, generic display). |
| `select-without-where` | medium | A `SELECT ... FROM <table>` statement with no `WHERE` and no `UP TO n ROWS` | Full table scan risk. Can be a legitimate `SELECT COUNT(*)` or a genuinely small table — confirm before treating as a defect. |
| `nested-loop` | medium | A `LOOP AT` opened while another `LOOP AT` is already open | O(n²) risk. Not a defect by itself if the inner table is `HASHED`/`SORTED` and the read uses a key or `BINARY SEARCH` — the scanner cannot see the table's declared type, so always ask before assuming this is wrong. |

### Known false positives / false negatives

- `select-without-where` will flag a deliberate full scan (e.g. nightly
  batch job) with no way to know intent from source text alone — treat as
  a prompt to ask, not an instruction to add a WHERE clause.
- `nested-loop` cannot see whether the inner table is buffered — always
  check the `DATA`/`TYPES` declaration before proposing a fix.
- A `SELECT` that spans many lines and is chained with commas
  (`SELECT a, b, c`) is still detected correctly because statement grouping
  waits for the terminating period, not the first line.
- `select-in-loop` fires on every SELECT inside the loop body, including
  ones a human may already know are cheap (buffered customizing tables) —
  still worth a mention, but do not treat every hit as equally urgent.

## Embedded API / hardcoded value findings (`category: embedded_api`, `kind: issue`)

| id | Severity | Trigger | Notes |
|----|----------|---------|-------|
| `hardcoded-url` | high | A string literal starting with `http://` or `https://` | Move the endpoint to a logical destination (SM59 / `cl_http_destination_provider`) so it can change per system without a code change. |
| `hardcoded-host-ip` | medium | A string literal that is exactly an IPv4-shaped value (`\d{1,3}(\.\d{1,3}){3}`) | Same fix as above. Does not validate octet ranges (0–255), so a string like `999.999.999.999` would still match — rare in practice. |
| `hardcoded-credential` | high | A line assigning a string literal to an identifier whose name contains `PASSWORD`, `PWD`, `SECRET`, `TOKEN`, `API_KEY`/`APIKEY`, `BEARER`, or `CREDENTIAL` (case-insensitive), via `=` or a `TYPE ... VALUE` constant declaration | Name-based heuristic — it does not know the value is actually secret, only that the variable name says so. |

### Explicitly out of scope for this scanner

These were considered and deliberately excluded from `embedded_api`
detection in this version. Do not claim the scanner covers them:

- Hardcoded RFC destinations (`CALL FUNCTION ... DESTINATION 'LITERAL'`).
- Literal endpoints passed to `cl_http_client=>create_by_url` or
  `cl_web_http_client=>create_by_url`.

If a user specifically asks about either of the above, say so explicitly
and offer to grep for the pattern manually (`CALL FUNCTION` with
`DESTINATION '`, or `create_by_url(`) rather than presenting the scanner's
"no findings" as clearance.

### Known false positives / false negatives

- `hardcoded-credential` will flag `lv_password_prompt_text = 'Enter your password'` because the
  identifier name matches even though the literal is a UI label, not a
  secret. Read the snippet before relaying the finding as "a password is
  hardcoded here."
- A credential-shaped value assembled from two concatenated literal
  fragments on one line, or read from a constant defined elsewhere in the
  program, will not be caught — the rule only looks at a single-literal,
  same-line assignment.
- A URL built via `CONCATENATE` from a literal scheme and a separate host
  variable will not be caught as `hardcoded-url` if `http://` and the host
  are not in the same string literal.

## CRUD findings (`category: crud`, `kind: alert`)

These are not "issues" to fix — they are the alert/preview the human asked
for: anywhere the reviewed code performs a database write, shown before
that code is touched. Always surface all of them regardless of severity
(all are `severity: info` by design).

| id | Trigger | Confidence |
|----|---------|------------|
| `db-insert` | `INSERT INTO <table>` or `INSERT <table> FROM ...` (not `INSERT <workarea> INTO TABLE <itab>`) | High — this literal syntax shape only exists for database inserts. |
| `db-update` | Any statement starting with `UPDATE <table>` | High — `UPDATE` is DB-only in ABAP; there is no internal-table `UPDATE` statement. |
| `db-delete` | `DELETE FROM <table>` | High — `DELETE FROM` is DB-only syntax. |
| `db-delete-ambiguous` | `DELETE <name> FROM <workarea-or-table>` (without `FROM` immediately after `DELETE`, and without a leading `TABLE`) | Medium — this shape is used for both `DELETE dbtab FROM wa.` (DB) and, less commonly, some internal-table forms. The scanner has no symbol table, so it cannot tell which. Verify the target's declaration before assuming either way. |
| `db-modify` | `MODIFY <name> FROM ...` (without a leading `TABLE`) | Medium — `MODIFY dbtab FROM wa.` (DB) and `MODIFY itab FROM wa INDEX n.` (internal table) share this exact shape. Always verify. |
| `native-sql-block` | `EXEC SQL` | Informational only — the scanner does not parse inside `EXEC SQL ... ENDEXEC`. Flag it and tell the human to inspect it manually; native SQL bypasses Open SQL buffering and authorization checks regardless of what statements are inside. |

### Why MODIFY/DELETE-ambiguous exist as separate ids

`UPDATE` and `DELETE FROM`/`INSERT INTO` are unambiguous in ABAP grammar —
those keyword shapes simply do not exist for internal tables. `MODIFY` and
the workarea form of `DELETE`, however, are genuinely shared syntax between
database tables and internal tables. Reporting them as a distinct,
lower-confidence id (rather than silently guessing, or silently dropping
them) keeps the alert honest: it says "there is a write-shaped statement
here, and the scanner cannot tell you which kind" instead of pretending to
know.

## Severity is a triage aid, not a verdict

Use severity to order what gets discussed first (`high` → `medium` →
`low`), not to decide unilaterally what to fix. A `low` `select-star`
finding on a hot path may matter more to the user than a `high`
`hardcoded-url` in a one-time migration report. Ask.
