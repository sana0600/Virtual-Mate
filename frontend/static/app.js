const API = () =>
    document.getElementById("api-base").value.replace(/\/$/, "");

document.getElementById("api-base").value = window.location.origin;

/* =========================
STATUS CHECK
========================= */
async function checkStatus() {
    const dot = document.getElementById("sdot");

    try {
        const res = await fetch(API() + "/");
        dot.className = res.ok ? "status-dot online" : "status-dot offline";
    } catch {
        dot.className = "status-dot offline";
    }
}

checkStatus();
setInterval(checkStatus, 10000);

/* =========================
HELPERS
========================= */
function show(id) {
    document.getElementById(id).classList.remove("section-hidden");
}

function hide(id) {
    document.getElementById(id).classList.add("section-hidden");
}

function escapeHtml(text) {
    if (!text) return "";
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}

function showToast(message) {

    const toast = document.createElement("div");

    toast.className = "toast";
    toast.textContent = message;

    document.body.appendChild(toast);

    // animate in
    setTimeout(() => {
        toast.classList.add("show");
    }, 10);

    // animate out
    setTimeout(() => {

        toast.classList.remove("show");

        setTimeout(() => {
            toast.remove();
        }, 300);

    }, 2000);
}

function copyToClipboard(text, message) {

    console.log("Trying to copy:", text);

    navigator.clipboard.writeText(text)
        .then(() => {
            console.log("Copied!");
            alert(message);
        })
        .catch(err => {
            console.error("Clipboard error:", err);

            // fallback method
            const textarea = document.createElement("textarea");
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();

            try {
                document.execCommand("copy");
                alert(message);
            } catch (e) {
                alert("Copy failed");
            }

            document.body.removeChild(textarea);
        });
}


/* =========================
FILL TASK (EXAMPLE PROMPTS)
========================= */

function fillTask(btn, text) {

    if (btn) {
        document.querySelectorAll(".ex-btn")
            .forEach(b => b.classList.remove("active"));

        btn.classList.add("active");
    }

    const input = document.getElementById("task-input");
    if (input) input.value = text;
}

/* =========================
RESET (KEEP ALL UI BLOCKS)
========================= */
function resetAll() {

    [
        "plan-section",
        "log-section",
        "results-section",
        "files-section",
        "email-section",
        "report-section",
        "raw-section",
        "error-box"
    ].forEach(hide);

    document.getElementById("plan-steps").innerHTML = "";
    document.getElementById("log-list").innerHTML = "";
    document.getElementById("result-items").innerHTML = "";
    document.getElementById("generated-files-list").innerHTML = "";
    document.getElementById("email-preview-box").innerHTML = "";
    document.getElementById("raw-output").textContent = "";

    const btn = document.getElementById("exec-btn");
    btn.disabled = false;
    btn.innerHTML = "Execute Task";
}

/* =========================
LOGS
========================= */
function addLog(msg, state = "running") {
    show("log-section");

    const div = document.createElement("div");
    div.className = "log-entry " + state;

    div.innerHTML = `<strong>${state.toUpperCase()}</strong><br>${escapeHtml(msg)}`;

    document.getElementById("log-list").appendChild(div);
}

/* =========================
PLAN
========================= */
function renderPlan(plan) {
    show("plan-section");

    const container = document.getElementById("plan-steps");
    container.innerHTML = "";

    plan.forEach(p => {
        const card = document.createElement("div");
        card.className = "plan-step";

        card.innerHTML = `
            <h4>Step ${p.step}</h4>
            <p><b>${escapeHtml(p.subtask)}</b></p>
            <ul>
                ${p.actions.map(a => `<li>${escapeHtml(a)}</li>`).join("")}
            </ul>
        `;

        container.appendChild(card);
    });
}

/* =========================
RESULTS
========================= */
function renderResults(data) {

    show("results-section");

    const container = document.getElementById("result-items");
    container.innerHTML = "";

    (data.execution_results || []).forEach(step => {

        const card = document.createElement("div");
        card.className = "result-item";

        let html = `
            <h4>Step ${step.step}</h4>
            <p><b>${escapeHtml(step.subtask)}</b></p>
        `;

        step.results.forEach(r => {
            if (typeof r === "string") {
                html += `<div>${escapeHtml(r)}</div>`;
            } else {
                html += `<pre>${escapeHtml(JSON.stringify(r, null, 2))}</pre>`;
            }
        });

        card.innerHTML = html;
        container.appendChild(card);
    });
}

/* =========================
FILES
========================= */
function renderDownloads(data) {

    const grid = document.getElementById("generated-files-list");
    grid.innerHTML = "";

    let files = [];

    (data.execution_results || []).forEach(step => {
        step.results.forEach(r => {
            if (r && typeof r === "object" && r.file_path) {
                files.push(r.file_path);
            }
        });
    });

    files = [...new Set(files)];

    if (files.length === 0) {
        hide("files-section");
        return;
    }

    show("files-section");

    files.forEach(path => {

        const filename = path.split("\\").pop();

        const a = document.createElement("a");
        a.className = "dl-btn";
        a.href = `${API()}/download/${filename}?t=${Date.now()}`;
        a.target = "_blank";
        a.download = filename;
        a.innerHTML = "⬇ Download " + filename;

        grid.appendChild(a);
    });
}

/* =========================
EMAIL
========================= */
function renderEmail(data) {

    let email = null;

    (data.execution_results || []).forEach(step => {
        step.results.forEach(r => {
            if (typeof r === "string" &&
                r.toLowerCase().includes("subject")) {
                email = r;
            }
        });
    });

    if (!email) return;

    show("email-section");

    const box = document.getElementById("email-preview-box");
    box.innerHTML = "";

    const btn = document.createElement("copy-btn");
    btn.className = "copy-btn";
    btn.textContent = "📋 Copy Email";

    btn.addEventListener("click", () => {
        console.log("EMAIL CLICKED");
        copyToClipboard(email, "Email copied successfully");
    });

    const pre = document.createElement("pre");
    pre.textContent = email;

    box.appendChild(btn);
    box.appendChild(pre);
}
/* =========================
EXECUTE TASK (FIXED FLOW)
========================= */
async function runTask() {

    const task = document.getElementById("task-input").value.trim();

    if (!task) {
        alert("Enter a task first.");
        return;
    }

    resetAll();

    const btn = document.getElementById("exec-btn");
    btn.disabled = true;
    btn.innerHTML = "Running...";

    try {

        addLog("Executing task");

        const res = await fetch(API() + "/execute", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ task })
        });

        const data = await res.json();

        /* ================= CHAT MODE ================= */
        if (data.mode === "chat") {

            show("report-section");

            document.getElementById("report-preview-box").textContent = data.answer;

            document.getElementById("copy-response-btn").classList.remove("section-hidden");

            document.getElementById("copy-response-btn")
                .onclick = () => {
                copyToClipboard(data.answer, "Response copied successfully");
            };

            show("raw-section");
            document.getElementById("raw-output").textContent =
                JSON.stringify(data, null, 2);

            addLog("Answer generated", "done");

            return;
        }

        /* ================= AGENT MODE ================= */
        renderPlan(data.plan);
        renderResults(data);
        renderDownloads(data);
        renderEmail(data);

        show("raw-section");
        document.getElementById("raw-output").textContent =
            JSON.stringify(data, null, 2);

        addLog("Execution completed", "done");

    } catch (err) {

        show("error-box");
        document.getElementById("error-msg").innerHTML = err.message;
        addLog(err.message, "error");

    } finally {
        btn.disabled = false;
        btn.innerHTML = "Execute Task";

    }

    
}

