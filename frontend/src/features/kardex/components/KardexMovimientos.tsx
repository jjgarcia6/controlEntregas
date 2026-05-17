import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCurrency, formatDate } from "@/shared/utils/formatters";
import type { KardexMovimientoType } from "../types/kardex.types";

interface KardexMovimientosProps {
  movimientos: KardexMovimientoType[];
  isLoading: boolean;
}

const SKELETON_ROWS = 5;

export function KardexMovimientos({ movimientos, isLoading }: KardexMovimientosProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Fecha</TableHead>
          <TableHead>Tipo</TableHead>
          <TableHead>Documento Origen</TableHead>
          <TableHead className="text-right">Cantidad</TableHead>
          <TableHead className="text-right">Peso Total</TableHead>
          <TableHead className="text-right">Costo Unit.</TableHead>
          <TableHead className="text-right">Costo Total</TableHead>
          <TableHead className="text-right">Saldo Cant.</TableHead>
          <TableHead className="text-right">Saldo Valor</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {isLoading
          ? Array.from({ length: SKELETON_ROWS }).map((_, i) => (
              <TableRow key={i}>
                {Array.from({ length: 9 }).map((__, j) => (
                  <TableCell key={j}>
                    <Skeleton className="h-4 w-full" />
                  </TableCell>
                ))}
              </TableRow>
            ))
          : movimientos.map((mov) => (
              <TableRow key={mov.id}>
                <TableCell className="text-xs whitespace-nowrap">
                  {formatDate(mov.fecha_movimiento, "dd/MM/yyyy HH:mm")}
                </TableCell>
                <TableCell>
                  <span
                    className={
                      mov.tipo === "ingreso"
                        ? "text-green-600 dark:text-green-400 font-medium"
                        : "text-red-600 dark:text-red-400 font-medium"
                    }
                  >
                    {mov.tipo}
                  </span>
                </TableCell>
                <TableCell
                  className={`text-xs font-medium ${
                    mov.origen === "reversa_entrega"
                      ? "text-amber-500 dark:text-amber-400"
                      : ""
                  }`}
                >
                  {mov.documento_origen_ref}
                </TableCell>
                <TableCell className="text-right">{mov.cantidad}</TableCell>
                <TableCell className="text-right">{mov.peso_total}</TableCell>
                <TableCell className="text-right">{formatCurrency(mov.costo_unitario, 4)}</TableCell>
                <TableCell className="text-right">{formatCurrency(mov.costo_total)}</TableCell>
                <TableCell className="text-right font-medium">{mov.saldo_cantidad}</TableCell>
                <TableCell className="text-right font-medium">
                  {formatCurrency(mov.saldo_valor)}
                </TableCell>
              </TableRow>
            ))}
        {!isLoading && movimientos.length === 0 && (
          <TableRow>
            <TableCell colSpan={9} className="text-center text-muted-foreground py-8">
              Sin movimientos registrados
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}
