from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.database import (
    get_schema,
    get_database_dialect,
    execute_database_action
)
from backend.nl2sql import generate_sql, correct_sql
from backend.safety import (
    validate_sql_action,
    is_dangerous_action,
    get_sql_action_type
)


app = FastAPI(title="Natural Language Database Assistant API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    user_request: str


class ExecuteRequest(BaseModel):
    sql: str


class CorrectRequest(BaseModel):
    user_request: str
    failed_sql: str
    error_message: str


@app.get("/api/schema")
def api_get_schema():
    return {
        "dialect": get_database_dialect(),
        "schema": get_schema()
    }


@app.post("/api/generate")
def api_generate_sql(request: GenerateRequest):
    schema = get_schema()
    dialect = get_database_dialect()

    sql, error = generate_sql(
        schema=schema,
        question=request.user_request,
        dialect=dialect
    )

    if error:
        return {
            "success": False,
            "sql": "",
            "error": error
        }

    is_valid, validation_message = validate_sql_action(sql)

    return {
        "success": True,
        "sql": sql,
        "is_valid": is_valid,
        "validation_message": validation_message,
        "action_type": get_sql_action_type(sql),
        "dangerous": is_dangerous_action(sql)
    }


@app.post("/api/execute")
def api_execute_sql(request: ExecuteRequest):
    try:
        is_valid, validation_message = validate_sql_action(request.sql)

        if not is_valid:
            return {
                "success": False,
                "type": "validation_error",
                "message": validation_message,
                "columns": [],
                "rows": [],
                "schema": get_schema()
            }

        result = execute_database_action(request.sql)
        result["schema"] = get_schema()

        return result

    except Exception as e:
        return {
            "success": False,
            "type": "server_error",
            "message": f"Backend error: {str(e)}",
            "columns": [],
            "rows": [],
            "schema": ""
        }


@app.post("/api/correct")
def api_correct_sql(request: CorrectRequest):
    schema = get_schema()
    dialect = get_database_dialect()

    corrected_sql, error = correct_sql(
        schema=schema,
        question=request.user_request,
        failed_sql=request.failed_sql,
        error_message=request.error_message,
        dialect=dialect
    )

    if error:
        return {
            "success": False,
            "sql": "",
            "error": error
        }

    is_valid, validation_message = validate_sql_action(corrected_sql)

    return {
        "success": True,
        "sql": corrected_sql,
        "is_valid": is_valid,
        "validation_message": validation_message,
        "action_type": get_sql_action_type(corrected_sql),
        "dangerous": is_dangerous_action(corrected_sql)
    }


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")