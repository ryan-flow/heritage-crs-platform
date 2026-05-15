from typing import Any


def success(data: Any = None, message: str = "success", code: int = 0) -> dict:
    return {"code": code, "message": message, "data": data}


def error(message: str = "error", status_code: int = 500):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status_code,
        content={"code": -1, "message": message, "data": None}
    )
