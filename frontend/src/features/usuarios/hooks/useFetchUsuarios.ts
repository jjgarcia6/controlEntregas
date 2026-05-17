import { useQuery } from "@tanstack/react-query";
import { z } from "zod";

import apiClient from "@/api/client";
import { usuarioResponseSchema } from "../types/usuario.types";

export function useFetchUsuarios() {
  return useQuery({
    queryKey: ["usuarios"],
    queryFn: async () => {
      const { data } = await apiClient.get("/usuarios");
      return z.array(usuarioResponseSchema).parse(data);
    },
  });
}
