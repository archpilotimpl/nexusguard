#!/usr/bin/env python3
"""
NexusGuard NOC - Intelligent Monitoring Agent using CrewAI

This agent monitors transactions, infrastructure, and network health,
detects anomalies, and recommends playbooks. When no existing playbook
matches, it consults Claude Sonnet 4.5 for solutions and learns from them.
"""

import os
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from pydantic import BaseModel
import anthropic

# Load environment variables
load_dotenv()

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
PLAYBOOKS_PATH = Path(os.getenv("PLAYBOOKS_PATH", "../ansible/playbooks"))
LEARNED_PLAYBOOKS_PATH = Path(os.getenv("LEARNED_PLAYBOOKS_PATH", "./learned_playbooks"))
TEST_DATA_PATH = Path(os.getenv("TEST_DATA_PATH", "../prometheus/test_data"))

# Thresholds
THRESHOLD_LATENCY_MS = int(os.getenv("ANOMALY_THRESHOLD_LATENCY_MS", "1000"))
THRESHOLD_ERROR_RATE = float(os.getenv("ANOMALY_THRESHOLD_ERROR_RATE", "0.05"))
THRESHOLD_CPU = int(os.getenv("ANOMALY_THRESHOLD_CPU", "85"))
THRESHOLD_MEMORY = int(os.getenv("ANOMALY_THRESHOLD_MEMORY", "90"))

# Ensure learned playbooks directory exists
LEARNED_PLAYBOOKS_PATH.mkdir(parents=True, exist_ok=True)


class AnomalyReport(BaseModel):
    """Model for anomaly detection results"""
    anomaly_type: str
    severity: str
    description: str
    affected_service: str
    affected_region: str
    metrics: dict
    timestamp: str


class PlaybookRecommendation(BaseModel):
    """Model for playbook recommendations"""
    playbook_name: str
    confidence: float
    reason: str
    source: str  # 'existing' or 'learned' or 'llm_generated'


# ============== TOOLS ==============

@tool("Load Transaction Data")
def load_transaction_data(data_type: str = "normal") -> str:
    """
    Load transaction test data from JSON files.

    Args:
        data_type: Type of data to load - 'normal', 'abnormal', or 'anomaly'

    Returns:
        JSON string of transaction data
    """
    file_map = {
        "normal": "transactions_normal.json",
        "abnormal": "transactions_abnormal.json",
        "anomaly": "transactions_anomaly.json"
    }

    file_name = file_map.get(data_type, "transactions_normal.json")
    file_path = TEST_DATA_PATH / file_name

    if file_path.exists():
        with open(file_path, 'r') as f:
            return f.read()
    return json.dumps({"error": f"File not found: {file_path}"})


@tool("Analyze Transactions for Anomalies")
def analyze_transactions(transaction_data: str) -> str:
    """
    Analyze transaction data and detect anomalies.

    Args:
        transaction_data: JSON string of transaction data

    Returns:
        JSON string with detected anomalies
    """
    try:
        data = json.loads(transaction_data)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON data"})

    anomalies = []
    transactions = data.get("transactions", [])

    for txn in transactions:
        # Check for high latency
        if txn.get("latency_ms", 0) > THRESHOLD_LATENCY_MS:
            anomalies.append({
                "type": "high_latency",
                "severity": "warning" if txn["latency_ms"] < 5000 else "critical",
                "transaction_id": txn["id"],
                "latency_ms": txn["latency_ms"],
                "service": txn.get("service", "unknown"),
                "region": txn.get("region", "unknown")
            })

        # Check for failures
        if txn.get("status") == "failed":
            severity = "critical" if txn.get("anomaly_type") else "high"
            anomalies.append({
                "type": txn.get("error", "unknown_failure"),
                "severity": severity,
                "transaction_id": txn["id"],
                "service": txn.get("service", "unknown"),
                "region": txn.get("region", "unknown"),
                "anomaly_type": txn.get("anomaly_type")
            })

        # Check for hash mismatches
        if txn.get("error") == "hash_mismatch":
            anomalies.append({
                "type": "hash_mismatch",
                "severity": "critical",
                "transaction_id": txn["id"],
                "expected_hash": txn.get("expected_hash"),
                "actual_hash": txn.get("hash"),
                "service": txn.get("service", "unknown"),
                "region": txn.get("region", "unknown")
            })

    # Check infrastructure
    infra = data.get("infrastructure", {})
    for server in infra.get("servers", []):
        if server.get("cpu", 0) > THRESHOLD_CPU:
            anomalies.append({
                "type": "high_cpu",
                "severity": "critical" if server["cpu"] > 95 else "warning",
                "server": server["name"],
                "cpu": server["cpu"]
            })
        if server.get("memory", 0) > THRESHOLD_MEMORY:
            anomalies.append({
                "type": "high_memory",
                "severity": "critical" if server["memory"] > 95 else "warning",
                "server": server["name"],
                "memory": server["memory"]
            })

    # Check network
    network = data.get("network", {})
    layer7 = network.get("layer7", {})
    total_requests = layer7.get("http_2xx", 0) + layer7.get("http_4xx", 0) + layer7.get("http_5xx", 0)
    if total_requests > 0:
        error_rate = layer7.get("http_5xx", 0) / total_requests
        if error_rate > THRESHOLD_ERROR_RATE:
            anomalies.append({
                "type": "high_error_rate",
                "severity": "critical" if error_rate > 0.1 else "warning",
                "error_rate": round(error_rate * 100, 2),
                "http_5xx": layer7.get("http_5xx", 0)
            })

    return json.dumps({
        "total_anomalies": len(anomalies),
        "anomalies": anomalies,
        "timestamp": datetime.utcnow().isoformat()
    }, indent=2)


@tool("Search Existing Playbooks")
def search_playbooks(anomaly_type: str) -> str:
    """
    Search for existing Ansible playbooks that can handle the anomaly.

    Args:
        anomaly_type: Type of anomaly to find playbook for

    Returns:
        JSON string with matching playbooks
    """
    # Mapping of anomaly types to playbooks
    playbook_mapping = {
        "high_latency": ["high_error_rate_investigation", "collect_diagnostics"],
        "timeout": ["network_connectivity_test", "restart_application"],
        "connection_refused": ["network_connectivity_test", "restart_application"],
        "hash_mismatch": ["collect_diagnostics", "blockchain_node_recovery"],
        "consensus_failure": ["blockchain_node_recovery"],
        "vault_sealed": ["collect_diagnostics"],
        "ddos_detected": ["firewall_emergency_block"],
        "replication_broken": ["database_failover"],
        "high_cpu": ["memory_pressure_relief", "collect_diagnostics"],
        "high_memory": ["memory_pressure_relief"],
        "high_error_rate": ["high_error_rate_investigation", "restart_application"],
        "jwt_validation_failed": ["restart_application", "collect_diagnostics"],
        "service_degradation": ["restart_application", "load_balancer_drain"]
    }

    matching = []
    playbook_names = playbook_mapping.get(anomaly_type, [])

    # Check existing playbooks
    for pb_name in playbook_names:
        pb_path = PLAYBOOKS_PATH / f"{pb_name}.yml"
        if pb_path.exists():
            matching.append({
                "name": pb_name,
                "path": str(pb_path),
                "source": "existing",
                "confidence": 0.9
            })

    # Check learned playbooks
    for learned_pb in LEARNED_PLAYBOOKS_PATH.glob("*.yml"):
        with open(learned_pb, 'r') as f:
            try:
                pb_content = yaml.safe_load(f)
                if pb_content and anomaly_type in str(pb_content.get("vars", {}).get("target_anomalies", [])):
                    matching.append({
                        "name": learned_pb.stem,
                        "path": str(learned_pb),
                        "source": "learned",
                        "confidence": 0.8
                    })
            except yaml.YAMLError:
                continue

    return json.dumps({
        "anomaly_type": anomaly_type,
        "matching_playbooks": matching,
        "playbook_found": len(matching) > 0
    }, indent=2)


@tool("Consult LLM for Solution")
def consult_llm(problem_description: str, context: str) -> str:
    """
    Consult Claude Sonnet 4.5 for a solution when no existing playbook matches.

    Args:
        problem_description: Description of the problem/anomaly
        context: Additional context including metrics and infrastructure state

    Returns:
        JSON string with LLM recommendation
    """
    if not ANTHROPIC_API_KEY:
        return json.dumps({"error": "ANTHROPIC_API_KEY not configured"})

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""You are an expert NOC (Network Operations Center) engineer.
Analyze the following problem and provide a detailed remediation plan that can be converted to an Ansible playbook.

PROBLEM:
{problem_description}

CONTEXT:
{context}

Provide your response in the following JSON format:
{{
    "diagnosis": "Brief diagnosis of the issue",
    "root_cause": "Likely root cause",
    "remediation_steps": [
        {{"step": 1, "action": "...", "command": "...", "is_destructive": false}},
        ...
    ],
    "playbook_name": "suggested_playbook_name",
    "requires_approval": true/false,
    "estimated_recovery_time": "X minutes",
    "prevention_measures": ["..."]
}}
"""

    try:
        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text

        # Try to extract JSON from response
        try:
            # Find JSON in response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response_text[start:end]
                recommendation = json.loads(json_str)
                recommendation["source"] = "llm_generated"
                recommendation["model"] = ANTHROPIC_MODEL
                return json.dumps(recommendation, indent=2)
        except json.JSONDecodeError:
            pass

        return json.dumps({
            "raw_response": response_text,
            "source": "llm_generated",
            "model": ANTHROPIC_MODEL
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("Save Learned Playbook")
def save_learned_playbook(playbook_name: str, remediation_data: str) -> str:
    """
    Save a new playbook learned from LLM recommendation for future use.

    Args:
        playbook_name: Name for the new playbook
        remediation_data: JSON string with remediation steps from LLM

    Returns:
        JSON string confirming save or error
    """
    try:
        remediation = json.loads(remediation_data)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid remediation data"})

    # Convert LLM recommendation to Ansible playbook format
    tasks = []
    for step in remediation.get("remediation_steps", []):
        task = {
            "name": step.get("action", f"Step {step.get('step', '?')}"),
            "shell": step.get("command", "echo 'No command specified'"),
            "register": f"step_{step.get('step', 0)}_result"
        }
        if step.get("is_destructive"):
            task["when"] = "approve_destructive | default(false)"
        tasks.append(task)

    playbook_content = [{
        "name": f"Learned Playbook: {playbook_name}",
        "hosts": "{{ target_hosts | default('all') }}",
        "become": True,
        "vars": {
            "target_anomalies": [remediation.get("root_cause", "unknown")],
            "learned_from": "llm",
            "created_at": datetime.utcnow().isoformat(),
            "requires_approval": remediation.get("requires_approval", True)
        },
        "tasks": tasks
    }]

    # Save playbook
    file_path = LEARNED_PLAYBOOKS_PATH / f"{playbook_name}.yml"
    with open(file_path, 'w') as f:
        yaml.dump(playbook_content, f, default_flow_style=False)

    return json.dumps({
        "success": True,
        "playbook_path": str(file_path),
        "playbook_name": playbook_name,
        "task_count": len(tasks)
    }, indent=2)


# ============== AGENTS ==============

# Anomaly Detection Agent
anomaly_detector = Agent(
    role="Anomaly Detection Specialist",
    goal="Detect anomalies in transaction data, infrastructure metrics, and network health",
    backstory="""You are an expert at analyzing system metrics and identifying
    anomalies. You have deep knowledge of NOC operations and can quickly spot
    patterns that indicate problems in transactions, infrastructure, or network layers.""",
    verbose=True,
    allow_delegation=False,
    tools=[load_transaction_data, analyze_transactions]
)

# Playbook Matcher Agent
playbook_matcher = Agent(
    role="Playbook Matching Specialist",
    goal="Find the best existing playbook to remediate detected anomalies",
    backstory="""You are an Ansible expert who knows all available playbooks
    and their capabilities. You match detected anomalies to the most appropriate
    remediation playbooks with high accuracy.""",
    verbose=True,
    allow_delegation=False,
    tools=[search_playbooks]
)

# LLM Consultant Agent
llm_consultant = Agent(
    role="AI Solutions Architect",
    goal="Consult Claude Sonnet 4.5 for solutions when no existing playbook matches",
    backstory="""You are a senior solutions architect who consults with AI
    when novel problems arise. You formulate clear problem descriptions and
    convert AI recommendations into actionable playbooks.""",
    verbose=True,
    allow_delegation=False,
    tools=[consult_llm, save_learned_playbook]
)


# ============== TASKS ==============

def create_detection_task(data_type: str = "anomaly"):
    """Create anomaly detection task"""
    return Task(
        description=f"""
        1. Load the {data_type} transaction data
        2. Analyze it for anomalies in:
           - Transaction patterns (latency, failures, hash mismatches)
           - Infrastructure health (CPU, memory, disk)
           - Network health (Layer 3, 4, 7)
        3. Categorize each anomaly by type and severity
        4. Return a comprehensive anomaly report
        """,
        expected_output="JSON report with all detected anomalies, their types, severities, and affected services",
        agent=anomaly_detector
    )


def create_matching_task():
    """Create playbook matching task"""
    return Task(
        description="""
        For each detected anomaly:
        1. Search existing Ansible playbooks for matches
        2. Check learned playbooks from previous LLM consultations
        3. Rank playbooks by confidence score
        4. Return list of recommended playbooks with confidence scores

        If no playbook matches, clearly indicate this so the LLM consultant can be engaged.
        """,
        expected_output="JSON with playbook recommendations for each anomaly, including confidence scores and sources",
        agent=playbook_matcher
    )


def create_consultation_task():
    """Create LLM consultation task"""
    return Task(
        description="""
        For any anomalies without matching playbooks:
        1. Formulate a clear problem description with all relevant context
        2. Consult Claude Sonnet 4.5 for remediation recommendations
        3. Convert the recommendation to an Ansible playbook format
        4. Save the new playbook for future use
        5. Return the final recommendations
        """,
        expected_output="JSON with LLM recommendations and paths to any newly created playbooks",
        agent=llm_consultant
    )


# ============== CREW ==============

def run_monitoring_crew(data_type: str = "anomaly"):
    """
    Run the complete monitoring crew workflow.

    Args:
        data_type: Type of test data to analyze ('normal', 'abnormal', 'anomaly')

    Returns:
        Crew execution result
    """
    crew = Crew(
        agents=[anomaly_detector, playbook_matcher, llm_consultant],
        tasks=[
            create_detection_task(data_type),
            create_matching_task(),
            create_consultation_task()
        ],
        process=Process.sequential,
        verbose=True
    )

    return crew.kickoff()


if __name__ == "__main__":
    import sys

    data_type = sys.argv[1] if len(sys.argv) > 1 else "anomaly"
    print(f"\n{'='*60}")
    print(f"NexusGuard NOC - Intelligent Monitoring Agent")
    print(f"Analyzing: {data_type} data")
    print(f"{'='*60}\n")

    result = run_monitoring_crew(data_type)

    print(f"\n{'='*60}")
    print("FINAL RESULT:")
    print(f"{'='*60}")
    print(result)
