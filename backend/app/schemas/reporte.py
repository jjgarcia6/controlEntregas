import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FiltrosXmls(BaseModel):
    model_config = ConfigDict(strict=True)
    xml_id: uuid.UUID | None = Field(None, description="Filtra por un XML específico.")
    fecha_desde: date | None = Field(
        None, description="Inicio del rango de fecha_emision."
    )
    fecha_hasta: date | None = Field(
        None, description="Fin del rango de fecha_emision."
    )
    codigo_principal: str | None = Field(
        None, description="Filtra ítems por código de producto."
    )


class FiltrosKardex(BaseModel):
    model_config = ConfigDict(strict=True)
    producto_id: uuid.UUID = Field(
        ..., description="Producto cuyo historial se consulta. Requerido."
    )
    fecha_desde: date | None = Field(
        None, description="Inicio del rango de fecha_movimiento."
    )
    fecha_hasta: date | None = Field(
        None, description="Fin del rango de fecha_movimiento."
    )


class FiltrosEntregas(BaseModel):
    model_config = ConfigDict(strict=True)
    fecha_desde: date | None = Field(
        None, description="Inicio del rango de created_at de entrega."
    )
    fecha_hasta: date | None = Field(
        None, description="Fin del rango de created_at de entrega."
    )
    destinatario_id: uuid.UUID | None = Field(
        None, description="Filtra por destinatario."
    )
    estado: Literal["activa", "eliminada"] | None = Field(
        None, description="Estado de la entrega."
    )


class FiltrosPagos(BaseModel):
    model_config = ConfigDict(strict=True)
    fecha_desde: date | None = Field(
        None, description="Inicio del rango de fecha_pago."
    )
    fecha_hasta: date | None = Field(None, description="Fin del rango de fecha_pago.")
    banco_id: uuid.UUID | None = Field(None, description="Filtra por banco del pago.")
    entrega_id: uuid.UUID | None = Field(
        None, description="Filtra pagos que incluyen esta entrega."
    )


# --- Reporte XMLs ---
class ReporteXmlItemRow(BaseModel):
    codigo_principal: str = Field(..., description="Código del producto en el ítem.")
    descripcion: str = Field(..., description="Descripción del ítem en la factura.")
    cantidad_documento: Decimal = Field(
        ..., description="Cantidad en la factura original."
    )
    cantidad_ingresada: Decimal = Field(
        ..., description="Cantidad ingresada al Kardex."
    )
    cantidad_pendiente: Decimal = Field(
        ..., description="Cantidad aún no ingresada al Kardex."
    )
    precio_unitario: Decimal = Field(..., description="Precio unitario del ítem.")
    precio_total_sin_imp: Decimal = Field(
        ..., description="Total del ítem sin impuestos."
    )


class ReporteXmlRow(BaseModel):
    xml_id: uuid.UUID = Field(..., description="ID del XML.")
    fecha_creacion: datetime = Field(
        ..., description="Fecha de registro en el sistema."
    )
    numero_factura: str = Field(
        ..., description="Número de factura (estab-ptoEmi-sec)."
    )
    fecha_emision: date = Field(..., description="Fecha de emisión del XML.")
    razon_social_emisor: str = Field(..., description="Razón social del emisor.")
    total_sin_impuestos: Decimal = Field(
        ..., description="Total sin impuestos del XML."
    )
    importe_total: Decimal = Field(..., description="Importe total incluido IVA.")
    items: list[ReporteXmlItemRow] = Field(..., description="Ítems del XML.")


class ReporteXmlsResponse(BaseModel):
    total_xmls: int = Field(..., description="Total de XMLs en la respuesta.")
    total_valor: Decimal = Field(
        ..., description="Suma de importe_total de todos los XMLs."
    )
    filas: list[ReporteXmlRow] = Field(..., description="Filas del reporte. Máx 1000.")


# --- Reporte Kardex ---
class ReporteKardexMovimientoRow(BaseModel):
    fecha_movimiento: datetime = Field(..., description="Fecha y hora del movimiento.")
    tipo: str = Field(..., description="ingreso, egreso o reversa_entrega.")
    origen: str = Field(..., description="xml, entrega o reversa_entrega.")
    cantidad: Decimal = Field(..., description="Cantidad del movimiento.")
    peso_unitario: Decimal = Field(..., description="Peso unitario en el movimiento.")
    peso_total: Decimal = Field(..., description="Peso total del movimiento.")
    costo_unitario: Decimal = Field(..., description="Costo unitario del lote.")
    costo_total: Decimal = Field(..., description="Costo total del movimiento.")
    saldo_cantidad: Decimal = Field(
        ..., description="Saldo de cantidad acumulado al momento."
    )
    saldo_valor: Decimal = Field(
        ..., description="Saldo de valor acumulado al momento."
    )


class ReporteKardexResponse(BaseModel):
    producto_codigo: str = Field(..., description="Código principal del producto.")
    producto_descripcion: str = Field(..., description="Descripción del producto.")
    saldo_cantidad_actual: Decimal = Field(..., description="Saldo de cantidad actual.")
    saldo_valor_actual: Decimal = Field(..., description="Saldo de valor actual.")
    movimientos: list[ReporteKardexMovimientoRow] = Field(
        ..., description="Historial ordenado por fecha_movimiento ASC."
    )


# --- Reporte Entregas ---
class ReporteEntregaItemRow(BaseModel):
    codigo_principal: str = Field(..., description="Código del producto entregado.")
    descripcion: str = Field(..., description="Descripción del producto.")
    cantidad: Decimal = Field(..., description="Cantidad entregada.")
    peso_total: Decimal = Field(..., description="Peso total del ítem.")
    costo_unitario: Decimal = Field(
        ..., description="Costo unitario FIFO al momento de entrega."
    )
    costo_total: Decimal = Field(..., description="Costo total del ítem de entrega.")


class ReporteEntregaRow(BaseModel):
    numero: int = Field(..., description="Número secuencial de la entrega.")
    fecha_creacion: datetime = Field(
        ..., description="Fecha de creación de la entrega."
    )
    snap_nombre: str = Field(..., description="Snapshot del nombre del destinatario.")
    snap_identificacion: str = Field(..., description="Snapshot de la identificación.")
    total_entrega: Decimal = Field(..., description="Valor total de la entrega.")
    saldo_pendiente: Decimal = Field(..., description="Monto aún no cobrado.")
    estado: str = Field(..., description="activa o eliminada.")
    items: list[ReporteEntregaItemRow] = Field(..., description="Ítems de la entrega.")


class ReporteEntregasResponse(BaseModel):
    total_entregas: int = Field(..., description="Total de entregas en la respuesta.")
    total_valor: Decimal = Field(
        ..., description="Suma de total_entrega de todas las filas."
    )
    total_cobrado: Decimal = Field(
        ..., description="Suma de montos ya cobrados (total_entrega - saldo_pendiente)."
    )
    total_pendiente: Decimal = Field(
        ..., description="Suma de saldo_pendiente de todas las filas."
    )
    filas: list[ReporteEntregaRow] = Field(
        ..., description="Filas del reporte. Máx 1000."
    )


# --- Reporte Pagos ---
class ReportePagoDistribucionRow(BaseModel):
    entrega_numero: int = Field(..., description="Número de la entrega receptora.")
    snap_nombre: str = Field(
        ..., description="Nombre del destinatario (snapshot de la entrega)."
    )
    monto_aplicado: Decimal = Field(..., description="Monto distribuido a la entrega.")


class ReportePagoRow(BaseModel):
    numero_comprobante: str = Field(..., description="Número de comprobante del pago.")
    fecha_pago: datetime = Field(..., description="Fecha y hora del pago.")
    banco_nombre: str = Field(
        ..., description="Nombre del banco (join desnormalizado)."
    )
    tipo_cuenta: str = Field(
        ..., description="Tipo de cuenta: corriente, ahorros, etc."
    )
    nombre_titular: str = Field(
        ..., description="Nombre del titular del instrumento de pago."
    )
    valor_total: Decimal = Field(..., description="Monto total del pago.")
    valor_aplicado: Decimal = Field(..., description="Monto aplicado a entregas.")
    estado: str = Field(..., description="Estado del pago.")
    distribuciones: list[ReportePagoDistribucionRow] = Field(
        ..., description="Distribución entre entregas."
    )


class ReportePagosResponse(BaseModel):
    total_pagos: int = Field(..., description="Total de pagos en la respuesta.")
    valor_total: Decimal = Field(
        ..., description="Suma de valor_total de todos los pagos."
    )
    filas: list[ReportePagoRow] = Field(..., description="Filas del reporte. Máx 1000.")
