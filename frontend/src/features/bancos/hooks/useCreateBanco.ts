import { useMutation, useQueryClient } from "@tanstack/react-query";

import apiClient from "@/api/client";
import { bancoResponseSchema } from "../types/banco.types";

export function useCreateBanco() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: { nombre: string }) => {
      const { data } = await apiClient.post("/bancos", payload);
      return bancoResponseSchema.parse(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bancos"] });
    },
  });
}
