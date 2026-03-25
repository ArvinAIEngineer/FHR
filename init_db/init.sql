-- ─────────────────────────────────────────────────────────────────────────────
-- FAHR conversation logs table
-- Created automatically on first Postgres boot via docker-entrypoint-initdb.d
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS conversation_logs (
    id                  SERIAL PRIMARY KEY,
    request_id          TEXT,
    message_id          TEXT UNIQUE,
    session_id          TEXT,
    person_id           TEXT,
    role                TEXT,
    full_name           TEXT,
    language            TEXT,
    msg_type            TEXT,
    user_message        TEXT,
    ai_response         TEXT,
    ai_reason           TEXT,
    conversation_state  TEXT DEFAULT 'complete',
    agent_used          TEXT,
    citations           JSONB,
    status              TEXT DEFAULT 'success',
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conv_logs_person_id  ON conversation_logs (person_id);
CREATE INDEX IF NOT EXISTS idx_conv_logs_session_id ON conversation_logs (session_id);
CREATE INDEX IF NOT EXISTS idx_conv_logs_message_id ON conversation_logs (message_id);
CREATE INDEX IF NOT EXISTS idx_conv_logs_created_at ON conversation_logs (created_at DESC);
