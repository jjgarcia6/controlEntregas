import { useQuery } from "@tanstack/react-query";
import { z } from "zod";

import apiClient from "@/api/client";
import { bancoResponseSchema } from "../types/banco.types";

export function useFetchBancos() {
  return useQuery({
    queryKey: ["bancos"],
    queryFn: async () => {
      const { data } = await apiClient.get("/bancos");
      return z.array(bancoResponseSchema).parse(data);
    },
  });
}
