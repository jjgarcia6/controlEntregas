import { useMutation, useQueryClient } from "@tanstack/react-query";

import apiClient from "@/api/client";
import { usuarioResponseSchema } from "../types/usuario.types";

export function useDeleteUsuario() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.delete(`/usuarios/${id}`);
      return usuarioResponseSchema.parse(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["usuarios"] });
    },
  });
}
