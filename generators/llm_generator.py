"""
LLM Integration: Gemini and OpenAI for AI-enhanced IaC generation and analysis.
"""
import os
import json
import re
from typing import Optional
from loguru import logger

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai not installed")


# ─── System prompt ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert Cloud Infrastructure Architect and IaC (Infrastructure as Code) specialist.
You help users generate, review, and optimize CloudFormation templates and OpenTofu/Terraform configurations.

Your tasks:
1. Analyze architecture diagrams described as JSON node/edge graphs
2. Generate production-ready, secure IaC with best practices
3. Identify missing components, security gaps, and cost optimizations
4. Explain architecture decisions in plain English

Rules:
- Always include security best practices (encryption, least-privilege IAM, private subnets)
- Add tags/labels for cost tracking and compliance
- Mention if something requires manual configuration (passwords, domain names, etc.)
- Be concise but thorough
- Return valid JSON or HCL as requested
"""


def _clean_json(text: str) -> str:
    """Strip markdown fences and extract JSON."""
    text = re.sub(r"```(?:json|hcl|terraform)?\s*", "", text)
    text = re.sub(r"```", "", text)
    return text.strip()


# ─── Gemini ──────────────────────────────────────────────────────────────────

def call_gemini(prompt: str, api_key: str, model: str = "gemini-1.5-flash") -> str:
    """Call Google Gemini API."""
    if not GEMINI_AVAILABLE:
        raise RuntimeError("google-generativeai package not installed")
    genai.configure(api_key=api_key)
    model_obj = genai.GenerativeModel(
        model_name=model,
        system_instruction=SYSTEM_PROMPT
    )
    response = model_obj.generate_content(prompt)
    return response.text


# ─── OpenAI ──────────────────────────────────────────────────────────────────

def call_openai(prompt: str, api_key: str, model: str = "gpt-4o-mini") -> str:
    """Call OpenAI API."""
    if not OPENAI_AVAILABLE:
        raise RuntimeError("openai package not installed")
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=4000
    )
    return response.choices[0].message.content


# ─── Unified LLM caller ──────────────────────────────────────────────────────

def call_llm(prompt: str, provider: str, gemini_key: str = "", openai_key: str = "") -> str:
    """Route to correct LLM based on provider preference."""
    if provider == "gemini" and gemini_key:
        logger.info("Calling Gemini API")
        return call_gemini(prompt, gemini_key)
    elif provider == "openai" and openai_key:
        logger.info("Calling OpenAI API")
        return call_openai(prompt, openai_key)
    elif gemini_key:
        logger.info("Falling back to Gemini")
        return call_gemini(prompt, gemini_key)
    elif openai_key:
        logger.info("Falling back to OpenAI")
        return call_openai(prompt, openai_key)
    else:
        raise ValueError("No API keys configured. Please add Gemini or OpenAI API key in Settings.")


# ─── AI-powered IaC enhancement ──────────────────────────────────────────────

def ai_enhance_iac(
    nodes: list,
    edges: list,
    provider: str,
    iac_type: str,
    existing_iac: str,
    gemini_key: str = "",
    openai_key: str = "",
    llm_provider: str = "gemini"
) -> str:
    """Use LLM to review and enhance generated IaC."""
    node_summary = [
        {"id": n["id"], "type": n.get("component_id"), "label": n.get("label"), "config": n.get("config", {})}
        for n in nodes
    ]
    edge_summary = [
        {"from": e.get("source"), "to": e.get("target"), "label": e.get("label", "")}
        for e in edges
    ]

    prompt = f"""Review and enhance this {iac_type} template for {provider.upper()}.

## Architecture Nodes (JSON):
{json.dumps(node_summary, indent=2)}

## Connections (edges):
{json.dumps(edge_summary, indent=2)}

## Generated IaC:
{existing_iac[:3000]}

## Your task:
1. Identify any security issues or missing best practices
2. Add any missing resource dependencies or outputs
3. Suggest 3-5 specific improvements with explanations
4. Give an overall architecture score (1-10) with reasoning

Format your response as:
## Security Issues
[list issues]

## Improvements
[numbered list]

## Architecture Score
[X/10 - reasoning]

## Enhanced Notes
[any important notes for deployment]
"""

    return call_llm(prompt, llm_provider, gemini_key, openai_key)


def ai_generate_from_description(
    description: str,
    cloud_provider: str,
    gemini_key: str = "",
    openai_key: str = "",
    llm_provider: str = "gemini"
) -> dict:
    """Generate architecture components from natural language description."""
    from components.cloud_components import CLOUD_COMPONENTS

    available_ids = []
    for cat, items in CLOUD_COMPONENTS.get(cloud_provider, {}).items():
        for item in items:
            available_ids.append(item["id"])

    prompt = f"""A user described this cloud architecture:
"{description}"

Cloud Provider: {cloud_provider.upper()}

Available component IDs for this provider:
{json.dumps(available_ids, indent=2)}

Generate a list of nodes and connections for this architecture.
Return ONLY valid JSON, no markdown:
{{
  "nodes": [
    {{
      "id": "unique_id_1",
      "component_id": "<one of the available IDs above>",
      "label": "Human readable name",
      "config": {{}}
    }}
  ],
  "edges": [
    {{
      "source": "unique_id_1",
      "target": "unique_id_2",
      "label": "connection description"
    }}
  ],
  "summary": "Brief architecture description"
}}
"""
    raw = call_llm(prompt, llm_provider, gemini_key, openai_key)
    try:
        return json.loads(_clean_json(raw))
    except json.JSONDecodeError:
        logger.error(f"LLM returned non-JSON: {raw[:500]}")
        return {"nodes": [], "edges": [], "summary": raw, "error": True}


def ai_analyze_architecture(
    nodes: list,
    edges: list,
    cloud_provider: str,
    gemini_key: str = "",
    openai_key: str = "",
    llm_provider: str = "gemini"
) -> str:
    """Analyze an architecture for best practices, cost, and security."""
    node_summary = [
        {"type": n.get("component_id"), "label": n.get("label")}
        for n in nodes
    ]
    edge_summary = [{"from": e.get("source"), "to": e.get("target")} for e in edges]

    prompt = f"""Analyze this {cloud_provider.upper()} cloud architecture:

Nodes: {json.dumps(node_summary, indent=2)}
Connections: {json.dumps(edge_summary, indent=2)}

Provide:
1. **Architecture Summary** - What does this do?
2. **Security Assessment** - Rating (High/Medium/Low risk) + specific findings
3. **Cost Estimate** - Rough monthly estimate and optimization tips
4. **High Availability** - Is it HA? What's missing?
5. **Compliance** - Common standards this meets/misses (SOC2, GDPR, HIPAA hints)
6. **Recommendations** - Top 5 actionable improvements
"""
    return call_llm(prompt, llm_provider, gemini_key, openai_key)


def ai_chat(
    user_message: str,
    context: dict,
    history: list,
    gemini_key: str = "",
    openai_key: str = "",
    llm_provider: str = "gemini"
) -> str:
    """AI chat assistant with architecture context."""
    nodes = context.get("nodes", [])
    provider = context.get("provider", "aws")

    context_str = f"""Current architecture ({provider.upper()}):
- {len(nodes)} components: {', '.join(n.get('label', n['id']) for n in nodes[:10])}
"""
    history_str = ""
    for h in history[-4:]:  # last 4 turns
        role = h.get("role", "user")
        content = h.get("content", "")[:300]
        history_str += f"{role.capitalize()}: {content}\n"

    prompt = f"""Context:
{context_str}

Previous conversation:
{history_str}

User: {user_message}

Answer as an IaC/cloud expert. Be concise and actionable."""

    return call_llm(prompt, llm_provider, gemini_key, openai_key)
