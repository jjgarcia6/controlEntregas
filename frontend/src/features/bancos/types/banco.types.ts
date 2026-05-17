import { z } from "zod";

export const bancoResponseSchema = z.object({
  id: z.string().uuid(),
  nombre: z.string(),
  is_active: z.boolean(),
  created_at: z.string().datetime(),
});

export type BancoResponseType = z.infer<typeof bancoResponseSchema>;
