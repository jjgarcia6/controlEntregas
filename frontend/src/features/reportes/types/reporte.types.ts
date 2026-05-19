import { z } from "zod";

// --- Filtros ---
export const filtrosXmlsSchema = z.object({
  xml_id: z.string().uuid().optional(),
  fecha_desde: z.string().optional(),
  fecha_hasta: z.string().optional(),
  codigo_principal: z.string().optional(),
});

export const filtrosKardexSchema = z.object({
  producto_id: z.string().uuid(),
  fecha_desde: z.string().optional(),
  fecha_hasta: z.string().optional(),
});

export const filtrosEntregasSchema = z.object({
  fecha_desde: z.string().optional(),
  fecha_hasta: z.string().optional(),
  destinatario_id: z.string().uuid().optional(),
  estado: z.enum(["activa", "eliminada"]).optional(),
});

export const filtrosPagosSchema = z.object({
  fecha_desde: z.string().optional(),
  fecha_hasta: z.string().optional(),
  banco_id: z.string().uuid().optional(),
  entrega_id: z.string().uuid().optional(),
});

// --- Reporte XMLs ---
export const reporteXmlItemRowSchema = z.object({
  codigo_principal: z.string(),
  descripcion: z.string(),
  cantidad_documento: z.coerce.number(),
  cantidad_ingresada: z.coerce.number(),
  cantidad_pendiente: z.coerce.number(),
  precio_unitario: z.coerce.number(),
  precio_total_sin_imp: z.coerce.number(),
});

export const reporteXmlRowSchema = z.object({
  xml_id: z.string().uuid(),
  numero_factura: z.string(),
  fecha_emision: z.string(),
  razon_social_emisor: z.string(),
  total_sin_impuestos: z.coerce.number(),
  importe_total: z.coerce.number(),
  items: z.array(reporteXmlItemRowSchema),
});

export const reporteXmlsResponseSchema = z.object({
  total_xmls: z.number().int(),
  total_valor: z.coerce.number(),
  filas: z.array(reporteXmlRowSchema),
});

// --- Reporte Kardex ---
export const reporteKardexMovimientoRowSchema = z.object({
  fecha_movimiento: z.string(),
  tipo: z.string(),
  origen: z.string(),
  cantidad: z.coerce.number(),
  peso_unitario: z.coerce.number(),
  peso_total: z.coerce.number(),
  costo_unitario: z.coerce.number(),
  costo_total: z.coerce.number(),
  saldo_cantidad: z.coerce.number(),
  saldo_valor: z.coerce.number(),
});

export const reporteKardexResponseSchema = z.object({
  producto_codigo: z.string(),
  producto_descripcion: z.string(),
  saldo_cantidad_actual: z.coerce.number(),
  saldo_valor_actual: z.coerce.number(),
  movimientos: z.array(reporteKardexMovimientoRowSchema),
});

// --- Reporte Entregas ---
export const reporteEntregaItemRowSchema = z.object({
  codigo_principal: z.string(),
  descripcion: z.string(),
  cantidad: z.coerce.number(),
  peso_total: z.coerce.number(),
  costo_unitario: z.coerce.number(),
  costo_total: z.coerce.number(),
});

export const reporteEntregaRowSchema = z.object({
  numero: z.number().int(),
  fecha_creacion: z.string(),
  snap_nombre: z.string(),
  snap_identificacion: z.string(),
  total_entrega: z.coerce.number(),
  saldo_pendiente: z.coerce.number(),
  estado: z.string(),
  items: z.array(reporteEntregaItemRowSchema),
});

export const reporteEntregasResponseSchema = z.object({
  total_entregas: z.number().int(),
  total_valor: z.coerce.number(),
  total_cobrado: z.coerce.number(),
  total_pendiente: z.coerce.number(),
  filas: z.array(reporteEntregaRowSchema),
});

// --- Reporte Pagos ---
export const reportePagoDistribucionRowSchema = z.object({
  entrega_numero: z.number().int(),
  snap_nombre: z.string(),
  monto_aplicado: z.coerce.number(),
});

export const reportePagoRowSchema = z.object({
  numero_comprobante: z.string(),
  fecha_pago: z.string(),
  banco_nombre: z.string(),
  tipo_cuenta: z.string(),
  nombre_titular: z.string(),
  valor_total: z.coerce.number(),
  valor_aplicado: z.coerce.number(),
  estado: z.string(),
  distribuciones: z.array(reportePagoDistribucionRowSchema),
});

export const reportePagosResponseSchema = z.object({
  total_pagos: z.number().int(),
  valor_total: z.coerce.number(),
  filas: z.array(reportePagoRowSchema),
});

// --- Tipos derivados ---
export type FiltrosXmlsType = z.infer<typeof filtrosXmlsSchema>;
export type FiltrosKardexType = z.infer<typeof filtrosKardexSchema>;
export type FiltrosEntregasType = z.infer<typeof filtrosEntregasSchema>;
export type FiltrosPagosType = z.infer<typeof filtrosPagosSchema>;
export type ReporteXmlsResponseType = z.infer<typeof reporteXmlsResponseSchema>;
export type ReporteKardexResponseType = z.infer<
  typeof reporteKardexResponseSchema
>;
export type ReporteEntregasResponseType = z.infer<
  typeof reporteEntregasResponseSchema
>;
export type ReportePagosResponseType = z.infer<
  typeof reportePagosResponseSchema
>;

// --- Tipo utilitario ---
export type TipoReporte = "xmls" | "kardex" | "entregas" | "pagos";
export type FormatoReporte = "json" | "pdf" | "xlsx";
