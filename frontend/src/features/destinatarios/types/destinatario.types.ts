import { z } from "zod";

export const destinatarioResponseSchema = z.object({
  id: z.string().uuid(),
  tipo_identificacion: z.enum(["cedula", "ruc"]),
  identificacion: z.string(),
  nombre: z.string(),
  direccion: z.string(),
  telefono: z.string(),
  email: z.string().email().nullable(),
  is_active: z.boolean(),
  created_at: z.string().datetime(),
});

export type DestinatarioResponseType = z.infer<typeof destinatarioResponseSchema>;
