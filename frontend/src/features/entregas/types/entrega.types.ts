import { z } from "zod";

export const entregaItemRequestSchema = z.object({
  producto_id: z.string().uuid({ message: "ID de producto inválido" }),
  cantidad: z
    .number({ invalid_type_error: "La cantidad debe ser un número" })
    .positive({ message: "La cantidad debe ser mayor a cero" }),
});

export const entregaRequestSchema = z.object({
  destinatario_id: z.string().uuid({ message: "ID de destinatario inválido" }),
  items: z
    .array(entregaItemRequestSchema)
    .min(1, { message: "Debe agregar al menos un producto" }),
  comentarios: z.string().max(255).nullable().optional(),
});

export const entregaItemResponseSchema = z.object({
  id: z.string().uuid(),
  producto_id: z.string().uuid(),
  xml_item_id: z.string().uuid(),
  codigo_principal: z.string(),
  descripcion: z.string(),
  cantidad: z.coerce.number(),
  peso_total: z.coerce.number(),
  costo_unitario: z.coerce.number(),
  costo_total: z.coerce.number(),
});

export const entregaResponseSchema = z.object({
  id: z.string().uuid(),
  numero: z.number().int(),
  destinatario_id: z.string().uuid(),
  snap_identificacion: z.string(),
  snap_nombre: z.string(),
  snap_direccion: z.string(),
  snap_telefono: z.string(),
  comentarios: z.string().nullable().optional(),
  total_entrega: z.coerce.number(),
  saldo_pendiente: z.coerce.number(),
  estado: z.enum(["activa", "eliminada"]),
  items: z.array(entregaItemResponseSchema),
  created_at: z.string().datetime(),
});

export const entregaListItemSchema = z.object({
  id: z.string().uuid(),
  numero: z.number().int(),
  snap_identificacion: z.string(),
  snap_nombre: z.string(),
  total_entrega: z.coerce.number(),
  saldo_pendiente: z.coerce.number(),
  estado: z.enum(["activa", "eliminada"]),
  created_at: z.string().datetime(),
});

export type EntregaItemRequestType = z.infer<typeof entregaItemRequestSchema>;
export type EntregaRequestType = z.infer<typeof entregaRequestSchema>;
export type EntregaItemResponseType = z.infer<typeof entregaItemResponseSchema>;
export type EntregaResponseType = z.infer<typeof entregaResponseSchema>;
export type EntregaListItemType = z.infer<typeof entregaListItemSchema>;
