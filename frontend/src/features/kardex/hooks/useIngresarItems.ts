import { useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";

import apiClient from "@/api/client";
import { KardexIngresoType, KardexMovimientoType, kardexMovimientoSchema } from "../types/kardex.types";

interface IngresarItemsPayload {
  xmlId: string;
  body: KardexIngresoType;
}

export function useIngresarItems() {
  const queryClient = useQueryClient();

  const mutation = useMutation<KardexMovimientoType[], Error, IngresarItemsPayload>({
    mutationFn: async ({ xmlId, body }) => {
      const { data } = await apiClient.post(`/xmls/${xmlId}/ingresos`, body);
      return (data as unknown[]).map((item) => kardexMovimientoSchema.parse(item));
    },
    onSuccess: (_data, { xmlId }) => {
      queryClient.invalidateQueries({ queryKey: ["kardex", "productos"] });
      queryClient.invalidateQueries({ queryKey: ["xmls", xmlId, "pendientes"] });
    },
  });

  const errorMessage: string | null = (() => {
    if (!mutation.error) return null;
    if (axios.isAxiosError(mutation.error)) {
      const detail = (mutation.error.response?.data as { detail?: string } | undefined)?.detail;
      return detail ?? "Error al ingresar ítems al Kardex";
    }
    return mutation.error.message || "Error al ingresar ítems al Kardex";
  })();

  return { ...mutation, errorMessage };
}
