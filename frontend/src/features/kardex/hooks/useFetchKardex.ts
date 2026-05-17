import { useQuery } from "@tanstack/react-query";

import apiClient from "@/api/client";
import { paginatedResponseSchema } from "@/shared/types/api.types";
import { kardexMovimientoSchema } from "../types/kardex.types";

export function useFetchKardex(
  productoId: string | undefined,
  page: number = 1,
  pageSize: number = 20,
  fechaDesde?: string,
  fechaHasta?: string,
) {
  return useQuery({
    queryKey: ["kardex", "historial", productoId, fechaDesde, fechaHasta, page],
    enabled: !!productoId,
    queryFn: async () => {
      const params: Record<string, string | number> = { page, page_size: pageSize };
      if (fechaDesde) params.fecha_desde = fechaDesde;
      if (fechaHasta) params.fecha_hasta = fechaHasta;
      const { data } = await apiClient.get(`/kardex/${productoId}`, { params });
      return paginatedResponseSchema(kardexMovimientoSchema).parse(data);
    },
  });
}
