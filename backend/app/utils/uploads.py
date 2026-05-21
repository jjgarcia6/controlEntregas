from fastapi import UploadFile

from app.config import settings
from app.utils.exceptions import ValidacionNegocio

_CHUNK_SIZE = 64 * 1024


async def read_upload_with_limit(file: UploadFile, max_bytes: int) -> bytes:
    """Lee un UploadFile en chunks; aborta apenas se supera max_bytes."""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise ValidacionNegocio(
                f"El archivo supera el tamaño máximo permitido de "
                f"{max_bytes // (1024 * 1024)} MB"
            )
        chunks.append(chunk)
    return b"".join(chunks)


async def read_xml_upload_as_text(file: UploadFile) -> str:
    """Lee un upload XML con el límite configurado y lo decodifica como UTF-8."""
    max_bytes = settings.MAX_XML_UPLOAD_MB * 1024 * 1024
    raw = await read_upload_with_limit(file, max_bytes)
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        raise ValidacionNegocio("El archivo no tiene codificación UTF-8 válida")
