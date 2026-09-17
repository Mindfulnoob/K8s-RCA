"""Secret redaction filter for logs and Kubernetes manifests."""

import re
from typing import Any, Dict, List, Union


class SecretRedactor:
    """Recursively redacts sensitive patterns, tokens, passwords, and credentials."""

    PATTERNS: List[re.Pattern] = [
        # Bearer tokens
        re.compile(r"(Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*", re.IGNORECASE),
        # Basic auth passwords
        re.compile(r"(Basic\s+)[A-Za-z0-9\-\._~\+\/]+=*", re.IGNORECASE),
        # Passwords in URLs
        re.compile(r"(://[^:]+:)([^@]+)(@)", re.IGNORECASE),
        # Key-value assignments (password=..., token=..., secret=...)
        re.compile(r"((?:password|passwd|secret|token|api_?key|access_?key|auth_?token|credential)[\s:=]+)(['\"][^'\"]+['\"]|[^\s,;]+)", re.IGNORECASE),
        # Private Keys
        re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+PRIVATE KEY-----", re.MULTILINE),
        # JWT tokens
        re.compile(r"(eyJ[a-zA-Z0-9_\-]+\.eyJ[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+)"),
    ]

    SENSITIVE_FIELD_NAMES = {
        "password",
        "passwd",
        "secret",
        "token",
        "apikey",
        "api_key",
        "access_token",
        "client_secret",
        "private_key",
        "tls.key",
        "db_password",
    }

    @classmethod
    def redact_text(cls, text: str) -> str:
        """Redacts sensitive matches in plain text."""
        if not text:
            return text
        result = text
        for pattern in cls.PATTERNS:
            if "PRIVATE KEY" in pattern.pattern:
                result = pattern.sub("[REDACTED_PRIVATE_KEY]", result)
            elif "://" in pattern.pattern:
                result = pattern.sub(r"\1[REDACTED_AUTH]\3", result)
            elif pattern.groups >= 2:
                result = pattern.sub(r"\1[REDACTED_SECRET]", result)
            else:
                result = pattern.sub("[REDACTED_SECRET]", result)
        return result

    @classmethod
    def redact_structure(cls, data: Union[Dict[str, Any], List[Any], str, Any]) -> Any:
        """Recursively traverses a Python dict/list and redacts sensitive keys and values."""
        if isinstance(data, str):
            return cls.redact_text(data)
        elif isinstance(data, dict):
            redacted_dict = {}
            for k, v in data.items():
                lower_k = str(k).lower().replace("-", "_")
                if any(sens in lower_k for sens in cls.SENSITIVE_FIELD_NAMES):
                    redacted_dict[k] = "[REDACTED_SECRET]"
                else:
                    redacted_dict[k] = cls.redact_structure(v)
            return redacted_dict
        elif isinstance(data, list):
            return [cls.redact_structure(item) for item in data]
        return data
