from fastapi import status
from src.app.utils.exceptions import (BaseAppException, JWTExpired, InvalidJWTSignature,
                                      InvalidJWT, JWTDecodeError, RefreshTokenNotGranted,
                                      SessionExpired)

def error_response(exception: type[BaseAppException], description: str | None = None) -> dict:
    return {
        exception.status_code: {
            "description": description,
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code":    exception.error_code,
                            "message": exception.default_message or "string",
                            "details": {}
                        }
                    }
                }
            }
        }
    }

def errors_list(status_code: status, description: str, examples: dict) -> dict:
    return {
        status_code: {
            "description": description,
            "content": {
                "application/json": {
                    "examples": examples
                }
            }
        }
    }

def error_example(exception: type[BaseAppException], description: str | None = None) -> dict:
    return {
        description: {
            "summary": description,
            "value": {
                "error": {
                    "code":    exception.error_code,
                    "message": exception.default_message or "string",
                    "details": {}
                }
            }
        }
    }

JWT_ERRORS = {
    **error_example(JWTExpired, "JWT Expired Error"),
    **error_example(InvalidJWTSignature, "Invalid JWT Signature Error"),
    **error_example(InvalidJWT, "Invalid JWT Error"),
    **error_example(JWTDecodeError, "JWT Decode Error")
}

SESSION_ERRORS = {
    **error_example(RefreshTokenNotGranted, "Refresh Token Not Granted Error"),
    **error_example(SessionExpired, "Session Not Found Or Expired Error")
}