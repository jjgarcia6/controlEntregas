import { useMutation, useQueryClient } from "@tanstack/react-query";

import apiClient from "@/api/client";
import { destinatarioResponseSchema } from "../types/destinatario.types";

interface DestinatarioCreatePayload {
  identificacion: string;
  nombre: string;
  direccion: string;
  telefono: string;
  email?: string | null;
}

export function useCreateDestinatario() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: DestinatarioCreatePayload) => {
      const { data } = await apiClient.post("/destinatarios", payload);
      return destinatarioResponseSchema.parse(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["destinatarios"] });
    },
  });
}
