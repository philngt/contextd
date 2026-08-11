#!/usr/bin/env python3
"""Focused regression tests for pack-devops-iac validators."""

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


def _by_rule(violations: list[dict], rule_id: str) -> list[dict]:
    return [item for item in violations if item["rule"] == rule_id]


def _test_terraform_dependency_pinning(rules) -> None:
    bad = _violations(rules, "/tmp/main.tf", '''
terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}
module "unversioned" {
  source = "git::https://example.test/unversioned.git"
}
module "develop_branch" {
  source = "git::https://example.test/develop.git?ref=develop"
  version = "1.0.0"
}
module "feature_branch" {
  source = "git::https://example.test/feature.git?ref=feature/foo"
}
''')
    assert len(_by_rule(
        bad, "pack-devops-iac-terraform-unpinned-provider"
    )) == 1, bad
    assert len(_by_rule(
        bad, "pack-devops-iac-terraform-unpinned-module"
    )) == 3, bad

    clean = _violations(rules, "/tmp/main.tf", '''
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
module "registry" {
  source  = "hashicorp/consul/aws"
  version = "0.11.0"
}
module "git_commit" {
  source = "git::https://example.test/network.git?ref=0123456789abcdef0123456789abcdef01234567"
}
module "local" {
  source = "./modules/local"
}
''')
    assert not clean, clean


def _test_apply_consumes_saved_plan(rules) -> None:
    plan_but_fresh_apply = _violations(
        rules, "/tmp/repo/.github/workflows/deploy.yml", '''
name: deploy
jobs:
  deploy:
    steps:
      - run: terraform plan -out=reviewed.tfplan
      - run: terraform apply -auto-approve
''')
    assert len(_by_rule(
        plan_but_fresh_apply,
        "pack-devops-iac-terraform-apply-without-saved-plan",
    )) == 1, plan_but_fresh_apply

    unrelated_jobs = _violations(
        rules, "/tmp/repo/.github/workflows/deploy.yml", '''
name: deploy
jobs:
  preview:
    steps:
      - run: terraform plan -out=preview.tfplan
  production:
    steps:
      - run: terraform apply -auto-approve
''')
    assert len(_by_rule(
        unrelated_jobs,
        "pack-devops-iac-terraform-apply-without-saved-plan",
    )) == 1, unrelated_jobs

    mixed_applies = _violations(
        rules, "/tmp/repo/.github/workflows/deploy.yml", '''
name: deploy
jobs:
  deploy:
    steps:
      - run: terraform apply reviewed.tfplan
      - run: tofu apply -auto-approve
''')
    assert len(_by_rule(
        mixed_applies,
        "pack-devops-iac-terraform-apply-without-saved-plan",
    )) == 1, mixed_applies

    saved_plan = _violations(
        rules, "/tmp/repo/.github/workflows/deploy.yml", '''
name: deploy
jobs:
  deploy:
    steps:
      - run: terraform apply reviewed.tfplan
      - run: tofu apply "$PLAN_FILE"
''')
    assert not _by_rule(
        saved_plan, "pack-devops-iac-terraform-apply-without-saved-plan"
    ), saved_plan


def _test_k8s_per_document_and_container(rules) -> None:
    multi_document = _violations(rules, "/tmp/workloads.yaml", '''
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  template:
    spec:
      containers:
        - name: api
          image: registry.example/api@sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
        - name: sidecar
          image: registry.example/sidecar@sha256:1123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: worker
spec:
  template:
    spec:
      containers:
        - name: worker
          image: registry.example/worker@sha256:2123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
''')
    assert len(_by_rule(
        multi_document, "pack-devops-iac-k8s-missing-readiness-probe"
    )) == 2, multi_document
    assert len(_by_rule(
        multi_document, "pack-devops-iac-k8s-missing-resource-requests"
    )) == 2, multi_document
    assert not _by_rule(
        multi_document, "pack-devops-iac-k8s-image-not-digest-pinned"
    ), multi_document


def _test_k8s_digest_pinning(rules) -> None:
    images = _violations(rules, "/tmp/deployment.yaml", '''
apiVersion: apps/v1
kind: Deployment
metadata:
  name: image-cases
spec:
  template:
    spec:
      containers:
        - name: untagged
          image: registry.example/api
          readinessProbe: {}
          resources:
            requests: {}
        - name: stable
          image: registry.example/api:stable
          readinessProbe: {}
          resources:
            requests: {}
        - name: semver
          image: registry.example/api:v1.2.3
          readinessProbe: {}
          resources:
            requests: {}
        - name: digest
          image: registry.example/api@sha256:3123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
          readinessProbe: {}
          resources:
            requests: {}
''')
    image_violations = _by_rule(
        images, "pack-devops-iac-k8s-image-not-digest-pinned"
    )
    assert len(image_violations) == 3, images
    messages = "\n".join(item["message"] for item in image_violations)
    assert "untagged" in messages
    assert "stable" in messages
    assert "semver" in messages
    assert "container 'digest'" not in messages


def _test_deployment_rollback(rules) -> None:
    bad = _violations(
        rules, "/tmp/workspaces/default/runbooks/deploy-api.md", '''
# API deployment
Run the release workflow and verify the health dashboard.
''')
    assert len(_by_rule(
        bad, "pack-devops-iac-deployment-no-rollback"
    )) == 1, bad

    clean = _violations(
        rules, "/tmp/workspaces/default/runbooks/deploy-api.md", '''
# API deployment
Deploy the release, verify readiness, and rollback with rollout undo on failure.
''')
    assert not _by_rule(
        clean, "pack-devops-iac-deployment-no-rollback"
    ), clean


def test_pack_devops_iac_rules() -> None:
    rules = _load_rules()
    _test_terraform_dependency_pinning(rules)
    _test_apply_consumes_saved_plan(rules)
    _test_k8s_per_document_and_container(rules)
    _test_k8s_digest_pinning(rules)
    _test_deployment_rollback(rules)


if __name__ == "__main__":
    test_pack_devops_iac_rules()
    print("All pack-devops-iac tests passed")
