import { z } from "zod";

export const xmlItemPreviewSchema = z.object({
  codigo_principal: z.string().max(50).describe("Código principal del ítem en la factura SRI"),
  codigo_auxiliar: z.string().max(50).nullable().describe("Código auxiliar del ítem"),
  descripcion: z.string().max(300).describe("Descripción del ítem del XML"),
  cantidad_documento: z.coerce.number().positive().describe("Cantidad según la factura original"),
  precio_unitario: z.coerce.number().positive().describe("Precio unitario sin impuestos"),
  descuento: z.coerce.number().min(0).describe("Descuento total del ítem"),
  precio_total_sin_imp: z.coerce.number().min(0).describe("Total del ítem sin impuestos"),
  tarifa_iva: z.coerce.number().min(0).describe("Porcentaje de IVA del XML"),
  valor_iva: z.coerce.number().min(0).describe("Monto de IVA calculado por el SRI"),
  peso_documento: z.coerce.number().min(0).describe("Peso total del ítem del XML"),
  peso_unitario: z.coerce.number().min(0).describe("Peso unitario calculado en backend"),
});

export const xmlPreviewSchema = z.object({
  clave_acceso: z.string().length(49).describe("Clave de acceso SRI (49 dígitos)"),
  ruc_emisor: z.string().max(13).describe("RUC del emisor"),
  razon_social_emisor: z.string().max(300).describe("Razón social del emisor"),
  nombre_comercial: z.string().max(300).nullable().describe("Nombre comercial (opcional)"),
  numero_factura: z.string().max(20).describe("Número de factura estab-ptoEmi-secuencial"),
  fecha_emision: z.string().describe("Fecha de emisión ISO 8601"),
  direccion_emisor: z.string().nullable().describe("Dirección del establecimiento emisor"),
  tipo_emision: z.number().int().describe("Tipo de emisión SRI"),
  ambiente: z.number().int().describe("Ambiente SRI: 1=pruebas, 2=producción"),
  ruc_comprador: z.string().max(13).describe("RUC del comprador"),
  razon_social_comprador: z.string().max(300).describe("Razón social del comprador"),
  direccion_comprador: z.string().nullable().describe("Dirección del comprador"),
  total_sin_impuestos: z.coerce.number().min(0).describe("Subtotal sin impuestos"),
  total_descuento: z.coerce.number().min(0).describe("Total de descuentos"),
  subtotal_iva_0: z.coerce.number().min(0).describe("Base imponible IVA 0%"),
  subtotal_gravado: z.coerce.number().min(0).describe("Base imponible gravada"),
  valor_iva: z.coerce.number().min(0).describe("Monto total de IVA"),
  importe_total: z.coerce.number().positive().describe("Total con impuestos"),
  moneda: z.string().max(10).describe("Moneda de la factura"),
  items: z.array(xmlItemPreviewSchema).min(1).describe("Ítems del detalle"),
});

export const xmlItemResponseSchema = xmlItemPreviewSchema.extend({
  id: z.string().uuid().describe("Identificador único del ítem persistido"),
  cantidad_ingresada: z.coerce.number().min(0).describe("Cantidad ingresada al Kardex"),
  cantidad_pendiente: z.coerce.number().min(0).describe("Cantidad pendiente de ingresar"),
});

export const xmlResponseSchema = xmlPreviewSchema.extend({
  id: z.string().uuid().describe("Identificador único del XML"),
  created_at: z.string().describe("Fecha de registro ISO 8601"),
  items: z.array(xmlItemResponseSchema),
});

export const xmlListItemSchema = z.object({
  id: z.string().uuid(),
  clave_acceso: z.string(),
  numero_factura: z.string(),
  fecha_emision: z.string(),
  razon_social_emisor: z.string(),
  ruc_emisor: z.string(),
  ruc_comprador: z.string(),
  razon_social_comprador: z.string(),
  importe_total: z.coerce.number(),
  created_at: z.string(),
});

export const xmlItemPendienteSchema = z.object({
  id: z.string().uuid(),
  codigo_principal: z.string(),
  descripcion: z.string(),
  cantidad_documento: z.coerce.number(),
  cantidad_ingresada: z.coerce.number(),
  cantidad_pendiente: z.coerce.number().positive(),
  precio_unitario: z.coerce.number(),
  precio_total_sin_imp: z.coerce.number(),
  peso_unitario: z.coerce.number(),
});

export type XmlItemPreviewType = z.infer<typeof xmlItemPreviewSchema>;
export type XmlPreviewType = z.infer<typeof xmlPreviewSchema>;
export type XmlItemResponseType = z.infer<typeof xmlItemResponseSchema>;
export type XmlResponseType = z.infer<typeof xmlResponseSchema>;
export type XmlListItemType = z.infer<typeof xmlListItemSchema>;
export type XmlItemPendienteType = z.infer<typeof xmlItemPendienteSchema>;
