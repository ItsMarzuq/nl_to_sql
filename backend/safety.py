import re


ALLOWED_START_KEYWORDS = [
    "select",
    "with",
    "create",
    "alter",
    "drop",
    "insert",
    "update",
    "delete"
]


DANGEROUS_KEYWORDS = [
    "drop",
    "delete",
    "update",
    "alter",
    "truncate"
]


BLOCKED_KEYWORDS = [
    "attach",
    "detach",
    "pragma",
    "grant",
    "revoke",
    "execute",
    "exec",
    "call",
    "merge"
]


def clean_sql_output(raw_output):
    sql = raw_output.strip()

    sql = sql.replace("```sql", "")
    sql = sql.replace("```SQL", "")
    sql = sql.replace("```", "")

    return sql.strip()


def get_sql_action_type(sql_query):
    sql = sql_query.strip().lower()

    if not sql:
        return "unknown"

    return sql.split()[0]


def is_dangerous_action(sql_query):
    action = get_sql_action_type(sql_query)
    return action in DANGEROUS_KEYWORDS


def validate_sql_action(sql_query):
    sql = sql_query.strip().lower()

    if not sql:
        return False, "SQL query is empty."

    first_word = sql.split()[0]

    if first_word not in ALLOWED_START_KEYWORDS:
        return False, f"SQL action not allowed: {first_word}"

    for keyword in BLOCKED_KEYWORDS:
        pattern = r"\b" + keyword + r"\b"
        if re.search(pattern, sql):
            return False, f"Blocked unsafe SQL keyword: {keyword}"

    if ";" in sql[:-1]:
        return False, "Multiple SQL statements are not allowed."

    if first_word == "drop" and "table" not in sql:
        return False, "Only DROP TABLE is allowed for drop operations."

    return True, "SQL action passed validation."