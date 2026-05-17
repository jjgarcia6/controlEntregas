import { useMutation, useQueryClient } from "@tanstack/react-query";

import apiClient from "@/api/client";
import { xmlResponseSchema } from "../types/xml.types";

export function useConfirmXml() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await apiClient.post("/xmls", formData);
      return xmlResponseSchema.parse(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["xmls"] });
    },
  });
}
