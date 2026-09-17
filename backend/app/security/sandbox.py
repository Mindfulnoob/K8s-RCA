"""Capability-based security sandbox for agent tool execution."""

import re
from typing import Any, Dict, List, Set, Tuple
from backend.app.models.security import ToolCallValidation, SecurityViolationType, SecurityAuditEntry


class SecuritySandbox:
    """Enforces strict read-only execution boundaries and argument validation."""

    ALLOWED_TOOLS: Set[str] = {
        "k8s_list_pods",
        "k8s_get_pod",
        "k8s_get_deployment",
        "k8s_get_service",
        "k8s_get_events",
        "k8s_get_nodes",
        "k8s_get_restarts",
        "k8s_get_resource_config",
        "logs_query",
        "logs_query_previous_container",
        "prometheus_query",
        "prometheus_range_query",
        "traces_query",
        "deployment_history",
        "config_change_history",
        "dependency_graph",
    }

    FORBIDDEN_KEYWORDS: List[re.Pattern] = [
        re.compile(r"\bdelete\b", re.IGNORECASE),
        re.compile(r"\bexec\b", re.IGNORECASE),
        re.compile(r"\bport-forward\b", re.IGNORECASE),
        re.compile(r"\bpatch\b", re.IGNORECASE),
        re.compile(r"\bapply\b", re.IGNORECASE),
        re.compile(r"\bsecrets?\b", re.IGNORECASE),
        re.compile(r"\brm\s+-rf\b", re.IGNORECASE),
        re.compile(r"\bcurl\b", re.IGNORECASE),
        re.compile(r"\bwget\b", re.IGNORECASE),
        re.compile(r"\bbash\b", re.IGNORECASE),
        re.compile(r"\bsh\b", re.IGNORECASE),
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
    ]

    DANGEROUS_RESOURCES: Set[str] = {
        "secret",
        "secrets",
        "serviceaccounttoken",
        "token",
        "clusterrolebinding",
        "rolebinding",
    }

    def __init__(self, allowed_namespaces: List[str] = None):
        self.allowed_namespaces = set(allowed_namespaces or ["default", "kube-system", "monitoring", "prod", "staging"])
        self.audit_log: List[SecurityAuditEntry] = []

    def validate_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> ToolCallValidation:
        """Validates that a tool and its arguments conform strictly to the read-only sandbox."""
        # 1. Check if tool is allowed
        if tool_name not in self.ALLOWED_TOOLS:
            audit = SecurityAuditEntry(
                id=f"audit-sec-{len(self.audit_log)+1}",
                event_type="UNAUTHORIZED_TOOL",
                action=tool_name,
                details={"arguments": arguments},
                blocked=True,
                warning_message=f"Execution of unapproved tool '{tool_name}' blocked by sandbox policy."
            )
            self.audit_log.append(audit)
            return ToolCallValidation(
                is_valid=False,
                tool_name=tool_name,
                arguments=arguments,
                violation_type=SecurityViolationType.FORBIDDEN_VERB,
                violation_reason=f"Tool '{tool_name}' is not in the permitted read-only capability set."
            )

        # 2. Check namespace restrictions if namespace is provided
        namespace = arguments.get("namespace")
        if namespace and namespace not in self.allowed_namespaces and namespace != "all":
            audit = SecurityAuditEntry(
                id=f"audit-sec-{len(self.audit_log)+1}",
                event_type="UNAUTHORIZED_NAMESPACE",
                action=tool_name,
                target_resource=namespace,
                details={"arguments": arguments},
                blocked=True,
                warning_message=f"Access to namespace '{namespace}' blocked by sandbox policy."
            )
            self.audit_log.append(audit)
            return ToolCallValidation(
                is_valid=False,
                tool_name=tool_name,
                arguments=arguments,
                violation_type=SecurityViolationType.UNAUTHORIZED_NAMESPACE,
                violation_reason=f"Namespace '{namespace}' is not in the allowed list."
            )

        # 3. Check for forbidden resource types (e.g. secret reading)
        resource_type = str(arguments.get("resource_type", "")).lower()
        resource_name = str(arguments.get("resource_name", "")).lower()
        if resource_type in self.DANGEROUS_RESOURCES or any(d in resource_name for d in self.DANGEROUS_RESOURCES):
            audit = SecurityAuditEntry(
                id=f"audit-sec-{len(self.audit_log)+1}",
                event_type="SECRET_ACCESS_ATTEMPT",
                action=tool_name,
                target_resource=resource_name,
                details={"arguments": arguments},
                blocked=True,
                warning_message="Direct access to secrets or sensitive credentials is strictly prohibited."
            )
            self.audit_log.append(audit)
            return ToolCallValidation(
                is_valid=False,
                tool_name=tool_name,
                arguments=arguments,
                violation_type=SecurityViolationType.SECRET_ACCESS_ATTEMPT,
                violation_reason="Direct access to Secrets or tokens is strictly forbidden."
            )

        # 4. Check for command injection or dangerous verb patterns in string arguments
        sanitized_args = dict(arguments)
        for key, val in arguments.items():
            if isinstance(val, str):
                for pattern in self.FORBIDDEN_KEYWORDS:
                    if pattern.search(val):
                        # If it's a log query searching for the word "delete" or "error", allow harmless search,
                        # but block destructive commands or exec sequences
                        if tool_name in ["logs_query", "logs_query_previous_container", "prometheus_query"] and key == "filter_pattern":
                            continue
                        
                        audit = SecurityAuditEntry(
                            id=f"audit-sec-{len(self.audit_log)+1}",
                            event_type="FORBIDDEN_KEYWORD_DETECTED",
                            action=tool_name,
                            details={"argument_key": key, "matched_pattern": pattern.pattern, "value": val},
                            blocked=True,
                            warning_message=f"Forbidden keyword '{pattern.pattern}' detected in parameter '{key}'."
                        )
                        self.audit_log.append(audit)
                        return ToolCallValidation(
                            is_valid=False,
                            tool_name=tool_name,
                            arguments=arguments,
                            violation_type=SecurityViolationType.PARAMETER_TAMPERING,
                            violation_reason=f"Parameter '{key}' contains forbidden keyword pattern: '{pattern.pattern}'."
                        )

        # 5. Enforce limits on numeric arguments to prevent Denial-of-Service / buffer exhaustion
        if "limit" in sanitized_args:
            sanitized_args["limit"] = min(int(sanitized_args["limit"]), 200)
        if "tail_lines" in sanitized_args:
            sanitized_args["tail_lines"] = min(int(sanitized_args["tail_lines"]), 500)

        # Approved
        return ToolCallValidation(
            is_valid=True,
            tool_name=tool_name,
            arguments=arguments,
            sanitized_arguments=sanitized_args
        )
