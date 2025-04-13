from abc import ABC, abstractmethod
from typing import Any, Callable


class BaseAPIManager(ABC):
    @abstractmethod
    def get_http_session(self) -> Any:
        pass

    @abstractmethod
    def safe_api_call(self, api_func: Callable, *args, **kwargs) -> Any:
        pass