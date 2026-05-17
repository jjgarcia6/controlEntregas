import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import apiClient from "@/api/client";
import { useAuthStore } from "@/store/authStore";
import { loginResponseSchema } from "../types/auth.types";

export function useLogin() {
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async (credentials: { email: string; password: string }) => {
      const { data } = await apiClient.post("/auth/login", credentials);
      return loginResponseSchema.parse(data);
    },
    onSuccess: (data) => {
      login(data.token, data.user);
      navigate("/dashboard");
    },
  });
}
