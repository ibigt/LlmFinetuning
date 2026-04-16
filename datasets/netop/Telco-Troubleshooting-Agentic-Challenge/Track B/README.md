# Track B: Telco Troubleshooting and Optimization Agentic Challenge

## Competition Overview

This task focuses on IP network operations and maintenance. Participants are required to build intelligent agents that complete IP network fault diagnosis and troubleshooting tasks by calling the CLI simulation interfaces provided by the **Agent Tool Server**.

**Base Model:** The entire competition (Phase 1 / 2 / 3) uses **Qwen3.5-35B-A3B** as the base model. Participants may fine-tune the model (LoRA, full fine-tuning, etc.), but are not allowed to replace it with a different architecture or a model of a different parameter scale.

**Server Core Capabilities:**
- Simulates CLI interactions for network devices (Huawei / Cisco / H3C)
- Supports regex whitelist validation for 45+ command categories
- Faithfully reproduces vendor-level syntax errors (incomplete / unrecognized / ambiguous / wrong parameter)
- Multiple command output file types covering routing tables, BGP, VXLAN, SRv6, and more

---

## Competition Design

### Schedule Overview

| Phase | Name | Duration      | Purpose | Problem Scale & Requirements                     | Participant Actions                                                   |
|-------|------|---------------|---------|--------------------------------------------------|-----------------------------------------------------------------------|
| **Phase 1** | Open Practice | 3 April–4 May | Debug Agent, familiarize with API | 50 problems / Multi vendor / advanced protocols  | Run locally, submit result.csv                                        |
| **Phase 2** | Elimination Round | 4 May-18 May  | Select top participants for Phase 3 | 100 problems / multi-vendor / advanced protocols | Run locally, 1 submission only, upload execution trace and result.csv |
| **Phase 3** | Final | 18 May-29 May | Final ranking | 70 problems / multi-vendor / advanced protocols    | Server-side Docker auto-execution                                     |

### Detailed Problem Distribution

| Phase | Problem Composition                                                 | Task Types | Protocols Covered (examples, not exhaustive) | Device Vendors       |
|-------|---------------------------------------------------------------------|------------|-------------------------------|----------------------|
| **Phase 1** | 32-node financial network & 22-node cloud computing network (50 problems) | Topology reconstruction, path query, fault localization | +LLDP, OSPF, VXLAN            | **Multi-vendor mix** |
| **Phase 2** | 40-node campus network (100)                                        | Topology reconstruction, path query, fault localization | +VLAN, VRRP, MP-BGP           | **Multi-vendor mix** |
| **Phase 3** | 64-node financial network (70)                                      | Topology reconstruction, path query, fault localization | +VXLAN, EVPN, SRv6, ISIS, BGP | **Multi-vendor mix** |

### Phase 1 (Open Practice)

- **Number of Problems:** 50
- **Execution Environment:** Participants run Agent locally
- **Base Model:** Qwen3.5-35B-A3B (participants may fine-tune)
- **API Call Limit:** Max **1,000 API calls per participant per day** (only Phase 1 enforces this daily quota; Phase 2 and Phase 3 do not have this restriction)
- **Scoring:** Participants submit `result.csv`; scored by **accuracy only** (the sole evaluation metric for Phase 1)
- **Tool Call Rules:**
  - Agent must call tools **sequentially** when solving a single problem; no concurrent calls within a problem
  - Max concurrency per participant is **2** (i.e., at most 2 problems running in parallel)
- **Onboarding:** Server source code and local deployment guide provided to help participants deploy locally

### Phase 2 (Elimination Round)

- **Number of Problems:** 100 (released in batches of **20 problems every 3 days**)
- **Base Model:** Qwen3.5-35B-A3B (participants may fine-tune)
- **Submission Limit:** Each participant is allowed **only three submissions**; execution trace must be uploaded to the server. Unlike Phase 1, there is no daily API call quota, but participants must ensure at least a single run completes successfully.
- **Scoring:** **Accuracy** as the primary metric; for participants with the same accuracy, the **number of API calls used to solve correct problems** serves as the secondary metric (fewer calls = higher rank)
- **Selection Mechanism:** Participants reserve a submission time slot; top 30 advance to the final
- **Focus:** Agent generalization across multi-vendor environments and stability in one-shot execution

### Phase 3 (Final)

- **Number of Problems:** 70
- **Participants:** Top 30 selected from Phase 2
- **Execution Environment:** Organizer-provided GPU resources + isolated Docker environment
- **Base Model:** Qwen3.5-35B-A3B (participants may fine-tune)
- **Time Limit:** Must be completed within 24 hours
- **Network Data:** Uses **different network data** from Phase 1 / 2
- **Focus:** Complex protocol reasoning (SRv6/EVPN) and deep fault isolation in large-scale networks (64 nodes)
- **Resource Allocation:**
  - **GPU Resources:** Huawei Cloud GPU instances for deploying the base model, independently allocated per participant
  - **Agent Tool Server:** Deployed on HuggingFace free CPU resources (free within 24h)
- **Base Model:** Qwen3.5-35B-A3B, deployed by the organizer to each participant's GPU instance
- **Submission Requirements:** Participants must upload their **fine-tuned model weights** and **Agent code** to the organizer; the organizer will deploy and execute them in the isolated environment

---

## Authentication & Security

### Agent Tool Server API

To help participants get started quickly, we provide access to an online Agent Tool API with two locations. 
```
- Hong Kong & Others: 124.71.227.61
- China: 120.46.145.77
```


### Token Authentication

All API requests must include a Bearer Token:

```
Authorization: ${Token}
```

Token type is **READ permission**, only allowing calls to the `/api/agent/execute` endpoint.

### Security Measures

| Measure | Implementation |
|---------|---------------|
| Access Authentication | Bearer Token validation |
| Rate Limiting | Nginx rate limit: 50 req/s per IP |
| Daily Quota | 1,000 calls per participant per day (Phase 1 only) |
| Concurrency Limit | Max 2 concurrent per participant |
| Network Isolation | Backends have no public IP; only the router is exposed |
| Fault Isolation | Backend failures are automatically circuit-broken; no impact on other nodes |

---

## API Reference

### Request

```
POST /api/agent/execute
Content-Type: application/json
Authorization: Bearer ${Token}

{
    "device_name": "BoardLeaf1",
    "command": "display ip routing-table"
}
```

### Response

**Success (200):**
```json
{
    "status": "success",
    "device_name": "BoardLeaf1",
    "vendor": "huawei",
    "command_executed": "display ip routing-table",
    "result": "<BoardLeaf1> display ip routing-table\n..."
}
```

**Command Syntax Error (422):**
```json
{
    "status": "execution_failed",
    "device_name": "BoardLeaf1",
    "vendor": "huawei",
    "command_executed": "display ip rout",
    "result": "<BoardLeaf1> display ip rout\n                              ^\nError: Incomplete command found at '^' position."
}
```

**Device Not Found (404):**
```json
{
    "error": "Device 'UnknownDevice' not found"
}
```

---

## Available Device Commands

This section provides a comprehensive reference of all network device commands available for interacting with the Agent Tool Server. Commands are organized by vendor and device type, covering routers, switches, and firewalls from **Huawei (VRP)**, **Cisco (IOS/IOS-XE/NX-OS)**, and **H3C (Comware)**.

### Supported Vendors & Device Types

| Vendor | Routers | Switches | Firewalls |
|--------|---------|----------|-----------|
| Huawei (VRP) | Supported | Supported | Supported |
| Cisco (IOS/IOS-XE/NX-OS) | Supported | Supported | Supported |
| H3C (Comware) | Supported | Supported | N/A |

### Placeholder Notation

| Placeholder | Meaning |
|-------------|---------|
| `[x]` | Port name (e.g., `GigabitEthernet0/0/1`) |
| `[id]` | Interface ID |
| `[xxx]` | VRF or VPN instance name |
| `[type] [num]` | Interface type and number (e.g., `GigabitEthernet 1/0/1`) |

> Replace placeholders with actual values from your network topology when calling commands via the API.

---

### 1. Configuration & Logging

| Function | Huawei (All) | Cisco Router | Cisco Switch | Cisco FW | H3C Router | H3C Switch |
|----------|-------------|--------------|--------------|----------|------------|------------|
| View current configuration | `display current-configuration` | `show running-config` | `show running-config` | `show running-config` | `display current-configuration` | `display current-configuration` |
| View log buffer | `display logbuffer` | `show logging` | `show logging` | `show logging` | `display logbuffer` | `display logbuffer` |

### 2. Alarms & Monitoring

| Function | Huawei (All) | Cisco Router | Cisco Switch | Cisco FW | H3C Router | H3C Switch |
|----------|-------------|--------------|--------------|----------|------------|------------|
| Active alarms | `display alarm active` | `show facility-alarm status` | N/A | N/A | `display alarm active` | `display alarm` |
| Memory usage | `display memory-usage` | `show processes memory` | `show processes memory` | `show processes memory` | `display memory` | `display memory` |

### 3. Interface & Link Status

| Function | Huawei (All) | Cisco Router | Cisco Switch | Cisco FW | H3C Router | H3C Switch |
|----------|-------------|--------------|--------------|----------|------------|------------|
| LLDP neighbor summary | `display lldp neighbor brief` | `show lldp neighbors` | `show lldp neighbors` | N/A | `display lldp neighbor-information` | `display lldp neighbor-information` |
| Interface brief status | `display interface brief` | `show ip interface brief` | `show interface brief` | `show interface summary` | `display interface brief` | `display interface brief` |
| Interface description | `display interface description` | `show interface description` | `show interface description` | N/A | N/A | N/A |
| Link aggregation (Eth-Trunk) | `display eth-trunk` | `show etherchannel summary` | N/A | N/A | `display link-aggregation summary` | N/A |
| IP interface brief | `display ip interface brief` | `show ip interface brief` | `show ip interface brief` | `show interface ip brief` | `display ip interface brief` | `display ip interface brief` |
| IPv6 interface | `display ipv6 interface [x]` | `show ipv6 interface [type] [num]` | N/A | N/A | `display ipv6 interface [type] [num]` | N/A |

### 4. Layer 2 (VLAN, MAC, STP)

| Function | Huawei (All) | Cisco Router | Cisco Switch | Cisco FW | H3C Router | H3C Switch |
|----------|-------------|--------------|--------------|----------|------------|------------|
| VLAN status | `display vlan` | `show vlans` | `show vlan` | `show vlan` | `display vlan` | `display vlan` |
| MAC address table | `display mac-address` | N/A | `show mac address-table` | `show mac-address-table` | `display mac-address` | `display mac-address` |
| STP summary | `display stp brief` | `show spanning-tree summary` | `show spanning-tree summary` | N/A | N/A | `display stp brief` |
| STP interface state | `display stp interface [x]` | `show spanning-tree interface [id]` | N/A | N/A | `display stp interface brief` | N/A |

### 5. Address Resolution & Neighbor Discovery

| Function | Huawei (All) | Cisco Router | Cisco Switch | Cisco FW | H3C Router | H3C Switch |
|----------|-------------|--------------|--------------|----------|------------|------------|
| ARP table | `display arp all` (Router)<br/>`display arp` (Switch/FW) | `show ip arp` | `show ip arp` | `show arp` | `display arp all` | `display arp all` |
| IPv6 neighbors | `display ipv6 neighbors` | `show ipv6 neighbors` | `show ipv neighbor` | `show ipv6 neighbor` | `display ipv6 neighbors` | `display ipv6 neighbor all` |

### 6. Routing

| Function | Huawei (All) | Cisco Router | Cisco Switch | Cisco FW | H3C Router | H3C Switch |
|----------|-------------|--------------|--------------|----------|------------|------------|
| IPv4 routing table | `display ip routing-table` | `show ip route` | `show ip route` | `show route` | `display ip routing-table` | `display ip routing-table` |
| VPN instance routing table | `display ip routing-table vpn-instance [x]` | `show ip route vrf [xxx]` | N/A | N/A | `display ip routing-table vpn-instance [xxx]` | N/A |
| IPv6 routing table | `display ipv6 routing-table` | `show ipv6 route` | `show ipv6 route` | `show ipv6 route` | `display ipv6 routing-table` | `display ipv6 routing-table` |

### 7. OSPF

| Function | Huawei (All) | Cisco Router | Cisco Switch | Cisco FW | H3C Router | H3C Switch |
|----------|-------------|--------------|--------------|----------|------------|------------|
| OSPF neighbor state | `display ospf peer` | `show ip ospf neighbor` | `show ip ospf neighbors` | `show ospf neighbor` | `display ospf peer` | `display ospf peer` |
| OSPF internal routes | `display ospf routing` | `show ip route ospf` | `show ip ospf route` | `show route ospf` | `display ospf routing` | `display ospf routing` |
| OSPF LSDB | `display ospf lsdb` | `show ip ospf database` | `show ip ospf database` | `show ospf database` | `display ospf lsdb` | `display ospf lsdb` |

### 8. BGP

| Function | Huawei (All) | Cisco Router | Cisco Switch | Cisco FW | H3C Router | H3C Switch |
|----------|-------------|--------------|--------------|----------|------------|------------|
| BGP EVPN routes | `display bgp evpn all routing-table` | `show bgp l2vpn evpn` | N/A | N/A | `display bgp l2vpn evpn` | `display bgp l2vpn evpn` |
| BGP VPNv4 routes | `display bgp vpnv4 all routing-table` | `show bgp vpnv4 unicast all` | N/A | N/A | `display bgp vpnv4 all routing-table` | `display bgp routing-table vpnv4` |

### 9. VXLAN

| Function | Huawei (All) | Cisco Router | Cisco Switch | Cisco FW | H3C Router | H3C Switch |
|----------|-------------|--------------|--------------|----------|------------|------------|
| VXLAN tunnel status | `display vxlan tunnel` | `show nve vni`<br/>`show nve peers` | N/A | `show nve` | `display vxlan tunnel` | `display vxlan tunnel` |
| VXLAN troubleshooting | `display vxlan troubleshooting` | `show nve [detailed debugs]` | N/A | N/A | `display vxlan troubleshooting` | N/A |

### 10. High Availability & Forwarding

| Function | Huawei (All) | Cisco Router | Cisco Switch | Cisco FW | H3C Router | H3C Switch |
|----------|-------------|--------------|--------------|----------|------------|------------|
| VRRP verbose state | `display vrrp verbose` | `show vrrp detail` | N/A | N/A | `display vrrp verbose` | N/A |
| BFD session state | `display bfd session all` | `show bfd neighbors` | `show bfd neighbors` | `show bfd neighbors` | `display bfd session` | `display bfd session` |

### 11. DHCP

| Function | Huawei (All) | Cisco Router | Cisco Switch | Cisco FW | H3C Router | H3C Switch |
|----------|-------------|--------------|--------------|----------|------------|------------|
| DHCP address pool | `display ip pool` | `show ip dhcp pool` | N/A | `show ip local pool [x]` | `display ip pool` | `display ip pool` |

### 12. SRv6 (Segment Routing over IPv6)

| Function | Huawei (All) | Cisco Router | Cisco Switch | Cisco FW | H3C Router | H3C Switch |
|----------|-------------|--------------|--------------|----------|------------|------------|
| SRv6 Policy status | `display srv6-te policy status` | `show segment-routing srv6 policy` | N/A | N/A | `display segment-routing ipv6 te policy` | N/A |
| SRv6 Policy details | `display srv6-te policy` | N/A | N/A | N/A | `display segment-routing ipv6 te policy` | N/A |
| SRv6 End forwarding info | `display segment-routing ipv6 local-sid end forwarding` | N/A | N/A | N/A | `display segment-routing ipv6 local-sid` | N/A |
| SRv6 End.X forwarding info | `display segment-routing ipv6 local-sid end-x forwarding` | N/A | N/A | N/A | `display segment-routing ipv6 local-sid` | N/A |

---

### Quick Command Reference by Vendor

Below are consolidated command lists grouped by vendor for quick reference when building your Agent's tool-calling logic.

<details>
<summary><strong>Huawei (VRP) - All Device Types</strong></summary>

```
# Configuration & Logging
display current-configuration
display logbuffer

# Monitoring
display alarm active
display memory-usage

# Interface & Link
display lldp neighbor brief
display interface brief
display interface description
display eth-trunk
display ip interface brief
display ipv6 interface [x]

# Layer 2
display vlan
display mac-address
display stp brief
display stp interface [x]

# Address Resolution
display arp all          # Router; use "display arp" on Switch/Firewall
display ipv6 neighbors

# Routing
display ip routing-table
display ip routing-table vpn-instance [x]
display ipv6 routing-table

# OSPF
display ospf peer
display ospf routing
display ospf lsdb

# BGP
display bgp evpn all routing-table
display bgp vpnv4 all routing-table

# VXLAN
display vxlan tunnel
display vxlan troubleshooting

# HA & Forwarding
display vrrp verbose
display bfd session all

# DHCP
display ip pool

# SRv6
display srv6-te policy status
display srv6-te policy
display segment-routing ipv6 local-sid end forwarding
display segment-routing ipv6 local-sid end-x forwarding
```

</details>

<details>
<summary><strong>Cisco (IOS/IOS-XE/NX-OS) - Router</strong></summary>

```
# Configuration & Logging
show running-config
show logging

# Monitoring
show facility-alarm status
show processes memory

# Interface & Link
show lldp neighbors
show ip interface brief
show interface description
show etherchannel summary
show ipv6 interface [type] [num]

# Layer 2
show vlans
show spanning-tree summary
show spanning-tree interface [id]
show ip arp
show ipv6 neighbors

# Routing
show ip route
show ip route vrf [xxx]
show ipv6 route

# OSPF
show ip ospf neighbor
show ip route ospf
show ip ospf database

# BGP
show bgp l2vpn evpn
show bgp vpnv4 unicast all

# VXLAN
show nve vni
show nve peers
show nve [detailed debugs]

# HA & Forwarding
show vrrp detail
show bfd neighbors

# DHCP
show ip dhcp pool

# SRv6
show segment-routing srv6 policy
```

</details>

<details>
<summary><strong>Cisco (IOS/IOS-XE/NX-OS) - Switch</strong></summary>

```
# Configuration & Logging
show running-config
show logging

# Monitoring
show processes memory

# Interface & Link
show lldp neighbors
show interface brief
show ip interface brief

# Layer 2
show vlan
show mac address-table
show spanning-tree summary
show ip arp
show ipv neighbor

# Routing
show ip route
show ipv6 route

# OSPF
show ip ospf neighbors
show ip ospf route
show ip ospf database

# HA & Forwarding
show bfd neighbors

# DHCP
show ip dhcp pool
```

</details>

<details>
<summary><strong>Cisco (IOS/IOS-XE/NX-OS) - Firewall</strong></summary>

```
# Configuration & Logging
show running-config
show logging

# Monitoring
show processes memory

# Interface & Link
show interface summary
show interface ip brief

# Layer 2
show vlan
show mac-address-table
show arp
show ipv6 neighbor

# Routing
show route
show ipv6 route

# OSPF
show ospf neighbor
show route ospf
show ospf database

# VXLAN
show nve

# DHCP
show ip local pool [x]
```

</details>

<details>
<summary><strong>H3C (Comware) - Router</strong></summary>

```
# Configuration & Logging
display current-configuration
display logbuffer

# Monitoring
display alarm active
display memory

# Interface & Link
display lldp neighbor-information
display interface brief
display ip interface brief
display ipv6 interface [type] [num]

# Layer 2
display vlan
display mac-address
display stp brief
display arp all
display ipv6 neighbors

# Routing
display ip routing-table
display ip routing-table vpn-instance [xxx]
display ipv6 routing-table

# OSPF
display ospf peer
display ospf routing
display ospf lsdb

# BGP
display bgp l2vpn evpn
display bgp vpnv4 all routing-table

# VXLAN
display vxlan tunnel
display vxlan troubleshooting

# HA & Forwarding
display vrrp verbose
display bfd session

# DHCP
display ip pool

# SRv6
display segment-routing ipv6 te policy
display segment-routing ipv6 local-sid
```

</details>

<details>
<summary><strong>H3C (Comware) - Switch</strong></summary>

```
# Configuration & Logging
display current-configuration
display logbuffer

# Monitoring
display alarm
display memory

# Interface & Link
display lldp neighbor-information
display interface brief
display ip interface brief

# Layer 2
display vlan
display mac-address
display stp brief
display arp all
display ipv6 neighbor all

# Routing
display ip routing-table
display ipv6 routing-table

# OSPF
display ospf peer
display ospf routing
display ospf lsdb

# BGP
display bgp l2vpn evpn
display bgp routing-table vpnv4

# VXLAN
display vxlan tunnel

# HA & Forwarding
display bfd session

# DHCP
display ip pool
```

</details>

---

### Important Notes

- Commands marked as **N/A** are not supported on that vendor/device combination. Attempting to use them will result in a command syntax error (HTTP 422).
- **Placeholder values** in brackets (e.g., `[x]`, `[xxx]`) must be replaced with actual interface names, VRF/VPN instance names, or interface types/numbers appropriate for your network topology.
- On **Cisco NX-OS switches**, certain features (e.g., NVE/VXLAN) require activation via `configure terminal` followed by the appropriate `feature` command before the related `show` commands become available.
- The Agent Tool Server faithfully reproduces vendor-level syntax errors including **incomplete**, **unrecognized**, **ambiguous**, and **wrong parameter** errors (HTTP 422). Use this to validate your Agent's error handling.
---

## Participant Guide

### Environment Requirements

- Participants run Agent **locally** (Phase 1 / Phase 2)
- Agent calls the remote Agent Tool Server via HTTP
- No need to deploy the server locally (but a fallback option is provided)

### Model Rules

1. **Base Model:** The entire competition (Phase 1 / 2 / 3) uses **Qwen3.5-35B-A3B** as the base model
2. **Fine-tuning Allowed:** Participants may fine-tune Qwen3.5-35B-A3B (LoRA, full fine-tuning, etc.)
3. **No Replacement:** Replacing it with a different architecture or parameter scale is not allowed; final inference must be based on Qwen3.5-35B-A3B
4. **Phase 3 Submission:** For Phase 3, the organizer deploys the base model on GPU instances; participants only need to submit their fine-tuned weights

### API Call Rules

1. **Sequential Calls:** When solving a single problem, the Agent must call tools sequentially; no concurrent calls within a problem
2. **Concurrency Limit:** Each participant may run at most 2 tasks simultaneously (2 problems in parallel)
3. **Daily Quota:** Max 1,000 API calls per day (Phase 1 only; Phase 2 and Phase 3 are not subject to this limit)
4. **Authentication:** Every request must include the Authorization header

### Local Server Deployment

If server access issues occur, participants may deploy the Agent Tool Server locally:

1. First, unzip `devices_outputs.zip` inside the same directory
2. Then, run `python server.py` to deploy the local server.
3. An example agent workflow is provide in `agent/` folder.

After local deployment, change the Agent's target URL to `http://localhost:7860/api/agent/execute`; no Token required.

---

## Evaluation Metrics & Scoring

Each phase uses different evaluation criteria, progressively increasing in rigor:

### Scoring by Phase

| Phase | Primary Metric | Secondary Metric | Description |
|-------|---------------|-----------------|-------------|
| **Phase 1** | Accuracy | — | Scored by accuracy only |
| **Phase 2** | Accuracy | API Call Count | Accuracy first; ties broken by fewer API calls on correct problems |
| **Phase 3** | Accuracy + Speed | — | Correctness and time-based scoring (see table below) |

### Phase 3: Detailed Scoring Standards

- **Pass@1 (Consistency Metric):** Rewards agents with high success rates across 4 independent trials to ensure solution robustness.
- **TTS (Time To Solve):** Measures efficiency in pinpointing and fixing faults via logical deduction.
- **Execution Guardrail:** A strict 15-minute cutoff is implemented to prevent infinite loops and resource exhaustion.

Points are awarded only if the task is completed correctly within the allotted time. We will select the fastest solution in 4 generations. The faster the resolution, the higher the score:

| Answering time            | Discount |
| ------------------------- | -------- |
| `< 5 minutes`             | 100%     |
| `5 minutes  - 10 minutes` | 80%      |
| `10 minutes - 15 minutes` | 60%      |
| `> 15 minutes`            | 0%       |

---

## Quick Start: Running the Agent with OpenClaw

The `agent/` directory provides a ready-to-use agent solution based on **OpenClaw** (an open-source agentic framework). By combining the pre-configured skills, OpenClaw configuration files, and the batch evaluation script, participants can quickly launch an agent to solve CTBench problems locally.

### Prerequisites

1. **Clone and install OpenClaw** from its open-source repository, and ensure it runs locally (refer to the OpenClaw official documentation for installation steps).
2. **Python 3.8+** and **Node.js** installed.
3. **Agent Tool Server** running locally at `http://127.0.0.1:7860` (or the remote server with a valid Token).

### Directory Structure

```
agent/
├── openclaw_config/          # OpenClaw configuration files
│   ├── IDENTITY.md           # Agent identity definition (name, persona)
│   ├── SOUL.md               # Code of conduct & core principles
│   ├── USER.md               # Competition scenario & requirements
│   ├── AGENTS.md             # Agent coordination settings
│   └── TOOLS.md              # Available tools & NOC API conventions
├── skills/                   # Skill definitions for the agent
│   ├── infra_maintenance/    # Infrastructure maintenance (config/log/alarm/memory/LLDP)
│   ├── l2_link/              # Layer 2 link O&M (interface/VLAN/MAC/STP)
│   ├── l3_route/             # Layer 3 routing (IP/ARP/OSPF/BGP)
│   └── adv_tunnel/           # Advanced tunnels (VXLAN/VRRP/BFD/DHCP/SRv6)
├── evaluate_openclaw.py      # Batch evaluation script
├── evaluate_openclaw_guideline.md  # Detailed usage guide for the evaluation script
└── requirements.txt          # Python dependencies
```

### Configuration

1. **Copy the `openclaw_config/` files** into your local OpenClaw project's configuration directory (or symlink them) so that OpenClaw loads the agent identity, tools, and skills at startup.

2. **Copy the `skills/` directory** into your local OpenClaw project's skills directory so that the four network O&M skills (`infra_maintenance`, `l2_link`, `l3_route`, `adv_tunnel`) are available to the agent.

3. **Edit `evaluate_openclaw.py`** and set the following paths at the top of the file:

   ```python
   # Set to the absolute path of your local OpenClaw project directory
   OPENCLAW_DIR = r"C:\path\to\your\openclaw"

   # Set to the absolute path where OpenClaw stores session logs
   OPENCLAW_SESSION_DIR = r"C:\Users\YourUser\.openclaw\agents\main\sessions"
   ```

### Running the Agent

```bash
# Install Python dependencies
pip install -r agent/requirements.txt

# Run all questions from the input JSON
python agent/evaluate_openclaw.py -i data/Phase_1/test.json

# Run specific questions only
python agent/evaluate_openclaw.py -i data/Phase_1/test.json --questions 1,2,5

# Run with concurrency (max 2 for competition compliance)
python agent/evaluate_openclaw.py -i data/Phase_1/test.json --concurrency 2

# Resume from an interrupted run
python agent/evaluate_openclaw.py -i data/Phase_1/test.json --resume
```

### How It Works

1. **`evaluate_openclaw.py`** loads questions from the input JSON file, then invokes the locally running OpenClaw agent for each question.
2. The OpenClaw agent, guided by `openclaw_config/` (identity, tools, and behavioral rules), uses the four **skills** to collect device data via the API (`http://127.0.0.1:7860/api/agent/execute`).
3. The agent analyzes the collected data and produces a final answer.
4. The script extracts the answer from the OpenClaw session log and writes results to `agent/eval_results/result.csv`.

### Output

Results are saved under `agent/eval_results/`:

| File | Description |
|------|-------------|
| `result.csv` | Final answers (`id`, `prediction`) — the file to submit |
| `eval_detail.jsonl` | Detailed execution logs per question |
| `progress.json` | Progress tracking for the `--resume` feature |

For more details on the evaluation script, see [`agent/evaluate_openclaw_guideline.md`](agent/evaluate_openclaw_guideline.md).


# 赛道B：电信网络故障排查与优化智能体挑战赛
## 竞赛概述
本任务聚焦**IP网络运维**领域。参赛选手需构建智能体，通过调用智能体工具服务器提供的**CLI仿真接口**，完成IP网络故障诊断与排查任务。

**基座模型**：竞赛全程（阶段1/2/3）统一使用 **Qwen3.5-35B-A3B** 作为基座模型。选手可对模型进行微调（LoRA、全量微调等），但**禁止替换为其他网络架构或不同参数量级的模型**。

### 服务器核心能力
- 仿真网络设备（华为/思科/华三）CLI交互
- 支持45+类命令的正则白名单校验
- 精准复现厂商级语法错误（命令不完整/无法识别/存在歧义/参数错误）
- 输出多种命令结果文件，涵盖路由表、BGP、VXLAN、SRv6等协议

---

## 竞赛设计
### 赛程总览
| 阶段 | 阶段名称 | 时间 | 目标 | 题目规模与要求 | 选手操作 |
|------|--------|------|------|--------------|---------|
| 阶段1 | 公开练习赛 | 4月3日–5月4日 | 调试智能体，熟悉API | 50题 / 多厂商 / 高级协议 | 本地运行，提交result.csv |
| 阶段2 | 淘汰赛 | 5月4日–5月18日 | 选拔晋级阶段3的队伍 | 100题 / 多厂商 / 高级协议 | 本地运行，仅可提交1次，上传执行日志与result.csv |
| 阶段3 | 总决赛 | 5月18日–5月29日 | 最终排名 | 70题 / 多厂商 / 高级协议 | 服务器端Docker自动执行 |

### 题目详细分布
| 阶段 | 题目构成 | 任务类型 | 涉及协议（示例，非全部） | 设备厂商 |
|------|---------|---------|----------------------|---------|
| 阶段1 | 32节点金融网 & 22节点云计算网（共50题） | 拓扑重构、路径查询、故障定位 | LLDP、OSPF、VXLAN | 多厂商混合 |
| 阶段2 | 40节点园区网（100题） | 拓扑重构、路径查询、故障定位 | VLAN、VRRP、MP-BGP | 多厂商混合 |
| 阶段3 | 64节点金融网（70题） | 拓扑重构、路径查询、故障定位 | VXLAN、EVPN、SRv6、ISIS、BGP | 多厂商混合 |

---

## 各阶段详细规则
### 阶段1（公开练习赛）
- 题目数量：50题
- 运行环境：选手本地运行智能体
- 基座模型：Qwen3.5-35B-A3B（可微调）
- API调用限制：每位选手每日最多调用1000次API（仅阶段1有此日限额，阶段2、3无限制）
- 评分规则：选手提交result.csv，**仅以准确率评分**（阶段1唯一评估指标）
- 工具调用规则：
  - 单个题目内智能体必须**串行调用工具**，不允许并发调用
  - 选手最大并发数为2（最多同时处理2道题）
- 上手支持：提供服务器源码与本地部署指南，方便选手本地部署

### 阶段2（淘汰赛）
- 题目数量：100题（每3天分批发布20题）
- 基座模型：Qwen3.5-35B-A3B（可微调）
- 提交限制：每位选手仅允许提交3次，必须上传执行日志至服务器；无每日API限额，但需保证至少一次完整运行成功
- 评分规则：
  - 主指标：准确率
  - 准确率相同时，以**正确题目所使用的API调用次数**为次指标（次数越少排名越高）
- 晋级机制：选手预约提交时段，每条赛道前30名晋级总决赛
- 考察重点：智能体在多厂商环境下的泛化能力与一次性执行稳定性

### 阶段3（总决赛）
- 题目数量：70题
- 参赛队伍：阶段2选拔出的前30名
- 运行环境：主办方提供GPU资源 + 隔离Docker环境
- 基座模型：Qwen3.5-35B-A3B（可微调）
- 时间限制：必须在24小时内完成
- 网络数据：使用与阶段1/2不同的网络数据
- 考察重点：复杂协议推理（SRv6/EVPN）与大规模网络（64节点）深度故障隔离能力

#### 资源分配
- GPU资源：华为云GPU实例，独立部署基座模型
- 智能体工具服务器：部署于HuggingFace免费CPU资源（24小时内免费）
- 基座模型：由主办方统一部署至各选手GPU实例
- 提交要求：选手需上传微调后模型权重与智能体代码，由主办方在隔离环境中部署执行

---

## 认证与安全
### 智能体工具服务器API
为方便选手快速上手，提供两地在线智能体工具API：
- 中国香港及其他地区：124.71.227.61
- 中国大陆：120.46.145.77

### Token认证
所有API请求必须携带Bearer Token：
```
Authorization: ${Token}
```
Token为只读权限，仅允许调用 `/api/agent/execute` 接口。

### 安全措施
| 安全措施 | 实现方式 |
|---------|---------|
| 访问认证 | Bearer Token校验 |
| 请求限流 | Nginx限流：单IP每秒50次请求 |
| 每日限额 | 选手每日1000次调用（仅阶段1） |
| 并发限制 | 单选手最大并发2个任务 |
| 网络隔离 | 后端无公网IP，仅暴露路由 |
| 故障隔离 | 后端故障自动熔断，不影响其他节点 |

---

## API参考
### 请求
```http
POST /api/agent/execute
Content-Type: application/json
Authorization: Bearer ${Token}

{
    "device_name": "BoardLeaf1",
    "command": "display ip routing-table"
}
```

### 响应
- 成功（200）
```json
{
    "status": "success",
    "device_name": "BoardLeaf1",
    "vendor": "huawei",
    "command_executed": "display ip routing-table",
    "result": "<BoardLeaf1> display ip routing-table\n..."
}
```

- 命令语法错误（422）
```json
{
    "status": "execution_failed",
    "device_name": "BoardLeaf1",
    "vendor": "huawei",
    "command_executed": "display ip rout",
    "result": "<BoardLeaf1> display ip rout\n                              ^\nError: Incomplete command found at '^' position."
}
```

- 设备不存在（404）
```json
{
    "error": "Device 'UnknownDevice' not found"
}
```

---

## 可用设备命令
本节提供智能体工具服务器支持的所有网络设备命令参考，按厂商与设备类型分类，涵盖华为（VRP）、思科（IOS/IOS-XE/NX-OS）、华三（Comware）的路由器、交换机与防火墙。

### 支持厂商与设备类型
| 厂商 | 路由器 | 交换机 | 防火墙 |
|------|-------|-------|-------|
| 华为（VRP） | 支持 | 支持 | 支持 |
| 思科（IOS/IOS-XE/NX-OS） | 支持 | 支持 | 支持 |
| 华三（Comware） | 支持 | 支持 | 不支持 |

### 占位符说明
| 占位符 | 含义 |
|-------|------|
| [x] | 端口名称（如GigabitEthernet0/0/1） |
| [id] | 接口编号 |
| [xxx] | VRF或VPN实例名称 |
| [type] [num] | 接口类型与编号（如GigabitEthernet 1/0/1） |

通过API调用命令时，需根据网络拓扑将占位符替换为实际值。

### 命令速查表（按功能分类）
#### 1. 配置与日志
| 功能 | 华为（全系列） | 思科路由器 | 思科交换机 | 思科防火墙 | 华三路由器 | 华三交换机 |
|------|--------------|-----------|-----------|-----------|-----------|-----------|
| 查看当前配置 | display current-configuration | show running-config | show running-config | show running-config | display current-configuration | display current-configuration |
| 查看日志缓冲区 | display logbuffer | show logging | show logging | show logging | display logbuffer | display logbuffer |

#### 2. 告警与监控
| 功能 | 华为（全系列） | 思科路由器 | 思科交换机 | 思科防火墙 | 华三路由器 | 华三交换机 |
|------|--------------|-----------|-----------|-----------|-----------|-----------|
| 活动告警 | display alarm active | show facility-alarm status | 不支持 | 不支持 | display alarm active | display alarm |
| 内存使用率 | display memory-usage | show processes memory | show processes memory | show processes memory | display memory | display memory |

#### 3. 接口与链路状态
| 功能 | 华为（全系列） | 思科路由器 | 思科交换机 | 思科防火墙 | 华三路由器 | 华三交换机 |
|------|--------------|-----------|-----------|-----------|-----------|-----------|
| LLDP邻居概要 | display lldp neighbor brief | show lldp neighbors | show lldp neighbors | 不支持 | display lldp neighbor-information | display lldp neighbor-information |
| 接口概要状态 | display interface brief | show ip interface brief | show interface brief | show interface summary | display interface brief | display interface brief |
| 接口描述 | display interface description | show interface description | show interface description | 不支持 | 不支持 | 不支持 |
| 链路聚合 | display eth-trunk | show etherchannel summary | 不支持 | 不支持 | display link-aggregation summary | 不支持 |
| IP接口概要 | display ip interface brief | show ip interface brief | show ip interface brief | show interface ip brief | display ip interface brief | display ip interface brief |
| IPv6接口 | display ipv6 interface [x] | show ipv6 interface [type] [num] | 不支持 | 不支持 | display ipv6 interface [type] [num] | 不支持 |

#### 4. 二层（VLAN、MAC、STP）
| 功能 | 华为（全系列） | 思科路由器 | 思科交换机 | 思科防火墙 | 华三路由器 | 华三交换机 |
|------|--------------|-----------|-----------|-----------|-----------|-----------|
| VLAN状态 | display vlan | show vlans | show vlan | show vlan | display vlan | display vlan |
| MAC地址表 | display mac-address | 不支持 | show mac address-table | show mac-address-table | display mac-address | display mac-address |
| STP概要 | display stp brief | show spanning-tree summary | show spanning-tree summary | 不支持 | 不支持 | display stp brief |
| STP接口状态 | display stp interface [x] | show spanning-tree interface [id] | 不支持 | 不支持 | display stp interface brief | 不支持 |

#### 5. 地址解析与邻居发现
| 功能 | 华为（全系列） | 思科路由器 | 思科交换机 | 思科防火墙 | 华三路由器 | 华三交换机 |
|------|--------------|-----------|-----------|-----------|-----------|-----------|
| ARP表 | display arp all（路由器）<br>display arp（交换机/防火墙） | show ip arp | show ip arp | show arp | display arp all | display arp all |
| IPv6邻居 | display ipv6 neighbors | show ipv6 neighbors | show ipv neighbor | show ipv6 neighbor | display ipv6 neighbors | display ipv6 neighbor all |

#### 6. 路由
| 功能 | 华为（全系列） | 思科路由器 | 思科交换机 | 思科防火墙 | 华三路由器 | 华三交换机 |
|------|--------------|-----------|-----------|-----------|-----------|-----------|
| IPv4路由表 | display ip routing-table | show ip route | show ip route | show route | display ip routing-table | display ip routing-table |
| VPN实例路由表 | display ip routing-table vpn-instance [x] | show ip route vrf [xxx] | 不支持 | 不支持 | display ip routing-table vpn-instance [xxx] | 不支持 |
| IPv6路由表 | display ipv6 routing-table | show ipv6 route | show ipv6 route | show ipv6 route | display ipv6 routing-table | display ipv6 routing-table |

#### 7. OSPF
| 功能 | 华为（全系列） | 思科路由器 | 思科交换机 | 思科防火墙 | 华三路由器 | 华三交换机 |
|------|--------------|-----------|-----------|-----------|-----------|-----------|
| OSPF邻居状态 | display ospf peer | show ip ospf neighbor | show ip ospf neighbors | show ospf neighbor | display ospf peer | display ospf peer |
| OSPF内部路由 | display ospf routing | show ip route ospf | show ip ospf route | show route ospf | display ospf routing | display ospf routing |
| OSPF链路状态数据库 | display ospf lsdb | show ip ospf database | show ip ospf database | show ospf database | display ospf lsdb | display ospf lsdb |

#### 8. BGP
| 功能 | 华为（全系列） | 思科路由器 | 思科交换机 | 思科防火墙 | 华三路由器 | 华三交换机 |
|------|--------------|-----------|-----------|-----------|-----------|-----------|
| BGP EVPN路由 | display bgp evpn all routing-table | show bgp l2vpn evpn | 不支持 | 不支持 | display bgp l2vpn evpn | display bgp l2vpn evpn |
| BGP VPNv4路由 | display bgp vpnv4 all routing-table | show bgp vpnv4 unicast all | 不支持 | 不支持 | display bgp vpnv4 all routing-table | display bgp routing-table vpnv4 |

#### 9. VXLAN
| 功能 | 华为（全系列） | 思科路由器 | 思科交换机 | 思科防火墙 | 华三路由器 | 华三交换机 |
|------|--------------|-----------|-----------|-----------|-----------|-----------|
| VXLAN隧道状态 | display vxlan tunnel | show nve vni<br>show nve peers | 不支持 | show nve | display vxlan tunnel | display vxlan tunnel |
| VXLAN故障排查 | display vxlan troubleshooting | show nve [detailed debugs] | 不支持 | 不支持 | display vxlan troubleshooting | 不支持 |

#### 10. 高可用与转发
| 功能 | 华为（全系列） | 思科路由器 | 思科交换机 | 思科防火墙 | 华三路由器 | 华三交换机 |
|------|--------------|-----------|-----------|-----------|-----------|-----------|
| VRRP详细状态 | display vrrp verbose | show vrrp detail | 不支持 | 不支持 | display vrrp verbose | 不支持 |
| BFD会话状态 | display bfd session all | show bfd neighbors | show bfd neighbors | show bfd neighbors | display bfd session | display bfd session |

#### 11. DHCP
| 功能 | 华为（全系列） | 思科路由器 | 思科交换机 | 思科防火墙 | 华三路由器 | 华三交换机 |
|------|--------------|-----------|-----------|-----------|-----------|-----------|
| DHCP地址池 | display ip pool | show ip dhcp pool | 不支持 | show ip local pool [x] | display ip pool | display ip pool |

#### 12. SRv6（IPv6分段路由）
| 功能 | 华为（全系列） | 思科路由器 | 思科交换机 | 思科防火墙 | 华三路由器 | 华三交换机 |
|------|--------------|-----------|-----------|-----------|-----------|-----------|
| SRv6策略状态 | display srv6-te policy status | show segment-routing srv6 policy | 不支持 | 不支持 | display segment-routing ipv6 te policy | 不支持 |
| SRv6策略详情 | display srv6-te policy | 不支持 | 不支持 | 不支持 | display segment-routing ipv6 te policy | 不支持 |
| SRv6 End转发信息 | display segment-routing ipv6 local-sid end forwarding | 不支持 | 不支持 | 不支持 | display segment-routing ipv6 local-sid | 不支持 |
| SRv6 End.X转发信息 | display segment-routing ipv6 local-sid end-x forwarding | 不支持 | 不支持 | 不支持 | display segment-routing ipv6 local-sid | 不支持 |

### 按厂商快速命令参考
- 华为（VRP）- 全设备类型
- 思科（IOS/IOS-XE/NX-OS）- 路由器
- 思科（IOS/IOS-XE/NX-OS）- 交换机
- 思科（IOS/IOS-XE/NX-OS）- 防火墙
- 华三（Comware）- 路由器
- 华三（Comware）- 交换机

### 重要说明
- 标注为**N/A**的命令在对应厂商/设备上不支持，调用将返回语法错误（HTTP 422）
- 方括号内占位符需替换为拓扑中实际接口名、VRF/VPN实例名等
- 思科NX-OS交换机部分功能（如NVE/VXLAN）需先在配置模式下启用，对应show命令才可用
- 工具服务器会精准复现厂商级语法错误，可用于验证智能体异常处理能力

---

## 选手指南
### 环境要求
- 阶段1/2：选手本地运行智能体
- 智能体通过HTTP调用远程工具服务器
- 无需本地部署服务器（但提供备选方案）

### 模型规则
- 基座模型：全程使用Qwen3.5-35B-A3B
- 允许微调：LoRA、全量微调等均可
- 禁止替换：不得更换模型架构或参数量，最终推理必须基于该基座模型
- 阶段3提交：主办方统一部署基座模型，选手仅需提交微调权重

### API调用规则
- 串行调用：单题目内工具必须串行调用，不允许并发
- 并发限制：单选手最多同时运行2个任务
- 每日限额：每日最多1000次调用（仅阶段1）
- 认证要求：所有请求必须携带Authorization请求头

### 本地服务器部署
若远程服务器访问异常，选手可本地部署工具服务器：
1. 将`devices_outputs.zip`解压至同目录
2. 运行`python server.py`启动本地服务
3. 智能体目标URL改为`http://localhost:7860/api/agent/execute`，无需Token

`agent/`目录提供示例智能体工作流。

---

## 评估指标与评分
各阶段评估标准逐步严格：

### 分阶段评分
| 阶段 | 主指标 | 次指标 | 说明 |
|------|-------|-------|------|
| 阶段1 | 准确率 | — | 仅按准确率评分 |
| 阶段2 | 准确率 | API调用次数 | 准确率优先，相同则正确题目调用次数更少者排名更高 |
| 阶段3 | 准确率+速度 | — | 按正确性与耗时评分 |

### 阶段3详细评分标准
- **Pass@1**（一致性指标）：奖励4次独立测试均高成功率的智能体，保证方案鲁棒性
- **TTS**（解题耗时）：衡量逻辑推理定位与修复故障的效率
- **执行约束**：严格15分钟超时限制，避免死循环与资源耗尽
- 仅在规定时间内正确完成任务方可得分，取4次生成中最快结果，耗时越短得分越高：

| 答题耗时 | 得分系数 |
|---------|---------|
| ＜5分钟 | 100% |
| 5–10分钟 | 80% |
| 10–15分钟 | 60% |
| ＞15分钟 | 0% |

---

## 快速上手：基于OpenClaw运行智能体
`agent/`目录提供基于开源智能体框架OpenClaw的开箱即用方案。结合预配置技能、配置文件与批量评测脚本，选手可快速启动智能体本地解题。

### 前置条件
- 克隆并安装OpenClaw，确保本地可运行（参考官方文档）
- Python 3.8+ 与 Node.js
- 智能体工具服务器本地运行于`http://127.0.0.1:7860`，或使用带有效Token的远程服务

### 目录结构
```
agent/
├── openclaw_config/          # OpenClaw配置文件
│   ├── IDENTITY.md           # 智能体身份定义
│   ├── SOUL.md               # 行为准则与核心原则
│   ├── USER.md               # 竞赛场景与需求
│   ├── AGENTS.md             # 智能体协同设置
│   └── TOOLS.md              # 可用工具与网管API规范
├── skills/                   # 智能体技能定义
│   ├── infra_maintenance/    # 基础设施运维
│   ├── l2_link/              # 二层链路运维
│   ├── l3_route/             # 三层路由
│   └── adv_tunnel/           # 高级隧道
├── evaluate_openclaw.py      # 批量评测脚本
├── evaluate_openclaw_guideline.md  # 使用指南
└── requirements.txt          # 依赖
```

### 配置
1. 将`openclaw_config/`复制或软链接至OpenClaw配置目录
2. 将`skills/`复制至OpenClaw技能目录
3. 在`evaluate_openclaw.py`顶部配置路径：
```python
OPENCLAW_DIR = r"C:\path\to\your\openclaw"
OPENCLAW_SESSION_DIR = r"C:\Users\YourUser\.openclaw\agents\main\sessions"
```

### 运行命令
```bash
# 安装依赖
pip install -r agent/requirements.txt

# 运行全部题目
python agent/evaluate_openclaw.py -i data/Phase_1/test.json

# 运行指定题目
python agent/evaluate_openclaw.py -i data/Phase_1/test.json --questions 1,2,5

# 并发运行（最大2）
python agent/evaluate_openclaw.py -i data/Phase_1/test.json --concurrency 2

# 断点续跑
python agent/evaluate_openclaw.py -i data/Phase_1/test.json --resume
```

### 工作流程
1. 脚本从JSON加载题目，调用本地OpenClaw智能体
2. 智能体依据配置，通过API采集设备数据
3. 分析数据并生成答案
4. 从会话日志提取答案，写入`agent/eval_results/result.csv`

### 输出文件
| 文件 | 说明 |
|------|------|
| result.csv | 最终答案（提交用） |
| eval_detail.jsonl | 单题执行日志 |
| progress.json | 断点续跑进度 |

更多细节参见`evaluate_openclaw_guideline.md`。

