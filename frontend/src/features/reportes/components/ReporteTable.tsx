import { Skeleton } from "@/components/ui/skeleton";

const NUMERIC_COLUMNS = new Set([
  "cantidad",
  "costo_unitario",
  "costo_total",
  "saldo_cantidad",
  "saldo_valor",
  "total_sin_impuestos",
  "importe_total",
  "total_entrega",
  "saldo_pendiente",
  "valor_total",
  "numero",
  "fecha_creacion",
  "nombre",
  "identificacion",
  "estado",
]);

interface ReporteTableProps {
  columnas: string[];
  filas: Record<string, unknown>[];
  isLoading: boolean;
}

export function ReporteTable({
  columnas,
  filas,
  isLoading,
}: ReporteTableProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-8 w-full" />
        ))}
      </div>
    );
  }

  if (filas.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-muted/20 py-12 text-center text-sm text-muted-foreground">
        Sin resultados para los filtros aplicados
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-md border border-border">
      <table className="min-w-full text-sm">
        <thead className="bg-muted/50">
          <tr>
            {columnas.map((col) => {
              const isNumeric = NUMERIC_COLUMNS.has(col);
              return (
                <th
                  key={col}
                  className={`whitespace-nowrap px-4 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wide ${
                    isNumeric ? "text-right" : "text-left"
                  }`}
                >
                  {col}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {filas.map((fila, rowIdx) => (
            <tr
              key={rowIdx}
              className="border-t border-border odd:bg-background even:bg-muted/20 hover:bg-muted/40 transition-colors"
            >
              {columnas.map((col) => {
                const isNumeric = NUMERIC_COLUMNS.has(col);
                return (
                  <td
                    key={col}
                    className={`whitespace-nowrap px-4 py-2 text-foreground ${
                      isNumeric ? "text-right" : ""
                    }`}
                  >
                    {String(fila[col] ?? "")}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
