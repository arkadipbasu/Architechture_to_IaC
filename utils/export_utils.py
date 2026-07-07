"""
Export utilities — zip files, YAML/JSON/HCL serialization.
"""
import io
import json
import zipfile
import yaml
from datetime import datetime
from typing import Dict


def files_to_zip(files: Dict[str, str]) -> bytes:
    """Pack multiple text files into a ZIP archive and return bytes."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for filename, content in files.items():
            zf.writestr(filename, content)
    buf.seek(0)
    return buf.read()


def diagram_to_json(nodes: list, edges: list, provider: str, project_name: str) -> str:
    """Serialize diagram state to JSON."""
    data = {
        "meta": {
            "project_name": project_name,
            "provider": provider,
            "exported_at": datetime.now().isoformat(),
            "version": "1.0"
        },
        "nodes": nodes,
        "edges": edges
    }
    return json.dumps(data, indent=2)


def cloudformation_to_yaml(cf_dict: dict) -> str:
    """Convert CloudFormation dict to YAML string."""
    return yaml.dump(cf_dict, default_flow_style=False, sort_keys=False, allow_unicode=True)


def cloudformation_to_json(cf_dict: dict) -> str:
    """Convert CloudFormation dict to JSON string."""
    return json.dumps(cf_dict, indent=2)


def build_export_package(
    nodes: list,
    edges: list,
    provider: str,
    project_name: str,
    cf_template: dict = None,
    tofu_files: dict = None,
    ai_analysis: str = None
) -> bytes:
    """Build a complete ZIP export package."""
    files = {}

    # Diagram state
    files["diagram.json"] = diagram_to_json(nodes, edges, provider, project_name)

    # CloudFormation
    if cf_template:
        files["cloudformation/template.yaml"] = cloudformation_to_yaml(cf_template)
        files["cloudformation/template.json"] = cloudformation_to_json(cf_template)

    # OpenTofu / Terraform
    if tofu_files:
        for fname, content in tofu_files.items():
            files[f"opentofu/{fname}"] = content

    # AI Analysis
    if ai_analysis:
        files["ai_analysis.md"] = ai_analysis

    # Deployment guide
    files["DEPLOY.md"] = _build_deploy_guide(provider, project_name, nodes)

    return files_to_zip(files)


def _build_deploy_guide(provider: str, project_name: str, nodes: list) -> str:
    guides = {
        "aws": """## AWS Deployment

### CloudFormation
```bash
aws cloudformation deploy \\
  --template-file cloudformation/template.yaml \\
  --stack-name {name} \\
  --capabilities CAPABILITY_NAMED_IAM
```

### OpenTofu
```bash
cd opentofu/
tofu init
tofu plan
tofu apply
```

### Prerequisites
- AWS CLI configured (`aws configure`)
- OpenTofu installed (`brew install opentofu`)
""",
        "azure": """## Azure Deployment

### OpenTofu
```bash
az login
cd opentofu/
tofu init
tofu plan
tofu apply
```

### Prerequisites
- Azure CLI (`brew install azure-cli`)
- OpenTofu (`brew install opentofu`)
""",
        "gcp": """## GCP Deployment

### OpenTofu
```bash
gcloud auth application-default login
cd opentofu/
tofu init
tofu plan
tofu apply
```

### Prerequisites
- Google Cloud SDK (`brew install --cask google-cloud-sdk`)
- OpenTofu (`brew install opentofu`)
""",
        "openstack": """## OpenStack Deployment

### OpenTofu
```bash
source openstack-rc.sh   # Load your OpenStack credentials
cd opentofu/
tofu init
tofu plan
tofu apply
```

### Prerequisites
- OpenStack CLI configured
- OpenTofu (`brew install opentofu`)
"""
    }

    guide = guides.get(provider, "See provider documentation.")
    return f"# {project_name} — Deployment Guide\n\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{guide}\n\n## Resources\n" + \
           "\n".join(f"- {n.get('label', n['id'])} (`{n.get('component_id', 'unknown')}`)" for n in nodes)
