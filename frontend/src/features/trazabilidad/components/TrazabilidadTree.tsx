import { FileText, Package, CreditCard, AlertTriangle } from "lucide-react";

import { formatDate } from "@/shared/utils/formatters";

import {
  type TrazabilidadXmlResponseType,
  type TrazabilidadEntregaResponseType,
  type TrazabilidadPagoResponseType,
  type TipoBusqueda,
  type XmlOrigenTrazaType,
} from "../types/trazabilidad.types";

type TreeData =
  | TrazabilidadXmlResponseType
  | TrazabilidadEntregaResponseType
  | TrazabilidadPagoResponseType;

interface Props {
  tipo: TipoBusqueda;
  data: TreeData;
}

function EliminadoBadge() {
  return (
    <span className="ml-2 inline-flex items-center gap-1 rounded-full bg-destructive/10 px-2 py-0.5 text-xs font-medium text-destructive print:border print:border-destructive">
      <AlertTriangle className="h-3 w-3" />
      Eliminado
    </span>
  );
}

function SectionTitle({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-muted-foreground uppercase tracking-wide">
      {icon}
      {text}
    </h3>
  );
}

function XmlOrigenList({ xmls }: { xmls: XmlOrigenTrazaType[] }) {
  if (xmls.length === 0) return null;
  return (
    <ul className="ml-4 mt-1 space-y-1 border-l border-border pl-3">
      {xmls.map((origen, i) => (
        <li key={i} className="text-sm">
          <span className="font-medium">{origen.xml.numero_factura}</span>
          {!origen.xml.is_active && <EliminadoBadge />}
          <span className="ml-2 text-muted-foreground">
            — {origen.xml_item.descripcion} | Cant:{" "}
            {Number(origen.cantidad_consumida).toFixed(4)} | Costo U: $
            {Number(origen.costo_unitario).toFixed(4)}
          </span>
        </li>
      ))}
    </ul>
  );
}

function TreeXml({ data }: { data: TrazabilidadXmlResponseType }) {
  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
        <div className="flex items-center gap-2 text-base font-semibold">
          <FileText className="h-5 w-5 text-primary" />
          XML — {data.xml.numero_factura}
          {!data.xml.is_active && <EliminadoBadge />}
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          {data.xml.razon_social_emisor} · {data.xml.ruc_emisor} ·{" "}
          {data.xml.fecha_emision}
        </p>
      </div>

      <div>
        <SectionTitle
          icon={<Package className="h-4 w-4" />}
          text="Ingresos al Kardex"
        />
        {data.ingresos_kardex.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Sin ingresos al Kardex.
          </p>
        ) : (
          <ul className="space-y-2">
            {data.ingresos_kardex.map((ing, i) => (
              <li
                key={i}
                className="rounded border border-border bg-background p-3 text-sm"
              >
                <div className="font-medium">
                  {ing.xml_item.descripcion} ({ing.xml_item.codigo_principal})
                </div>
                <div className="mt-1 text-muted-foreground">
                  Producto: {ing.producto.descripcion} | Cant ingresada:{" "}
                  {Number(ing.xml_item.cantidad_ingresada).toFixed(4)} | Costo
                  U: ${Number(ing.kardex_movimiento.costo_unitario).toFixed(4)}{" "}
                  | Fecha:{" "}
                  {new Date(
                    ing.kardex_movimiento.fecha_movimiento,
                  ).toLocaleDateString()}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div>
        <SectionTitle icon={<Package className="h-4 w-4" />} text="Entregas" />
        {data.entregas.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Sin entregas asociadas.
          </p>
        ) : (
          <ul className="space-y-2">
            {data.entregas.map((ec, i) => (
              <li
                key={i}
                className="rounded border border-border bg-background p-3 text-sm"
              >
                <div className="flex items-center font-medium">
                  Entrega #{ec.entrega.numero} — {ec.entrega.snap_nombre}
                  {ec.entrega.estado === "eliminada" && <EliminadoBadge />}
                </div>
                <div className="mt-1 text-muted-foreground">
                  Cant consumida: {Number(ec.cantidad_consumida).toFixed(4)} |
                  Costo: ${Number(ec.costo_total_consumido).toFixed(2)}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div>
        <SectionTitle icon={<CreditCard className="h-4 w-4" />} text="Pagos" />
        {data.pagos.length === 0 ? (
          <p className="text-sm text-muted-foreground">Sin pagos asociados.</p>
        ) : (
          <ul className="space-y-2">
            {data.pagos.map((p, i) => (
              <li
                key={i}
                className="rounded border border-border bg-background p-3 text-sm"
              >
                <div className="flex items-center font-medium">
                  {p.numero_comprobante} — {p.banco_nombre}
                  {p.estado === "eliminado" && <EliminadoBadge />}
                </div>
                <div className="mt-1 text-muted-foreground">
                  Total: ${Number(p.valor_total).toFixed(2)} | Fecha:{" "}
                  {formatDate(p.fecha_pago, "dd-MM-yyyy HH:mm:ss")}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function TreeEntrega({ data }: { data: TrazabilidadEntregaResponseType }) {
  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
        <div className="flex items-center gap-2 text-base font-semibold">
          <Package className="h-5 w-5 text-primary" />
          Entrega #{data.entrega.numero} — {data.entrega.snap_nombre}
          {data.entrega.estado === "eliminada" && <EliminadoBadge />}
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          Total: ${Number(data.entrega.total_entrega).toFixed(2)} | Saldo: $
          {Number(data.entrega.saldo_pendiente).toFixed(2)}
        </p>
      </div>

      <div>
        <SectionTitle
          icon={<FileText className="h-4 w-4" />}
          text="XMLs de Origen"
        />
        {data.xmls_origen.length === 0 ? (
          <p className="text-sm text-muted-foreground">Sin XMLs de origen.</p>
        ) : (
          <ul className="space-y-2">
            {data.xmls_origen.map((origen, i) => (
              <li
                key={i}
                className="rounded border border-border bg-background p-3 text-sm"
              >
                <div className="flex items-center font-medium">
                  {origen.xml.numero_factura} — {origen.xml.razon_social_emisor}
                  {!origen.xml.is_active && <EliminadoBadge />}
                </div>
                <div className="mt-1 text-muted-foreground">
                  {origen.xml_item.descripcion} (
                  {origen.xml_item.codigo_principal}) | Cant:{" "}
                  {Number(origen.cantidad_consumida).toFixed(4)} | Costo U: $
                  {Number(origen.costo_unitario).toFixed(4)}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div>
        <SectionTitle
          icon={<CreditCard className="h-4 w-4" />}
          text="Pagos Aplicados"
        />
        {data.pagos.length === 0 ? (
          <p className="text-sm text-muted-foreground">Sin pagos aplicados.</p>
        ) : (
          <ul className="space-y-2">
            {data.pagos.map((p, i) => (
              <li
                key={i}
                className="rounded border border-border bg-background p-3 text-sm"
              >
                <div className="flex items-center font-medium">
                  {p.numero_comprobante} — {p.banco_nombre}
                  {p.estado === "eliminado" && <EliminadoBadge />}
                </div>
                <div className="mt-1 text-muted-foreground">
                  Monto aplicado: ${Number(p.monto_aplicado).toFixed(2)} |
                  Fecha: {formatDate(p.fecha_pago, "dd-MM-yyyy HH:mm:ss")}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function TreePago({ data }: { data: TrazabilidadPagoResponseType }) {
  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
        <div className="flex items-center gap-2 text-base font-semibold">
          <CreditCard className="h-5 w-5 text-primary" />
          Pago {data.pago.numero_comprobante} — {data.pago.banco_nombre}
          {data.pago.estado === "eliminado" && <EliminadoBadge />}
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          Total: ${Number(data.pago.valor_total).toFixed(2)} | Fecha:{" "}
          {formatDate(data.pago.fecha_pago, "dd-MM-yyyy HH:mm:ss")}
        </p>
      </div>

      <div>
        <SectionTitle
          icon={<Package className="h-4 w-4" />}
          text="Entregas en Distribución"
        />
        {data.distribuciones.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Sin entregas en distribución.
          </p>
        ) : (
          <ul className="space-y-3">
            {data.distribuciones.map((dist, i) => (
              <li
                key={i}
                className="rounded border border-border bg-background p-3 text-sm"
              >
                <div className="flex items-center font-medium">
                  Entrega #{dist.entrega.numero} — {dist.entrega.snap_nombre}
                  {dist.entrega.estado === "eliminada" && <EliminadoBadge />}
                </div>
                <div className="mt-1 text-muted-foreground">
                  Monto aplicado: ${Number(dist.monto_aplicado).toFixed(2)}
                </div>
                <XmlOrigenList xmls={dist.xmls_origen} />
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export function TrazabilidadTree({ tipo, data }: Props) {
  if (tipo === "xml")
    return <TreeXml data={data as TrazabilidadXmlResponseType} />;
  if (tipo === "entrega")
    return <TreeEntrega data={data as TrazabilidadEntregaResponseType} />;
  return <TreePago data={data as TrazabilidadPagoResponseType} />;
}
