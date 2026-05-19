import { z } from "zod";

export const pagoItemRequestSchema = z.object({
  entrega_id: z.string().uuid({ message: "ID de entrega inválido" }),
  monto_aplicado: z
    .number({ invalid_type_error: "El monto debe ser un número" })
    .positive({ message: "El monto debe ser mayor a cero" }),
});

export const pagoRequestSchema = z.object({
  numero_comprobante: z
    .string()
    .min(1, { message: "El número de comprobante es requerido" })
    .max(100),
  fecha_pago: z.string().regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$/, {
    message: "Formato de fecha inválido (YYYY-MM-DDTHH:MM)",
  }),
  banco_id: z.string().uuid({ message: "Seleccione un banco válido" }),
  tipo_cuenta: z.enum(
    ["corriente", "ahorros", "transferencia", "cheque", "efectivo"],
    {
      errorMap: () => ({ message: "Seleccione un tipo de cuenta válido" }),
    },
  ),
  nombre_titular: z
    .string()
    .min(1, { message: "El nombre del titular es requerido" })
    .max(255),
  valor_total: z
    .number({ invalid_type_error: "El valor total debe ser un número" })
    .positive({ message: "El valor total debe ser mayor a cero" }),
  distribuciones: z
    .array(pagoItemRequestSchema)
    .min(1, { message: "Debe agregar al menos una entrega a la distribución" }),
});

export const pagoItemResponseSchema = z.object({
  id: z.string().uuid(),
  entrega_id: z.string().uuid(),
  entrega_numero: z.number().int().positive(),
  monto_aplicado: z.coerce.number(),
});

export const pagoResponseSchema = z.object({
  id: z.string().uuid(),
  numero_comprobante: z.string(),
  fecha_pago: z.string(),
  banco_id: z.string().uuid(),
  banco_nombre: z.string(),
  tipo_cuenta: z.enum([
    "corriente",
    "ahorros",
    "transferencia",
    "cheque",
    "efectivo",
  ]),
  nombre_titular: z.string(),
  valor_total: z.coerce.number(),
  valor_aplicado: z.coerce.number(),
  estado: z.enum(["activo", "eliminado"]),
  created_at: z.string(),
});

export const pagoDetailResponseSchema = pagoResponseSchema.extend({
  distribuciones: z.array(pagoItemResponseSchema),
});

export const entregaPendienteResponseSchema = z.object({
  id: z.string().uuid(),
  numero: z.number().int().positive(),
  snap_nombre: z.string(),
  total_entrega: z.coerce.number(),
  saldo_pendiente: z.coerce.number(),
});

export type PagoItemRequestType = z.infer<typeof pagoItemRequestSchema>;
export type PagoRequestType = z.infer<typeof pagoRequestSchema>;
export type PagoItemResponseType = z.infer<typeof pagoItemResponseSchema>;
export type PagoResponseType = z.infer<typeof pagoResponseSchema>;
export type PagoDetailResponseType = z.infer<typeof pagoDetailResponseSchema>;
export type EntregaPendienteType = z.infer<
  typeof entregaPendienteResponseSchema
>;
