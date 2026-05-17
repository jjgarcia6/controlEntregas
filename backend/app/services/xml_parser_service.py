import xml.etree.ElementTree as ET  # nosec B405 — fromstring only, content pre-validated in memory
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from app.utils.exceptions import ValidacionNegocio

_MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


@dataclass
class ItemParseado:
    codigo_principal: str
    codigo_auxiliar: str | None
    descripcion: str
    cantidad_documento: Decimal
    precio_unitario: Decimal
    descuento: Decimal
    precio_total_sin_imp: Decimal
    tarifa_iva: Decimal
    valor_iva: Decimal
    peso_documento: Decimal
    peso_unitario: Decimal


@dataclass
class XmlParseado:
    clave_acceso: str
    ruc_emisor: str
    razon_social_emisor: str
    nombre_comercial: str | None
    numero_factura: str
    fecha_emision: date
    direccion_emisor: str | None
    tipo_emision: int
    ambiente: int
    ruc_comprador: str
    razon_social_comprador: str
    direccion_comprador: str | None
    total_sin_impuestos: Decimal
    total_descuento: Decimal
    subtotal_iva_0: Decimal
    subtotal_gravado: Decimal
    valor_iva: Decimal
    importe_total: Decimal
    moneda: str
    xml_raw: str
    items: list[ItemParseado] = field(default_factory=list)


def _get_text(elem: ET.Element, path: str, default: str | None = None) -> str | None:
    node = elem.find(path)
    if node is None or node.text is None:
        return default
    text = node.text.strip()
    return text if text else default


def _require_text(elem: ET.Element, path: str, label: str) -> str:
    value = _get_text(elem, path)
    if not value:
        raise ValidacionNegocio(f"Campo requerido ausente en el XML: {label}")
    return value


def _to_decimal(value: str | None, default: Decimal = Decimal("0")) -> Decimal:
    if value is None:
        return default
    try:
        return Decimal(value.strip())
    except InvalidOperation:
        return default


def parsear(xml_content: str) -> XmlParseado:
    if len(xml_content.encode("utf-8")) > _MAX_SIZE_BYTES:
        raise ValidacionNegocio("El archivo XML supera el tamaño máximo permitido de 5 MB")

    try:
        root = ET.fromstring(xml_content)  # nosec B314 — UTF-8 decoded, size-limited to 5 MB, no external entity loading
    except ET.ParseError:
        raise ValidacionNegocio("Archivo no es XML válido")

    if root.tag != "factura":
        raise ValidacionNegocio("Formato no corresponde a factura SRI 2.x")
    version = root.get("version", "")
    if not version.startswith("2."):
        raise ValidacionNegocio("Formato no corresponde a factura SRI 2.x")

    info_trib = root.find("infoTributaria")
    if info_trib is None:
        raise ValidacionNegocio("Estructura XML inválida: falta infoTributaria")

    info_fact = root.find("infoFactura")
    if info_fact is None:
        raise ValidacionNegocio("Estructura XML inválida: falta infoFactura")

    ambiente_str = _require_text(info_trib, "ambiente", "ambiente")
    try:
        ambiente = int(ambiente_str)
    except ValueError:
        raise ValidacionNegocio("Campo 'ambiente' inválido en el XML")

    if ambiente != 2:
        raise ValidacionNegocio(
            "Solo se aceptan facturas de ambiente de producción (ambiente=2)"
        )

    clave_acceso = _require_text(info_trib, "claveAcceso", "claveAcceso")
    ruc_emisor = _require_text(info_trib, "ruc", "ruc")
    razon_social_emisor = _require_text(info_trib, "razonSocial", "razonSocial")
    nombre_comercial = _get_text(info_trib, "nombreComercial")
    estab = _require_text(info_trib, "estab", "estab")
    pto_emi = _require_text(info_trib, "ptoEmi", "ptoEmi")
    secuencial = _require_text(info_trib, "secuencial", "secuencial")
    numero_factura = f"{estab}-{pto_emi}-{secuencial}"

    tipo_emision_str = _require_text(info_trib, "tipoEmision", "tipoEmision")
    try:
        tipo_emision = int(tipo_emision_str)
    except ValueError:
        raise ValidacionNegocio("Campo 'tipoEmision' inválido en el XML")

    fecha_str = _require_text(info_fact, "fechaEmision", "fechaEmision")
    try:
        fecha_emision = datetime.strptime(fecha_str, "%d/%m/%Y").date()
    except ValueError:
        raise ValidacionNegocio(f"Formato de fecha inválido: {fecha_str}")

    direccion_emisor = _get_text(info_fact, "dirEstablecimiento")
    ruc_comprador = _require_text(
        info_fact, "identificacionComprador", "identificacionComprador"
    )
    razon_social_comprador = _require_text(
        info_fact, "razonSocialComprador", "razonSocialComprador"
    )
    direccion_comprador = _get_text(info_fact, "direccionComprador")

    total_sin_impuestos = _to_decimal(_get_text(info_fact, "totalSinImpuestos"))
    total_descuento = _to_decimal(_get_text(info_fact, "totalDescuento"))
    importe_total = _to_decimal(_get_text(info_fact, "importeTotal"))
    moneda = _get_text(info_fact, "moneda") or "DOLAR"

    subtotal_iva_0 = Decimal("0")
    subtotal_gravado = Decimal("0")
    valor_iva_total = Decimal("0")

    total_con_imp = info_fact.find("totalConImpuestos")
    if total_con_imp is not None:
        for imp in total_con_imp.findall("totalImpuesto"):
            codigo = _get_text(imp, "codigo")
            codigo_porcentaje = _get_text(imp, "codigoPorcentaje")
            base = _to_decimal(_get_text(imp, "baseImponible"))
            valor = _to_decimal(_get_text(imp, "valor"))
            if codigo == "2":
                if codigo_porcentaje == "0":
                    subtotal_iva_0 = base
                else:
                    subtotal_gravado += base
                    valor_iva_total += valor

    detalles_elem = root.find("detalles")
    if detalles_elem is None:
        raise ValidacionNegocio("Estructura XML inválida: falta sección detalles")

    items: list[ItemParseado] = []
    for detalle in detalles_elem.findall("detalle"):
        cod_principal = _require_text(detalle, "codigoPrincipal", "codigoPrincipal del ítem")
        cod_auxiliar = _get_text(detalle, "codigoAuxiliar")
        descripcion_item = _require_text(detalle, "descripcion", "descripcion del ítem")
        cantidad = _to_decimal(_get_text(detalle, "cantidad"))
        precio_unitario = _to_decimal(_get_text(detalle, "precioUnitario"))
        descuento_item = _to_decimal(_get_text(detalle, "descuento"))
        precio_total_sin_imp = _to_decimal(_get_text(detalle, "precioTotalSinImpuesto"))

        tarifa_iva_item = Decimal("0")
        valor_iva_item = Decimal("0")
        impuestos = detalle.find("impuestos")
        if impuestos is not None:
            for imp in impuestos.findall("impuesto"):
                if _get_text(imp, "codigo") == "2":
                    tarifa_iva_item = _to_decimal(_get_text(imp, "tarifa"))
                    valor_iva_item = _to_decimal(_get_text(imp, "valor"))
                    break

        peso_documento = Decimal("0")
        det_adicionales = detalle.find("detallesAdicionales")
        if det_adicionales is not None:
            for det_ad in det_adicionales.findall("detAdicional"):
                if det_ad.get("nombre", "").lower() == "peso":
                    peso_documento = _to_decimal(det_ad.get("valor"))
                    break

        peso_unitario = (
            peso_documento / cantidad if cantidad > Decimal("0") else Decimal("0")
        )

        items.append(
            ItemParseado(
                codigo_principal=cod_principal,
                codigo_auxiliar=cod_auxiliar,
                descripcion=descripcion_item,
                cantidad_documento=cantidad,
                precio_unitario=precio_unitario,
                descuento=descuento_item,
                precio_total_sin_imp=precio_total_sin_imp,
                tarifa_iva=tarifa_iva_item,
                valor_iva=valor_iva_item,
                peso_documento=peso_documento,
                peso_unitario=peso_unitario,
            )
        )

    if not items:
        raise ValidacionNegocio("La factura no contiene ítems en el detalle")

    return XmlParseado(
        clave_acceso=clave_acceso,
        ruc_emisor=ruc_emisor,
        razon_social_emisor=razon_social_emisor,
        nombre_comercial=nombre_comercial,
        numero_factura=numero_factura,
        fecha_emision=fecha_emision,
        direccion_emisor=direccion_emisor,
        tipo_emision=tipo_emision,
        ambiente=ambiente,
        ruc_comprador=ruc_comprador,
        razon_social_comprador=razon_social_comprador,
        direccion_comprador=direccion_comprador,
        total_sin_impuestos=total_sin_impuestos,
        total_descuento=total_descuento,
        subtotal_iva_0=subtotal_iva_0,
        subtotal_gravado=subtotal_gravado,
        valor_iva=valor_iva_total,
        importe_total=importe_total,
        moneda=moneda,
        xml_raw=xml_content,
        items=items,
    )
