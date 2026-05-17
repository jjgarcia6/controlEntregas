import { useLogin } from "../hooks/useLogin";
import { LoginForm } from "./LoginForm";

export function LoginContainer() {
  const { mutate, isPending, error } = useLogin();

  const errorMessage =
    error instanceof Error ? error.message : error ? String(error) : null;

  return (
    <LoginForm
      onSubmit={(values) => mutate(values)}
      isPending={isPending}
      error={errorMessage}
    />
  );
}
