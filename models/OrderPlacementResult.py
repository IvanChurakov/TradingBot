class OrderPlacementResult:
    def __init__(self, success, error_message=None, result=None):
        self.success = success
        self.error_message = error_message
        self.result = result

    def __repr__(self):
        if self.success:
            return f"OrderPlacementResult(success=True, result={self.result})"
        else:
            return f"OrderPlacementResult(success=False, error_message='{self.error_message}')"