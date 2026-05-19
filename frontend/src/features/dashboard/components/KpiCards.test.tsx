import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { KpiCards } from "./KpiCards";
import type { DashboardResponse } from "../types/dashboard.types";

function makeData(overrides: Partial<DashboardResponse> = {}): DashboardResponse {
  return {
    entregas_activas: 3,
    saldo_pendiente_total: 1500.5,
    total_facturado: 3000.0,
    total_cobrado: 1499.5,
    pagos_mes_actual: 800.0,
    entregas_mas_antiguas: [],
    ...overrides,
  };
}

describe("KpiCards", () => {
  it("renders all 4 card titles and correct values from data", () => {
    render(<KpiCards data={makeData()} />);

    expect(screen.getByText("Entregas activas")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();

    expect(screen.getByText("Saldo pendiente")).toBeInTheDocument();
    expect(screen.getByText("$1500.50")).toBeInTheDocument();

    expect(screen.getByText("Cobrado mes actual")).toBeInTheDocument();
    expect(screen.getByText("$800.00")).toBeInTheDocument();

    expect(screen.getByText("Tasa de cobranza")).toBeInTheDocument();
    // total_cobrado / total_facturado * 100 = 1499.5 / 3000 * 100 ≈ 49.983... → 50.0%
    expect(screen.getByText("50.0%")).toBeInTheDocument();
  });

  it("shows 0% tasa when total_facturado is 0 (no division by zero)", () => {
    render(
      <KpiCards
        data={makeData({
          total_facturado: 0,
          saldo_pendiente_total: 0,
          total_cobrado: 0,
          pagos_mes_actual: 0,
        })}
      />
    );

    // Multiple cards show $0.00; verify at least one exists and the tasa shows 0% safely
    const zeroAmounts = screen.getAllByText("$0.00");
    expect(zeroAmounts.length).toBeGreaterThan(0);
    expect(screen.getByText("0%")).toBeInTheDocument();
  });

  it("each card has accessible text for the metric name", () => {
    render(<KpiCards data={makeData()} />);

    const titles = [
      "Entregas activas",
      "Saldo pendiente",
      "Cobrado mes actual",
      "Tasa de cobranza",
    ];
    for (const title of titles) {
      expect(screen.getByText(title)).toBeInTheDocument();
    }
  });
});
