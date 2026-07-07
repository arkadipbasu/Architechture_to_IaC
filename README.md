# 🏗️ Arch2IaC — Enterprise Architecture to Infrastructure as Code

> Visual cloud architecture designer that generates production-ready CloudFormation and OpenTofu/Terraform code with AI enhancement.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🎨 **Visual Canvas** | Drag-and-drop component palette with 86 cloud components |
| ☁️ **4 Cloud Providers** | AWS · Microsoft Azure · Google Cloud · OpenStack |
| ⚙️ **OpenTofu / Terraform** | Complete `.tf` files: `main.tf`, `variables.tf`, `outputs.tf`, `terraform.tfvars` |
| ☁️ **CloudFormation** | AWS-native YAML + JSON templates |
| 🤖 **AI Enhancement** | Gemini 1.5 Flash + GPT-4o-mini for code review, generation, and chat |
| 📦 **ZIP Export** | Full package with IaC, diagram JSON, AI analysis, deployment guide |
| 📋 **Logging** | Loguru structured logging (file rotation, session log panel) |
| 💾 **Diagram Save/Load** | Export/import diagram state as JSON |

---

## 🚀 Quick Start (macOS)

```bash
# Clone / unzip the project
cd arch2iac

# Launch (auto-installs dependencies)
bash run.sh
```

Open **http://localhost:8501** in your browser.

---

## 🔧 Manual Setup

```bash
# Install dependencies
pip3 install -r requirements.txt --break-system-packages

# Run
streamlit run app.py --server.port 8501
```

---

## 🤖 AI Setup

Add API keys in the sidebar **AI Settings** panel:

| LLM | Get Key |
|---|---|
| **Gemini** (recommended, free tier) | https://aistudio.google.com/app/apikey |
| **OpenAI** | https://platform.openai.com/api-keys |

AI features:
- **AI Enhance** — reviews your generated IaC for security issues and improvements
- **Architecture Generator** — describe in plain English, get a full diagram
- **Architecture Analyzer** — security, cost, HA, compliance assessment
- **Chat Assistant** — ask anything about your architecture

---

## 🏗️ Component Library

### AWS (27 components)
Compute: EC2, Lambda, ECS, EKS, Auto Scaling  
Networking: VPC, Subnet, ALB, CloudFront, Route53, API Gateway, Security Group  
Storage: S3, EBS, EFS  
Database: RDS, DynamoDB, ElastiCache, Aurora  
Security: IAM Role, KMS, WAF  
Messaging: SQS, SNS, EventBridge  
Monitoring: CloudWatch, X-Ray  

### Azure (23 components)
Compute, Networking, Storage, Database, Security, Messaging, Monitoring

### GCP (22 components)
Compute Engine, Cloud Run, GKE, Cloud SQL, Firestore, Pub/Sub, and more

### OpenStack (14 components)
Nova, Neutron, Octavia, Cinder, Swift, Trove, Keystone

---

## 📁 Project Structure

```
arch2iac/
├── app.py                    # Main Streamlit dashboard
├── run.sh                    # macOS launch script
├── requirements.txt
├── .streamlit/
│   └── config.toml           # Dark theme config
├── components/
│   └── cloud_components.py   # All 86 cloud component definitions
├── generators/
│   ├── iac_generator.py      # CloudFormation + OpenTofu generators
│   └── llm_generator.py      # Gemini + OpenAI integration
├── utils/
│   ├── logging_config.py     # Loguru logging setup
│   └── export_utils.py       # ZIP/YAML/JSON export helpers
└── logs/                     # Auto-created log files
```

---

## 📦 Export Package Contents

The ZIP download includes:
```
MyProject_iac.zip
├── diagram.json              # Importable diagram state
├── opentofu/
│   ├── main.tf               # Resources + provider config
│   ├── variables.tf          # All input variables
│   ├── outputs.tf            # Resource outputs
│   ├── terraform.tfvars      # Variable values
│   └── README.md
├── cloudformation/           # AWS only
│   ├── template.yaml
│   └── template.json
├── ai_analysis.md            # AI review (if generated)
└── DEPLOY.md                 # Step-by-step deployment guide
```

---

## 🔒 Security Notes

- API keys are stored only in Streamlit session state (not persisted to disk)
- Generated IaC uses placeholder secrets — use AWS Secrets Manager / Azure Key Vault / GCP Secret Manager in production
- Generated IAM roles use least-privilege starting points — review before applying

---

## 🛠️ OpenTofu Deployment

```bash
cd opentofu/
tofu init
tofu plan -var-file=terraform.tfvars
tofu apply -var-file=terraform.tfvars
```

Install OpenTofu: `brew install opentofu`

---

Built with: **Streamlit** · **OpenTofu** · **Loguru** · **Gemini** · **OpenAI** · **Python 3.12**
