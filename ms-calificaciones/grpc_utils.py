import grpc
from grpc import StatusCode

def map_grpc_error(exc):
    """Map a grpc.RpcError-like object to a Python exception.

    Returns: raises a mapped exception.
    """
    try:
        code = exc.code()
    except Exception:
        raise exc

    details = getattr(exc, 'details', lambda: str(exc))()

    if code == StatusCode.NOT_FOUND:
        raise LookupError(details)
    if code in (StatusCode.UNAUTHENTICATED, StatusCode.PERMISSION_DENIED):
        raise PermissionError(details)
    if code == StatusCode.DEADLINE_EXCEEDED:
        raise TimeoutError(details)
    # default fallback
    raise RuntimeError(details)
