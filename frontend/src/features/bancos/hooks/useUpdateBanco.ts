import { useMutation, useQueryClient } from "@tanstack/react-query";

import apiClient from "@/api/client";
import { bancoResponseSchema } from "../types/banco.types";

export function useUpdateBanco() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, nombre }: { id: string; nombre: string }) => {
      const { data } = await apiClient.patch(`/bancos/${id}`, { nombre });
      return bancoResponseSchema.parse(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bancos"] });
    },
  });
}
