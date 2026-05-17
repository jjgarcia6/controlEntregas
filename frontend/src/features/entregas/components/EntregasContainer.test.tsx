import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { EntregasContainer } from "./EntregasContainer";

// ── Mocks ─────────────────────────────────────────────────────────────────────

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock("../hooks/useFetchEntregas");
vi.mock("@/store/authStore");

import { useAuthStore } from "@/store/authStore";
import { useFetchEntregas } from "../hooks/useFetchEntregas";

const mockUseFetchEntregas = vi.mocked(useFetchEntregas);
const mockUseAuthStore = vi.mocked(useAuthStore);

// ── Fixture data ──────────────────────────────────────────────────────────────

const ENTREGA_ACTIVA = {
  id: "ent-uuid-0001-0000-000000000001",
  numero: 1,
  snap_identificacion: "1234567890",
  snap_nombre: "Juan Pérez",
  total_entrega: "150.00",
  saldo_pendiente: "150.00",
  estado: "activa" as const,
  created_at: "2026-05-17T10:00:00Z",
};

const ENTREGA_ELIMINADA = {
  id: "ent-uuid-0002-0000-000000000002",
  numero: 2,
  snap_identificacion: "0987654321",
  snap_nombre: "María García",
  total_entrega: "200.00",
  saldo_pendiente: "0.00",
  estado: "eliminada" as const,
  created_at: "2026-05-16T09:00:00Z",
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function renderContainer() {
  return render(
    <MemoryRouter>
      <EntregasContainer />
    </MemoryRouter>,
  );
}

function setupAdminUser() {
  mockUseAuthStore.mockReturnValue({
    user: { id: "user-001", nombre: "Admin", rol: "admin" },
    token: "tok",
  } as unknown as ReturnType<typeof useAuthStore>);
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("EntregasContainer", () => {
  beforeEach(() => {
    mockNavigate.mockReset();
    mockUseFetchEntregas.mockReturnValue({
      data: undefined,
      isLoading: false,
    } as unknown as ReturnType<typeof useFetchEntregas>);
    setupAdminUser();
  });

  it("muestra la tabla con encabezados en estado inicial", () => {
    renderContainer();
    expect(screen.getByRole("columnheader", { name: "N°" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Destinatario" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Estado" })).toBeInTheDocument();
  });

  it("muestra el botón Nueva Entrega para rol admin", () => {
    setupAdminUser();
    renderContainer();
    expect(screen.getByRole("button", { name: /nueva entrega/i })).toBeInTheDocument();
  });

  it("muestra el botón Nueva Entrega para rol operador", () => {
    mockUseAuthStore.mockReturnValue({
      user: { id: "user-003", nombre: "Operador", rol: "operador" },
      token: "tok",
    } as unknown as ReturnType<typeof useAuthStore>);
    renderContainer();
    expect(screen.getByRole("button", { name: /nueva entrega/i })).toBeInTheDocument();
  });

  it("oculta el botón Nueva Entrega para rol lectura", () => {
    mockUseAuthStore.mockReturnValue({
      user: { id: "user-002", nombre: "Lector", rol: "lectura" },
      token: "tok",
    } as unknown as ReturnType<typeof useAuthStore>);
    renderContainer();
    expect(screen.queryByRole("button", { name: /nueva entrega/i })).not.toBeInTheDocument();
  });

  it("muestra mensaje vacío cuando no hay entregas", () => {
    mockUseFetchEntregas.mockReturnValue({
      data: { items: [], total: 0, page: 1, page_size: 20 },
      isLoading: false,
    } as unknown as ReturnType<typeof useFetchEntregas>);
    renderContainer();
    expect(screen.getByText(/sin entregas registradas/i)).toBeInTheDocument();
  });

  it("muestra las entregas con nombre del destinatario", async () => {
    mockUseFetchEntregas.mockReturnValue({
      data: {
        items: [ENTREGA_ACTIVA, ENTREGA_ELIMINADA],
        total: 2,
        page: 1,
        page_size: 20,
      },
      isLoading: false,
    } as unknown as ReturnType<typeof useFetchEntregas>);

    renderContainer();

    await waitFor(() => {
      expect(screen.getByText("Juan Pérez")).toBeInTheDocument();
      expect(screen.getByText("María García")).toBeInTheDocument();
    });
  });

  it("muestra badge activa y eliminada por estado", async () => {
    mockUseFetchEntregas.mockReturnValue({
      data: {
        items: [ENTREGA_ACTIVA, ENTREGA_ELIMINADA],
        total: 2,
        page: 1,
        page_size: 20,
      },
      isLoading: false,
    } as unknown as ReturnType<typeof useFetchEntregas>);

    renderContainer();

    await waitFor(() => {
      expect(screen.getByText("activa")).toBeInTheDocument();
      expect(screen.getByText("eliminada")).toBeInTheDocument();
    });
  });

  it("navega a /entregas/nueva al hacer click en Nueva Entrega", async () => {
    renderContainer();
    await userEvent.click(screen.getByRole("button", { name: /nueva entrega/i }));
    expect(mockNavigate).toHaveBeenCalledWith("/entregas/nueva");
  });

  it("muestra el número de entrega y la identificación del destinatario", async () => {
    mockUseFetchEntregas.mockReturnValue({
      data: {
        items: [ENTREGA_ACTIVA],
        total: 1,
        page: 1,
        page_size: 20,
      },
      isLoading: false,
    } as unknown as ReturnType<typeof useFetchEntregas>);

    renderContainer();

    await waitFor(() => {
      expect(screen.getByText("1")).toBeInTheDocument();
      expect(screen.getByText("1234567890")).toBeInTheDocument();
      expect(screen.getByText("Juan Pérez")).toBeInTheDocument();
    });
  });

  it("navega al detalle al hacer click en una fila", async () => {
    mockUseFetchEntregas.mockReturnValue({
      data: {
        items: [ENTREGA_ACTIVA],
        total: 1,
        page: 1,
        page_size: 20,
      },
      isLoading: false,
    } as unknown as ReturnType<typeof useFetchEntregas>);

    renderContainer();

    await waitFor(() => {
      expect(screen.getByText("Juan Pérez")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("Juan Pérez"));
    expect(mockNavigate).toHaveBeenCalledWith(`/entregas/${ENTREGA_ACTIVA.id}`);
  });
});
