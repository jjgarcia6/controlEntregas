import { z } from "zod";

export const usuarioPublicoSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  nombre: z.string(),
  rol: z.enum(["admin", "operador", "lectura"]),
});

export const loginResponseSchema = z.object({
  token: z.string(),
  user: usuarioPublicoSchema,
});

export const refreshResponseSchema = z.object({ token: z.string() });

export type UsuarioPublicoType = z.infer<typeof usuarioPublicoSchema>;
export type LoginResponseType = z.infer<typeof loginResponseSchema>;
export type RefreshResponseType = z.infer<typeof refreshResponseSchema>;
