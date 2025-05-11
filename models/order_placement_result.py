from typing import Optional, Any


class OrderActionResult:
    def __init__(self, success: bool, result: Optional[Any] = None, error_message: Optional[str] = None):
        self.success = success
        self.error_message = error_message
        self.result = result

    def __repr__(self):
        if self.success:
            return f"OrderActionResult(success=True, result={self.result})"
        else:
            return f"OrderActionResult(success=False, error_message='{self.error_message}')"