import os
import requests
from dotenv import load_dotenv
from safety import clean_sql_output


load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3.2:1b")


def call_ollama(prompt):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    headers = {
        "ngrok-skip-browser-warning": "true",
        "Content-Type": "application/json"
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        headers=headers,
        timeout=120
    )

    response.raise_for_status()

    result = response.json()
    raw_output = result.get("response", "")

    return clean_sql_output(raw_output)


def build_prompt(schema, question, dialect):
    return f"""
You are an expert database assistant.

Convert the user's natural language request into one valid {dialect} SQL statement.

Allowed SQL actions:
SELECT, CREATE TABLE, ALTER TABLE, DROP TABLE, INSERT, UPDATE, DELETE.

Critical rules:
- Return only one SQL statement.
- Do not include explanations.
- Do not use Markdown.
- Do not generate multiple SQL statements.
- Use SQL compatible with this database dialect: {dialect}.
- Use only the tables and columns listed in the current database schema.
- Never invent table names.
- Never invent column names.
- If a table or column does not exist, do not use it.
- For spending, revenue, or sales questions, use orders.total_amount if it exists.
- For customer spending questions, join customers to orders using customer_id.
- For product revenue questions, join products to orders using product_id.
- If creating a new table, choose sensible column names and types.
- Never generate ATTACH, DETACH, PRAGMA, GRANT, REVOKE, EXEC, EXECUTE, CALL, or MERGE.

Example:
User request: Which customer spent the most money?

Correct SQL:
SELECT c.customer_id, c.name, SUM(o.total_amount) AS total_spent
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_spent DESC
LIMIT 1;

Current database schema:
{schema}

User request:
{question}

SQL statement:
"""


def build_correction_prompt(schema, question, failed_sql, error_message, dialect):
    return f"""
You are an expert SQL debugger.

The previous SQL statement failed. Fix it.

Rules:
- Return only one valid {dialect} SQL statement.
- Do not include explanations.
- Do not use Markdown.
- Do not generate multiple SQL statements.
- Use only tables and columns from the current database schema.
- Never invent table names.
- Never invent column names.
- If the failed SQL used a non-existing table, remove it and use only valid schema tables.
- For spending, revenue, or sales questions, use orders.total_amount if it exists.
- For customer spending questions, join customers to orders using customer_id.
- For product revenue questions, join products to orders using product_id.
- Never generate ATTACH, DETACH, PRAGMA, GRANT, REVOKE, EXEC, EXECUTE, CALL, or MERGE.

Current database schema:
{schema}

Original user request:
{question}

Failed SQL:
{failed_sql}

Database error:
{error_message}

Corrected SQL statement:
"""


def generate_sql(schema, question, dialect):
    prompt = build_prompt(schema, question, dialect)

    try:
        sql = call_ollama(prompt)
        return sql, None

    except Exception as e:
        return None, str(e)


def correct_sql(schema, question, failed_sql, error_message, dialect):
    prompt = build_correction_prompt(
        schema=schema,
        question=question,
        failed_sql=failed_sql,
        error_message=error_message,
        dialect=dialect
    )

    try:
        corrected_sql = call_ollama(prompt)
        return corrected_sql, None

    except Exception as e:
        return None, str(e)