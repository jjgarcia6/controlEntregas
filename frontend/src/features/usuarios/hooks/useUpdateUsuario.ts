import { useMutation, useQueryClient } from "@tanstack/react-query";

import apiClient from "@/api/client";
import { usuarioResponseSchema } from "../types/usuario.types";

interface UsuarioUpdatePayload {
  id: string;
  email?: string;
  nombre?: string;
  rol?: "admin" | "operador" | "lectura";
}

export function useUpdateUsuario() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, ...payload }: UsuarioUpdatePayload) => {
      const { data } = await apiClient.patch(`/usuarios/${id}`, payload);
      return usuarioResponseSchema.parse(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["usuarios"] });
    },
  });
}
