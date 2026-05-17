import { z } from "zod";

export const kardexIngresoItemSchema = z.object({
  xml_item_id: z.string().uuid({ message: "ID de ítem inválido" }),
  cantidad: z
    .number({ invalid_type_error: "La cantidad debe ser un número" })
    .positive({ message: "La cantidad debe ser mayor a cero" }),
});

export const kardexIngresoSchema = z.object({
  items: z
    .array(kardexIngresoItemSchema)
    .min(1, { message: "Debe seleccionar al menos un ítem" }),
});

export const kardexMovimientoSchema = z.object({
  id: z.string().uuid(),
  producto_id: z.string().uuid(),
  tipo: z.enum(["ingreso", "egreso"]),
  origen: z.enum(["xml", "entrega", "reversa_entrega"]),
  documento_origen_id: z.string().uuid(),
  documento_origen_ref: z.string(),
  fecha_movimiento: z.string().datetime(),
  cantidad: z.coerce.number(),
  peso_unitario: z.coerce.number(),
  peso_total: z.coerce.number(),
  costo_unitario: z.coerce.number(),
  costo_total: z.coerce.number(),
  saldo_cantidad: z.coerce.number(),
  saldo_valor: z.coerce.number(),
});

export const productoConSaldoSchema = z.object({
  id: z.string().uuid(),
  codigo_principal: z.string(),
  descripcion: z.string(),
  unidad_medida: z.string().nullable(),
  peso_unitario: z.coerce.number(),
  saldo_cantidad: z.coerce.number(),
  saldo_valor: z.coerce.number(),
});

export type KardexIngresoItemType = z.infer<typeof kardexIngresoItemSchema>;
export type KardexIngresoType = z.infer<typeof kardexIngresoSchema>;
export type KardexMovimientoType = z.infer<typeof kardexMovimientoSchema>;
export type ProductoConSaldoType = z.infer<typeof productoConSaldoSchema>;
