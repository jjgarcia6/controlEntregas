import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { XmlIngresoContainer } from "./XmlIngresoContainer";

// ── Mock hooks ───────────────────────────────────────────────────────────────

vi.mock("../hooks/usePreviewXml");
vi.mock("../hooks/useConfirmXml");

// ── Mock navigation ──────────────────────────────────────────────────────────

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return { ...actual, useNavigate: () => mockNavigate };
});

// ── Mock toast ───────────────────────────────────────────────────────────────

vi.mock("sonner", () => ({ toast: { success: vi.fn() } }));

// ── Mock axios.isAxiosError (duck-type on { isAxiosError: true }) ─────────────

vi.mock("axios", async (importOriginal) => {
  const actual = await importOriginal<typeof import("axios")>();
  const isAxiosError = (e: unknown) => !!(e as Record<string, unknown>)?.isAxiosError;
  return { ...actual, default: { ...actual.default, isAxiosError }, isAxiosError };
});

// ── Hook imports (after mocks) ────────────────────────────────────────────────

import { useConfirmXml } from "../hooks/useConfirmXml";
import { usePreviewXml } from "../hooks/usePreviewXml";

const mockUsePreviewXml = vi.mocked(usePreviewXml);
const mockUseConfirmXml = vi.mocked(useConfirmXml);

// ── Fixture data ─────────────────────────────────────────────────────────────

const mockPreviewData = {
  clave_acceso: "1234567890123456789012345678901234567890123456789",
  ruc_emisor: "1790012345001",
  razon_social_emisor: "EMPRESA TEST SA",
  nombre_comercial: null,
  numero_factura: "001-001-000000001",
  fecha_emision: "2024-01-15",
  direccion_emisor: null,
  tipo_emision: 1,
  ambiente: 2,
  ruc_comprador: "0912345678001",
  razon_social_comprador: "CLIENTE TEST SA",
  direccion_comprador: null,
  total_sin_impuestos: 100,
  total_descuento: 0,
  subtotal_iva_0: 0,
  subtotal_gravado: 100,
  valor_iva: 15,
  importe_total: 115,
  moneda: "DOLAR",
  items: [
    {
      codigo_principal: "PROD001",
      codigo_auxiliar: null,
      descripcion: "Producto de prueba",
      cantidad_documento: 4,
      precio_unitario: 25,
      descuento: 0,
      precio_total_sin_imp: 100,
      tarifa_iva: 15,
      valor_iva: 15,
      peso_documento: 10,
      peso_unitario: 2.5,
    },
  ],
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function renderContainer() {
  const result = render(
    <MemoryRouter>
      <XmlIngresoContainer />
    </MemoryRouter>
  );
  return result;
}

async function selectFile(container: HTMLElement, name = "test.xml") {
  const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
  const file = new File(["<xml/>"], name, { type: "text/xml" });
  fireEvent.change(fileInput, { target: { files: [file] } });
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("XmlIngresoContainer", () => {
  beforeEach(() => {
    mockNavigate.mockReset();
    mockUsePreviewXml.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      error: null,
      data: undefined,
    } as unknown as ReturnType<typeof usePreviewXml>);
    mockUseConfirmXml.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      error: null,
      data: undefined,
    } as unknown as ReturnType<typeof useConfirmXml>);
  });

  it("muestra uploader en estado inicial sin preview", () => {
    renderContainer();
    expect(screen.getByText(/seleccionar archivo xml/i)).toBeInTheDocument();
    expect(screen.queryByText(/ítems de la factura/i)).not.toBeInTheDocument();
  });

  it("preview exitoso muestra datos de la factura", async () => {
    const mockMutate = vi.fn((_file: unknown, callbacks: { onSuccess: (d: unknown) => void }) => {
      callbacks.onSuccess(mockPreviewData);
    });
    mockUsePreviewXml.mockReturnValue({
      mutate: mockMutate,
      isPending: false,
      error: null,
      data: undefined,
    } as unknown as ReturnType<typeof usePreviewXml>);

    const { container } = renderContainer();
    await selectFile(container);
    await userEvent.click(screen.getByRole("button", { name: /vista previa/i }));

    await waitFor(() => {
      expect(screen.getByText(/ítems de la factura/i)).toBeInTheDocument();
    });
    expect(screen.getByText("EMPRESA TEST SA")).toBeInTheDocument();
  });

  it("error de preview muestra mensaje de error", async () => {
    const mockMutate = vi.fn(
      (_file: unknown, callbacks: { onError: (e: unknown) => void }) => {
        callbacks.onError({
          isAxiosError: true,
          response: { data: { detail: "Archivo no válido para el sistema" } },
        });
      }
    );
    mockUsePreviewXml.mockReturnValue({
      mutate: mockMutate,
      isPending: false,
      error: null,
      data: undefined,
    } as unknown as ReturnType<typeof usePreviewXml>);

    const { container } = renderContainer();
    await selectFile(container);
    await userEvent.click(screen.getByRole("button", { name: /vista previa/i }));

    await waitFor(() => {
      expect(screen.getByText("Archivo no válido para el sistema")).toBeInTheDocument();
    });
  });

  it("confirmacion exitosa navega a /xml/lista", async () => {
    const mockPreviewMutate = vi.fn(
      (_file: unknown, callbacks: { onSuccess: (d: unknown) => void }) => {
        callbacks.onSuccess(mockPreviewData);
      }
    );
    const mockConfirmMutate = vi.fn(
      (_file: unknown, callbacks: { onSuccess: (d: unknown) => void }) => {
        callbacks.onSuccess({});
      }
    );
    mockUsePreviewXml.mockReturnValue({
      mutate: mockPreviewMutate,
      isPending: false,
      error: null,
      data: undefined,
    } as unknown as ReturnType<typeof usePreviewXml>);
    mockUseConfirmXml.mockReturnValue({
      mutate: mockConfirmMutate,
      isPending: false,
      error: null,
      data: undefined,
    } as unknown as ReturnType<typeof useConfirmXml>);

    const { container } = renderContainer();
    await selectFile(container);
    await userEvent.click(screen.getByRole("button", { name: /vista previa/i }));
    await waitFor(() => expect(screen.getByText(/ítems de la factura/i)).toBeInTheDocument());

    await userEvent.click(screen.getByRole("button", { name: /confirmar ingreso/i }));
    const dialog = await screen.findByRole("dialog");
    await userEvent.click(within(dialog).getByRole("button", { name: /confirmar ingreso/i }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/xml/lista");
    });
  });

  it("clave duplicada muestra mensaje especifico de 409", async () => {
    const mockPreviewMutate = vi.fn(
      (_file: unknown, callbacks: { onSuccess: (d: unknown) => void }) => {
        callbacks.onSuccess(mockPreviewData);
      }
    );
    const mockConfirmMutate = vi.fn(
      (_file: unknown, callbacks: { onError: (e: unknown) => void }) => {
        callbacks.onError({
          isAxiosError: true,
          response: { status: 409, data: { detail: "Ya existe un XML con esa clave de acceso" } },
        });
      }
    );
    mockUsePreviewXml.mockReturnValue({
      mutate: mockPreviewMutate,
      isPending: false,
      error: null,
      data: undefined,
    } as unknown as ReturnType<typeof usePreviewXml>);
    mockUseConfirmXml.mockReturnValue({
      mutate: mockConfirmMutate,
      isPending: false,
      error: null,
      data: undefined,
    } as unknown as ReturnType<typeof useConfirmXml>);

    const { container } = renderContainer();
    await selectFile(container);
    await userEvent.click(screen.getByRole("button", { name: /vista previa/i }));
    await waitFor(() => expect(screen.getByText(/ítems de la factura/i)).toBeInTheDocument());

    await userEvent.click(screen.getByRole("button", { name: /confirmar ingreso/i }));
    const dialog = await screen.findByRole("dialog");
    await userEvent.click(within(dialog).getByRole("button", { name: /confirmar ingreso/i }));

    await waitFor(() => {
      expect(screen.getByText(/clave de acceso duplicada/i)).toBeInTheDocument();
    });
  });
});
