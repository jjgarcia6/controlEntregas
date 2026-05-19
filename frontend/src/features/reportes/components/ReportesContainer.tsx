import { useState } from "react";

import {
  type ReporteEntregasResponseType,
  type ReporteKardexResponseType,
  type ReportePagosResponseType,
  type ReporteXmlsResponseType,
  type TipoReporte,
} from "../types/reporte.types";
import { useDownloadReportePdf } from "../hooks/useDownloadReportePdf";
import { useDownloadReporteXlsx } from "../hooks/useDownloadReporteXlsx";
import { useFetchReporte } from "../hooks/useFetchReporte";
import { ReporteExportButtons } from "./ReporteExportButtons";
import { ReporteFilters } from "./ReporteFilters";
import { ReporteSelector } from "./ReporteSelector";
import { ReporteTable } from "./ReporteTable";

const COLUMNAS: Record<TipoReporte, string[]> = {
  xmls: [
    "numero_factura",
    "fecha_emision",
    "razon_social_emisor",
    "total_sin_impuestos",
    "importe_total",
  ],
  kardex: [
    "fecha_movimiento",
    "tipo",
    "origen",
    "cantidad",
    "costo_unitario",
    "costo_total",
    "saldo_cantidad",
    "saldo_valor",
  ],
  entregas: [
    "fecha_creacion",
    "numero",
    "identificacion",
    "nombre",
    "total_entrega",
    "saldo_pendiente",
    "estado",
  ],
  pagos: [
    "tipo_cuenta",
    "numero_comprobante",
    "fecha_pago",
    "banco_nombre",
    "nombre_titular",
    "valor_total",
    "valor_aplicado",
    "estado",
  ],
};

function formatearFecha(fecha: string): string {
  try {
    const d = new Date(fecha);
    const dd = String(d.getDate()).padStart(2, "0");
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const yyyy = d.getFullYear();
    const hh = String(d.getHours()).padStart(2, "0");
    const min = String(d.getMinutes()).padStart(2, "0");
    const ss = String(d.getSeconds()).padStart(2, "0");
    return `${dd}-${mm}-${yyyy} ${hh}:${min}:${ss}`;
  } catch {
    return fecha;
  }
}

function formatearFechaPago(fecha: string): string {
  if (/^\d{4}-\d{2}-\d{2}$/.test(fecha)) {
    const [yyyy, mm, dd] = fecha.split("-");
    return `${dd}-${mm}-${yyyy} 00:00:00`;
  }
  return formatearFecha(fecha);
}

function buildFilas(
  tipo: TipoReporte,
  data: unknown,
): Record<string, unknown>[] {
  if (!data) return [];
  if (tipo === "xmls") {
    return (data as ReporteXmlsResponseType).filas.map((f) => ({
      numero_factura: f.numero_factura,
      fecha_emision: f.fecha_emision,
      razon_social_emisor: f.razon_social_emisor,
      total_sin_impuestos: Number(f.total_sin_impuestos).toFixed(2),
      importe_total: Number(f.importe_total).toFixed(2),
    }));
  }
  if (tipo === "kardex") {
    return (data as ReporteKardexResponseType).movimientos.map((m) => ({
      tipo: m.tipo,
      origen: m.origen,
      fecha_movimiento: formatearFecha(m.fecha_movimiento),
      cantidad: Number(m.cantidad).toFixed(2),
      costo_unitario: Number(m.costo_unitario).toFixed(2),
      costo_total: Number(m.costo_total).toFixed(2),
      saldo_cantidad: Number(m.saldo_cantidad).toFixed(2),
      saldo_valor: Number(m.saldo_valor).toFixed(2),
    }));
  }
  if (tipo === "entregas") {
    return (data as ReporteEntregasResponseType).filas.map((f) => ({
      numero: f.numero,
      fecha_creacion: formatearFecha(f.fecha_creacion),
      nombre: f.snap_nombre,
      identificacion: f.snap_identificacion,
      total_entrega: Number(f.total_entrega).toFixed(2),
      saldo_pendiente: Number(f.saldo_pendiente).toFixed(2),
      estado: f.estado,
    }));
  }
  if (tipo === "pagos") {
    return (data as ReportePagosResponseType).filas.map((f) => ({
      tipo_cuenta: f.tipo_cuenta,
      numero_comprobante: f.numero_comprobante,
      fecha_pago: formatearFechaPago(f.fecha_pago),
      banco_nombre: f.banco_nombre,
      nombre_titular: f.nombre_titular,
      valor_total: Number(f.valor_total).toFixed(2),
      valor_aplicado: Number(f.valor_aplicado).toFixed(2),
      estado: f.estado,
    }));
  }
  return [];
}

function buildResumen(tipo: TipoReporte, data: unknown): string | null {
  if (!data) return null;
  if (tipo === "xmls") {
    const d = data as ReporteXmlsResponseType;
    return `${d.total_xmls} XMLs | Total: $${Number(d.total_valor).toFixed(2)}`;
  }
  if (tipo === "kardex") {
    const d = data as ReporteKardexResponseType;
    return `${d.producto_codigo} — ${d.producto_descripcion} | Saldo: ${Number(d.saldo_cantidad_actual).toFixed(4)} uds / $${Number(d.saldo_valor_actual).toFixed(2)}`;
  }
  if (tipo === "entregas") {
    const d = data as ReporteEntregasResponseType;
    return `${d.total_entregas} entregas | Total: $${Number(d.total_valor).toFixed(2)} | Cobrado: $${Number(d.total_cobrado).toFixed(2)} | Pendiente: $${Number(d.total_pendiente).toFixed(2)}`;
  }
  if (tipo === "pagos") {
    const d = data as ReportePagosResponseType;
    return `${d.total_pagos} pagos | Total: $${Number(d.valor_total).toFixed(2)}`;
  }
  return null;
}

export function ReportesContainer() {
  const [tipoActivo, setTipoActivo] = useState<TipoReporte>("xmls");
  const [filtrosActivos, setFiltrosActivos] = useState<Record<string, unknown>>(
    {},
  );
  const [enabled, setEnabled] = useState(false);

  const { data, isLoading } = useFetchReporte(
    tipoActivo,
    filtrosActivos,
    enabled,
  );
  const { mutate: downloadPdf, isPending: isPdfPending } =
    useDownloadReportePdf(tipoActivo, filtrosActivos);
  const { mutate: downloadXlsx, isPending: isXlsxPending } =
    useDownloadReporteXlsx(tipoActivo, filtrosActivos);

  function handleTipoChange(tipo: TipoReporte) {
    setTipoActivo(tipo);
    setEnabled(false);
    setFiltrosActivos({});
  }

  function handleFiltersSubmit(filtros: Record<string, unknown>) {
    setFiltrosActivos(filtros);
    setEnabled(true);
  }

  const filas = buildFilas(tipoActivo, data);
  const resumen = buildResumen(tipoActivo, data);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-foreground">Reportes</h1>
        {data && (
          <ReporteExportButtons
            onDownloadPdf={() => downloadPdf()}
            onDownloadXlsx={() => downloadXlsx()}
            isPdfPending={isPdfPending}
            isXlsxPending={isXlsxPending}
          />
        )}
      </div>

      <ReporteSelector tipoActivo={tipoActivo} onChange={handleTipoChange} />

      <ReporteFilters
        key={tipoActivo}
        tipoActivo={tipoActivo}
        onSubmit={handleFiltersSubmit}
      />

      {resumen && (
        <div className="rounded-md border border-border bg-muted/30 px-4 py-2 text-sm text-muted-foreground">
          {resumen}
        </div>
      )}

      {enabled && (
        <ReporteTable
          columnas={COLUMNAS[tipoActivo]}
          filas={filas}
          isLoading={isLoading}
        />
      )}
    </div>
  );
}
