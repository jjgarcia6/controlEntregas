import { useQuery } from "@tanstack/react-query";

import apiClient from "@/api/client";
import { paginatedResponseSchema } from "@/shared/types/api.types";
import { entregaListItemSchema } from "../types/entrega.types";

interface EntregasFiltros {
  destinatario_id?: string;
  estado?: "activa" | "eliminada";
  fecha_desde?: string;
  fecha_hasta?: string;
}

export function useFetchEntregas(
  filtros: EntregasFiltros = {},
  page: number = 1,
  pageSize: number = 20,
) {
  return useQuery({
    queryKey: ["entregas", filtros, page, pageSize],
    queryFn: async () => {
      const params: Record<string, string | number> = {
        page,
        page_size: pageSize,
      };
      if (filtros.destinatario_id) params.destinatario_id = filtros.destinatario_id;
      if (filtros.estado) params.estado = filtros.estado;
      if (filtros.fecha_desde) params.fecha_desde = filtros.fecha_desde;
      if (filtros.fecha_hasta) params.fecha_hasta = filtros.fecha_hasta;

      const { data } = await apiClient.get("/entregas", { params });
      return paginatedResponseSchema(entregaListItemSchema).parse(data);
    },
  });
}
