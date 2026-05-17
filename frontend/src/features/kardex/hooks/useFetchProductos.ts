import { useQuery } from "@tanstack/react-query";

import apiClient from "@/api/client";
import { paginatedResponseSchema } from "@/shared/types/api.types";
import { productoConSaldoSchema } from "../types/kardex.types";

export function useFetchProductos(page: number = 1, pageSize: number = 20) {
  return useQuery({
    queryKey: ["kardex", "productos", page, pageSize],
    queryFn: async () => {
      const { data } = await apiClient.get("/kardex/productos", {
        params: { page, page_size: pageSize },
      });
      return paginatedResponseSchema(productoConSaldoSchema).parse(data);
    },
  });
}
