"""Unit tests for the capability-based security sandbox."""

import pytest
from backend.app.security.sandbox import SecuritySandbox
from backend.app.security.secret_redactor import SecretRedactor
from backend.app.models.security import SecurityViolationType


def test_sandbox_allows_safe_tools():
    sandbox = SecuritySandbox(allowed_namespaces=["default", "prod"])
    
    # Allowed list pods
    res = sandbox.validate_tool_call("k8s_list_pods", {"namespace": "default"})
    assert res.is_valid is True
    assert res.violation_type is None
    
    # Allowed prometheus query
    res2 = sandbox.validate_tool_call("prometheus_query", {"query": "rate(http_requests_total[5m])"})
    assert res2.is_valid is True


def test_sandbox_blocks_forbidden_tools():
    sandbox = SecuritySandbox()
    
    # Attempt to execute forbidden tool
    res = sandbox.validate_tool_call("k8s_delete_pod", {"pod_name": "checkout-xyz"})
    assert res.is_valid is False
    assert res.violation_type == SecurityViolationType.FORBIDDEN_VERB
    assert len(sandbox.audit_log) == 1
    assert sandbox.audit_log[0].blocked is True


def test_sandbox_blocks_secret_access():
    sandbox = SecuritySandbox()
    
    # Attempt to read secret
    res = sandbox.validate_tool_call("k8s_get_resource_config", {
        "namespace": "default",
        "resource_type": "Secret",
        "resource_name": "db-credentials"
    })
    assert res.is_valid is False
    assert res.violation_type == SecurityViolationType.SECRET_ACCESS_ATTEMPT


def test_sandbox_blocks_destructive_keywords():
    sandbox = SecuritySandbox()
    
    # Attempt to pass dangerous command in an argument
    res = sandbox.validate_tool_call("k8s_get_pod", {
        "namespace": "default",
        "pod_name": "checkout; rm -rf /"
    })
    assert res.is_valid is False
    assert res.violation_type == SecurityViolationType.PARAMETER_TAMPERING


def test_secret_redactor():
    raw_log = "Connection error to postgresql://user:my_secret_pass123@db:5432 with Bearer eyJhbGciOiJIUzI1Ni.abc.xyz"
    redacted = SecretRedactor.redact_text(raw_log)
    assert "my_secret_pass123" not in redacted
    assert "[REDACTED_AUTH]" in redacted or "[REDACTED_SECRET]" in redacted

    struct_data = {
        "service": "checkout",
        "db_password": "super_secret_db_pass",
        "config": {
            "token": "secret_token_value",
            "host": "postgres.default.svc"
        }
    }
    redacted_struct = SecretRedactor.redact_structure(struct_data)
    assert redacted_struct["db_password"] == "[REDACTED_SECRET]"
    assert redacted_struct["config"]["token"] == "[REDACTED_SECRET]"
    assert redacted_struct["config"]["host"] == "postgres.default.svc"
