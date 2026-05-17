import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { LoginContainer } from "./LoginContainer";

const mockMutate = vi.fn();

vi.mock("../hooks/useLogin", () => ({
  useLogin: vi.fn(() => ({ mutate: mockMutate, isPending: false, error: null })),
}));

import { useLogin } from "../hooks/useLogin";
const mockUseLogin = vi.mocked(useLogin);

function renderContainer() {
  return render(
    <MemoryRouter>
      <LoginContainer />
    </MemoryRouter>
  );
}

describe("LoginContainer", () => {
  beforeEach(() => {
    mockMutate.mockReset();
    mockUseLogin.mockReturnValue({ mutate: mockMutate, isPending: false, error: null });
  });

  it("should display the error message returned by useLogin", () => {
    mockUseLogin.mockReturnValue({
      mutate: mockMutate,
      isPending: false,
      error: new Error("Credenciales inválidas"),
    });
    renderContainer();
    expect(screen.getByText("Credenciales inválidas")).toBeInTheDocument();
  });

  it("should disable the submit button and change its label while isPending", () => {
    mockUseLogin.mockReturnValue({ mutate: mockMutate, isPending: true, error: null });
    renderContainer();
    const button = screen.getByRole("button", { name: /iniciando sesión/i });
    expect(button).toBeDisabled();
  });

  it("should call mutate with credentials on successful form submission", async () => {
    renderContainer();
    await userEvent.type(screen.getByLabelText(/correo electrónico/i), "admin@test.com");
    await userEvent.type(screen.getByLabelText(/contraseña/i), "Password1!");
    await userEvent.click(screen.getByRole("button", { name: /iniciar sesión/i }));
    expect(mockMutate).toHaveBeenCalledWith({
      email: "admin@test.com",
      password: "Password1!",
    });
  });
});
