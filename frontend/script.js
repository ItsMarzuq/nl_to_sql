const schemaText = document.getElementById("schemaText");
const dialectBadge = document.getElementById("dialectBadge");

const userRequestInput = document.getElementById("userRequest");
const generateBtn = document.getElementById("generateBtn");

const sqlSection = document.getElementById("sqlSection");
const generatedSqlBox = document.getElementById("generatedSql");
const validationMessage = document.getElementById("validationMessage");

const dangerBox = document.getElementById("dangerBox");
const confirmInput = document.getElementById("confirmInput");
const executeBtn = document.getElementById("executeBtn");

const resultSection = document.getElementById("resultSection");
const resultMessage = document.getElementById("resultMessage");
const tableContainer = document.getElementById("tableContainer");

const correctionSection = document.getElementById("correctionSection");
const correctedSqlBox = document.getElementById("correctedSql");
const correctionMessage = document.getElementById("correctionMessage");

const historyList = document.getElementById("historyList");

let currentSql = "";
let currentRequest = "";
let currentDangerous = false;
let history = [];


async function loadSchema() {
    try {
        const response = await fetch("/api/schema");
        const rawText = await response.text();

        let data;

        try {
            data = JSON.parse(rawText);
        } catch (error) {
            dialectBadge.textContent = "Error";
            schemaText.textContent = "Backend returned a non-JSON response:\n\n" + rawText;
            return;
        }

        dialectBadge.textContent = data.dialect || "Unknown";
        schemaText.textContent = data.schema || "No schema available.";

    } catch (error) {
        dialectBadge.textContent = "Error";
        schemaText.textContent = "Could not load schema: " + error.message;
    }
}


function setLoading(button, isLoading, loadingText, normalText) {
    if (isLoading) {
        button.disabled = true;
        button.textContent = loadingText;
    } else {
        button.disabled = false;
        button.textContent = normalText;
    }
}


generateBtn.addEventListener("click", async () => {
    const userRequest = userRequestInput.value.trim();

    if (!userRequest) {
        alert("Please enter a natural language request.");
        return;
    }

    currentRequest = userRequest;

    resultSection.classList.add("hidden");
    correctionSection.classList.add("hidden");
    tableContainer.innerHTML = "";
    resultMessage.textContent = "";
    correctedSqlBox.textContent = "";
    correctionMessage.textContent = "";

    setLoading(generateBtn, true, "Generating...", "Generate SQL");

    try {
        const response = await fetch("/api/generate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_request: userRequest
            })
        });

        const rawText = await response.text();

        let data;

        try {
            data = JSON.parse(rawText);
        } catch (error) {
            resultSection.classList.remove("hidden");
            resultMessage.textContent = "Backend returned a non-JSON error:";
            tableContainer.innerHTML = `<pre class="sql-box">${escapeHtml(rawText)}</pre>`;
            return;
        }

        if (!data.success) {
            resultSection.classList.remove("hidden");
            resultMessage.textContent = data.error || "Failed to generate SQL.";
            return;
        }

        currentSql = data.sql;
        currentDangerous = data.dangerous;

        sqlSection.classList.remove("hidden");
        generatedSqlBox.textContent = data.sql;
        validationMessage.textContent = data.validation_message || "";

        if (data.dangerous) {
            dangerBox.classList.remove("hidden");
            confirmInput.value = "";
            executeBtn.disabled = true;
        } else {
            dangerBox.classList.add("hidden");
            executeBtn.disabled = false;
        }

    } catch (error) {
        resultSection.classList.remove("hidden");
        resultMessage.textContent = "Error generating SQL: " + error.message;
    } finally {
        setLoading(generateBtn, false, "Generating...", "Generate SQL");
    }
});


confirmInput.addEventListener("input", () => {
    if (currentDangerous) {
        executeBtn.disabled = confirmInput.value.trim() !== "RUN";
    }
});


executeBtn.addEventListener("click", async () => {
    if (!currentSql) {
        alert("No SQL to execute.");
        return;
    }

    setLoading(executeBtn, true, "Executing...", "Execute SQL");

    resultSection.classList.add("hidden");
    correctionSection.classList.add("hidden");
    tableContainer.innerHTML = "";
    resultMessage.textContent = "";

    try {
        const response = await fetch("/api/execute", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                sql: currentSql
            })
        });

        const rawText = await response.text();

        let data;

        try {
            data = JSON.parse(rawText);
        } catch (error) {
            resultSection.classList.remove("hidden");
            resultMessage.textContent = "Backend returned a non-JSON error:";
            tableContainer.innerHTML = `<pre class="sql-box">${escapeHtml(rawText)}</pre>`;
            return;
        }

        resultSection.classList.remove("hidden");
        resultMessage.textContent = data.message || "Execution complete.";

        if (data.success) {
            if (data.type === "read") {
                renderTable(data.columns, data.rows);
            } else {
                tableContainer.innerHTML = "";
            }

            addToHistory(
                currentRequest,
                currentSql,
                "Success",
                data.message || "Executed successfully."
            );

            await loadSchema();

            currentSql = "";
            currentRequest = "";
            currentDangerous = false;

            sqlSection.classList.add("hidden");
            dangerBox.classList.add("hidden");
            confirmInput.value = "";

        } else {
            tableContainer.innerHTML = "";

            addToHistory(
                currentRequest,
                currentSql,
                "Failed",
                data.message || "Execution failed."
            );

            await requestCorrection(data.message || "Unknown database error.");
        }

    } catch (error) {
        resultSection.classList.remove("hidden");
        resultMessage.textContent = "Error executing SQL: " + error.message;
    } finally {
        setLoading(executeBtn, false, "Executing...", "Execute SQL");

        if (currentDangerous) {
            executeBtn.disabled = confirmInput.value.trim() !== "RUN";
        }
    }
});


async function requestCorrection(errorMessage) {
    try {
        const response = await fetch("/api/correct", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_request: currentRequest,
                failed_sql: currentSql,
                error_message: errorMessage
            })
        });

        const rawText = await response.text();

        let data;

        try {
            data = JSON.parse(rawText);
        } catch (error) {
            correctionSection.classList.remove("hidden");
            correctedSqlBox.textContent = "";
            correctionMessage.textContent = "Correction endpoint returned a non-JSON response:\n\n" + rawText;
            return;
        }

        correctionSection.classList.remove("hidden");

        if (!data.success) {
            correctedSqlBox.textContent = "";
            correctionMessage.textContent = data.error || "Correction failed.";
            return;
        }

        correctedSqlBox.textContent = data.sql;
        correctionMessage.textContent = data.validation_message || "Review the corrected SQL suggestion.";

    } catch (error) {
        correctionSection.classList.remove("hidden");
        correctedSqlBox.textContent = "";
        correctionMessage.textContent = "Correction error: " + error.message;
    }
}


function renderTable(columns, rows) {
    if (!columns || columns.length === 0) {
        tableContainer.innerHTML = "<p>No columns returned.</p>";
        return;
    }

    if (!rows || rows.length === 0) {
        tableContainer.innerHTML = "<p>No rows returned.</p>";
        return;
    }

    let html = "<table><thead><tr>";

    columns.forEach(column => {
        html += `<th>${escapeHtml(column)}</th>`;
    });

    html += "</tr></thead><tbody>";

    rows.forEach(row => {
        html += "<tr>";

        columns.forEach(column => {
            const value = row[column] === null || row[column] === undefined
                ? ""
                : row[column];

            html += `<td>${escapeHtml(String(value))}</td>`;
        });

        html += "</tr>";
    });

    html += "</tbody></table>";

    tableContainer.innerHTML = html;
}


function addToHistory(request, sql, status, message) {
    history.unshift({
        request,
        sql,
        status,
        message
    });

    renderHistory();
}


function renderHistory() {
    if (history.length === 0) {
        historyList.innerHTML = "<p>No actions yet.</p>";
        return;
    }

    let html = "";

    history.forEach((item, index) => {
        html += `
            <div class="history-item">
                <strong>Action ${index + 1}: ${escapeHtml(item.request)}</strong>
                <p>Status: ${escapeHtml(item.status)}</p>
                <pre>${escapeHtml(item.sql)}</pre>
                <p>${escapeHtml(item.message)}</p>
            </div>
        `;
    });

    historyList.innerHTML = html;
}


function escapeHtml(value) {
    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


loadSchema();