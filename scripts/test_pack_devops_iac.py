#!/usr/bin/env python3
"""Focused positive and negative tests for pack-devops-iac validators."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = ROOT / "packs" / "pack-devops-iac" / "scripts" / "rules.py"


def _load_rules():
    spec = importlib.util.spec_from_file_location("pack_devops_iac_rules_test", RULES_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.RULES


def _violations(rules, file_path: str, content: str) -> list[dict]:
    out = []
    lines = content.strip().splitlines()
    for rule in rules:
        out.extend(rule(Path(file_path), lines, {}))
    return out


def test_pack_devops_iac_rules() -> None:
    rules = _load_rules()

    terraform_bad = _violations(rules, "/tmp/main.tf", '''
terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}
module "network" {
  source = "git::https://example.test/network.git"
}
''')
    terraform_rule_ids = {item["rule"] for item in terraform_bad}
    assert "pack-devops-iac-terraform-unpinned-provider" in terraform_rule_ids
    assert "pack-devops-iac-terraform-unpinned-module" in terraform_rule_ids

    workload_bad = _violations(rules, "/tmp/deployment.yaml", '''
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  template:
    spec:
      containers:
        - name: api
          image: registry.example/api:latest
''')
    workload_rule_ids = {item["rule"] for item in workload_bad}
    assert "pack-devops-iac-k8s-mutable-image-tag" in workload_rule_ids
    assert "pack-devops-iac-k8s-missing-readiness-probe" in workload_rule_ids
    assert "pack-devops-iac-k8s-missing-resource-requests" in workload_rule_ids

    workflow_bad = _violations(rules, "/tmp/repo/.github/workflows/deploy.yml", '''
name: deploy
jobs:
  apply:
    steps:
      - run: terraform apply -auto-approve
''')
    assert any(item["rule"] == "pack-devops-iac-terraform-apply-without-plan"
               for item in workflow_bad)

    runbook_bad = _violations(
        rules, "/tmp/workspaces/default/runbooks/deploy-api.md", '''
# API deployment
Run the release workflow and verify the health dashboard.
''')
    assert any(item["rule"] == "pack-devops-iac-deployment-no-rollback"
               for item in runbook_bad)

    clean_cases = [
        ("/tmp/main.tf", '''
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
module "network" {
  source = "git::https://example.test/network.git?ref=v1.2.3"
}
'''),
        ("/tmp/deployment.yaml", '''
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  template:
    spec:
      containers:
        - name: api
          image: registry.example/api:v1.2.3
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
'''),
        ("/tmp/repo/.github/workflows/deploy.yml", '''
name: deploy
jobs:
  apply:
    steps:
      - run: terraform plan -out=reviewed.tfplan
      - run: terraform apply reviewed.tfplan
'''),
        ("/tmp/workspaces/default/runbooks/deploy-api.md", '''
# API deployment
Deploy the release, verify readiness, and rollback with rollout undo on failure.
'''),
    ]
    for file_path, content in clean_cases:
        assert not _violations(rules, file_path, content), file_path


if __name__ == "__main__":
    test_pack_devops_iac_rules()
    print("All pack-devops-iac tests passed")
