from src.app.utils.exceptions import BaseAppException

def error_response(exception: type[BaseAppException], description: str | None = None) -> dict:
    return {
        exception.status_code: {
            "description": description,
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code":    exception.error_code,
                            "message": "string",
                            "details": {}
                        }
                    }
                }
            }
        }
    }