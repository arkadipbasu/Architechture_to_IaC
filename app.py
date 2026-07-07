"""
Arch2IaC — Enterprise Cloud Architecture to IaC Dashboard
Streamlit application entry point.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
import uuid
import streamlit as st
from loguru import logger
from streamlit_agraph import agraph, Node, Edge, Config

from utils.logging_config import get_log_contents, get_log_file_path
from components.cloud_components import CLOUD_COMPONENTS, get_all_components
from generators.iac_generator import generate_cloudformation, generate_opentofu
from generators.llm_generator import (
    ai_enhance_iac, ai_generate_from_description,
    ai_analyze_architecture, ai_chat
)
from utils.export_utils import (
    cloudformation_to_yaml, cloudformation_to_json,
    build_export_package, diagram_to_json
)

# ─── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Arch2IaC",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Arch2IaC — Architecture Diagram to Infrastructure as Code\nBuilt with Streamlit + OpenTofu + AI"
    }
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-primary: #0a0f1e;
    --bg-card: #111827;
    --bg-elevated: #1a2236;
    --border: #1e2d45;
    --accent-blue: #3b82f6;
    --accent-cyan: #06b6d4;
    --accent-green: #10b981;
    --accent-orange: #f59e0b;
    --accent-red: #ef4444;
    --accent-purple: #8b5cf6;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #475569;
    --radius: 10px;
}

* { font-family: 'Inter', sans-serif !important; }

.stApp { background: var(--bg-primary); color: var(--text-primary); }

.block-container { padding: 1.5rem 2rem; max-width: 100%; }

/* Header */
.arch-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem 2rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.arch-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(ellipse at 20% 50%, rgba(59, 130, 246, 0.08) 0%, transparent 60%);
}
.arch-title {
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(90deg, #60a5fa, #06b6d4, #10b981);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.02em;
}
.arch-subtitle {
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin-top: 0.2rem;
}
            
.gradient-text {
  font-size: 24px; 
  font-weight: bold;
  
  background: linear-gradient(45deg, #006a50, #005BED);
  
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.gradient-text2 {
  font-size: 24px; 
  font-weight: bold;
  
  background: linear-gradient(45deg, #005BED, #006a50);
  
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
                       
/* Canvas */
.canvas-container {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem;
    min-height: 520px;
    position: relative;
}
.canvas-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, 110px);
    gap: 12px;
    min-height: 420px;
    padding: 1rem;
    background-image:
        linear-gradient(rgba(255,255,255,.015) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.015) 1px, transparent 1px);
    background-size: 28px 28px;
    border-radius: 8px;
    border: 1px dashed #1e2d45;
}

/* Component cards */
.component-card {
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 8px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s ease;
    width: 105px;
    position: relative;
    user-select: none;
}
.component-card:hover {
    border-color: var(--accent-blue);
    background: #162035;
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(59, 130, 246, 0.2);
}
.component-card.selected {
    border-color: var(--accent-cyan);
    background: #0e2030;
    box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.3);
}
.component-icon { font-size: 1.8rem; margin-bottom: 4px; }
.component-name { font-size: 0.65rem; color: var(--text-secondary); font-weight: 500; line-height: 1.2; }
.component-badge {
    position: absolute;
    top: -6px; right: -6px;
    background: var(--accent-blue);
    color: white;
    border-radius: 50%;
    width: 18px; height: 18px;
    font-size: 0.6rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
}
.delete-btn {
    position: absolute;
    top: -6px; left: -6px;
    background: var(--accent-red);
    color: white;
    border-radius: 50%;
    width: 18px; height: 18px;
    font-size: 0.7rem;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-weight: 700;
    border: none;
}

/* Sidebar component palette */
.palette-component {
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 10px;
    margin-bottom: 6px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: all 0.15s;
}
.palette-component:hover {
    border-color: var(--accent-blue);
    background: #162035;
}
.palette-icon { font-size: 1.2rem; width: 24px; text-align: center; }
.palette-text { font-size: 0.75rem; color: var(--text-secondary); font-weight: 500; }

/* Code block */
.code-block {
    background: #060d1a;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.75rem;
    color: #c9d1d9;
    padding: 1rem;
    overflow-x: auto;
    max-height: 500px;
    overflow-y: auto;
    line-height: 1.6;
}

/* Metrics */
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--accent-cyan);
    font-variant-numeric: tabular-nums;
}
.metric-label { font-size: 0.75rem; color: var(--text-secondary); margin-top: 4px; }

/* Tags */
.tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    margin: 2px;
}
.tag-compute { background: rgba(251,140,0,.15); color: #fb8c00; border: 1px solid rgba(251,140,0,.3); }
.tag-networking { background: rgba(139,92,246,.15); color: #a78bfa; border: 1px solid rgba(139,92,246,.3); }
.tag-storage { background: rgba(16,185,129,.15); color: #34d399; border: 1px solid rgba(16,185,129,.3); }
.tag-database { background: rgba(59,130,246,.15); color: #60a5fa; border: 1px solid rgba(59,130,246,.3); }
.tag-security { background: rgba(239,68,68,.15); color: #f87171; border: 1px solid rgba(239,68,68,.3); }
.tag-messaging { background: rgba(236,72,153,.15); color: #f472b6; border: 1px solid rgba(236,72,153,.3); }
.tag-monitoring { background: rgba(6,182,212,.15); color: #22d3ee; border: 1px solid rgba(6,182,212,.3); }

/* Connection line indicator */
.connection-badge {
    background: rgba(6,182,212,0.1);
    border: 1px solid rgba(6,182,212,0.3);
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 0.72rem;
    color: var(--accent-cyan);
    display: inline-block;
    margin: 2px;
}

/* Alert styles */
.info-box {
    background: rgba(59,130,246,.08);
    border: 1px solid rgba(59,130,246,.2);
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.8rem;
    color: #93c5fd;
    margin: 8px 0;
}
.success-box {
    background: rgba(16,185,129,.08);
    border: 1px solid rgba(16,185,129,.2);
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.8rem;
    color: #6ee7b7;
    margin: 8px 0;
}
.warn-box {
    background: rgba(245,158,11,.08);
    border: 1px solid rgba(245,158,11,.2);
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.8rem;
    color: #fcd34d;
    margin: 8px 0;
}

/* Streamlit overrides */
.stButton > button {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: 6px !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    border-color: var(--accent-blue) !important;
    background: #162035 !important;
    color: var(--accent-blue) !important;
}
.stSelectbox > div, .stTextInput > div > div, .stTextArea > div > div {
    background: var(--bg-elevated) !important;
    border-color: var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: 6px !important;
}
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-card) !important;
    border-radius: 8px !important;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: var(--text-secondary) !important;
    font-size: 0.8rem !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent-blue) !important;
    background: var(--bg-elevated) !important;
}
.stSidebar { background: var(--bg-card) !important; border-right: 1px solid var(--border); }
.stSidebar .stSelectbox label, .stSidebar .stTextInput label { color: var(--text-secondary) !important; font-size: 0.78rem !important; }
div[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}
.stMarkdown h3 { color: var(--text-primary) !important; font-size: 1rem; font-weight: 600; }

/* Provider badge */
.provider-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 0.78rem;
    font-weight: 600;
}
.provider-aws { border-color: rgba(255,153,0,.4); color: #ff9900; }
.provider-azure { border-color: rgba(0,120,212,.4); color: #0078d4; }
.provider-gcp { border-color: rgba(66,133,244,.4); color: #4285f4; }
.provider-openstack { border-color: rgba(237,25,68,.4); color: #ed1944; }

/* Hide streamlit defaults */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─── Session State ────────────────────────────────────────────────────────────

def init_state():
    defaults = {
        "nodes": [],
        "edges": [],
        "selected_node": None,
        "connect_mode": False,
        "connect_source": None,
        "project_name": "MyArchitecture",
        "provider": "aws",
        "iac_type": "opentofu",
        "cf_template": None,
        "tofu_files": None,
        "ai_analysis": None,
        "ai_enhanced": None,
        "llm_provider": "gemini",
        "gemini_key": "",
        "openai_key": "",
        "chat_history": [],
        "generation_log": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─── Helpers ─────────────────────────────────────────────────────────────────

PROVIDER_META = {
    "aws": {"icon": "🟠", "label": "Amazon Web Services", "color": "#FF9900"},
    "azure": {"icon": "🔵", "label": "Microsoft Azure", "color": "#0078D4"},
    "gcp": {"icon": "🔴", "label": "Google Cloud Platform", "color": "#4285F4"},
    "openstack": {"icon": "⚫", "label": "OpenStack", "color": "#ED1944"},
}

CATEGORY_TAG_CLASS = {
    "Compute": "tag-compute", "Networking": "tag-networking",
    "Storage": "tag-storage", "Database": "tag-database",
    "Security": "tag-security", "Messaging": "tag-messaging",
    "Monitoring": "tag-monitoring",
}

def add_node(component: dict):
    node_id = str(uuid.uuid4())[:8]
    node = {
        "id": node_id,
        "component_id": component["id"],
        "label": component["label"],
        "icon": component.get("icon", "📦"),
        "category": component.get("category", "General"),
        "color": component.get("color", "#3b82f6"),
        "config": dict(component.get("config", {})),
        "provider": component.get("provider", st.session_state.provider),
    }
    st.session_state.nodes.append(node)
    logger.info(f"Added node: {component['label']} ({component['id']}) id={node_id}")
    return node_id

def remove_node(node_id: str):
    st.session_state.nodes = [n for n in st.session_state.nodes if n["id"] != node_id]
    st.session_state.edges = [
        e for e in st.session_state.edges
        if e["source"] != node_id and e["target"] != node_id
    ]
    if st.session_state.selected_node == node_id:
        st.session_state.selected_node = None
    logger.info(f"Removed node id={node_id}")

# Connection type definitions — label, color, dash style
CONNECTION_TYPES = {
    "traffic":    {"label": "Traffic / HTTP",       "color": "#06b6d4", "dashes": False, "width": 2},
    "data":       {"label": "Data Flow",             "color": "#10b981", "dashes": False, "width": 2},
    "depends_on": {"label": "Depends On",            "color": "#f59e0b", "dashes": True,  "width": 1.5},
    "triggers":   {"label": "Triggers / Event",      "color": "#ec4899", "dashes": False, "width": 2},
    "auth":       {"label": "Auth / IAM",            "color": "#ef4444", "dashes": True,  "width": 1.5},
    "replication":{"label": "Replication / Sync",    "color": "#8b5cf6", "dashes": True,  "width": 2},
    "monitoring": {"label": "Monitoring / Metrics",  "color": "#84cc16", "dashes": True,  "width": 1.5},
    "storage":    {"label": "Storage / Read-Write",  "color": "#fb923c", "dashes": False, "width": 2},
    "vpc":        {"label": "VPC / Network Link",    "color": "#64748b", "dashes": False, "width": 3},
    "custom":     {"label": "Custom",                "color": "#94a3b8", "dashes": False, "width": 1.5},
}

def add_edge(source: str, target: str, label: str = "", conn_type: str = "traffic"):
    if source == target:
        return
    for e in st.session_state.edges:
        if e["source"] == source and e["target"] == target:
            return
    edge = {
        "id": str(uuid.uuid4())[:8],
        "source": source,
        "target": target,
        "label": label,
        "conn_type": conn_type,
    }
    st.session_state.edges.append(edge)
    logger.info(f"Added edge ({conn_type}): {source} → {target} [{label}]")

def get_node_by_id(node_id: str) -> dict:
    for n in st.session_state.nodes:
        if n["id"] == node_id:
            return n
    return {}

def log_event(msg: str, level: str = "INFO"):
    ts = __import__("datetime").datetime.now().strftime("%H:%M:%S")
    st.session_state.generation_log.append(f"[{ts}] {level}: {msg}")
    if level == "ERROR":
        logger.error(msg)
    else:
        logger.info(msg)


# ─── Sidebar ─────────────────────────────────────────────────────────────────
# <div style="font-size:1.1rem;font-weight:700;background:linear-gradient(90deg,#60a5fa,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">Arch2IaC</div>

def render_sidebar():
    with st.sidebar:
        # Logo
        st.markdown("""
        <div style="padding:1rem 0 0.5rem; text-align:center;">
            <div style="font-size:2rem;">🏗️</div>
            <h2 class="gradient-text2">Architechture to IaC</h2>
            <h3 class="gradient-text">arkadipbasu.github.io</h3>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Project settings
        st.markdown("**📁 Project**")
        st.session_state.project_name = st.text_input(
            "Project Name", value=st.session_state.project_name, label_visibility="collapsed",
            placeholder="Project name…"
        )

        prov_options = {"aws": "🟠 AWS", "azure": "🔵 Azure", "gcp": "🔴 GCP", "openstack": "⚫ OpenStack"}
        st.session_state.provider = st.selectbox(
            "Cloud Provider",
            options=list(prov_options.keys()),
            format_func=lambda x: prov_options[x],
            index=list(prov_options.keys()).index(st.session_state.provider)
        )

        st.session_state.iac_type = st.radio(
            "IaC Output",
            options=["opentofu", "cloudformation"],
            format_func=lambda x: "⚙️ OpenTofu / Terraform" if x == "opentofu" else "☁️ CloudFormation (AWS only)",
            horizontal=False
        )
        if st.session_state.iac_type == "cloudformation" and st.session_state.provider != "aws":
            st.markdown('<div class="warn-box">⚠️ CloudFormation is AWS-only. Switch to OpenTofu for other providers.</div>', unsafe_allow_html=True)

        st.divider()

        # Component palette
        st.markdown("**🧩 Component Palette**")
        components = get_all_components(st.session_state.provider)
        categories = sorted(set(c["category"] for c in components))
        selected_cat = st.selectbox("Category", ["All"] + categories, label_visibility="collapsed")

        filtered = components if selected_cat == "All" else [c for c in components if c["category"] == selected_cat]

        search = st.text_input("🔍 Search", placeholder="Filter components…", label_visibility="collapsed")
        if search:
            filtered = [c for c in filtered if search.lower() in c["label"].lower()]

        for comp in filtered[:30]:
            tag_cls = CATEGORY_TAG_CLASS.get(comp["category"], "tag-compute")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"""
                <div class="palette-component">
                    <span class="palette-icon">{comp['icon']}</span>
                    <div>
                        <div class="palette-text">{comp['label']}</div>
                        <span class="tag {tag_cls}">{comp['category']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("➕", key=f"add_{comp['id']}_{comp['category']}", help=f"Add {comp['label']}"):
                    add_node(comp)
                    st.rerun()

        st.divider()

        # LLM Settings
        with st.expander("🤖 AI Settings"):
            st.session_state.llm_provider = st.radio(
                "LLM Provider",
                ["gemini", "openai"],
                format_func=lambda x: "✨ Gemini" if x == "gemini" else "🧠 OpenAI"
            )
            st.session_state.gemini_key = st.text_input(
                "Gemini API Key", type="password",
                value=st.session_state.gemini_key,
                placeholder="AIza…"
            )
            st.session_state.openai_key = st.text_input(
                "OpenAI API Key", type="password",
                value=st.session_state.openai_key,
                placeholder="sk-…"
            )
            has_key = bool(st.session_state.gemini_key or st.session_state.openai_key)
            if has_key:
                st.markdown('<div class="success-box">✅ API key configured</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="warn-box">⚠️ Add API key for AI features</div>', unsafe_allow_html=True)

        st.divider()

        # Quick actions
        st.markdown("**⚡ Quick Actions**")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.nodes = []
                st.session_state.edges = []
                st.session_state.cf_template = None
                st.session_state.tofu_files = None
                st.session_state.ai_analysis = None
                log_event("Canvas cleared")
                st.rerun()
        with c2:
            if st.button("📋 Sample", use_container_width=True):
                _load_sample_architecture()
                st.rerun()

        # Stats
        n_nodes = len(st.session_state.nodes)
        n_edges = len(st.session_state.edges)
        st.markdown(f"""
        <div style="display:flex;gap:8px;margin-top:8px;">
            <div class="metric-card" style="flex:1;padding:8px;">
                <div class="metric-value" style="font-size:1.4rem;">{n_nodes}</div>
                <div class="metric-label">Components</div>
            </div>
            <div class="metric-card" style="flex:1;padding:8px;">
                <div class="metric-value" style="font-size:1.4rem;">{n_edges}</div>
                <div class="metric-label">Connections</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def _load_sample_architecture():
    """Load a sample 3-tier web app architecture."""
    st.session_state.nodes = []
    st.session_state.edges = []
    prov = st.session_state.provider

    samples = {
        "aws": [
            ("aws_cloudfront", "CDN", "n1"),
            ("aws_alb", "Load Balancer", "n2"),
            ("aws_ec2", "Web Server 1", "n3"),
            ("aws_ec2", "Web Server 2", "n4"),
            ("aws_rds", "Primary DB", "n5"),
            ("aws_elasticache", "Redis Cache", "n6"),
            ("aws_s3", "Static Assets", "n7"),
            ("aws_cloudwatch", "Monitoring", "n8"),
        ],
        "azure": [
            ("azurerm_application_gateway", "App Gateway", "n1"),
            ("azurerm_app_service", "Web App", "n2"),
            ("azurerm_postgresql_server", "PostgreSQL", "n3"),
            ("azurerm_redis_cache", "Redis Cache", "n4"),
            ("azurerm_storage_account", "Storage", "n5"),
            ("azurerm_log_analytics_workspace", "Log Analytics", "n6"),
        ],
        "gcp": [
            ("google_compute_forwarding_rule", "Load Balancer", "n1"),
            ("google_cloud_run_service", "Cloud Run", "n2"),
            ("google_sql_database_instance", "Cloud SQL", "n3"),
            ("google_redis_instance", "Memorystore", "n4"),
            ("google_storage_bucket", "GCS Bucket", "n5"),
            ("google_monitoring_dashboard", "Monitoring", "n6"),
        ],
        "openstack": [
            ("openstack_lb_loadbalancer_v2", "Octavia LB", "n1"),
            ("openstack_compute_instance_v2", "Web VM", "n2"),
            ("openstack_compute_instance_v2", "App VM", "n3"),
            ("openstack_db_instance_v1", "Database", "n4"),
            ("openstack_objectstorage_container_v1", "Object Store", "n5"),
            ("openstack_networking_floatingip_v2", "Floating IP", "n6"),
        ]
    }

    from components.cloud_components import get_component_by_id
    sample = samples.get(prov, samples["aws"])
    id_map = {}

    for comp_id, label, key in sample:
        comp = get_component_by_id(comp_id, prov)
        if comp:
            comp["label"] = label
            nid = add_node(comp)
            id_map[key] = nid

    # Add connections
    edge_map = {
        "aws": [("n1","n2","CDN→LB"), ("n2","n3","LB→Web1"), ("n2","n4","LB→Web2"),
                ("n3","n5","Web→DB"), ("n4","n5","Web→DB"), ("n3","n6","Cache"),
                ("n2","n7","Static"), ("n3","n8","Metrics")],
        "azure": [("n1","n2","Gateway→App"), ("n2","n3","App→DB"),
                  ("n2","n4","Cache"), ("n2","n5","Storage"), ("n2","n6","Logs")],
        "gcp": [("n1","n2","LB→CR"), ("n2","n3","App→DB"),
                ("n2","n4","Cache"), ("n2","n5","Objects"), ("n2","n6","Metrics")],
        "openstack": [("n6","n1","Ext→LB"), ("n1","n2","LB→Web"), ("n2","n3","Web→App"),
                      ("n3","n4","App→DB"), ("n2","n5","Objects")],
    }

    for src_key, tgt_key, lbl in edge_map.get(prov, []):
        if src_key in id_map and tgt_key in id_map:
            add_edge(id_map[src_key], id_map[tgt_key], lbl)

    log_event(f"Loaded sample {prov.upper()} 3-tier architecture")


# ─── Canvas ───────────────────────────────────────────────────────────────────

# Category → vis.js group colour (hex, no alpha — agraph passes these straight to vis.js)
CATEGORY_NODE_COLOR = {
    "Compute":    {"background": "#1c2e1c", "border": "#fb8c00", "highlight": {"background": "#2a4a1a", "border": "#fbbf24"}},
    "Networking": {"background": "#1a1530", "border": "#8b5cf6", "highlight": {"background": "#261e46", "border": "#a78bfa"}},
    "Storage":    {"background": "#0e2218", "border": "#10b981", "highlight": {"background": "#123020", "border": "#34d399"}},
    "Database":   {"background": "#0d1e36", "border": "#3b82f6", "highlight": {"background": "#112540", "border": "#60a5fa"}},
    "Security":   {"background": "#2a0e10", "border": "#ef4444", "highlight": {"background": "#38100e", "border": "#f87171"}},
    "Messaging":  {"background": "#2a0e22", "border": "#ec4899", "highlight": {"background": "#381230", "border": "#f472b6"}},
    "Monitoring": {"background": "#0c2228", "border": "#06b6d4", "highlight": {"background": "#0e2c38", "border": "#22d3ee"}},
}

def _build_agraph_elements():
    """Convert session-state nodes/edges into agraph Node/Edge objects."""
    ag_nodes = []
    ag_edges = []
    selected = st.session_state.selected_node
    connect_src = st.session_state.connect_source

    for n in st.session_state.nodes:
        cat = n.get("category", "Compute")
        colors = CATEGORY_NODE_COLOR.get(cat, CATEGORY_NODE_COLOR["Compute"])

        # Highlight selected or connect-source node with a bright border
        node_color = dict(colors)
        if n["id"] == selected:
            node_color = {"background": "#0e2030", "border": "#06b6d4",
                          "highlight": {"background": "#0e2030", "border": "#06b6d4"}}
        elif n["id"] == connect_src:
            node_color = {"background": "#0e2818", "border": "#10b981",
                          "highlight": {"background": "#0e2818", "border": "#10b981"}}

        # Label shown inside the node: icon on top line, short name below
        short_label = n["label"] if len(n["label"]) <= 14 else n["label"][:13] + "…"
        display_label = f"{n['icon']}\n{short_label}"

        # Tooltip shown on hover
        tooltip = (
            f"<b>{n['label']}</b><br/>"
            f"Type: {n.get('component_id','')}<br/>"
            f"Category: {cat}<br/>"
            f"ID: {n['id']}"
        )

        ag_nodes.append(Node(
            id=n["id"],
            label=display_label,
            title=tooltip,
            shape="box",
            size=28,
            color=node_color,
            font={"color": "#f1f5f9", "size": 12, "face": "Inter, sans-serif", "multi": True},
            borderWidth=2,
            borderWidthSelected=3,
            shadow={"enabled": True, "color": node_color.get("border", "#3b82f6"), "size": 8, "x": 0, "y": 0},
        ))

    for e in st.session_state.edges:
        ct = e.get("conn_type", "traffic")
        cdef = CONNECTION_TYPES.get(ct, CONNECTION_TYPES["traffic"])
        lbl = e.get("label") or cdef["label"]
        ag_edges.append(Edge(
            source=e["source"],
            target=e["target"],
            label=lbl,
            color={"color": cdef["color"], "highlight": "#ffffff", "hover": "#ffffff"},
            width=cdef["width"],
            dashes=cdef["dashes"],
            arrows={"to": {"enabled": True, "scaleFactor": 0.8}},
            font={"color": cdef["color"], "size": 10, "strokeWidth": 2, "strokeColor": "#0a0f1e"},
            smooth={"type": "curvedCW", "roundness": 0.2},
        ))

    return ag_nodes, ag_edges


def render_canvas():
    nodes = st.session_state.nodes

    if not nodes:
        st.markdown("""
        <div style="text-align:center;padding:4rem 2rem;color:#475569;background:var(--bg-card);border-radius:12px;border:2px dashed #1e2d45;">
            <div style="font-size:3rem;margin-bottom:1rem;">🏗️</div>
            <div style="font-size:1.1rem;font-weight:600;color:#64748b;">Empty Canvas</div>
            <div style="font-size:0.85rem;margin-top:0.5rem;">Add components from the sidebar palette<br>or load a sample architecture</div>
        </div>
        """, unsafe_allow_html=True)
        return

    ag_nodes, ag_edges = _build_agraph_elements()

    config = Config(
        height=520,
        width=1200,          # integer px; avoids "100%px" agraph bug
        directed=True,
        physics=True,
        solver="barnesHut",
        minVelocity=0.5,
        maxVelocity=60,
        stabilization=True,
        fit=True,
        timestep=0.4,
        hierarchical=False,
        interaction={
            "hover": True,
            "tooltipDelay": 100,
            "navigationButtons": True,
            "keyboard": {"enabled": True},
            "dragNodes": True,
            "zoomView": True,
            "selectConnectedEdges": True,
        },
        edges={
            "arrows": {"to": {"enabled": True, "scaleFactor": 0.7}},
            "smooth": {"type": "curvedCW", "roundness": 0.15},
            "font":   {"size": 10, "color": "#64748b", "strokeWidth": 0},
            "color":  {"color": "#4b6a8a", "highlight": "#06b6d4", "hover": "#60a5fa"},
        },
        nodes={
            "borderWidth": 2,
            "borderWidthSelected": 3,
            "chosen": True,
            "font": {"color": "#f1f5f9", "size": 12},
        },
    )

    # agraph returns the id of the last clicked node (or None)
    clicked = agraph(nodes=ag_nodes, edges=ag_edges, config=config)

    # Handle node click → select / deselect
    if clicked is not None and clicked != st.session_state.get("_last_click"):
        st.session_state["_last_click"] = clicked
        if st.session_state.connect_mode and st.session_state.connect_source:
            # Second click in connect mode → create edge using selected type
            if clicked != st.session_state.connect_source:
                ct = st.session_state.get("new_edge_type", "traffic")
                lbl = st.session_state.get("new_edge_label", "")
                add_edge(st.session_state.connect_source, clicked, lbl, ct)
                st.session_state.connect_mode = False
                st.session_state.connect_source = None
                log_event("Connected nodes via graph click")
                st.rerun()
        else:
            # Normal click → toggle selection
            if st.session_state.selected_node == clicked:
                st.session_state.selected_node = None
            else:
                st.session_state.selected_node = clicked
            st.rerun()

    # ── Canvas toolbar (below graph) ─────────────────────────────────────────
    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # Connect-mode status bar
    if st.session_state.connect_mode:
        src = get_node_by_id(st.session_state.connect_source)
        st.markdown(f"""
        <div class="info-box">
            🔗 <b>Connect Mode</b> — now click a <em>second node</em> in the graph above to draw an edge from
            <b>{src.get('icon','')} {src.get('label','')}</b>. Or cancel below.
        </div>
        """, unsafe_allow_html=True)

    # Per-node action toolbar — flat selectbox + buttons (no nested columns)
    if nodes:
        sel_id = st.session_state.selected_node
        node_labels = {n["id"]: f"{n['icon']} {n['label']}" for n in nodes}

        # Dropdown to pick a node for actions
        action_target = st.selectbox(
            "Node actions",
            options=list(node_labels.keys()),
            format_func=lambda x: node_labels[x],
            index=list(node_labels.keys()).index(sel_id) if sel_id in node_labels else 0,
            label_visibility="collapsed",
            key="node_action_select",
        )
        node = get_node_by_id(action_target)
        is_sel = sel_id == action_target
        is_src = st.session_state.connect_source == action_target
        connect_mode = st.session_state.connect_mode

        # Status badge
        status_color = "#06b6d4" if is_sel else ("#10b981" if is_src else node["color"])
        st.markdown(
            f'''<div style="background:#111827;border:2px solid {status_color};border-radius:8px;
            padding:6px 12px;display:flex;align-items:center;gap:10px;margin-bottom:6px;">
            <span style="font-size:1.4rem;">{node["icon"]}</span>
            <div>
              <div style="font-size:0.78rem;color:#f1f5f9;font-weight:600;">{node["label"]}</div>
              <div style="font-size:0.65rem;color:#475569;">{node.get("component_id","")} · {node["category"]} · ID: {node["id"]}</div>
            </div>
            </div>''',
            unsafe_allow_html=True,
        )

        # Three action buttons as a flat horizontal group (no nesting)
        edit_btn, conn_btn, del_btn, cancel_btn = st.columns([1, 1, 1, 1])
        with edit_btn:
            edit_label = "✏️ Editing" if is_sel else "✏️ Edit"
            if st.button(edit_label, key=f"sel_{action_target}", use_container_width=True,
                         help="Select this node for the property editor"):
                st.session_state.selected_node = action_target if not is_sel else None
                st.session_state["_last_click"] = None
                st.rerun()
        with conn_btn:
            if is_src:
                conn_label = "⬛ Source set"
            elif connect_mode:
                conn_label = "🔗 Set target"
            else:
                conn_label = "🔗 Connect"
            if st.button(conn_label, key=f"con_{action_target}", use_container_width=True,
                         help="Draw edge from this node to another"):
                if connect_mode and st.session_state.connect_source:
                    if st.session_state.connect_source != action_target:
                        ct = st.session_state.get("new_edge_type", "traffic")
                        lbl = st.session_state.get("new_edge_label", "")
                        add_edge(st.session_state.connect_source, action_target, lbl, ct)
                        st.session_state.connect_mode = False
                        st.session_state.connect_source = None
                        log_event("Connected nodes via toolbar")
                    else:
                        st.session_state.connect_mode = False
                        st.session_state.connect_source = None
                else:
                    st.session_state.connect_mode = True
                    st.session_state.connect_source = action_target
                st.rerun()
        with del_btn:
            if st.button("🗑️ Delete", key=f"del_{action_target}", use_container_width=True,
                         help="Remove this component from canvas"):
                remove_node(action_target)
                st.rerun()
        with cancel_btn:
            if st.button("✖ Cancel", key="cancel_connect", use_container_width=True,
                         help="Cancel connect mode / deselect"):
                st.session_state.connect_mode = False
                st.session_state.connect_source = None
                st.session_state.selected_node = None
                st.session_state["_last_click"] = None
                st.rerun()

    # ── Connections Panel ────────────────────────────────────────────────────
    render_connections_panel(nodes)



# ─── Connections Panel ────────────────────────────────────────────────────────

def render_connections_panel(nodes: list):
    """Dedicated panel: add new connections + manage existing ones."""
    st.divider()
    st.markdown("### 🔗 Connections")

    if len(nodes) < 2:
        st.markdown('<div class="info-box">Add at least 2 components to create connections.</div>',
                    unsafe_allow_html=True)
        return

    node_options = {n["id"]: f"{n['icon']} {n['label']}" for n in nodes}

    # ── Add new connection ────────────────────────────────────────────────────
    with st.expander("➕ Add Connection", expanded=True):
        ca, cb, cc = st.columns([2, 2, 2])
        with ca:
            src_id = st.selectbox(
                "From (source)",
                options=list(node_options.keys()),
                format_func=lambda x: node_options[x],
                key="new_edge_src",
            )
        with cb:
            # Exclude source from target options
            tgt_options = {k: v for k, v in node_options.items() if k != src_id}
            tgt_id = st.selectbox(
                "To (target)",
                options=list(tgt_options.keys()),
                format_func=lambda x: tgt_options[x],
                key="new_edge_tgt",
            )
        with cc:
            conn_type = st.selectbox(
                "Connection type",
                options=list(CONNECTION_TYPES.keys()),
                format_func=lambda x: CONNECTION_TYPES[x]["label"],
                key="new_edge_type",
            )

        cd, ce = st.columns([3, 1])
        with cd:
            custom_label = st.text_input(
                "Custom label (optional)",
                placeholder="e.g. HTTPS:443, SQL, gRPC…",
                key="new_edge_label",
            )
        with ce:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("➕ Add", use_container_width=True, type="primary", key="btn_add_edge"):
                cdef = CONNECTION_TYPES[conn_type]
                # Preview color badge
                src_node = get_node_by_id(src_id)
                tgt_node = get_node_by_id(tgt_id)
                # Check for duplicate
                exists = any(
                    e["source"] == src_id and e["target"] == tgt_id
                    for e in st.session_state.edges
                )
                if exists:
                    st.warning(f"Connection from {src_node['label']} → {tgt_node['label']} already exists.")
                else:
                    add_edge(src_id, tgt_id, custom_label, conn_type)
                    log_event(f"Edge added: {src_node['label']} →[{cdef['label']}]→ {tgt_node['label']}")
                    st.success(f"✅ Connected {src_node['label']} → {tgt_node['label']}")
                    st.rerun()

        # Live preview of what the edge will look like
        if src_id and tgt_id:
            cdef = CONNECTION_TYPES.get(conn_type, CONNECTION_TYPES["traffic"])
            src_node = get_node_by_id(src_id)
            tgt_node = get_node_by_id(tgt_id)
            edge_lbl = custom_label or cdef["label"]
            dash_style = "dashed" if cdef["dashes"] else "solid"
            st.markdown(
                f'''<div style="margin-top:6px;padding:8px 14px;background:#0a1020;border-radius:8px;
                display:flex;align-items:center;gap:8px;font-size:0.78rem;">
                <span style="background:#1a2236;border:1px solid {cdef["color"]};border-radius:6px;
                    padding:4px 10px;color:{cdef["color"]};font-weight:600;">
                    {src_node.get("icon","")} {src_node.get("label","?")}
                </span>
                <span style="color:{cdef["color"]};letter-spacing:2px;">
                    {"╌╌╌" if cdef["dashes"] else "───"}▶
                </span>
                <span style="background:#111827;border:1px solid {cdef["color"]}66;border-radius:4px;
                    padding:2px 8px;color:{cdef["color"]}cc;font-size:0.7rem;">{edge_lbl}</span>
                <span style="color:{cdef["color"]};letter-spacing:2px;">
                    {"╌╌╌" if cdef["dashes"] else "───"}▶
                </span>
                <span style="background:#1a2236;border:1px solid {cdef["color"]};border-radius:6px;
                    padding:4px 10px;color:{cdef["color"]};font-weight:600;">
                    {tgt_node.get("icon","")} {tgt_node.get("label","?")}
                </span>
                </div>''',
                unsafe_allow_html=True,
            )

    # ── Connection type legend ────────────────────────────────────────────────
    with st.expander("🎨 Connection Type Legend", expanded=False):
        legend_html = "<div style='display:flex;flex-wrap:wrap;gap:8px;padding:4px 0;'>"
        for ct_key, ct_val in CONNECTION_TYPES.items():
            dash_icon = "╌" if ct_val["dashes"] else "─"
            legend_html += (
                f'<div style="display:flex;align-items:center;gap:6px;background:#111827;'
                f'border:1px solid {ct_val["color"]}44;border-radius:6px;padding:5px 10px;">'
                f'<span style="color:{ct_val["color"]};font-size:1rem;letter-spacing:1px;">{dash_icon}{dash_icon}▶</span>'
                f'<span style="font-size:0.72rem;color:#94a3b8;font-weight:500;">{ct_val["label"]}</span>'
                f'</div>'
            )
        legend_html += "</div>"
        st.markdown(legend_html, unsafe_allow_html=True)

    # ── Existing connections table ────────────────────────────────────────────
    edges = st.session_state.edges
    if not edges:
        st.markdown('<div class="info-box">No connections yet. Use the panel above to add one.</div>',
                    unsafe_allow_html=True)
        return

    st.markdown(f"**{len(edges)} connection(s)**")

    # Header row
    st.markdown(
        '''<div style="display:grid;grid-template-columns:2fr 2fr 2fr 1fr 1fr;gap:6px;
        padding:6px 10px;background:#0a1020;border-radius:6px 6px 0 0;
        font-size:0.68rem;color:#475569;font-weight:700;text-transform:uppercase;letter-spacing:.05em;
        margin-top:8px;">
        <div>From</div><div>To</div><div>Type</div><div>Label</div><div>Action</div>
        </div>''',
        unsafe_allow_html=True,
    )

    edges_to_delete = []
    for i, e in enumerate(edges):
        src_n = get_node_by_id(e["source"])
        tgt_n = get_node_by_id(e["target"])
        ct = e.get("conn_type", "traffic")
        cdef = CONNECTION_TYPES.get(ct, CONNECTION_TYPES["traffic"])
        lbl = e.get("label") or cdef["label"]
        dash_icon = "╌╌▶" if cdef["dashes"] else "──▶"

        row_bg = "#0e1520" if i % 2 == 0 else "#111827"
        st.markdown(
            f'''<div style="display:grid;grid-template-columns:2fr 2fr 2fr 1fr 1fr;gap:6px;
            padding:8px 10px;background:{row_bg};border-bottom:1px solid #1e2d45;
            align-items:center;font-size:0.75rem;">
            <div style="color:#f1f5f9;font-weight:500;">{src_n.get("icon","")} {src_n.get("label","?")}</div>
            <div style="color:#f1f5f9;font-weight:500;">{tgt_n.get("icon","")} {tgt_n.get("label","?")}</div>
            <div style="color:{cdef["color"]};font-weight:600;">{dash_icon} {cdef["label"]}</div>
            <div style="color:#64748b;font-style:italic;">{lbl}</div>
            <div></div>
            </div>''',
            unsafe_allow_html=True,
        )
        if st.button("🗑️", key=f"del_edge_{e['id']}", help=f"Remove this connection"):
            edges_to_delete.append(e["id"])

    if edges_to_delete:
        st.session_state.edges = [e for e in st.session_state.edges if e["id"] not in edges_to_delete]
        log_event(f"Deleted {len(edges_to_delete)} edge(s)")
        st.rerun()

    # Bulk clear
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    if st.button("🗑️ Clear All Connections", key="clear_all_edges", use_container_width=True):
        st.session_state.edges = []
        log_event("All edges cleared")
        st.rerun()

# ─── Node editor ─────────────────────────────────────────────────────────────

def render_node_editor():
    if not st.session_state.selected_node:
        st.markdown('<div class="info-box">👆 Click ✏️ on a component in the canvas to edit its properties.</div>', unsafe_allow_html=True)
        return

    node = get_node_by_id(st.session_state.selected_node)
    if not node:
        return

    st.markdown(f"### {node['icon']} {node['label']}")
    st.markdown(f'<span class="tag {CATEGORY_TAG_CLASS.get(node["category"],"")}">{node["category"]}</span> <span style="font-size:0.7rem;color:#475569;">ID: {node["id"]}</span>', unsafe_allow_html=True)
    st.divider()

    node["label"] = st.text_input("Display Name", value=node["label"])

    if node.get("config"):
        st.markdown("**Configuration**")
        updated_config = {}
        for key, val in node["config"].items():
            if isinstance(val, bool):
                updated_config[key] = st.checkbox(key, value=val)
            elif isinstance(val, int):
                updated_config[key] = st.number_input(key, value=val, step=1)
            elif isinstance(val, float):
                updated_config[key] = st.number_input(key, value=val)
            elif isinstance(val, list):
                updated_config[key] = val  # skip list editing for now
            else:
                updated_config[key] = st.text_input(key, value=str(val))
        node["config"] = updated_config

    # Update in session state
    for i, n in enumerate(st.session_state.nodes):
        if n["id"] == node["id"]:
            st.session_state.nodes[i] = node
            break


# ─── IaC Generation ──────────────────────────────────────────────────────────

def render_iac_panel():
    nodes = st.session_state.nodes
    provider = st.session_state.provider
    iac_type = st.session_state.iac_type

    if not nodes:
        st.markdown('<div class="warn-box">⚠️ Add components to the canvas first.</div>', unsafe_allow_html=True)
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("⚙️ Generate IaC", type="primary", use_container_width=True):
            with st.spinner("Generating IaC…"):
                try:
                    edges = st.session_state.edges
                    project = st.session_state.project_name

                    if iac_type == "cloudformation" and provider == "aws":
                        st.session_state.cf_template = generate_cloudformation(nodes, edges, project)
                        log_event(f"CloudFormation generated: {len(nodes)} resources")

                    st.session_state.tofu_files = generate_opentofu(nodes, edges, provider, project)
                    log_event(f"OpenTofu generated: {len(nodes)} resources for {provider}")
                    st.success("✅ IaC generated successfully!")
                except Exception as e:
                    st.error(f"Generation error: {e}")
                    log_event(str(e), "ERROR")

    with c2:
        has_key = bool(st.session_state.gemini_key or st.session_state.openai_key)
        if st.button("🤖 AI Enhance", use_container_width=True, disabled=not has_key):
            with st.spinner("AI analyzing architecture…"):
                try:
                    iac_str = ""
                    if st.session_state.tofu_files:
                        iac_str = st.session_state.tofu_files.get("main.tf", "")
                    elif st.session_state.cf_template:
                        iac_str = cloudformation_to_yaml(st.session_state.cf_template)

                    result = ai_enhance_iac(
                        nodes, st.session_state.edges, provider, iac_type,
                        iac_str, st.session_state.gemini_key, st.session_state.openai_key,
                        st.session_state.llm_provider
                    )
                    st.session_state.ai_enhanced = result
                    log_event("AI enhancement completed")
                    st.success("✅ AI analysis done!")
                except Exception as e:
                    st.error(f"AI error: {e}")
                    log_event(str(e), "ERROR")

    with c3:
        has_iac = st.session_state.tofu_files or st.session_state.cf_template
        if st.button("📦 Export ZIP", use_container_width=True, disabled=not has_iac):
            try:
                pkg = build_export_package(
                    nodes, st.session_state.edges, provider,
                    st.session_state.project_name,
                    st.session_state.cf_template,
                    st.session_state.tofu_files,
                    st.session_state.ai_analysis or st.session_state.ai_enhanced
                )
                st.download_button(
                    "⬇️ Download Package",
                    data=pkg,
                    file_name=f"{st.session_state.project_name.replace(' ', '_')}_iac.zip",
                    mime="application/zip",
                    use_container_width=True
                )
                log_event("ZIP export downloaded")
            except Exception as e:
                st.error(f"Export error: {e}")

    st.divider()

    # IaC Output tabs
    if st.session_state.tofu_files or st.session_state.cf_template:
        tab_names = ["⚙️ OpenTofu"]
        if st.session_state.cf_template:
            tab_names += ["☁️ CloudFormation YAML", "☁️ CloudFormation JSON"]
        if st.session_state.ai_enhanced:
            tab_names.append("🤖 AI Review")

        tabs = st.tabs(tab_names)
        tab_idx = 0

        if st.session_state.tofu_files:
            with tabs[tab_idx]:
                tab_idx += 1
                tf_tab = st.tabs(list(st.session_state.tofu_files.keys()))
                for i, (fname, content) in enumerate(st.session_state.tofu_files.items()):
                    with tf_tab[i]:
                        st.markdown(f'<div class="code-block"><pre>{content}</pre></div>', unsafe_allow_html=True)
                        st.download_button(f"⬇️ {fname}", content, file_name=fname, key=f"dl_{fname}")

        if st.session_state.cf_template:
            with tabs[tab_idx]:
                yaml_str = cloudformation_to_yaml(st.session_state.cf_template)
                st.markdown(f'<div class="code-block"><pre>{yaml_str}</pre></div>', unsafe_allow_html=True)
                st.download_button("⬇️ template.yaml", yaml_str, file_name="template.yaml")
            tab_idx += 1

            with tabs[tab_idx]:
                json_str = cloudformation_to_json(st.session_state.cf_template)
                st.markdown(f'<div class="code-block"><pre>{json_str}</pre></div>', unsafe_allow_html=True)
                st.download_button("⬇️ template.json", json_str, file_name="template.json")
            tab_idx += 1

        if st.session_state.ai_enhanced:
            with tabs[tab_idx]:
                st.markdown(st.session_state.ai_enhanced)


# ─── AI Assistant ─────────────────────────────────────────────────────────────

def render_ai_assistant():
    has_key = bool(st.session_state.gemini_key or st.session_state.openai_key)

    if not has_key:
        st.markdown('<div class="warn-box">⚠️ Add a Gemini or OpenAI API key in Settings (sidebar) to use AI features.</div>', unsafe_allow_html=True)
        return

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### 💬 AI Chat Assistant")
        # Display history
        for msg in st.session_state.chat_history[-10:]:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                st.markdown(f"""
                <div style="background:#1a2236;border:1px solid #1e2d45;border-radius:8px;padding:10px 14px;margin:6px 0;text-align:right;">
                    <div style="font-size:0.7rem;color:#475569;margin-bottom:4px;">You</div>
                    <div style="font-size:0.82rem;color:#f1f5f9;">{content}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background:#0e1c30;border:1px solid #1e3a5f;border-radius:8px;padding:10px 14px;margin:6px 0;">
                    <div style="font-size:0.7rem;color:#475569;margin-bottom:4px;">🤖 AI</div>
                    <div style="font-size:0.82rem;color:#94a3b8;white-space:pre-wrap;">{content}</div>
                </div>
                """, unsafe_allow_html=True)

        user_input = st.text_area("Ask about your architecture…", height=80, key="chat_input", label_visibility="collapsed", placeholder="Ask anything: security review, cost estimate, missing components…")

        if st.button("📨 Send", use_container_width=True) and user_input.strip():
            with st.spinner("Thinking…"):
                try:
                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    response = ai_chat(
                        user_input,
                        {"nodes": st.session_state.nodes, "provider": st.session_state.provider},
                        st.session_state.chat_history,
                        st.session_state.gemini_key, st.session_state.openai_key,
                        st.session_state.llm_provider
                    )
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    log_event("AI chat response received")
                    st.rerun()
                except Exception as e:
                    st.error(f"Chat error: {e}")
                    log_event(str(e), "ERROR")

        if st.session_state.chat_history:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

    with c2:
        st.markdown("### ✨ AI Architecture Generator")
        desc = st.text_area(
            "Describe your architecture in plain English:",
            height=100,
            placeholder="e.g. A scalable web app with a load balancer, two web servers, a PostgreSQL database, Redis cache, and S3 for file storage"
        )
        if st.button("🪄 Generate Architecture", use_container_width=True):
            if desc.strip():
                with st.spinner("AI generating architecture…"):
                    try:
                        result = ai_generate_from_description(
                            desc, st.session_state.provider,
                            st.session_state.gemini_key, st.session_state.openai_key,
                            st.session_state.llm_provider
                        )
                        if result.get("error"):
                            st.warning("AI returned a description instead of structured JSON. Showing summary:")
                            st.info(result.get("summary", ""))
                        else:
                            # Merge AI nodes into canvas
                            from components.cloud_components import get_component_by_id
                            id_map = {}
                            for ai_node in result.get("nodes", []):
                                comp = get_component_by_id(ai_node["component_id"], st.session_state.provider)
                                if comp:
                                    comp["label"] = ai_node.get("label", comp["label"])
                                    nid = add_node(comp)
                                    id_map[ai_node["id"]] = nid

                            for ai_edge in result.get("edges", []):
                                src_id = id_map.get(ai_edge["source"])
                                tgt_id = id_map.get(ai_edge["target"])
                                if src_id and tgt_id:
                                    add_edge(src_id, tgt_id, ai_edge.get("label", ""))

                            summary = result.get("summary", "")
                            st.success(f"✅ Generated {len(result.get('nodes', []))} components!")
                            if summary:
                                st.info(f"📋 {summary}")
                            log_event(f"AI generated {len(result.get('nodes',[]))} components from description")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Generation error: {e}")
                        log_event(str(e), "ERROR")

        st.divider()
        st.markdown("### 📊 AI Architecture Analysis")
        if st.session_state.nodes:
            if st.button("🔍 Analyze Architecture", use_container_width=True):
                with st.spinner("Analyzing…"):
                    try:
                        analysis = ai_analyze_architecture(
                            st.session_state.nodes, st.session_state.edges,
                            st.session_state.provider,
                            st.session_state.gemini_key, st.session_state.openai_key,
                            st.session_state.llm_provider
                        )
                        st.session_state.ai_analysis = analysis
                        log_event("Architecture analysis completed")
                    except Exception as e:
                        st.error(f"Analysis error: {e}")

            if st.session_state.ai_analysis:
                st.markdown(st.session_state.ai_analysis)
        else:
            st.markdown('<div class="info-box">Add components to the canvas first.</div>', unsafe_allow_html=True)


# ─── Logs panel ──────────────────────────────────────────────────────────────

def render_logs():
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### 📋 Session Log")
        if st.session_state.generation_log:
            log_text = "\n".join(reversed(st.session_state.generation_log[-50:]))
            st.markdown(f'<div class="code-block"><pre style="font-size:0.72rem;">{log_text}</pre></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-box">No events yet in this session.</div>', unsafe_allow_html=True)

        if st.button("🗑️ Clear Session Log"):
            st.session_state.generation_log = []
            st.rerun()

    with c2:
        st.markdown("### 📁 File Logs")
        n = st.slider("Lines to show", 20, 200, 50, step=10)
        log_content = get_log_contents(n)
        st.markdown(f'<div class="code-block"><pre style="font-size:0.7rem;">{log_content}</pre></div>', unsafe_allow_html=True)
        st.download_button("⬇️ Download Log File", log_content, file_name="arch2iac.log")
        st.caption(f"Log file: `{get_log_file_path()}`")


# ─── Diagram export ──────────────────────────────────────────────────────────

def render_export():
    nodes = st.session_state.nodes
    edges = st.session_state.edges

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### 💾 Save / Load Diagram")
        diagram_json = diagram_to_json(nodes, edges, st.session_state.provider, st.session_state.project_name)
        st.download_button(
            "⬇️ Export Diagram (JSON)",
            data=diagram_json,
            file_name=f"{st.session_state.project_name.replace(' ','_')}_diagram.json",
            mime="application/json",
            use_container_width=True
        )

        uploaded = st.file_uploader("📤 Import Diagram (JSON)", type=["json"])
        if uploaded:
            try:
                data = json.loads(uploaded.read())
                st.session_state.nodes = data.get("nodes", [])
                st.session_state.edges = data.get("edges", [])
                st.session_state.project_name = data.get("meta", {}).get("project_name", "ImportedProject")
                st.session_state.provider = data.get("meta", {}).get("provider", "aws")
                st.success(f"✅ Loaded {len(st.session_state.nodes)} components!")
                log_event(f"Diagram imported: {st.session_state.project_name}")
                st.rerun()
            except Exception as e:
                st.error(f"Import error: {e}")

    with c2:
        st.markdown("### 📦 Full Export Package")
        if st.button("⚙️ Generate All IaC for Export", use_container_width=True):
            if nodes:
                with st.spinner("Generating all IaC…"):
                    st.session_state.cf_template = generate_cloudformation(nodes, edges, st.session_state.project_name) if st.session_state.provider == "aws" else None
                    st.session_state.tofu_files = generate_opentofu(nodes, edges, st.session_state.provider, st.session_state.project_name)
                    log_event("Full IaC generated for export")
                    st.success("✅ Ready!")

        pkg = build_export_package(
            nodes, edges, st.session_state.provider, st.session_state.project_name,
            st.session_state.cf_template, st.session_state.tofu_files,
            st.session_state.ai_analysis
        )
        st.download_button(
            "📦 Download Full Package (ZIP)",
            data=pkg,
            file_name=f"{st.session_state.project_name.replace(' ','_')}_full.zip",
            mime="application/zip",
            use_container_width=True
        )
        st.caption("Includes: OpenTofu files, CloudFormation, diagram JSON, AI analysis, deployment guide")


# ─── Main Layout ─────────────────────────────────────────────────────────────

def main():
    render_sidebar()

    # Header
    prov = st.session_state.provider
    pmeta = PROVIDER_META[prov]
    st.markdown(f"""
    <div class="arch-header">
        <div>
            <div class="arch-title">🏗️ Arch2IaC</div>
            <div class="arch-subtitle">Enterprise Architecture → Infrastructure as Code Generator</div>
        </div>
        <div style="margin-left:auto;display:flex;gap:10px;align-items:center;">
            <div class="provider-badge provider-{prov}">{pmeta['icon']} {pmeta['label']}</div>
            <div class="provider-badge" style="color:#94a3b8;">
                {'⚙️ OpenTofu' if st.session_state.iac_type == 'opentofu' else '☁️ CloudFormation'}
            </div>
            <div class="provider-badge" style="color:#94a3b8;">
                📂 {st.session_state.project_name}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Main tabs
    tab_canvas, tab_iac, tab_ai, tab_export, tab_logs = st.tabs([
        "🎨 Canvas", "⚙️ IaC Output", "🤖 AI Assistant", "📦 Export", "📋 Logs"
    ])

    with tab_canvas:
        st.markdown("### 🎨 Architecture Canvas")
        st.caption("Add components from the sidebar · Click a node or use the dropdown below to edit/connect/delete · Drag nodes to reposition")
        # Graph at full width (avoids nested-columns errors from inner st.columns calls)
        render_canvas()
        # Property editor below, in its own top-level column pair
        if st.session_state.nodes:
            st.divider()
            _ec, _ee = st.columns([1, 1])
            with _ec:
                st.markdown("#### ✏️ Property Editor")
                render_node_editor()

    with tab_iac:
        st.markdown("### ⚙️ Infrastructure as Code")
        render_iac_panel()

    with tab_ai:
        render_ai_assistant()

    with tab_export:
        render_export()

    with tab_logs:
        render_logs()


if __name__ == "__main__":
    main()
