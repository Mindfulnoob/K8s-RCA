"""Base tool classes and registry."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field
from backend.app.security.sandbox import SecuritySandbox
from backend.app.security.secret_redactor import SecretRedactor
from backend.app.security.injection_defense import InjectionDefense


class ToolResult(BaseModel):
    success: bool
    tool_name: str
    output: Any
    error: Optional[str] = None
    security_flagged: bool = False
    security_note: Optional[str] = None
    raw_evidence_envelope: Optional[str] = None


class BaseTool(ABC):
    """Abstract base class for all agent tools."""
    name: str
    description: str
    schema: Type[BaseModel]

    def __init__(self, sandbox: Optional[SecuritySandbox] = None):
        self.sandbox = sandbox or SecuritySandbox()

    def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        """Executes the tool with sandbox validation and secret redaction."""
        # 1. Sandbox validation
        validation = self.sandbox.validate_tool_call(self.name, arguments)
        if not validation.is_valid:
            return ToolResult(
                success=False,
                tool_name=self.name,
                output=None,
                error=f"SECURITY SANDBOX BLOCKED EXECUTION: {validation.violation_reason}",
                security_flagged=True,
                security_note=str(validation.violation_type)
            )

        sanitized_args = validation.sanitized_arguments or arguments

        # 2. Call implementation
        try:
            raw_output = self._run(**sanitized_args)
            
            # 3. Secret Redaction
            redacted_output = SecretRedactor.redact_structure(raw_output)
            
            # 4. Prompt Injection Defense Scan
            content_str = str(redacted_output)
            is_injected, detected_patterns = InjectionDefense.scan_for_injection(content_str)
            
            envelope = None
            if isinstance(redacted_output, (str, list, dict)):
                envelope = InjectionDefense.wrap_untrusted_data(
                    data_type=self.name,
                    content=content_str[:4000],
                    source=f"tool:{self.name}"
                )

            return ToolResult(
                success=True,
                tool_name=self.name,
                output=redacted_output,
                security_flagged=is_injected,
                security_note=f"Adversarial patterns neutralized: {', '.join(detected_patterns)}" if is_injected else None,
                raw_evidence_envelope=envelope
            )
        except Exception as e:
            return ToolResult(
                success=False,
                tool_name=self.name,
                output=None,
                error=f"Execution error in {self.name}: {str(e)}"
            )

    @abstractmethod
    def _run(self, **kwargs) -> Any:
        pass


class ToolRegistry:
    """Central registry of all permissible agent tools."""

    def __init__(self, sandbox: Optional[SecuritySandbox] = None):
        self.sandbox = sandbox or SecuritySandbox()
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        tool.sandbox = self.sandbox
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tool_names(self) -> List[str]:
        return list(self._tools.keys())

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Returns JSON schema definitions for LLM function calling."""
        definitions = []
        for name, tool in self._tools.items():
            definitions.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.schema.model_json_schema()
            })
        return definitions

    def execute(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                success=False,
                tool_name=name,
                output=None,
                error=f"Tool '{name}' is not registered in capability registry."
            )
        return tool.execute(arguments)
