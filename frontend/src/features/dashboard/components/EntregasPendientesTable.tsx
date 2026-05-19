import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { type EntregaPendienteRow } from "../types/dashboard.types";

interface EntregasPendientesTableProps {
  filas: EntregaPendienteRow[];
}

function formatFecha(iso: string): string {
  try {
    const d = new Date(iso);
    const dd = String(d.getDate()).padStart(2, "0");
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const yyyy = d.getFullYear();
    return `${dd}-${mm}-${yyyy}`;
  } catch {
    return iso;
  }
}

export function EntregasPendientesTable({
  filas,
}: EntregasPendientesTableProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold">
          Entregas con saldo pendiente más antiguas
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/40 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground">
                <th className="px-4 py-2">#</th>
                <th className="px-4 py-2">Destinatario</th>
                <th className="px-4 py-2">Identificación</th>
                <th className="px-4 py-2">Fecha</th>
                <th className="px-4 py-2 text-right">Total</th>
                <th className="px-4 py-2 text-right">Pendiente</th>
              </tr>
            </thead>
            <tbody>
              {filas.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-6 text-center text-muted-foreground"
                  >
                    No hay entregas con saldo pendiente.
                  </td>
                </tr>
              ) : (
                filas.map((f) => (
                  <tr
                    key={f.id}
                    className="border-b border-border last:border-0 hover:bg-muted/20"
                  >
                    <td className="px-4 py-3 font-medium">{f.numero}</td>
                    <td className="px-4 py-3">{f.snap_nombre}</td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {f.snap_identificacion}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {formatFecha(f.created_at)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      ${Number(f.total_entrega).toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-right font-semibold text-destructive">
                      ${Number(f.saldo_pendiente).toFixed(2)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
