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

export const usuarioDesbloqueoSchema = z.object({
  usuario_id: z.string().uuid().describe("ID del usuario desbloqueado"),
  email: z.string().email().describe("Email del usuario"),
  intentos_eliminados: z
    .number()
    .int()
    .nonnegative()
    .describe("Cantidad de intentos fallidos eliminados"),
});

export type UsuarioDesbloqueoType = z.infer<typeof usuarioDesbloqueoSchema>;
