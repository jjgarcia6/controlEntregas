import { useQuery } from "@tanstack/react-query";

import apiClient from "@/api/client";
import { paginatedResponseSchema } from "@/shared/types/api.types";
import { xmlListItemSchema } from "../types/xml.types";

export function useFetchXmls(page: number = 1, pageSize: number = 20) {
  return useQuery({
    queryKey: ["xmls", page, pageSize],
    queryFn: async () => {
      const { data } = await apiClient.get("/xmls", {
        params: { page, page_size: pageSize },
      });
      return paginatedResponseSchema(xmlListItemSchema).parse(data);
    },
  });
}
