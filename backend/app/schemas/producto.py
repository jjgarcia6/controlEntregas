from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProductoResponse(BaseModel):
    id: UUID = Field(..., description="Identificador único del producto")
    codigo_principal: str = Field(..., description="Código principal (clave de negocio)", max_length=50)
    descripcion: str = Field(..., description="Descripción del producto", max_length=300)
    unidad_medida: Optional[str] = Field(None, description="Unidad de medida (opcional)", max_length=20)
    peso_unitario: Decimal = Field(..., description="Peso unitario del producto (del último XML)", ge=0)
    saldo_cantidad: Decimal = Field(..., description="Saldo actual en Kardex (0 hasta Fase 3)", ge=0)
    saldo_valor: Decimal = Field(..., description="Valor del saldo en Kardex (0 hasta Fase 3)", ge=0)
