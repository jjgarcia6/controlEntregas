import { useQuery } from "@tanstack/react-query";
import { z } from "zod";

import apiClient from "@/api/client";
import { xmlItemPendienteSchema } from "@/features/xmls/types/xml.types";

export type XmlItemPendienteType = z.infer<typeof xmlItemPendienteSchema>;

export function useFetchXmlPendientes(xmlId: string | undefined) {
  return useQuery({
    queryKey: ["xmls", xmlId, "pendientes"],
    enabled: !!xmlId,
    queryFn: async () => {
      const { data } = await apiClient.get(`/xmls/${xmlId}/pendientes`);
      return z.array(xmlItemPendienteSchema).parse(data);
    },
  });
}
