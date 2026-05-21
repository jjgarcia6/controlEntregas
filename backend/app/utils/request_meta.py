from fastapi import Request


def get_client_ip(request: Request) -> str | None:
    """
    Devuelve la IP real del cliente.

    En Cloud Run, el load balancer de GCP inyecta X-Forwarded-For con la IP
    real como primera entrada y reemplaza cualquier valor que el cliente
    intente inyectar. Para entornos sin proxy (dev local), cae a
    request.client.host.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    return request.client.host if request.client else None
