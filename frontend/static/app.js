const API = () => document.getElementById("api-base").value.replace(/\/$/, "");

document.getElementById("api-base").value = window.location.origin;

async function checkStatus() {
    const dot = document.getElementById("sdot");
    try {
        const response = await fetch(API() + "/health");
        dot.className = response.ok ? "status-dot online" : "status-dot offline";
        dot.title = response.ok ? "API ready" : "API is missing required configuration";
    } catch {
        dot.className = "status-dot offline";
        dot.title = "API unavailable";
    }
}

checkStatus();
setInterval(checkStatus, 10000);

function show(id) {
    document.getElementById(id).classList.remove("section-hidden");
}

function hide(id) {
    document.getElementById(id).classList.add("section-hidden");
}

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatInlineMarkdown(value) {
    const codeSegments = [];
    let formatted = escapeHtml(value).replace(/`([^`]+)`/g, (_match, code) => {
        const token = `@@VM_CODE_${codeSegments.length}@@`;
        codeSegments.push(`<code>${code}</code>`);
        return token;
    });

    formatted = formatted
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/__(.+?)__/g, "<strong>$1</strong>")
        .replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>");

    codeSegments.forEach((code, index) => {
        formatted = formatted.replace(`@@VM_CODE_${index}@@`, code);
    });
    return formatted;
}

function tableCells(line) {
    return line.trim().replace(/^\||\|$/g, "").split("|").map(cell => cell.trim());
}

function isTableRow(line) {
    const trimmed = line.trim();
    return trimmed.startsWith("|") && trimmed.endsWith("|");
}

function isTableSeparator(line) {
    return isTableRow(line) && tableCells(line).every(cell => /^:?-{3,}:?$/.test(cell));
}

function tableAlignment(marker) {
    if (marker.startsWith(":") && marker.endsWith(":")) return "center";
    if (marker.endsWith(":")) return "right";
    return "left";
}

function isMarkdownBlockStart(lines, index) {
    const line = lines[index] || "";
    const trimmed = line.trim();
    return /^#{1,6}\s+/.test(trimmed)
        || /^([-*_])\1{2,}$/.test(trimmed.replace(/\s/g, ""))
        || /^[-*+]\s+/.test(trimmed)
        || /^\d+[.)]\s+/.test(trimmed)
        || /^>\s?/.test(trimmed)
        || (isTableRow(line) && isTableSeparator(lines[index + 1] || ""));
}

function markdownToHtml(markdown) {
    const lines = String(markdown ?? "").replace(/\r\n?/g, "\n").split("\n");
    const output = [];
    let index = 0;

    while (index < lines.length) {
        const line = lines[index];
        const trimmed = line.trim();

        if (!trimmed) {
            index += 1;
            continue;
        }

        if (isTableRow(line) && isTableSeparator(lines[index + 1] || "")) {
            const headings = tableCells(line);
            const markers = tableCells(lines[index + 1]);
            const alignments = markers.map(tableAlignment);
            index += 2;
            const rows = [];
            while (index < lines.length && isTableRow(lines[index])) {
                rows.push(tableCells(lines[index]));
                index += 1;
            }
            output.push(`
                <div class="response-table-wrap">
                    <table>
                        <thead><tr>${headings.map((cell, cellIndex) =>
                            `<th style="text-align:${alignments[cellIndex] || "left"}">${formatInlineMarkdown(cell)}</th>`
                        ).join("")}</tr></thead>
                        <tbody>${rows.map(row => `<tr>${row.map((cell, cellIndex) =>
                            `<td style="text-align:${alignments[cellIndex] || "left"}">${formatInlineMarkdown(cell)}</td>`
                        ).join("")}</tr>`).join("")}</tbody>
                    </table>
                </div>
            `);
            continue;
        }

        const heading = trimmed.match(/^(#{1,6})\s+(.+)$/);
        if (heading) {
            const level = heading[1].length;
            output.push(`<h${level}>${formatInlineMarkdown(heading[2])}</h${level}>`);
            index += 1;
            continue;
        }

        if (/^([-*_])\1{2,}$/.test(trimmed.replace(/\s/g, ""))) {
            output.push("<hr>");
            index += 1;
            continue;
        }

        if (/^[-*+]\s+/.test(trimmed)) {
            const items = [];
            while (index < lines.length && /^[-*+]\s+/.test(lines[index].trim())) {
                items.push(lines[index].trim().replace(/^[-*+]\s+/, ""));
                index += 1;
            }
            output.push(`<ul>${items.map(item => `<li>${formatInlineMarkdown(item)}</li>`).join("")}</ul>`);
            continue;
        }

        if (/^\d+[.)]\s+/.test(trimmed)) {
            const items = [];
            while (index < lines.length && /^\d+[.)]\s+/.test(lines[index].trim())) {
                items.push(lines[index].trim().replace(/^\d+[.)]\s+/, ""));
                index += 1;
            }
            output.push(`<ol>${items.map(item => `<li>${formatInlineMarkdown(item)}</li>`).join("")}</ol>`);
            continue;
        }

        if (/^>\s?/.test(trimmed)) {
            const quotes = [];
            while (index < lines.length && /^>\s?/.test(lines[index].trim())) {
                quotes.push(lines[index].trim().replace(/^>\s?/, ""));
                index += 1;
            }
            output.push(`<blockquote>${quotes.map(formatInlineMarkdown).join("<br>")}</blockquote>`);
            continue;
        }

        const paragraph = [trimmed];
        index += 1;
        while (
            index < lines.length
            && lines[index].trim()
            && !isMarkdownBlockStart(lines, index)
        ) {
            paragraph.push(lines[index].trim());
            index += 1;
        }
        output.push(`<p>${paragraph.map(formatInlineMarkdown).join("<br>")}</p>`);
    }

    return output.join("");
}

function renderFormattedText(container, text) {
    container.innerHTML = markdownToHtml(text);
}

function showToast(message) {
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add("show"), 10);
    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}

async function copyToClipboard(text, message) {
    try {
        await navigator.clipboard.writeText(text);
        showToast(message);
    } catch {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        const copied = document.execCommand("copy");
        textarea.remove();
        showToast(copied ? message : "Copy failed");
    }
}

function fillTask(btn, text) {
    document.querySelectorAll(".ex-btn").forEach(button => button.classList.remove("active"));
    if (btn) btn.classList.add("active");
    document.getElementById("task-input").value = text;
}

function resetAll(clearTask = false) {
    [
        "plan-section", "log-section", "results-section", "files-section",
        "email-section", "report-section", "raw-section", "error-box"
    ].forEach(hide);

    [
        "plan-steps", "log-list", "result-items", "generated-files-list",
        "email-preview-box", "report-preview-box", "raw-output", "error-msg"
    ].forEach(id => {
        document.getElementById(id).textContent = "";
    });

    hide("copy-response-btn");
    hide("copy-email-btn");
    if (clearTask) {
        document.getElementById("task-input").value = "";
        document.querySelectorAll(".ex-btn").forEach(button => button.classList.remove("active"));
    }
    const button = document.getElementById("exec-btn");
    button.disabled = false;
    button.textContent = "Execute Task";
}

function addLog(message, state = "running") {
    show("log-section");
    const entry = document.createElement("div");
    entry.className = `log-entry ${state}`;
    entry.innerHTML = `<strong>${escapeHtml(state.toUpperCase())}</strong><br>${escapeHtml(message)}`;
    document.getElementById("log-list").appendChild(entry);
}

function renderPlan(plan = []) {
    show("plan-section");
    const container = document.getElementById("plan-steps");
    container.textContent = "";
    plan.forEach(item => {
        const card = document.createElement("div");
        card.className = "plan-step";
        const actions = (item.actions || []).map(action => {
            const label = action.instruction || action;
            const type = action.type ? `<span class="action-type">${escapeHtml(action.type)}</span> ` : "";
            return `<li>${type}${escapeHtml(label)}</li>`;
        }).join("");
        card.innerHTML = `
            <h4>Step ${escapeHtml(item.step)}</h4>
            <p><b>${escapeHtml(item.subtask)}</b></p>
            <ul>${actions}</ul>
        `;
        container.appendChild(card);
    });
}

function renderResults(data) {
    show("results-section");
    const container = document.getElementById("result-items");
    container.textContent = "";
    (data.execution_results || []).forEach(step => {
        const card = document.createElement("div");
        card.className = "result-item";
        card.innerHTML = `
            <h4>Step ${escapeHtml(step.step)}</h4>
            <p><b>${escapeHtml(step.subtask)}</b></p>
        `;

        (step.results || []).forEach(result => {
            const resultBlock = document.createElement("div");
            resultBlock.className = "typed-result";

            const type = document.createElement("span");
            type.className = "result-type";
            type.textContent = result.type || "result";
            resultBlock.appendChild(type);

            const content = document.createElement("div");
            content.className = "result-content formatted-response compact-response";
            if (typeof result.content === "string") {
                renderFormattedText(content, result.content);
            } else if (result.content !== undefined) {
                const pre = document.createElement("pre");
                pre.textContent = JSON.stringify(result.content, null, 2);
                content.appendChild(pre);
            } else {
                content.textContent = result.message || "Completed";
            }
            resultBlock.appendChild(content);
            card.appendChild(resultBlock);
        });
        container.appendChild(card);
    });
}

function renderAgentReport(data) {
    const summary = (data.execution_results || [])
        .flatMap(step => step.results || [])
        .filter(result => result.type === "summary" && typeof result.content === "string")
        .at(-1);

    if (!summary) {
        hide("report-section");
        return;
    }

    show("report-section");
    hide("copy-response-btn");
    renderFormattedText(document.getElementById("report-preview-box"), summary.content);
}

function renderDownloads(data) {
    const container = document.getElementById("generated-files-list");
    container.textContent = "";
    const uniqueFiles = [...new Map(
        (data.files || []).map(file => [file.filename, file])
    ).values()];
    if (!uniqueFiles.length) {
        hide("files-section");
        return;
    }
    show("files-section");
    uniqueFiles.forEach(file => {
        const link = document.createElement("a");
        link.className = "dl-btn";
        link.href = `${API()}${file.download_url}`;
        link.download = file.filename;
        link.textContent = `⬇ Download ${file.filename}`;
        container.appendChild(link);
    });
}

function renderEmail(data) {
    const emailResult = (data.execution_results || [])
        .flatMap(step => step.results || [])
        .find(result => result.type === "email" && typeof result.content === "string");
    if (!emailResult) {
        hide("email-section");
        return;
    }
    show("email-section");
    const pre = document.createElement("pre");
    pre.textContent = emailResult.content;
    document.getElementById("email-preview-box").replaceChildren(pre);
    const button = document.getElementById("copy-email-btn");
    show("copy-email-btn");
    button.onclick = () => copyToClipboard(emailResult.content, "Email copied successfully");
}

async function parseResponse(response) {
    const text = await response.text();
    let data = {};
    try {
        data = text ? JSON.parse(text) : {};
    } catch {
        if (!response.ok) throw new Error(`Request failed with HTTP ${response.status}`);
        throw new Error("The API returned an invalid response.");
    }
    if (!response.ok) {
        const detail = typeof data.detail === "string" ? data.detail : null;
        throw new Error(data.error?.message || detail || `Request failed with HTTP ${response.status}`);
    }
    return data;
}

async function runTask() {
    const task = document.getElementById("task-input").value.trim();
    if (!task) {
        showToast("Enter a task first.");
        return;
    }
    resetAll(false);
    const button = document.getElementById("exec-btn");
    button.disabled = true;
    button.textContent = "Running...";
    try {
        addLog("Executing task");
        const response = await fetch(API() + "/execute", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ task })
        });
        const data = await parseResponse(response);
        if (data.mode === "chat") {
            show("report-section");
            renderFormattedText(document.getElementById("report-preview-box"), data.answer);
            const copyButton = document.getElementById("copy-response-btn");
            show("copy-response-btn");
            copyButton.onclick = () => copyToClipboard(data.answer, "Response copied successfully");
            addLog("Answer generated", "done");
        } else {
            renderAgentReport(data);
            renderEmail(data);
            renderDownloads(data);
            renderPlan(data.plan);
            renderResults(data);
            addLog("Execution completed", "done");
        }
        show("raw-section");
        document.getElementById("raw-output").textContent = JSON.stringify(data, null, 2);
    } catch (error) {
        show("error-box");
        document.getElementById("error-msg").textContent = error.message;
        addLog(error.message, "error");
    } finally {
        button.disabled = false;
        button.textContent = "Execute Task";
    }
}
