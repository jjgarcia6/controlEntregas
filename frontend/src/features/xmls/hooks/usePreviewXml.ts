import { useMutation } from "@tanstack/react-query";

import apiClient from "@/api/client";
import { xmlPreviewSchema } from "../types/xml.types";

export function usePreviewXml() {
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await apiClient.post("/xmls/preview", formData);
      return xmlPreviewSchema.parse(data);
    },
  });
}
