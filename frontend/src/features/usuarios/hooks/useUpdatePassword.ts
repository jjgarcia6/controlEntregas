import { useMutation, useQueryClient } from "@tanstack/react-query";

import apiClient from "@/api/client";
import { usuarioResponseSchema } from "../types/usuario.types";

interface UpdatePasswordPayload {
  id: string;
  nueva_password: string;
}

export function useUpdatePassword() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, nueva_password }: UpdatePasswordPayload) => {
      const { data } = await apiClient.patch(`/usuarios/${id}/password`, {
        nueva_password,
      });
      return usuarioResponseSchema.parse(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["usuarios"] });
    },
  });
}
