"""Observability Provider Abstract Base Classes."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime


class BaseKubernetesProvider(ABC):
    """Abstract interface for Kubernetes cluster inspection."""

    @abstractmethod
    def list_pods(self, namespace: str = "default", label_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_pod(self, pod_name: str, namespace: str = "default") -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_deployment(self, name: str, namespace: str = "default") -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_service(self, name: str, namespace: str = "default") -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_events(self, namespace: str = "default", involved_object: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_nodes(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_restarts(self, namespace: str = "default") -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_resource_config(self, resource_type: str, resource_name: str, namespace: str = "default") -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_deployment_history(self, name: str, namespace: str = "default") -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_config_change_history(self, name: str, namespace: str = "default") -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_dependency_graph(self, namespace: str = "default") -> Dict[str, Any]:
        pass


class BasePrometheusProvider(ABC):
    """Abstract interface for Prometheus metrics inspection."""

    @abstractmethod
    def query(self, query: str, time: Optional[datetime] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def range_query(self, query: str, start: datetime, end: datetime, step: str = "30s") -> Dict[str, Any]:
        pass


class BaseLokiProvider(ABC):
    """Abstract interface for Loki logs inspection."""

    @abstractmethod
    def query_logs(self, query: str, limit: int = 50, start: Optional[datetime] = None, end: Optional[datetime] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def query_previous_container_logs(self, pod_name: str, container_name: Optional[str] = None, namespace: str = "default", tail_lines: int = 100) -> List[Dict[str, Any]]:
        pass


class BaseJaegerProvider(ABC):
    """Abstract interface for distributed tracing inspection."""

    @abstractmethod
    def query_traces(self, service_name: str, operation: Optional[str] = None, limit: int = 10, tags: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_trace(self, trace_id: str) -> Dict[str, Any]:
        pass
