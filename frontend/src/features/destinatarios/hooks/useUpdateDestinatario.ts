import { useMutation, useQueryClient } from "@tanstack/react-query";

import apiClient from "@/api/client";
import { destinatarioResponseSchema } from "../types/destinatario.types";

interface DestinatarioUpdatePayload {
  id: string;
  nombre?: string;
  direccion?: string;
  telefono?: string;
  email?: string | null;
}

export function useUpdateDestinatario() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, ...payload }: DestinatarioUpdatePayload) => {
      const { data } = await apiClient.patch(`/destinatarios/${id}`, payload);
      return destinatarioResponseSchema.parse(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["destinatarios"] });
    },
  });
}
