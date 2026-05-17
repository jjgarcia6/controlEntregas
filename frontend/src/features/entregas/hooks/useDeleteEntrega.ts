import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import apiClient from "@/api/client";

export function useDeleteEntrega() {
  const queryClient = useQueryClient();
  const [pagosBlockers, setPagosBlockers] = useState<string[]>([]);

  const mutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/entregas/${id}`);
    },
    onSuccess: () => {
      setPagosBlockers([]);
      queryClient.invalidateQueries({ queryKey: ["entregas"] });
      queryClient.invalidateQueries({ queryKey: ["kardex", "productos"] });
    },
    onError: (error: unknown) => {
      const response = (error as { response?: { status?: number; data?: { detail?: unknown } } })
        ?.response;
      if (response?.status === 409) {
        const detail = response.data?.detail;
        if (Array.isArray(detail)) {
          setPagosBlockers(detail as string[]);
        } else if (typeof detail === "string") {
          setPagosBlockers([detail]);
        }
      }
    },
  });

  return { ...mutation, pagosBlockers };
}
