import { z } from "zod";

export const usuarioResponseSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  nombre: z.string(),
  rol: z.enum(["admin", "operador", "lectura"]),
  ultimo_login: z.string().datetime().nullable(),
  is_active: z.boolean(),
  created_at: z.string().datetime(),
});

export type UsuarioResponseType = z.infer<typeof usuarioResponseSchema>;
