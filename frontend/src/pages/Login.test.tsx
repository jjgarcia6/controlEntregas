import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect } from "vitest";

import { Login } from "./Login";

function renderLogin() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("Login page", () => {
  it("should_render_login_form_with_email_and_password_inputs", () => {
    renderLogin();
    expect(screen.getByRole("textbox", { name: /correo electrónico/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /iniciar sesión/i })).toBeInTheDocument();
  });

  it("should_associate_labels_with_inputs_via_htmlFor", () => {
    renderLogin();
    const emailInput = screen.getByLabelText(/correo electrónico/i);
    const passwordInput = screen.getByLabelText(/contraseña/i);
    expect(emailInput).toHaveAttribute("id", "email");
    expect(passwordInput).toHaveAttribute("id", "password");
  });

  it("should_have_submit_button_with_type_submit", () => {
    renderLogin();
    const submitBtn = screen.getByRole("button", { name: /iniciar sesión/i });
    expect(submitBtn).toHaveAttribute("type", "submit");
  });
});
