from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class XmlItemPreviewResponse(BaseModel):
    codigo_principal: str = Field(..., description="Código principal del ítem en la factura SRI", max_length=50)
    codigo_auxiliar: Optional[str] = Field(None, description="Código auxiliar del ítem (opcional en SRI)", max_length=50)
    descripcion: str = Field(..., description="Descripción del ítem del XML", max_length=300)
    cantidad_documento: Decimal = Field(..., description="Cantidad según la factura original", gt=0)
    precio_unitario: Decimal = Field(..., description="Precio unitario sin impuestos del XML", gt=0)
    descuento: Decimal = Field(..., description="Descuento total del ítem", ge=0)
    precio_total_sin_imp: Decimal = Field(..., description="Total del ítem sin impuestos", ge=0)
    tarifa_iva: Decimal = Field(..., description="Porcentaje de IVA tomado del XML", ge=0)
    valor_iva: Decimal = Field(..., description="Monto de IVA calculado por el SRI", ge=0)
    peso_documento: Decimal = Field(..., description="Peso total del ítem (de detAdicional Peso)", ge=0)
    peso_unitario: Decimal = Field(..., description="Peso unitario: peso_documento / cantidad_documento", ge=0)


class XmlPreviewResponse(BaseModel):
    clave_acceso: str = Field(..., description="Clave de acceso única del SRI (49 dígitos)", max_length=49)
    ruc_emisor: str = Field(..., description="RUC del emisor de la factura", max_length=13)
    razon_social_emisor: str = Field(..., description="Razón social del emisor", max_length=300)
    nombre_comercial: Optional[str] = Field(None, description="Nombre comercial del emisor (opcional)", max_length=300)
    numero_factura: str = Field(..., description="Número de factura: estab-ptoEmi-secuencial", max_length=20)
    fecha_emision: date = Field(..., description="Fecha de emisión de la factura")
    direccion_emisor: Optional[str] = Field(None, description="Dirección del establecimiento emisor")
    tipo_emision: int = Field(..., description="Tipo de emisión: 1=normal, 2=indisponibilidad")
    ambiente: int = Field(..., description="Ambiente SRI: 1=pruebas, 2=producción")
    ruc_comprador: str = Field(..., description="RUC del comprador (receptor)", max_length=13)
    razon_social_comprador: str = Field(..., description="Razón social del comprador", max_length=300)
    direccion_comprador: Optional[str] = Field(None, description="Dirección del comprador")
    total_sin_impuestos: Decimal = Field(..., description="Subtotal de la factura sin impuestos", ge=0)
    total_descuento: Decimal = Field(..., description="Total de descuentos aplicados", ge=0)
    subtotal_iva_0: Decimal = Field(..., description="Base imponible de ítems con IVA 0%", ge=0)
    subtotal_gravado: Decimal = Field(..., description="Base imponible de ítems gravados con IVA", ge=0)
    valor_iva: Decimal = Field(..., description="Monto total de IVA de la factura", ge=0)
    importe_total: Decimal = Field(..., description="Total de la factura con impuestos", gt=0)
    moneda: str = Field(..., description="Moneda de la factura", max_length=10)
    items: list[XmlItemPreviewResponse] = Field(..., description="Ítems del detalle de la factura")


class XmlItemResponse(XmlItemPreviewResponse):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Identificador único del ítem persistido")
    cantidad_ingresada: Decimal = Field(..., description="Cantidad ya ingresada al Kardex", ge=0)
    cantidad_pendiente: Decimal = Field(..., description="Cantidad pendiente de ingresar al Kardex", ge=0)


class XmlResponse(XmlPreviewResponse):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Identificador único del XML persistido")
    created_at: datetime = Field(..., description="Fecha y hora de registro en el sistema")
    items: list[XmlItemResponse] = Field(..., description="Ítems del detalle persistidos")  # type: ignore[assignment]


class XmlListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Identificador único del XML")
    clave_acceso: str = Field(..., description="Clave de acceso SRI")
    numero_factura: str = Field(..., description="Número de factura: estab-ptoEmi-secuencial")
    fecha_emision: date = Field(..., description="Fecha de emisión de la factura")
    razon_social_emisor: str = Field(..., description="Razón social del emisor")
    ruc_emisor: str = Field(..., description="RUC del emisor")
    ruc_comprador: str = Field(..., description="RUC del comprador")
    razon_social_comprador: str = Field(..., description="Razón social del comprador")
    importe_total: Decimal = Field(..., description="Total de la factura con impuestos")
    created_at: datetime = Field(..., description="Fecha y hora de registro")


class XmlItemPendienteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Identificador del xml_item")
    codigo_principal: str = Field(..., description="Código principal del ítem")
    descripcion: str = Field(..., description="Descripción del ítem")
    cantidad_documento: Decimal = Field(..., description="Cantidad total de la factura")
    cantidad_ingresada: Decimal = Field(..., description="Cantidad ya ingresada al Kardex")
    cantidad_pendiente: Decimal = Field(..., description="Cantidad pendiente de ingresar al Kardex")
    precio_unitario: Decimal = Field(..., description="Precio unitario sin impuestos")
    precio_total_sin_imp: Decimal = Field(..., description="Total del ítem sin impuestos")
    peso_unitario: Decimal = Field(..., description="Peso por unidad calculado en backend")
