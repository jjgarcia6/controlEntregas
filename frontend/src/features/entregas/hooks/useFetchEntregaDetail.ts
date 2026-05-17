import { useQuery } from "@tanstack/react-query";

import apiClient from "@/api/client";
import { entregaResponseSchema } from "../types/entrega.types";

export function useFetchEntregaDetail(id: string | undefined) {
  return useQuery({
    queryKey: ["entregas", id],
    queryFn: async () => {
      const { data } = await apiClient.get(`/entregas/${id}`);
      return entregaResponseSchema.parse(data);
    },
    enabled: !!id,
  });
}
