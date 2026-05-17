import { useMutation, useQueryClient } from "@tanstack/react-query";

import apiClient from "@/api/client";
import { usuarioResponseSchema } from "../types/usuario.types";

interface UsuarioCreatePayload {
  email: string;
  password: string;
  nombre: string;
  rol: "admin" | "operador" | "lectura";
}

export function useCreateUsuario() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: UsuarioCreatePayload) => {
      const { data } = await apiClient.post("/usuarios", payload);
      return usuarioResponseSchema.parse(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["usuarios"] });
    },
  });
}
