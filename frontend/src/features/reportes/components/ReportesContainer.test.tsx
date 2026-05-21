import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ReportesContainer } from "./ReportesContainer";

// ── Mocks ────────────────────────────────────────────────────────────────────

vi.mock("../hooks/useFetchReporte");
vi.mock("../hooks/useDownloadReportePdf");
vi.mock("../hooks/useDownloadReporteXlsx");
vi.mock("@/features/kardex/hooks/useFetchProductos");
vi.mock("@/features/bancos/hooks/useFetchBancos");
vi.mock("@/features/entregas/hooks/useFetchEntregas");

import { useFetchReporte } from "../hooks/useFetchReporte";
import { useDownloadReportePdf } from "../hooks/useDownloadReportePdf";
import { useDownloadReporteXlsx } from "../hooks/useDownloadReporteXlsx";
import { useFetchProductos } from "@/features/kardex/hooks/useFetchProductos";
import { useFetchBancos } from "@/features/bancos/hooks/useFetchBancos";
import { useFetchEntregas } from "@/features/entregas/hooks/useFetchEntregas";

const mockUseFetchReporte = vi.mocked(useFetchReporte);
const mockUseDownloadReportePdf = vi.mocked(useDownloadReportePdf);
const mockUseDownloadReporteXlsx = vi.mocked(useDownloadReporteXlsx);
const mockUseFetchProductos = vi.mocked(useFetchProductos);
const mockUseFetchBancos = vi.mocked(useFetchBancos);
const mockUseFetchEntregas = vi.mocked(useFetchEntregas);

// ── Helpers ───────────────────────────────────────────────────────────────────

function setupBaseMocks() {
  mockUseDownloadReportePdf.mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
  } as unknown as ReturnType<typeof useDownloadReportePdf>);

  mockUseDownloadReporteXlsx.mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
  } as unknown as ReturnType<typeof useDownloadReporteXlsx>);

  mockUseFetchProductos.mockReturnValue({
    data: { items: [], total: 0, page: 1, page_size: 200 },
  } as unknown as ReturnType<typeof useFetchProductos>);

  mockUseFetchBancos.mockReturnValue({
    data: [],
  } as unknown as ReturnType<typeof useFetchBancos>);

  mockUseFetchEntregas.mockReturnValue({
    data: { items: [], total: 0, page: 1, page_size: 200 },
  } as unknown as ReturnType<typeof useFetchEntregas>);
}

function renderContainer() {
  return render(
    <MemoryRouter>
      <ReportesContainer />
    </MemoryRouter>
  );
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("ReportesContainer", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupBaseMocks();
    mockUseFetchReporte.mockReturnValue({
      data: undefined,
      isLoading: false,
    } as unknown as ReturnType<typeof useFetchReporte>);
  });

  it("renders report selector with four tabs", () => {
    renderContainer();
    expect(screen.getByText("XMLs")).toBeInTheDocument();
    expect(screen.getByText("Kardex")).toBeInTheDocument();
    expect(screen.getByText("Entregas")).toBeInTheDocument();
    expect(screen.getByText("Pagos")).toBeInTheDocument();
  });

  it("shows empty state message when no results", async () => {
    mockUseFetchReporte.mockReturnValue({
      data: { total_xmls: 0, total_valor: 0, filas: [] },
      isLoading: false,
    } as unknown as ReturnType<typeof useFetchReporte>);

    renderContainer();
    const user = userEvent.setup();
    await user.click(screen.getByText("Consultar"));

    expect(
      screen.getByText("Sin resultados para los filtros aplicados")
    ).toBeInTheDocument();
  });

  it("shows loading skeleton while fetching", async () => {
    mockUseFetchReporte.mockReturnValue({
      data: undefined,
      isLoading: true,
    } as unknown as ReturnType<typeof useFetchReporte>);

    const { container } = renderContainer();
    const user = userEvent.setup();
    await user.click(screen.getByText("Consultar"));

    // ReporteTable renders 5 Skeleton divs when isLoading=true
    const skeletons = container.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("disables download pdf button while pdf is pending", () => {
    mockUseDownloadReportePdf.mockReturnValue({
      mutate: vi.fn(),
      isPending: true,
    } as unknown as ReturnType<typeof useDownloadReportePdf>);

    mockUseFetchReporte.mockReturnValue({
      data: {
        total_xmls: 1,
        total_valor: 100,
        filas: [
          {
            xml_id: "abc",
            numero_factura: "001-001-001",
            fecha_emision: "2024-01-01",
            razon_social_emisor: "Test",
            total_sin_impuestos: 100,
            importe_total: 115,
            items: [],
          },
        ],
      },
      isLoading: false,
    } as unknown as ReturnType<typeof useFetchReporte>);

    renderContainer();
    const pdfButton = screen.getByText("Descargar PDF").closest("button");
    expect(pdfButton).toBeDisabled();
  });
});
