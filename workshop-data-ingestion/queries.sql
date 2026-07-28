-- Question 2: count dlt-created normalized tables.
SELECT COUNT(*) AS table_count
FROM information_schema.tables
WHERE table_schema = 'agent_traces';

-- Inspect the normalized schema before selecting the token-usage column.
SELECT table_name, column_name
FROM information_schema.columns
WHERE table_schema = 'agent_traces'
ORDER BY table_name, ordinal_position;

-- Question 3: list each agent trace and its total LLM input token usage. Use
-- the trace ID from the Question 1 run (identified by its timestamp in Logfire).
SELECT
    trace_id,
    MIN(start_timestamp) AS started_at,
    COUNT(*) AS span_count,
    SUM(COALESCE(attributes__gen_ai_usage_input_tokens, 0)) AS input_tokens
FROM agent_traces.spans
GROUP BY trace_id
ORDER BY started_at;