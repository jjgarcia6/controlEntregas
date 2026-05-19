import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { type DashboardResponse } from "../types/dashboard.types";

interface KpiCardsProps {
  data: DashboardResponse;
}

function fmt(value: number): string {
  return `$${value.toFixed(2)}`;
}

function pct(cobrado: number, facturado: number): string {
  if (facturado === 0) return "0%";
  return `${((cobrado / facturado) * 100).toFixed(1)}%`;
}

export function KpiCards({ data }: KpiCardsProps) {
  const tasaCobranza = pct(data.total_cobrado, data.total_facturado);

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Entregas activas
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold text-foreground">
            {data.entregas_activas}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Saldo pendiente
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold text-destructive">
            {fmt(data.saldo_pendiente_total)}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Cobrado mes actual
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold text-green-600 dark:text-green-400">
            {fmt(data.pagos_mes_actual)}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Tasa de cobranza
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold text-foreground">{tasaCobranza}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {fmt(data.total_cobrado)} de {fmt(data.total_facturado)}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
