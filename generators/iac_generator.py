"""
IaC Generators: CloudFormation (AWS) and OpenTofu/Terraform (Azure, GCP, OpenStack, AWS)
"""
import json
import yaml
from typing import Dict, List, Any
from datetime import datetime


# ─────────────────────────────────────────────
#  CloudFormation Generator (AWS native)
# ─────────────────────────────────────────────

CF_RESOURCE_MAP = {
    "aws_ec2": {
        "type": "AWS::EC2::Instance",
        "props": lambda c: {
            "InstanceType": c.get("instance_type", "t3.micro"),
            "ImageId": c.get("ami", "ami-0c55b159cbfafe1f0"),
            "Tags": [{"Key": "Name", "Value": c.get("label", "EC2")}]
        }
    },
    "aws_lambda": {
        "type": "AWS::Lambda::Function",
        "props": lambda c: {
            "FunctionName": c.get("label", "MyFunction").replace(" ", ""),
            "Runtime": c.get("runtime", "python3.11"),
            "Handler": "index.handler",
            "MemorySize": c.get("memory", 128),
            "Timeout": c.get("timeout", 30),
            "Role": {"Fn::GetAtt": ["LambdaExecutionRole", "Arn"]},
            "Code": {"ZipFile": "def handler(event, context):\n    return {'statusCode': 200}"}
        }
    },
    "aws_s3": {
        "type": "AWS::S3::Bucket",
        "props": lambda c: {
            "BucketName": c.get("label", "my-bucket").lower().replace(" ", "-"),
            "VersioningConfiguration": {"Status": "Enabled" if c.get("versioning") else "Suspended"},
            "BucketEncryption": {
                "ServerSideEncryptionConfiguration": [{
                    "ServerSideEncryptionByDefault": {"SSEAlgorithm": c.get("encryption", "AES256")}
                }]
            }
        }
    },
    "aws_vpc": {
        "type": "AWS::EC2::VPC",
        "props": lambda c: {
            "CidrBlock": c.get("cidr", "10.0.0.0/16"),
            "EnableDnsHostnames": c.get("enable_dns", True),
            "EnableDnsSupport": True,
            "Tags": [{"Key": "Name", "Value": c.get("label", "VPC")}]
        }
    },
    "aws_subnet": {
        "type": "AWS::EC2::Subnet",
        "props": lambda c: {
            "CidrBlock": c.get("cidr", "10.0.1.0/24"),
            "AvailabilityZone": c.get("availability_zone", "us-east-1a"),
            "Tags": [{"Key": "Name", "Value": c.get("label", "Subnet")}]
        }
    },
    "aws_rds": {
        "type": "AWS::RDS::DBInstance",
        "props": lambda c: {
            "DBInstanceClass": c.get("instance_class", "db.t3.micro"),
            "Engine": c.get("engine", "postgres"),
            "AllocatedStorage": str(c.get("allocated_storage", 20)),
            "MasterUsername": "admin",
            "MasterUserPassword": "{{resolve:secretsmanager:DBPassword}}"
        }
    },
    "aws_dynamodb": {
        "type": "AWS::DynamoDB::Table",
        "props": lambda c: {
            "BillingMode": c.get("billing_mode", "PAY_PER_REQUEST"),
            "AttributeDefinitions": [{"AttributeName": c.get("hash_key", "id"), "AttributeType": "S"}],
            "KeySchema": [{"AttributeName": c.get("hash_key", "id"), "KeyType": "HASH"}]
        }
    },
    "aws_sqs": {
        "type": "AWS::SQS::Queue",
        "props": lambda c: {
            "MessageRetentionPeriod": c.get("message_retention", 345600),
            "VisibilityTimeout": c.get("visibility_timeout", 30)
        }
    },
    "aws_sns": {
        "type": "AWS::SNS::Topic",
        "props": lambda c: {
            "TopicName": c.get("label", "MyTopic").replace(" ", "")
        }
    },
    "aws_alb": {
        "type": "AWS::ElasticLoadBalancingV2::LoadBalancer",
        "props": lambda c: {
            "Scheme": c.get("scheme", "internet-facing"),
            "Type": c.get("type", "application"),
            "Tags": [{"Key": "Name", "Value": c.get("label", "ALB")}]
        }
    },
    "aws_cloudwatch": {
        "type": "AWS::Logs::LogGroup",
        "props": lambda c: {
            "RetentionInDays": c.get("retention_days", 30)
        }
    },
    "aws_sg": {
        "type": "AWS::EC2::SecurityGroup",
        "props": lambda c: {
            "GroupDescription": c.get("label", "Security Group"),
            "SecurityGroupIngress": [{
                "IpProtocol": c.get("protocol", "tcp"),
                "FromPort": c.get("ingress_port", 443),
                "ToPort": c.get("ingress_port", 443),
                "CidrIp": "0.0.0.0/0"
            }]
        }
    },
    "aws_iam_role": {
        "type": "AWS::IAM::Role",
        "props": lambda c: {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": c.get("assume_role_service", "ec2.amazonaws.com")},
                    "Action": "sts:AssumeRole"
                }]
            }
        }
    },
    "aws_kms": {
        "type": "AWS::KMS::Key",
        "props": lambda c: {
            "EnableKeyRotation": c.get("enable_rotation", True),
            "PendingWindowInDays": c.get("deletion_window", 10),
            "KeyPolicy": {
                "Version": "2012-10-17",
                "Statement": [{"Effect": "Allow", "Principal": {"AWS": {"Fn::Sub": "arn:aws:iam::${AWS::AccountId}:root"}}, "Action": "kms:*", "Resource": "*"}]
            }
        }
    },
    "aws_elasticache": {
        "type": "AWS::ElastiCache::CacheCluster",
        "props": lambda c: {
            "Engine": c.get("engine", "redis"),
            "CacheNodeType": c.get("node_type", "cache.t3.micro"),
            "NumCacheNodes": 1
        }
    },
    "aws_cloudfront": {
        "type": "AWS::CloudFront::Distribution",
        "props": lambda c: {
            "DistributionConfig": {
                "Enabled": True,
                "PriceClass": c.get("price_class", "PriceClass_100"),
                "DefaultCacheBehavior": {
                    "ViewerProtocolPolicy": "redirect-to-https",
                    "AllowedMethods": ["GET", "HEAD"],
                    "ForwardedValues": {"QueryString": False, "Cookies": {"Forward": "none"}}
                }
            }
        }
    },
}


def generate_cloudformation(nodes: list, edges: list, project_name: str = "MyArchitecture") -> dict:
    """Generate AWS CloudFormation template from diagram nodes."""
    template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": f"{project_name} - Generated by Arch2IaC on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "Parameters": {
            "Environment": {
                "Type": "String",
                "Default": "production",
                "AllowedValues": ["development", "staging", "production"]
            }
        },
        "Outputs": {},
        "Resources": {}
    }

    resource_ids = []
    for node in nodes:
        comp_id = node.get("component_id", "")
        node_id = node["id"].replace("-", "").replace(" ", "")
        label = node.get("label", node_id)
        user_config = node.get("config", {})

        if comp_id in CF_RESOURCE_MAP:
            mapper = CF_RESOURCE_MAP[comp_id]
            merged_config = {**user_config, "label": label}
            resource = {
                "Type": mapper["type"],
                "Properties": mapper["props"](merged_config)
            }
            template["Resources"][f"{node_id}Resource"] = resource
            resource_ids.append(node_id)
        else:
            # Generic placeholder
            template["Resources"][f"{node_id}Resource"] = {
                "Type": "AWS::CloudFormation::WaitConditionHandle",
                "Metadata": {
                    "Note": f"Component '{comp_id}' — manual configuration needed",
                    "Label": label
                }
            }

    # Add some auto-outputs
    for node in nodes:
        comp_id = node.get("component_id", "")
        node_id = node["id"].replace("-", "").replace(" ", "")
        if comp_id == "aws_s3":
            template["Outputs"][f"{node_id}BucketName"] = {
                "Value": {"Ref": f"{node_id}Resource"},
                "Description": "S3 Bucket Name"
            }
        elif comp_id == "aws_rds":
            template["Outputs"][f"{node_id}Endpoint"] = {
                "Value": {"Fn::GetAtt": [f"{node_id}Resource", "Endpoint.Address"]},
                "Description": "RDS Endpoint"
            }
        elif comp_id == "aws_alb":
            template["Outputs"][f"{node_id}DNS"] = {
                "Value": {"Fn::GetAtt": [f"{node_id}Resource", "DNSName"]},
                "Description": "Load Balancer DNS"
            }

    return template


# ─────────────────────────────────────────────
#  OpenTofu / Terraform Generator
# ─────────────────────────────────────────────

PROVIDER_CONFIGS = {
    "aws": {
        "terraform": {
            "required_providers": {
                "aws": {
                    "source": "hashicorp/aws",
                    "version": "~> 5.0"
                }
            },
            "required_version": ">= 1.6.0"
        },
        "provider": 'provider "aws" {\n  region = var.aws_region\n}\n',
        "variables": {
            "aws_region": {"type": "string", "default": "us-east-1"},
            "environment": {"type": "string", "default": "production"},
        }
    },
    "azure": {
        "terraform": {
            "required_providers": {
                "azurerm": {
                    "source": "hashicorp/azurerm",
                    "version": "~> 3.0"
                }
            },
            "required_version": ">= 1.6.0"
        },
        "provider": 'provider "azurerm" {\n  features {}\n}\n',
        "variables": {
            "resource_group_name": {"type": "string", "default": "my-resource-group"},
            "location": {"type": "string", "default": "East US"},
            "environment": {"type": "string", "default": "production"},
        }
    },
    "gcp": {
        "terraform": {
            "required_providers": {
                "google": {
                    "source": "hashicorp/google",
                    "version": "~> 5.0"
                }
            },
            "required_version": ">= 1.6.0"
        },
        "provider": 'provider "google" {\n  project = var.project_id\n  region  = var.region\n}\n',
        "variables": {
            "project_id": {"type": "string", "default": "my-gcp-project"},
            "region": {"type": "string", "default": "us-central1"},
            "environment": {"type": "string", "default": "production"},
        }
    },
    "openstack": {
        "terraform": {
            "required_providers": {
                "openstack": {
                    "source": "terraform-provider-openstack/openstack",
                    "version": "~> 1.53"
                }
            },
            "required_version": ">= 1.6.0"
        },
        "provider": 'provider "openstack" {\n  user_name   = var.os_username\n  tenant_name = var.os_tenant\n  password    = var.os_password\n  auth_url    = var.os_auth_url\n}\n',
        "variables": {
            "os_username": {"type": "string", "default": "admin"},
            "os_tenant": {"type": "string", "default": "my-tenant"},
            "os_password": {"type": "string", "sensitive": True},
            "os_auth_url": {"type": "string", "default": "http://controller:5000/v3"},
            "environment": {"type": "string", "default": "production"},
        }
    }
}


def _tofu_resource_block(comp_id: str, resource_name: str, label: str, config: dict) -> str:
    """Generate a single Terraform/OpenTofu resource block."""
    lines = [f'resource "{comp_id}" "{resource_name}" {{']
    lines.append(f'  # {label}')

    def _value(v):
        if isinstance(v, bool):
            return str(v).lower()
        if isinstance(v, str):
            return f'"{v}"'
        return str(v)

    for k, v in config.items():
        if isinstance(v, dict) or isinstance(v, list):
            continue  # skip nested for now
        lines.append(f'  {k} = {_value(v)}')

    # add tags/labels generically
    lines.append('')
    lines.append('  tags = {')
    lines.append(f'    Name        = "{label}"')
    lines.append('    Environment = var.environment')
    lines.append('    ManagedBy   = "opentofu"')
    lines.append('  }')

    lines.append('}')
    lines.append('')
    return '\n'.join(lines)


def generate_opentofu(nodes: list, edges: list, provider: str, project_name: str = "MyArchitecture") -> dict:
    """Generate OpenTofu/Terraform files from diagram nodes."""
    pconfig = PROVIDER_CONFIGS.get(provider, PROVIDER_CONFIGS["aws"])

    files = {}

    # ── main.tf ──
    main_lines = [
        f"# {project_name} - OpenTofu/Terraform",
        f"# Generated by Arch2IaC on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"# Provider: {provider.upper()}",
        "",
        'terraform {',
        f'  required_version = "{pconfig["terraform"]["required_version"]}"',
        '  required_providers {',
    ]
    for pname, pinfo in pconfig["terraform"]["required_providers"].items():
        main_lines.append(f'    {pname} = {{')
        main_lines.append(f'      source  = "{pinfo["source"]}"')
        main_lines.append(f'      version = "{pinfo["version"]}"')
        main_lines.append('    }')
    main_lines += ['  }', '}', '', pconfig["provider"]]

    for node in nodes:
        comp_id = node.get("component_id", "")
        if not comp_id:
            continue
        resource_name = node["id"].replace("-", "_").lower()
        label = node.get("label", resource_name)
        user_config = node.get("config", {})

        main_lines.append(_tofu_resource_block(comp_id, resource_name, label, user_config))

    files["main.tf"] = '\n'.join(main_lines)

    # ── variables.tf ──
    var_lines = [
        f"# Variables for {project_name}",
        ""
    ]
    for var_name, var_info in pconfig["variables"].items():
        var_lines.append(f'variable "{var_name}" {{')
        var_lines.append(f'  type    = {var_info["type"]}')
        if "default" in var_info:
            val = var_info["default"]
            var_lines.append(f'  default = "{val}"' if isinstance(val, str) else f'  default = {val}')
        if var_info.get("sensitive"):
            var_lines.append('  sensitive = true')
        var_lines.append('}')
        var_lines.append('')

    files["variables.tf"] = '\n'.join(var_lines)

    # ── outputs.tf ──
    out_lines = [f"# Outputs for {project_name}", ""]
    for node in nodes:
        node_id = node["id"].replace("-", "_").lower()
        comp_id = node.get("component_id", "")
        label = node.get("label", node_id)
        out_lines.append(f'output "{node_id}_id" {{')
        out_lines.append(f'  description = "ID of {label}"')
        out_lines.append(f'  value       = {comp_id}.{node_id}.id')
        out_lines.append('}')
        out_lines.append('')

    files["outputs.tf"] = '\n'.join(out_lines)

    # ── terraform.tfvars ──
    tfvars_lines = [f"# Terraform variable values for {project_name}", ""]
    for var_name, var_info in pconfig["variables"].items():
        if not var_info.get("sensitive"):
            val = var_info.get("default", "")
            tfvars_lines.append(f'{var_name} = "{val}"')
    files["terraform.tfvars"] = '\n'.join(tfvars_lines)

    # ── README.md ──
    files["README.md"] = f"""# {project_name}

Generated by **Arch2IaC** on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Provider
**{provider.upper()}** — OpenTofu / Terraform

## Resources ({len(nodes)} total)
{chr(10).join(f"- `{n.get('component_id', 'unknown')}` — {n.get('label', n['id'])}" for n in nodes)}

## Deploy

```bash
# Initialize
tofu init

# Plan
tofu plan -var-file=terraform.tfvars

# Apply
tofu apply -var-file=terraform.tfvars -auto-approve
```

## Notes
- Review `variables.tf` and update `terraform.tfvars` with actual values
- Sensitive variables (passwords, secrets) should use environment variables or a secrets manager
- Edges/connections may require manual dependency references (`depends_on`)
"""

    return files
