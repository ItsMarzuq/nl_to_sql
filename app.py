import streamlit as st

from database import (
    get_schema,
    get_database_dialect,
    execute_database_action
)

from nl2sql import generate_sql, correct_sql

from safety import (
    validate_sql_action,
    is_dangerous_action,
    get_sql_action_type
)


st.set_page_config(
    page_title="Natural Language Database Assistant",
    page_icon="🧠",
    layout="wide"
)


st.title("Natural Language Database Assistant")

st.write(
    "Type a database request in plain English. The system generates SQL, "
    "lets you review/edit it, validates it, and executes it only after confirmation."
)


# -----------------------------
# Session state
# -----------------------------
if "generated_sql" not in st.session_state:
    st.session_state.generated_sql = ""

if "corrected_sql" not in st.session_state:
    st.session_state.corrected_sql = ""

if "user_request" not in st.session_state:
    st.session_state.user_request = ""

if "history" not in st.session_state:
    st.session_state.history = []

if "sql_editor_version" not in st.session_state:
    st.session_state.sql_editor_version = 0

if "corrected_editor_version" not in st.session_state:
    st.session_state.corrected_editor_version = 0


dialect = get_database_dialect()
schema = get_schema()


st.info(f"Connected database dialect: `{dialect}`")


with st.expander("View Current Schema", expanded=False):
    st.code(schema, language="text")


# -----------------------------
# Natural language request
# -----------------------------
st.subheader("Natural Language Request")

user_request = st.text_area(
    "Enter your database request:",
    placeholder="Type your request here...",
    height=180
)


generate_clicked = st.button("Generate SQL", type="primary")


if generate_clicked:
    if not user_request.strip():
        st.warning("Please enter a natural language request.")
    else:
        st.session_state.user_request = user_request
        st.session_state.generated_sql = ""
        st.session_state.corrected_sql = ""

        with st.spinner("Generating SQL using Ollama..."):
            sql, error = generate_sql(
                schema=schema,
                question=user_request,
                dialect=dialect
            )

        if error:
            st.error(error)
        else:
            st.session_state.generated_sql = sql

            st.session_state.sql_editor_version += 1
            editor_key = f"sql_editor_{st.session_state.sql_editor_version}"
            st.session_state[editor_key] = sql

            st.rerun()


# -----------------------------
# Generated SQL editor
# -----------------------------
if st.session_state.generated_sql:
    st.subheader("Generated SQL Preview")

    editor_key = f"sql_editor_{st.session_state.sql_editor_version}"

    if editor_key not in st.session_state:
        st.session_state[editor_key] = st.session_state.generated_sql

    edited_sql = st.text_area(
        "Edit SQL before execution:",
        height=180,
        key=editor_key
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        ask_llm_correction = st.button("Ask LLM to Correct Edited SQL")

    with col2:
        st.caption("Manual edits are validated before execution.")

    if ask_llm_correction:
        with st.spinner("Sending edited SQL to Ollama for correction..."):
            corrected_sql, correction_error = correct_sql(
                schema=schema,
                question=st.session_state.user_request,
                failed_sql=edited_sql,
                error_message=(
                    "The user manually edited this SQL. "
                    "Review it against the schema and return a corrected version."
                ),
                dialect=dialect
            )

        if correction_error:
            st.error(correction_error)
        else:
            st.session_state.corrected_sql = corrected_sql

            st.session_state.corrected_editor_version += 1
            corrected_key = (
                f"corrected_sql_editor_"
                f"{st.session_state.corrected_editor_version}"
            )
            st.session_state[corrected_key] = corrected_sql

            st.rerun()

    is_valid, validation_message = validate_sql_action(edited_sql)

    if not is_valid:
        st.error(validation_message)

    else:
        st.success(validation_message)

        action_type = get_sql_action_type(edited_sql)
        dangerous = is_dangerous_action(edited_sql)

        can_execute = True

        if dangerous:
            st.warning(
                f"This is a potentially destructive `{action_type.upper()}` action. "
                "Type RUN below to confirm execution."
            )

            confirm_text = st.text_input(
                "Confirmation required:",
                placeholder="Type RUN"
            )

            can_execute = confirm_text == "RUN"

        execute_clicked = st.button(
            "Execute SQL",
            disabled=not can_execute
        )

        if execute_clicked:
            result = execute_database_action(edited_sql)

            st.subheader("Result")

            if result["success"]:
                st.success(result["message"])

                if result["type"] == "read":
                    st.dataframe(result["data"], use_container_width=True)

                else:
                    st.info("Schema has been updated.")
                    with st.expander("Updated Schema", expanded=True):
                        st.code(get_schema(), language="text")

                st.session_state.history.append(
                    {
                        "request": st.session_state.user_request,
                        "sql": edited_sql,
                        "status": "Success",
                        "message": result["message"]
                    }
                )

                st.session_state.generated_sql = ""
                st.session_state.corrected_sql = ""

                st.rerun()

            else:
                st.error(result["message"])

                st.session_state.history.append(
                    {
                        "request": st.session_state.user_request,
                        "sql": edited_sql,
                        "status": "Failed",
                        "message": result["message"]
                    }
                )

                with st.spinner("Trying to correct the SQL..."):
                    corrected_sql, correction_error = correct_sql(
                        schema=schema,
                        question=st.session_state.user_request,
                        failed_sql=edited_sql,
                        error_message=result["message"],
                        dialect=dialect
                    )

                if correction_error:
                    st.error(correction_error)
                else:
                    st.session_state.corrected_sql = corrected_sql

                    st.session_state.corrected_editor_version += 1
                    corrected_key = (
                        f"corrected_sql_editor_"
                        f"{st.session_state.corrected_editor_version}"
                    )
                    st.session_state[corrected_key] = corrected_sql

                    st.rerun()


# -----------------------------
# Corrected SQL suggestion
# -----------------------------
if st.session_state.corrected_sql:
    st.subheader("Corrected SQL Suggestion")

    corrected_key = (
        f"corrected_sql_editor_"
        f"{st.session_state.corrected_editor_version}"
    )

    if corrected_key not in st.session_state:
        st.session_state[corrected_key] = st.session_state.corrected_sql

    edited_corrected_sql = st.text_area(
        "You can also edit the corrected SQL:",
        height=180,
        key=corrected_key
    )

    use_corrected = st.button("Use Corrected SQL")

    if use_corrected:
        st.session_state.generated_sql = edited_corrected_sql
        st.session_state.corrected_sql = ""

        st.session_state.sql_editor_version += 1
        new_editor_key = f"sql_editor_{st.session_state.sql_editor_version}"
        st.session_state[new_editor_key] = edited_corrected_sql

        st.rerun()


# -----------------------------
# History
# -----------------------------
st.subheader("Action History")

if st.session_state.history:
    for index, item in enumerate(
        reversed(st.session_state.history),
        start=1
    ):
        with st.expander(f"Action {index}: {item['request']}"):
            st.write(f"Status: {item['status']}")
            st.code(item["sql"], language="sql")
            st.write(item["message"])
else:
    st.write("No actions executed yet.")