import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCurrency, formatDate } from "@/shared/utils/formatters";
import type { PagoDetailResponseType } from "../types/pago.types";

const TIPO_CUENTA_LABEL: Record<string, string> = {
  corriente: "Cuenta Corriente",
  ahorros: "Cuenta de Ahorros",
  transferencia: "Transferencia",
  cheque: "Cheque",
  efectivo: "Efectivo",
};

interface PagoDetailProps {
  pago: PagoDetailResponseType;
}

export function PagoDetail({ pago }: PagoDetailProps) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
        <div>
          <p className="text-muted-foreground text-xs uppercase tracking-wide">
            Comprobante
          </p>
          <p className="font-mono font-medium">{pago.numero_comprobante}</p>
        </div>
        <div>
          <p className="text-muted-foreground text-xs uppercase tracking-wide">
            Fecha
          </p>
          <p>{formatDate(pago.fecha_pago, "dd-MM-yyyy HH:mm:ss")}</p>
        </div>
        <div>
          <p className="text-muted-foreground text-xs uppercase tracking-wide">
            Estado
          </p>
          <p
            className={
              pago.estado === "activo"
                ? "text-green-700 dark:text-green-400"
                : "text-destructive"
            }
          >
            {pago.estado}
          </p>
        </div>
        <div>
          <p className="text-muted-foreground text-xs uppercase tracking-wide">
            Banco
          </p>
          <p>{pago.banco_nombre}</p>
        </div>
        <div>
          <p className="text-muted-foreground text-xs uppercase tracking-wide">
            Tipo
          </p>
          <p>{TIPO_CUENTA_LABEL[pago.tipo_cuenta] ?? pago.tipo_cuenta}</p>
        </div>
        <div>
          <p className="text-muted-foreground text-xs uppercase tracking-wide">
            Titular
          </p>
          <p>{pago.nombre_titular}</p>
        </div>
        <div>
          <p className="text-muted-foreground text-xs uppercase tracking-wide">
            Valor Total
          </p>
          <p className="font-semibold">{formatCurrency(pago.valor_total)}</p>
        </div>
        <div>
          <p className="text-muted-foreground text-xs uppercase tracking-wide">
            Valor Aplicado
          </p>
          <p>{formatCurrency(pago.valor_aplicado)}</p>
        </div>
      </div>

      <div>
        <h3 className="font-medium text-base mb-2">Distribución</h3>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>N° Entrega</TableHead>
              <TableHead className="text-right">Monto Aplicado</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {pago.distribuciones.map((d) => (
              <TableRow key={d.id}>
                <TableCell className="font-mono">#{d.entrega_numero}</TableCell>
                <TableCell className="text-right">
                  {formatCurrency(d.monto_aplicado)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
