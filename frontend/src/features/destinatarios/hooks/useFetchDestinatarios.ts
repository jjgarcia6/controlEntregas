import { useQuery } from "@tanstack/react-query";
import { z } from "zod";

import apiClient from "@/api/client";
import { destinatarioResponseSchema } from "../types/destinatario.types";

export function useFetchDestinatarios() {
  return useQuery({
    queryKey: ["destinatarios"],
    queryFn: async () => {
      const { data } = await apiClient.get("/destinatarios");
      return z.array(destinatarioResponseSchema).parse(data);
    },
  });
}
