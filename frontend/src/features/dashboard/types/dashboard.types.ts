import { z } from "zod";

export const entregaPendienteRowSchema = z.object({
  id: z.string().uuid(),
  numero: z.number().int(),
  snap_nombre: z.string(),
  snap_identificacion: z.string(),
  total_entrega: z.coerce.number(),
  saldo_pendiente: z.coerce.number(),
  created_at: z.string(),
});

export const dashboardResponseSchema = z.object({
  entregas_activas: z.number().int(),
  saldo_pendiente_total: z.coerce.number(),
  total_facturado: z.coerce.number(),
  total_cobrado: z.coerce.number(),
  pagos_mes_actual: z.coerce.number(),
  entregas_mas_antiguas: z.array(entregaPendienteRowSchema),
});

export type EntregaPendienteRow = z.infer<typeof entregaPendienteRowSchema>;
export type DashboardResponse = z.infer<typeof dashboardResponseSchema>;
