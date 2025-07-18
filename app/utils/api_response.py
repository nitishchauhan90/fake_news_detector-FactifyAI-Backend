def api_response(message: str, status: int, data: any = None) -> dict:
    return {
        "message": message,
        "status": status,
        "success": status < 400,
        "data": data
    }