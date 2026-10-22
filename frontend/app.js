const API_BASE = window.location.origin.includes("8000") ? "" : "http://127.0.0.1:8000";

let currentReport = null;

async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      document.getElementById("agent-status-text").textContent = "Fetch.ai Orchestrator: ONLINE";
    }
  } catch (e) {
    document.getElementById("agent-status-text").textContent = "Backend: Connecting...";
  }
}

async function runSimulation(promptText = null) {
  const submitBtn = document.getElementById("btn-submit-prompt");
  submitBtn.disabled = true;
  submitBtn.textContent = "Orchestrating Agents...";

  try {
    let res;
    if (promptText) {
      res = await fetch(`${API_BASE}/simulate-nl`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_prompt: promptText })
      });
      const data = await res.json();
      currentReport = data.report;
      document.getElementById("intent-provider-badge").textContent = data.intent_parser || "Deterministic NLP";
    } else {
      res = await fetch(`${API_BASE}/scenarios/scenario-flood-tri-zone/simulate`, {
        method: "POST"
      });
      currentReport = await res.json();
      document.getElementById("intent-provider-badge").textContent = "Baseline Tri-Zone Drill";
    }

    renderDashboard(currentReport);
    loadInventory();
  } catch (err) {
    console.error("Simulation error:", err);
    alert("Could not reach backend API at " + API_BASE + ". Ensure 'run_backend.ps1' is running.");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Dispatch to Agents";
  }
}

async function resetDemo() {
  try {
    const res = await fetch(`${API_BASE}/inventory/reset-demo`, { method: "POST" });
    if (res.ok) {
      alert("Demo state successfully reset to default baseline!");
      runSimulation();
    }
  } catch (e) {
    alert("Failed to reset demo: " + e.message);
  }
}

async function loadInventory() {
  try {
    const res = await fetch(`${API_BASE}/inventory`);
    if (!res.ok) return;
    const inv = await res.json();
    const tbody = document.getElementById("inventory-tbody");
    tbody.innerHTML = "";

    for (const [key, item] of Object.entries(inv)) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${item.resource_type.replace('_', ' ').toUpperCase()}</strong></td>
        <td>${item.total_initial_quantity}</td>
        <td><strong style="color: ${item.available_quantity > 0 ? 'var(--accent-emerald)' : 'var(--accent-rose)'};">${item.available_quantity}</strong></td>
        <td>${item.reserved_quantity}</td>
        <td>${item.unit}</td>
      `;
      tbody.appendChild(tr);
    }
  } catch (e) {
    console.warn("Could not load inventory:", e);
  }
}

function renderDashboard(report) {
  if (!report) return;

  // 1. Metric Cards
  document.getElementById("metric-requests").textContent = report.total_requests_received || 0;
  document.getElementById("metric-requests-sub").textContent = `${report.duplicate_requests_flagged || 0} duplicates quarantined`;

  const totalAllocUnits = Object.values(report.total_resources_allocated || {}).reduce((a, b) => a + b, 0);
  document.getElementById("metric-allocated").textContent = totalAllocUnits;

  const shortageKeys = Object.keys(report.total_shortages || {});
  document.getElementById("metric-shortages").textContent = shortageKeys.length;
  document.getElementById("metric-shortages-sub").textContent = shortageKeys.length > 0 ? shortageKeys.join(", ") : "Zero shortages";

  document.getElementById("metric-deliveries").textContent = report.delivery_tasks ? report.delivery_tasks.length : 0;
  document.getElementById("metric-deliveries-sub").textContent = `${report.unassigned_deliveries ? report.unassigned_deliveries.length : 0} unassigned`;

  const auditBadge = document.getElementById("metric-audit");
  auditBadge.textContent = report.verification_passed ? "PASSED" : "FAILED";
  auditBadge.style.color = report.verification_passed ? "var(--accent-emerald)" : "var(--accent-rose)";

  // 2. Allocations Table
  const allocTbody = document.getElementById("allocations-tbody");
  allocTbody.innerHTML = "";

  (report.allocations || []).forEach(a => {
    const tr = document.createElement("tr");
    const isShortage = a.unfulfilled_quantity > 0;
    tr.innerHTML = `
      <td><strong>#${a.priority_rank}</strong></td>
      <td><code>${a.request_id}</code></td>
      <td>${a.location_id}</td>
      <td>${a.resource_type}</td>
      <td>${a.requested_quantity}</td>
      <td><strong style="color: var(--accent-emerald);">${a.allocated_quantity}</strong></td>
      <td><span style="color: ${isShortage ? 'var(--accent-amber)' : 'var(--text-muted)'};">${a.unfulfilled_quantity}</span></td>
      <td><small style="color: var(--text-secondary);">${a.priority_explanation}</small></td>
    `;
    allocTbody.appendChild(tr);
  });

  // 3. Logistics Table
  const logTbody = document.getElementById("logistics-tbody");
  logTbody.innerHTML = "";

  (report.delivery_tasks || []).forEach(t => {
    const tr = document.createElement("tr");
    const cargoStr = Object.entries(t.items_loaded || {}).map(([k, v]) => `${v} ${k}`).join(", ");
    tr.innerHTML = `
      <td>${t.delivery_sequence}</td>
      <td><strong>${t.vehicle_name}</strong></td>
      <td>${t.destination_name}</td>
      <td>${cargoStr}</td>
      <td>${t.capacity_percentage}%</td>
      <td>${t.estimated_travel_time_min} min</td>
      <td><small style="color: var(--text-secondary);">${(t.assumptions || []).join('; ')}</small></td>
    `;
    logTbody.appendChild(tr);
  });

  // 4. Verification Findings Table
  const verTbody = document.getElementById("verification-tbody");
  verTbody.innerHTML = "";

  (report.verification_findings || []).forEach(f => {
    const tr = document.createElement("tr");
    const statusClass = f.passed ? "badge-success" : (f.severity === "CRITICAL" ? "badge-critical" : "badge-warning");
    tr.innerHTML = `
      <td><code>${f.check_id}</code></td>
      <td><strong>${f.check_name}</strong></td>
      <td><span class="badge ${statusClass}">${f.passed ? "PASSED" : "FAILED"}</span></td>
      <td>${f.details}</td>
    `;
    verTbody.appendChild(tr);
  });

  // 5. Execution Timeline
  const traceDiv = document.getElementById("trace-timeline");
  traceDiv.innerHTML = "";

  (report.execution_trace || []).forEach(e => {
    const item = document.createElement("div");
    item.className = "timeline-event";
    const statusClass = e.status === "SUCCESS" ? "badge-success" : (e.status === "ERROR" ? "badge-critical" : "badge-warning");
    item.innerHTML = `
      <div>
        <span class="event-agent">${e.agent_name}</span> &rarr; 
        <span class="event-action">${e.action}</span>
        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem;">${JSON.stringify(e.details)}</div>
      </div>
      <div>
        <span class="badge ${statusClass}">${e.status}</span>
      </div>
    `;
    traceDiv.appendChild(item);
  });

  // 6. Markdown Report View
  document.getElementById("markdown-report-view").textContent = report.human_readable_summary || "No report generated.";
}

// Setup Event Listeners
document.addEventListener("DOMContentLoaded", () => {
  checkBackendHealth();
  runSimulation();

  document.getElementById("btn-run-sim").addEventListener("click", () => {
    const prompt = document.getElementById("prompt-input").value;
    runSimulation(prompt);
  });

  document.getElementById("btn-submit-prompt").addEventListener("click", () => {
    const prompt = document.getElementById("prompt-input").value;
    runSimulation(prompt);
  });

  document.getElementById("btn-reset-demo").addEventListener("click", resetDemo);

  // Quick Prompt Chips
  document.querySelectorAll(".prompt-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const p = chip.getAttribute("data-prompt");
      document.getElementById("prompt-input").value = p;
      runSimulation(p);
    });
  });

  // Tab switching
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      const tabId = btn.getAttribute("data-tab");
      document.getElementById(tabId).classList.add("active");
    });
  });
});
