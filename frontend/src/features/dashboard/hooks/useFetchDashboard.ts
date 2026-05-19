import { useQuery } from "@tanstack/react-query";

import apiClient from "@/api/client";
import { dashboardResponseSchema } from "../types/dashboard.types";

export function useFetchDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => {
      const { data } = await apiClient.get("/dashboard");
      return dashboardResponseSchema.parse(data);
    },
    refetchInterval: 60_000,
  });
}
