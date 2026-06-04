import os
import requests
from backend.safety import clean_sql_output


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

The user may ask to:
- view data
- create a table
- edit a table structure
- delete a table
- insert data
- update data
- delete rows

Allowed SQL actions:
SELECT, CREATE TABLE, ALTER TABLE, DROP TABLE, INSERT, UPDATE, DELETE.

Rules:
- Return only one SQL statement.
- Do not include explanations.
- Do not use Markdown.
- Do not generate multiple SQL statements.
- Use SQL compatible with this database dialect: {dialect}.
- Use existing table and column names when modifying existing data.
- If creating a new table, choose sensible column names and types.
- If the request is ambiguous, generate the safest reasonable SQL statement.
- Never generate ATTACH, DETACH, PRAGMA, GRANT, REVOKE, EXEC, EXECUTE, CALL, or MERGE.

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
- Use only valid syntax for this database dialect: {dialect}.
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

    except requests.exceptions.ConnectionError:
        return None, (
            "Could not connect to Ollama. Make sure Ollama is running locally "
            "and the selected model is available."
        )

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