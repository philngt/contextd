"""Data-only retrieval presets; no I/O, classification or execution behavior.

Pack workstreams are authored in pack.yaml. The legacy map is used only at
input normalization for old manifests; remove it after their migration window.
Defaults retain the previous scores, budgets and precedence.
"""

INTENT_KEYWORDS = {
    "implement_feature": [
        "add", "implement", "create", "build", "write", "support", "enable",
        "introduce", "new feature", "feature", "endpoint", "api", "consumer",
        "producer", "service", "handler", "controller",
    ],
    "fix_bug": [
        "fix", "bug", "debug", "broken", "breaks", "error", "crash", "fails", "failing",
        "not working", "doesn't work", "exception", "regression", "issue",
    ],
    "design": [
        "design", "architecture", "approach", "how should", "structure",
        "pattern", "refactor", "restructure", "organize", "strategy", "proposal",
    ],
    "incident": [
        "incident", "outage", "down", "spike", "latency", "error rate",
        "production", "live", "oncall", "alert", "paged",
    ],
    "review": [
        "review", "pr", "pull request", "audit", "check", "verify", "assess",
        "code review", "walkthrough", "sign-off", "drift", "remediation",
        "đánh giá", "danh gia", "kiểm tra", "kiem tra", "nghiệm thu", "nghiem thu",
    ],
}

WORKSTREAM_KEYWORDS = {
    "product": [
        "product", "brief", "prd", "okr", "roadmap", "persona", "journey",
        "metric", "customer", "feature request",
    ],
    "business_analysis": [
        "requirement", "business requirement", "acceptance criteria", "user story",
        "gherkin", "stakeholder", "process map", "workflow map", "brd",
    ],
    "quality": [
        "test case", "test plan", "qa", "qc", "quality", "defect", "bug triage",
        "regression", "release gate", "performance", "benchmark", "profiling",
        "audit", "drift", "remediation", "acceptance criteria", "verification method",
        "đánh giá", "danh gia", "nghiệm thu", "nghiem thu",
    ],
    "security": [
        "security", "threat", "vulnerability", "pentest", "attack surface",
        "risk rating", "control", "authz", "secret",
    ],
    "design": [
        "design system", "accessibility", "a11y", "user flow", "wireframe",
        "ux", "ui", "prototype", "copy", "microcopy",
    ],
    "ops": [
        "incident", "runbook", "oncall", "outage", "alert", "rollback",
        "restore", "release", "deploy", "team sync",
    ],
    "domain_research": [
        "research", "interview", "regulation", "policy", "evidence", "source",
        "customer signal", "analytics", "support ticket",
    ],
}

LEGACY_PACK_WORKSTREAMS = {
    "pack-product": "product",
    "pack-ba": "business_analysis",
    "pack-qc": "quality",
    "pack-security": "security",
    "pack-ui-ux": "design",
    "pack-dba": "ops",
    "pack-solo-builder": "domain_research",
    "pack-operator-steering": "quality",
}

AUDIENCE_BY_WORKSTREAM = {
    "engineering": "engineering",
    "product": "product",
    "business_analysis": "ba",
    "quality": "qc",
    "security": "security",
    "design": "design",
    "ops": "ops",
    "domain_research": "domain",
}

SECTION_POLICY = {
    "contract": ["all"],
    "pattern": ["Flow", "Default Config", "Failure Strategy", "Implementation Rules", "Rules"],
    "project": ["Purpose", "Flow", "Config Overrides", "Failure"],
    "service": ["Purpose", "Flow", "Config Overrides", "Failure"],
    "domain": ["States", "Transitions", "Business Rules"],
    "workflow": ["States", "Transitions", "Business Rules"],
    "architecture": ["all"],
    "decision": ["Status", "Context", "Decision", "Consequences"],
    "runbook": ["Symptoms", "Diagnosis", "Mitigation", "Rollback"],
    "product": ["Problem", "Target User", "Success Metric", "Acceptance Criteria"],
    "requirement": ["Actor", "Trigger", "Business Outcome", "Acceptance Criteria"],
    "design": ["Flow", "Accessibility", "UX Writing", "Edge Cases"],
    "quality": ["Evidence", "Scope", "Risk", "Decision"],
    "evidence": ["Verified Facts", "Open Questions", "Source Summary"],
    "pitfalls": ["all"],
    "common-pitfalls": ["all"],
    "workspace-profile": ["all"],
    "engine-guidance": ["all"],
    "engine-rule": ["all"],
    "workspace-rule": ["all"],
    "pack-rule": ["all"],
    "pack-metadata": ["all"],
    "pack-knowledge": ["all"],
    "operator": ["all"],
}

CATEGORY_BUDGETS = {
    "contract": 2,
    "pattern": 2,
    "project": 2,
    "service": 2,
    "domain": 1,
    "workflow": 1,
    "architecture": 1,
    "decision": 2,
    "runbook": 2,
    "product": 2,
    "requirement": 2,
    "design": 2,
    "quality": 2,
    "evidence": 2,
    "pitfalls": 3,
    "common-pitfalls": 3,
    "workspace-profile": 1,
    "engine-guidance": 1,
    "engine-rule": 2,
    "workspace-rule": 3,
    "pack-rule": 3,
    "pack-metadata": 1,
    "pack-knowledge": 3,
    "operator": 3,
}

PRIORITY = {
    "contract": 0,
    "pattern": 1,
    "project": 2,
    "service": 2,
    "domain": 3,
    "workflow": 3,
    "architecture": 4,
    "decision": 4,
    "runbook": 2,
    "product": 2,
    "requirement": 2,
    "design": 2,
    "quality": 2,
    "evidence": 3,
    "pitfalls": 1,
    "common-pitfalls": 1,
    "workspace-profile": 2,
    "engine-guidance": 2,
    "engine-rule": 1,
    "workspace-rule": 1,
    "pack-rule": 1,
    "pack-metadata": 1,
    "pack-knowledge": 1,
    "operator": 1,
}

WORKSTREAM_BUDGETS = {
    "engineering": CATEGORY_BUDGETS,
    "product": {
        **CATEGORY_BUDGETS,
        "product": 3,
        "requirement": 2,
        "domain": 1,
        "decision": 1,
        "contract": 1,
        "pattern": 1,
    },
    "business_analysis": {
        **CATEGORY_BUDGETS,
        "requirement": 3,
        "domain": 2,
        "product": 1,
        "contract": 1,
        "runbook": 1,
    },
    "quality": {
        **CATEGORY_BUDGETS,
        "quality": 2,
        "evidence": 2,
        "runbook": 2,
        "project": 1,
        "contract": 1,
    },
    "security": {
        **CATEGORY_BUDGETS,
        "contract": 2,
        "runbook": 2,
        "project": 1,
        "architecture": 1,
        "decision": 1,
    },
    "design": {
        **CATEGORY_BUDGETS,
        "design": 3,
        "product": 1,
        "requirement": 1,
        "domain": 1,
        "decision": 1,
    },
    "ops": {
        **CATEGORY_BUDGETS,
        "runbook": 3,
        "evidence": 2,
        "project": 1,
        "architecture": 1,
    },
    "domain_research": {
        **CATEGORY_BUDGETS,
        "evidence": 3,
        "domain": 2,
        "product": 1,
        "requirement": 1,
        "design": 1,
    },
}

WORKSTREAM_PRIORITY = {
    "engineering": {
        "priority": ["contracts", "patterns", "project_docs", "domain_knowledge"],
        "context_goal": "prepare_code_change",
    },
    "product": {
        "priority": [
            "product_context", "requirements", "domain_knowledge",
            "source_evidence", "contracts", "patterns",
        ],
        "context_goal": "shape_product_decision",
    },
    "business_analysis": {
        "priority": [
            "requirements", "domain_knowledge", "product_context",
            "contracts", "operational_runbooks",
        ],
        "context_goal": "clarify_testable_requirements",
    },
    "quality": {
        "priority": [
            "quality_evidence", "operational_runbooks", "requirements",
            "project_docs", "contracts",
        ],
        "context_goal": "support_quality_decision",
    },
    "security": {
        "priority": [
            "contracts", "operational_runbooks", "source_evidence",
            "project_docs", "architecture",
        ],
        "context_goal": "support_security_review",
    },
    "design": {
        "priority": [
            "design_context", "product_context", "requirements",
            "domain_knowledge", "source_evidence",
        ],
        "context_goal": "shape_user_experience",
    },
    "ops": {
        "priority": [
            "operational_runbooks", "source_evidence", "project_docs",
            "architecture", "contracts",
        ],
        "context_goal": "support_operational_response",
    },
    "domain_research": {
        "priority": [
            "source_evidence", "domain_knowledge", "requirements",
            "product_context", "design_context",
        ],
        "context_goal": "ground_domain_understanding",
    },
}

INTENT_PRECEDENCE = ["incident", "fix_bug", "review", "design", "implement_feature"]

WORKSTREAM_PRECEDENCE = [
    "security", "ops", "quality", "business_analysis",
    "product", "design", "domain_research", "engineering",
]
