import { Navigate } from "react-router-dom";

import { LoginContainer } from "@/features/auth/components/LoginContainer";
import { useAuthStore } from "@/store/authStore";

export function Login() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  if (isAuthenticated()) {
    return <Navigate to="/dashboard" replace />;
  }

  return <LoginContainer />;
}
