# FAHR HR Assistant — Local Stack

Three Docker containers, one command.

```
fahr/
├── docker-compose.yml
├── .env
├── README.md
├── init_db/
│   └── init.sql                  ← auto-runs on first Postgres boot
├── mcp/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── fahr_mcp_server.py        ← 16 MCP tools (mock data)
└── n8n_workflows/
    └── fahr_workflow.json        ← import this into n8n
```

---

## Start

```bash
docker compose up -d
```

Check all three containers are healthy:

```bash
docker compose ps
```

---

## Services

| Container      | URL                          | Purpose                              |
|----------------|------------------------------|--------------------------------------|
| fahr_postgres  | internal only                | n8n data + conversation_logs table   |
| fahr_mcp       | http://localhost:8000/mcp    | 16 FAHR MCP tools                    |
| fahr_n8n       | http://localhost:5678        | n8n workflow UI                      |

---

## After Starting

### 1. Open n8n
Go to http://localhost:5678 and create your account on first launch.

### 2. Add Credentials

**Postgres** (for dedup check + conversation logging):
- Go to Credentials → New → PostgreSQL
- Host: `postgres`
- Port: `5432`
- Database: `fahr`
- User: `fahr`
- Password: value from `.env`
- Name it: `FAHR Postgres`

**Google Gemini**:
- Go to Credentials → New → Google Gemini (PaLM) API
- Paste your Gemini API key
- Name it: `Google Gemini FAHR`

### 3. Import the Workflow
- Settings → Import workflow
- Select `n8n_workflows/fahr_workflow.json`
- The credential IDs in the JSON are placeholders — n8n will prompt you to re-link them to your actual credentials

### 4. Activate and Test
- Toggle the workflow to Active
- Chat UI is live at: http://localhost:5678/webhook/fahr-chat-webhook/chat

---

## Test Employees (mock data)

| person_id | Name                      | Role     | Grade |
|-----------|---------------------------|----------|-------|
| 204319    | Mohammed Ali Al Mansoori  | employee | G8    |
| 204320    | Sara Khalid Al Zaabi      | manager  | G10   |
| 204321    | Omar Yusuf Al Rashidi     | employee | G6    |

The workflow defaults to `person_id=204319`. To test another employee,
pass `person_id` in the chat request body.

---

## MCP Tools (16 total)

| Tool                        | Purpose                                 |
|-----------------------------|-----------------------------------------|
| check_duplicate_message     | Dedup guard — always first              |
| get_employee_profile        | Name, role, grade, department           |
| get_conversation_history    | Last N turns for context                |
| get_leave_balance           | All leave types with balance/used/total |
| get_payslip                 | Salary breakdown, net pay               |
| get_attendance              | Check-in/out, late/absent records       |
| get_performance             | Appraisal rating, objectives, increment |
| get_crm_tickets             | Support ticket status                   |
| get_notifications           | Alerts, payslip notices, policy updates |
| get_job_card                | Job description, grade, responsibilities|
| get_pending_leave_requests  | Submitted leave awaiting approval       |
| submit_leave_request        | Apply for leave (write operation)       |
| get_team_members            | Manager-only — team attendance today    |
| search_hr_policy            | HR policy RAG search (mock ChromaDB)    |
| search_legal_policy         | UAE labor law RAG search (mock)         |
| log_conversation            | Log to DB — always last                 |

---

## Replacing Mock Data

Each tool has one block to replace with a real Bayanati API call.
Look for the comment:

```python
# Replace this block with: results = bayanati_client.post(...)
```

The tool signature and return shape never change — n8n and Gemini see
exactly the same interface before and after the swap.

---

## Useful Commands

```bash
# View logs
docker compose logs -f

# Restart just the MCP server after code changes
docker compose restart mcp

# Stop everything
docker compose down

# Full reset (deletes all data)
docker compose down -v
```