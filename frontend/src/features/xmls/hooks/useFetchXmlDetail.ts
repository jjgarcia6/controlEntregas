import { useQuery } from "@tanstack/react-query";

import apiClient from "@/api/client";
import { xmlResponseSchema } from "../types/xml.types";

export function useFetchXmlDetail(id: string) {
  return useQuery({
    queryKey: ["xmls", id],
    enabled: id.length > 0,
    queryFn: async () => {
      const { data } = await apiClient.get(`/xmls/${id}`);
      return xmlResponseSchema.parse(data);
    },
  });
}
