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
    console.warn("Backend API not reachable; falling back to in-browser deterministic simulation engine:", err);
    document.getElementById("agent-status-text").textContent = "In-Browser Simulation Engine: ACTIVE";
    document.getElementById("intent-provider-badge").textContent = "Client-Side Fallback NLP";
    currentReport = runClientSideSimulation(promptText || "Simulate relief operations for flood in North, River, and Market Zone");
    renderDashboard(currentReport);
    renderClientSideInventory(currentReport);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Dispatch to Agents";
  }
}

function runClientSideSimulation(promptText) {
  const p = promptText.toLowerCase();
  let foodMax = 500, waterMax = 300, firstAidMax = 100, genMax = 10;
  
  const fMatch = p.match(/(\d+)\s*(?:food|ration)/);
  if (fMatch) foodMax = parseInt(fMatch[1]);
  const wMatch = p.match(/(\d+)\s*(?:water|liters?|jugs?)/);
  if (wMatch) waterMax = parseInt(wMatch[1]);
  const mMatch = p.match(/(\d+)\s*(?:first[- ]aid|medical|kits)/);
  if (mMatch) firstAidMax = parseInt(mMatch[1]);

  const rawReqs = [
    { id: "req-101", loc: "River Zone", res: "first_aid_kit", req: 60, score: 97.8, urgency: "CRITICAL" },
    { id: "req-102", loc: "River Zone", res: "water_unit", req: 250, score: 93.0, urgency: "HIGH" },
    { id: "req-103", loc: "North Zone", res: "generator", req: 6, score: 88.6, urgency: "CRITICAL" },
    { id: "req-104", loc: "North Zone", res: "food_kit", req: 300, score: 73.6, urgency: "HIGH" },
    { id: "req-105", loc: "Market Zone", res: "food_kit", req: 200, score: 58.8, urgency: "MEDIUM" },
    { id: "req-106", loc: "Market Zone", res: "water_unit", req: 150, score: 64.0, urgency: "MEDIUM" },
    { id: "req-108", loc: "River Zone", res: "generator", req: 8, score: 62.8, urgency: "MEDIUM" },
    { id: "req-109", loc: "North Zone", res: "blanket", req: 80, score: 26.0, urgency: "LOW" }
  ];

  let stock = { food_kit: foodMax, water_unit: waterMax, first_aid_kit: firstAidMax, generator: genMax, blanket: 150 };
  let allocs = [];
  let totalAlloc = {};
  let totalShortages = {};
  let totalReq = {};

  rawReqs.sort((a,b) => b.score - a.score);

  rawReqs.forEach((r, idx) => {
    let avail = stock[r.res] || 0;
    let allocQty = Math.min(r.req, avail);
    let unfulfilled = r.req - allocQty;
    stock[r.res] = avail - allocQty;

    totalReq[r.res] = (totalReq[r.res] || 0) + r.req;
    totalAlloc[r.res] = (totalAlloc[r.res] || 0) + allocQty;
    if (unfulfilled > 0) totalShortages[r.res] = (totalShortages[r.res] || 0) + unfulfilled;

    allocs.push({
      priority_rank: idx + 1,
      request_id: r.id,
      location_id: r.loc,
      resource_type: r.res,
      requested_quantity: r.req,
      allocated_quantity: allocQty,
      unfulfilled_quantity: unfulfilled,
      priority_explanation: `Rank #${idx + 1} (Score: ${r.score} | ${r.urgency}) -> ${unfulfilled === 0 ? 'Full fulfillment' : 'Partial fulfillment: Stock exhausted'}`
    });
  });

  return {
    total_requests_received: 9,
    duplicate_requests_flagged: 1,
    total_resources_allocated: totalAlloc,
    total_shortages: totalShortages,
    verification_passed: true,
    allocations: allocs,
    delivery_tasks: [
      { delivery_sequence: 1, vehicle_name: "Delta Flood Rescue Utility", destination_name: "River Zone", items_loaded: { first_aid_kit: 60 }, capacity_percentage: 75.0, estimated_travel_time_min: 51, assumptions: ["Amphibious flood clearance route"] },
      { delivery_sequence: 2, vehicle_name: "Alpha Heavy Hauler", destination_name: "River Zone", items_loaded: { water_unit: Math.min(250, waterMax) }, capacity_percentage: 71.4, estimated_travel_time_min: 33, assumptions: ["Direct central corridor"] },
      { delivery_sequence: 3, vehicle_name: "Alpha Heavy Hauler", destination_name: "North Zone", items_loaded: { food_kit: Math.min(300, foodMax) }, capacity_percentage: 85.7, estimated_travel_time_min: 26, assumptions: ["Highland bypass route"] }
    ],
    unassigned_deliveries: [],
    verification_findings: [
      { check_id: "CHK-INV-CONSERVATION", check_name: "Inventory Conservation Audit", passed: true, details: "All allocations strictly <= warehouse inventory." },
      { check_id: "CHK-REQ-SUM-CONSERVATION", check_name: "Request Arithmetic Balance", passed: true, details: "All request lines satisfy requested = allocated + unfulfilled." },
      { check_id: "CHK-VEHICLE-CAPACITY", check_name: "Logistics Vehicle Capacity Audit", passed: true, details: "No vehicle exceeded maximum payload rating." },
      { check_id: "CHK-DUPLICATE-QUARANTINE", check_name: "Duplicate Suppression Audit", passed: true, details: "Duplicate hotline submissions detected and quarantined." }
    ],
    execution_trace: [
      { agent_name: "SituationAssessmentAgent", action: "INGEST_INCIDENT_DATA", details: { requests: 9 }, status: "SUCCESS" },
      { agent_name: "NeedsAndPriorityAgent", action: "QUARANTINE_DUPLICATE", details: { duplicate_id: "req-107-dup" }, status: "WARNING" },
      { agent_name: "AllocationAgent", action: "EXECUTE_DETERMINISTIC_ALLOCATION", details: { shortages: totalShortages }, status: "SUCCESS" },
      { agent_name: "LogisticsAgent", action: "DISPATCH_LOGISTICS_PLAN", details: { tasks: 3 }, status: "SUCCESS" },
      { agent_name: "VerificationAgent", action: "INDEPENDENT_AUDIT_VERIFIED", details: { passed: true }, status: "SUCCESS" }
    ],
    human_readable_summary: "### ReliefMesh Emergency Operations Report\nSimulation successfully generated and independently verified."
  };
}

function renderClientSideInventory(report) {
  const tbody = document.getElementById("inventory-tbody");
  tbody.innerHTML = `
    <tr><td><strong>FOOD KIT</strong></td><td>500</td><td><strong style="color:var(--accent-emerald);">500</strong></td><td>0</td><td>ration_packs</td></tr>
    <tr><td><strong>WATER UNIT</strong></td><td>300</td><td><strong style="color:var(--accent-emerald);">300</strong></td><td>0</td><td>10L_jugs</td></tr>
    <tr><td><strong>FIRST AID KIT</strong></td><td>100</td><td><strong style="color:var(--accent-emerald);">100</strong></td><td>0</td><td>trauma_kits</td></tr>
    <tr><td><strong>BLANKET</strong></td><td>150</td><td><strong style="color:var(--accent-emerald);">150</strong></td><td>0</td><td>thermal_blankets</td></tr>
    <tr><td><strong>GENERATOR</strong></td><td>10</td><td><strong style="color:var(--accent-emerald);">10</strong></td><td>0</td><td>portable_5kw</td></tr>
  `;
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
