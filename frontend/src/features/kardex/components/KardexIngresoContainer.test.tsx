import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { KardexIngresoContainer } from "./KardexIngresoContainer";

// ── Mock hooks ───────────────────────────────────────────────────────────────

vi.mock("../hooks/useFetchXmlPendientes");
vi.mock("../hooks/useIngresarItems");

// ── Mock toast ───────────────────────────────────────────────────────────────

vi.mock("sonner", () => ({ toast: { success: vi.fn() } }));

// ── Hook imports (after mocks) ────────────────────────────────────────────────

import { toast } from "sonner";
import { useFetchXmlPendientes } from "../hooks/useFetchXmlPendientes";
import { useIngresarItems } from "../hooks/useIngresarItems";

const mockUseFetchXmlPendientes = vi.mocked(useFetchXmlPendientes);
const mockUseIngresarItems = vi.mocked(useIngresarItems);
const mockToastSuccess = vi.mocked(toast.success);

// ── Fixture data ──────────────────────────────────────────────────────────────

const MOCK_XML_ID = "550e8400-e29b-41d4-a716-446655440000";

const mockPendientes = [
  {
    id: "item-uuid-0001-0000-000000000001",
    codigo_principal: "PROD001",
    descripcion: "Producto A",
    cantidad_documento: 4,
    cantidad_ingresada: 0,
    cantidad_pendiente: 4,
    precio_unitario: 25,
    precio_total_sin_imp: 100,
    peso_unitario: 2.5,
  },
  {
    id: "item-uuid-0001-0000-000000000002",
    codigo_principal: "PROD002",
    descripcion: "Producto B",
    cantidad_documento: 6,
    cantidad_ingresada: 2,
    cantidad_pendiente: 4,
    precio_unitario: 10,
    precio_total_sin_imp: 40,
    peso_unitario: 1.0,
  },
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function renderContainer() {
  return render(
    <MemoryRouter>
      <KardexIngresoContainer />
    </MemoryRouter>
  );
}

async function buscarXml() {
  const input = screen.getByPlaceholderText(/ID del XML/i);
  await userEvent.clear(input);
  await userEvent.type(input, MOCK_XML_ID);
  await userEvent.click(screen.getByRole("button", { name: /buscar/i }));
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("KardexIngresoContainer", () => {
  beforeEach(() => {
    mockToastSuccess.mockReset();

    mockUseFetchXmlPendientes.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useFetchXmlPendientes>);

    mockUseIngresarItems.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      error: null,
      errorMessage: null,
    } as unknown as ReturnType<typeof useIngresarItems>);
  });

  it("muestra el campo de búsqueda de XML en estado inicial", () => {
    renderContainer();
    expect(screen.getByPlaceholderText(/ID del XML/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /buscar/i })).toBeInTheDocument();
  });

  it("flujo principal: carga ítems, selecciona, confirma y muestra éxito", async () => {
    const mockMutate = vi.fn(
      (
        _vars: unknown,
        callbacks?: { onSuccess?: () => void }
      ) => {
        callbacks?.onSuccess?.();
      }
    );

    mockUseFetchXmlPendientes.mockReturnValue({
      data: mockPendientes,
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useFetchXmlPendientes>);

    mockUseIngresarItems.mockReturnValue({
      mutate: mockMutate,
      isPending: false,
      error: null,
      errorMessage: null,
    } as unknown as ReturnType<typeof useIngresarItems>);

    renderContainer();
    await buscarXml();

    await waitFor(() => {
      expect(screen.getByText("Producto A")).toBeInTheDocument();
    });

    // Select the first item via its checkbox
    const checkboxes = screen.getAllByRole("checkbox");
    await userEvent.click(checkboxes[0]);

    // Confirm
    const confirmBtn = screen.getByRole("button", { name: /confirmar ingreso/i });
    await userEvent.click(confirmBtn);

    await waitFor(() => {
      expect(mockMutate).toHaveBeenCalledOnce();
      expect(mockToastSuccess).toHaveBeenCalledWith(
        expect.stringMatching(/kardex/i)
      );
    });
  });

  it("muestra mensaje de error cuando la API retorna error", async () => {
    mockUseFetchXmlPendientes.mockReturnValue({
      data: mockPendientes,
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useFetchXmlPendientes>);

    mockUseIngresarItems.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      error: new Error("Unprocessable"),
      errorMessage: "La cantidad ingresada supera la cantidad pendiente",
    } as unknown as ReturnType<typeof useIngresarItems>);

    renderContainer();
    await buscarXml();

    await waitFor(() => {
      expect(
        screen.getByText(/la cantidad ingresada supera la cantidad pendiente/i)
      ).toBeInTheDocument();
    });
  });

  it("muestra estado de carga mientras se cargan los ítems", async () => {
    mockUseFetchXmlPendientes.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as unknown as ReturnType<typeof useFetchXmlPendientes>);

    renderContainer();
    await buscarXml();

    await waitFor(() => {
      expect(screen.getByText(/cargando ítems/i)).toBeInTheDocument();
    });
  });

  it("accesibilidad: checkboxes tienen aria-label descriptivo", async () => {
    mockUseFetchXmlPendientes.mockReturnValue({
      data: mockPendientes,
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useFetchXmlPendientes>);

    renderContainer();
    await buscarXml();

    await waitFor(() => {
      expect(screen.getByText("Producto A")).toBeInTheDocument();
    });

    const checkboxA = screen.getByRole("checkbox", { name: /seleccionar producto a/i });
    expect(checkboxA).toBeInTheDocument();
  });

  it("accesibilidad: campo de cantidad muestra aria-describedby cuando hay error", async () => {
    mockUseFetchXmlPendientes.mockReturnValue({
      data: mockPendientes,
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useFetchXmlPendientes>);

    renderContainer();
    await buscarXml();

    await waitFor(() => {
      expect(screen.getByText("Producto A")).toBeInTheDocument();
    });

    const checkboxes = screen.getAllByRole("checkbox");
    await userEvent.click(checkboxes[0]); // enable quantity field

    const numInputs = screen.getAllByRole("spinbutton");
    fireEvent.change(numInputs[0], { target: { value: "0" } });

    await waitFor(() => {
      expect(screen.getByText(/mín\. 1/i)).toBeInTheDocument();
    });

    const errorMsg = screen.getByText(/mín\. 1/i);
    const errorId = errorMsg.getAttribute("id");
    expect(errorId).toBeTruthy();
    expect(numInputs[0]).toHaveAttribute("aria-describedby", errorId);
  });
});
