import os
import json
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///sample_store.db")

engine = create_engine(DATABASE_URL)


def get_database_dialect():
    return engine.dialect.name


def get_schema():
    inspector = inspect(engine)
    schema_lines = []

    dialect = get_database_dialect()
    schema_lines.append(f"Database dialect: {dialect}")
    schema_lines.append("")

    table_names = inspector.get_table_names()

    if not table_names:
        schema_lines.append("No tables found in the current database.")
        return "\n".join(schema_lines)

    for table_name in table_names:
        schema_lines.append(f"Table: {table_name}")

        columns = inspector.get_columns(table_name)

        for column in columns:
            column_name = column["name"]
            column_type = str(column["type"])
            nullable = column.get("nullable", True)
            null_text = "NULL" if nullable else "NOT NULL"

            schema_lines.append(
                f"  - {column_name} ({column_type}, {null_text})"
            )

        primary_key = inspector.get_pk_constraint(table_name)

        if primary_key and primary_key.get("constrained_columns"):
            pk_columns = ", ".join(primary_key["constrained_columns"])
            schema_lines.append(f"  - PRIMARY KEY ({pk_columns})")

        foreign_keys = inspector.get_foreign_keys(table_name)

        for fk in foreign_keys:
            constrained_columns = ", ".join(fk["constrained_columns"])
            referred_table = fk["referred_table"]
            referred_columns = ", ".join(fk["referred_columns"])

            schema_lines.append(
                f"  - FOREIGN KEY ({constrained_columns}) "
                f"REFERENCES {referred_table}({referred_columns})"
            )

        schema_lines.append("")

    return "\n".join(schema_lines)


def dataframe_to_json_safe(df):
    """
    Converts pandas DataFrame into normal JSON-safe Python objects.
    This avoids FastAPI errors with numpy int64, float64, Timestamp, etc.
    """
    return json.loads(df.to_json(orient="records", date_format="iso"))


def execute_database_action(sql_query):
    cleaned_sql = sql_query.strip().rstrip(";")

    if not cleaned_sql:
        return {
            "success": False,
            "type": "error",
            "columns": [],
            "rows": [],
            "message": "SQL query is empty."
        }

    first_word = cleaned_sql.split()[0].lower()

    try:
        with engine.begin() as connection:
            if first_word in ["select", "with", "show", "describe"]:
                df = pd.read_sql_query(text(cleaned_sql), connection)

                return {
                    "success": True,
                    "type": "read",
                    "columns": list(df.columns),
                    "rows": dataframe_to_json_safe(df),
                    "message": f"Query executed successfully. Rows returned: {len(df)}"
                }

            result = connection.execute(text(cleaned_sql))

            return {
                "success": True,
                "type": "write",
                "columns": [],
                "rows": [],
                "message": (
                    "Database action executed successfully. "
                    f"Rows affected: {result.rowcount}"
                )
            }

    except Exception as e:
        return {
            "success": False,
            "type": "error",
            "columns": [],
            "rows": [],
            "message": str(e)
        }