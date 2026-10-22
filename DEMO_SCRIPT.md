# ReliefMesh — 3-to-5 Minute Hackathon Demo Script
## Fetch-a-thon | ASI:One Agent Challenge

**Title:** ReliefMesh: Autonomous Emergency Resource Coordinator  
**Presenter Role:** Disaster Response AI Architect & Fetch.ai Engineer  
**Duration:** 3 to 5 Minutes  
**Primary UI:** ASI:One Conversation (`https://asi1.ai`) & Emergency Operations Dashboard (`http://127.0.0.1:8000`)

---

### [0:00 - 0:45] 1. The Crisis & Problem Statement
- **Spoken:**
  > "During natural disasters like flash floods, relief teams face a critical challenge: uncoordinated requests flood in from shelters, medical clinics, and volunteers. Coordinators struggle to prioritize life-saving needs, double-allocation occurs, and transport vehicles are dispatched inefficiently.
  >
  > Today, we present **ReliefMesh** — an autonomous emergency resource coordination system powered by Fetch.ai uAgents and the ASI:One Agent Chat Protocol.
  >
  > ReliefMesh converts natural-language crisis reports into mathematically verified, shortage-aware, and auditable allocation plans."

---

### [0:45 - 1:45] 2. Submitting Intent in ASI:One
- **Action:** Open the ASI:One conversation interface connected to the ReliefMesh agent (`agent1qfmhx62fz5q2fpnc38la0hchcfu3a5mkhve0pzxnkdymqdqa4yj8j5eeq07`).
- **Prompt Sent:**
  ```text
  Simulate relief operations for a flood affecting North Zone, River Zone, and Market Zone. We have 500 food kits, 300 water units, 100 first-aid kits, and four transport vehicles. Prioritize urgent needs, allocate available supplies, and explain any shortages.
  ```
- **Spoken:**
  > "Notice what happens instantly in the background:
  > 1. Our Fetch.ai uAgent immediately returns a `ChatAcknowledgement` message conforming to the ACP specification.
  > 2. The Command Orchestrator dispatches the scenario to our specialist multi-agent pipeline.
  > 3. Our Intent Parser extracts the disaster type, target zones, and inventory constraints."

---

### [1:45 - 2:45] 3. Multi-Agent Orchestration & Priority-Based Allocation
- **Action:** Show the live execution trace and Priority Allocation table.
- **Spoken:**
  > "Rather than using an unverified LLM hallucination for disaster logistics, ReliefMesh executes deterministic computations:
  > - **SituationAssessmentAgent** validates 9 field requests, flagging low-confidence social media posts.
  > - **NeedsAndPriorityAgent** detects and quarantines duplicate requests (like duplicate food requests from Market Zone).
  > - Transparent scoring: Urgency (up to 40 pts), Vulnerability (up to 30 pts), Source Confidence (up to 20 pts), and Lifesaving bonuses (10 pts for medical/water).
  > - **AllocationAgent** greedily matches resources:
  >   - River Mobile Clinic receives 60 first-aid trauma kits (Rank #1, Score 96.8).
  >   - North Zone Clinic receives 6 critical generators.
  >   - High-water demand triggers a real shortage: 400 water units requested against 300 available. The agent allocates 250 to high-vulnerability River Zone, partially fulfills Market Zone with 50 units, and reports a clear 100-unit shortage."

---

### [2:45 - 3:45] 4. Logistics Dispatch & Independent Mathematical Audit
- **Action:** Switch to the Logistics & Fleet tab, then the Independent Audit tab.
- **Spoken:**
  > "Next, our **LogisticsAgent** plans transport assignments:
  > - Delta Flood Utility (amphibious boat) is specifically assigned to flood-submerged zones where standard trucks cannot pass.
  > - Vehicle payloads strictly observe maximum capacity limits—preventing overloading.
  > 
  > Most importantly, look at the **VerificationAgent**:
  > - It independently audits the output!
  > - Audit 1: Inventory Conservation (`allocated <= available stock`).
  > - Audit 2: Arithmetic Conservation (`requested == allocated + unfulfilled`).
  > - Audit 3: Vehicle Payload Capacity (`cargo <= gross vehicle rating`).
  > - Audit 4: Duplicate Quarantine (`zero duplicates fulfilled`)."

---

### [3:45 - 4:30] 5. Ecosystem Impact & Wrap-Up
- **Spoken:**
  > "ReliefMesh demonstrates the true power of the Fetch.ai and ASI:One ecosystem:
  > - Full compliance with Agent Chat Protocol (ACP v0.3 / 0.4).
  > - Registered agent identity with deterministic seed.
  > - Explainable, auditable AI that disaster coordinators can actually trust.
  >
  > ReliefMesh: When Every Resource Counts. Thank you!"

---

### [4:30 - 5:00] Q&A Reference Notes
- **Is this connected to live 911 dispatch?**  
  *No, it is strictly an explainable simulation and decision-support prototype using synthetic data.*
- **What happens if ASI1 API is unavailable?**  
  *ReliefMesh includes a built-in deterministic NLP fallback parser that continues running offline without paid keys.*
