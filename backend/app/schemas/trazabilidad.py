from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

# ─── Nodos reutilizados ────────────────────────────────────────────────────────


class XmlResumen(BaseModel):
    id: UUID = Field(..., description="ID del XML")
    numero_factura: str = Field(
        ..., description="Número de factura (estab-pto-secuencial)"
    )
    fecha_emision: date = Field(..., description="Fecha de emisión del XML")
    ruc_emisor: str = Field(..., description="RUC del emisor")
    razon_social_emisor: str = Field(..., description="Razón social del emisor")
    is_active: bool = Field(
        ..., description="False si el XML fue eliminado (soft delete)"
    )


class XmlItemResumen(BaseModel):
    id: UUID = Field(..., description="ID del ítem del XML")
    codigo_principal: str = Field(..., description="Código principal del producto")
    descripcion: str = Field(..., description="Descripción del ítem en la factura")
    cantidad_ingresada: Decimal = Field(
        ..., description="Cantidad ingresada al Kardex desde este ítem"
    )


class KardexMovimientoResumen(BaseModel):
    id: UUID = Field(..., description="ID del movimiento de Kardex")
    tipo: str = Field(..., description="ingreso | egreso | reversa_entrega")
    fecha_movimiento: datetime = Field(
        ..., description="Fecha y hora del movimiento (ISO 8601)"
    )
    cantidad: Decimal = Field(..., description="Cantidad del movimiento")
    costo_unitario: Decimal = Field(..., description="Costo unitario del lote")
    costo_total: Decimal = Field(..., description="Costo total del movimiento")


class ProductoResumen(BaseModel):
    id: UUID = Field(..., description="ID del producto")
    codigo_principal: str = Field(..., description="Código principal")
    descripcion: str = Field(..., description="Descripción del producto")


class EntregaResumen(BaseModel):
    id: UUID = Field(..., description="ID de la entrega")
    numero: int = Field(..., description="Número secuencial de la entrega")
    snap_nombre: str = Field(
        ..., description="Nombre del destinatario (snapshot inmutable)"
    )
    total_entrega: Decimal = Field(..., description="Valor total de la entrega")
    saldo_pendiente: Decimal = Field(
        ..., description="Saldo pendiente al momento de la consulta"
    )
    estado: str = Field(..., description="activa | eliminada")


class PagoResumen(BaseModel):
    id: UUID = Field(..., description="ID del pago")
    numero_comprobante: str = Field(..., description="Número del comprobante de pago")
    fecha_pago: datetime = Field(..., description="Fecha y hora del pago")
    banco_nombre: str = Field(..., description="Nombre del banco (desnormalizado)")
    valor_total: Decimal = Field(..., description="Valor total del comprobante")
    estado: str = Field(..., description="activo | eliminado")


class PagoAplicado(PagoResumen):
    monto_aplicado: Decimal = Field(
        ..., description="Monto de este pago aplicado a la entrega en contexto"
    )


# ─── Árbol desde XML ──────────────────────────────────────────────────────────


class IngresoKardexTraza(BaseModel):
    xml_item: XmlItemResumen = Field(
        ..., description="Ítem del XML ingresado al Kardex"
    )
    kardex_movimiento: KardexMovimientoResumen = Field(
        ..., description="Movimiento de ingreso generado"
    )
    producto: ProductoResumen = Field(
        ..., description="Producto afectado por el ingreso"
    )


class EntregaConsumoTraza(BaseModel):
    entrega: EntregaResumen = Field(
        ..., description="Entrega que consumió stock de este XML"
    )
    cantidad_consumida: Decimal = Field(
        ..., description="Cantidad consumida de los lotes de este XML"
    )
    costo_total_consumido: Decimal = Field(
        ..., description="Costo total aplicado desde este XML a la entrega"
    )


class TrazabilidadXmlResponse(BaseModel):
    xml: XmlResumen = Field(..., description="Nodo raíz: cabecera del XML consultado")
    ingresos_kardex: list[IngresoKardexTraza] = Field(
        ..., description="Ítems del XML ingresados al Kardex"
    )
    entregas: list[EntregaConsumoTraza] = Field(
        ..., description="Entregas que consumieron stock de este XML"
    )
    pagos: list[PagoResumen] = Field(
        ..., description="Pagos aplicados a las entregas relacionadas"
    )


# ─── Árbol desde Entrega ──────────────────────────────────────────────────────


class XmlOrigenTraza(BaseModel):
    xml: XmlResumen = Field(..., description="XML de origen del lote consumido")
    xml_item: XmlItemResumen = Field(..., description="Ítem del XML de origen")
    cantidad_consumida: Decimal = Field(
        ..., description="Cantidad de ese XML consumida en la entrega"
    )
    costo_unitario: Decimal = Field(
        ..., description="Costo unitario del lote FIFO consumido"
    )


class TrazabilidadEntregaResponse(BaseModel):
    entrega: EntregaResumen = Field(
        ..., description="Nodo raíz: cabecera de la entrega consultada"
    )
    xmls_origen: list[XmlOrigenTraza] = Field(
        ..., description="XMLs que aportaron stock a esta entrega"
    )
    pagos: list[PagoAplicado] = Field(
        ..., description="Pagos aplicados con monto específico por entrega"
    )


# ─── Árbol desde Pago ────────────────────────────────────────────────────────


class EntregaEnPagoTraza(BaseModel):
    entrega: EntregaResumen = Field(
        ..., description="Entrega dentro de la distribución del pago"
    )
    monto_aplicado: Decimal = Field(
        ..., description="Monto de este pago aplicado a la entrega"
    )
    xmls_origen: list[XmlOrigenTraza] = Field(
        ..., description="XMLs que dieron origen al stock entregado"
    )


class TrazabilidadPagoResponse(BaseModel):
    pago: PagoResumen = Field(
        ..., description="Nodo raíz: cabecera del pago consultado"
    )
    distribuciones: list[EntregaEnPagoTraza] = Field(
        ..., description="Entregas con trazabilidad completa hasta XMLs"
    )
