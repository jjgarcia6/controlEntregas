import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import apiClient from "@/api/client";
import { entregaResponseSchema, type EntregaRequestType } from "../types/entrega.types";

export function useCreateEntrega() {
  const queryClient = useQueryClient();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: async (payload: EntregaRequestType) => {
      const { data } = await apiClient.post("/entregas", payload);
      return entregaResponseSchema.parse(data);
    },
    onSuccess: () => {
      setErrorMessage(null);
      queryClient.invalidateQueries({ queryKey: ["entregas"] });
      queryClient.invalidateQueries({ queryKey: ["kardex", "productos"] });
    },
    onError: (error: unknown) => {
      const detail =
        (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setErrorMessage(detail ?? "Error al crear la entrega");
    },
  });

  return { ...mutation, errorMessage };
}
