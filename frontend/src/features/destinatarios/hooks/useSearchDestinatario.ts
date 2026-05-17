import { useQuery } from "@tanstack/react-query";

import apiClient from "@/api/client";
import { destinatarioResponseSchema } from "../types/destinatario.types";

export function useSearchDestinatario(identificacion: string) {
  return useQuery({
    queryKey: ["destinatarios", identificacion],
    queryFn: async () => {
      const { data } = await apiClient.get(
        `/destinatarios/${identificacion}`
      );
      return destinatarioResponseSchema.parse(data);
    },
    enabled: false,
  });
}
