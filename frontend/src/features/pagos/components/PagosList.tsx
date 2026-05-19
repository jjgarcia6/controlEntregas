import { GitBranch, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import type { PagoResponseType } from "../types/pago.types";

interface PagosListProps {
  pagos: PagoResponseType[];
  isLoading: boolean;
  canDelete: boolean;
  onVerDetalle: (id: string) => void;
  onEliminar: (pago: PagoResponseType) => void;
  onVerTrazabilidad?: (id: string) => void;
}

const SKELETON_ROWS = 5;

export function PagosList({
  pagos,
  isLoading,
  canDelete,
  onVerDetalle,
  onEliminar,
  onVerTrazabilidad,
}: PagosListProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Tipo de Cuenta</TableHead>
          <TableHead>Comprobante</TableHead>
          <TableHead>Fecha</TableHead>
          <TableHead>Banco</TableHead>
          <TableHead>Titular</TableHead>
          <TableHead className="text-right">Total</TableHead>
          <TableHead className="text-right">Aplicado</TableHead>
          <TableHead>Estado</TableHead>
          {onVerTrazabilidad && <TableHead />}
          {canDelete && <TableHead />}
        </TableRow>
      </TableHeader>
      <TableBody>
        {isLoading
          ? Array.from({ length: SKELETON_ROWS }).map((_, i) => (
              <TableRow key={i}>
                {Array.from({ length: canDelete ? 9 : 8 }).map((__, j) => (
                  <TableCell key={j}>
                    <Skeleton className="h-4 w-full" />
                  </TableCell>
                ))}
              </TableRow>
            ))
          : pagos.map((p) => (
              <TableRow
                key={p.id}
                onClick={() => onVerDetalle(p.id)}
                className="cursor-pointer hover:bg-muted/50"
              >
                <TableCell className="text-sm capitalize">
                  {p.tipo_cuenta}
                </TableCell>
                <TableCell className="font-mono text-sm font-medium">
                  {p.numero_comprobante}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {formatDate(p.fecha_pago, "dd-MM-yyyy HH:mm:ss")}
                </TableCell>
                <TableCell>{p.banco_nombre}</TableCell>
                <TableCell>{p.nombre_titular}</TableCell>
                <TableCell className="text-right">
                  {formatCurrency(p.valor_total)}
                </TableCell>
                <TableCell className="text-right">
                  {formatCurrency(p.valor_aplicado)}
                </TableCell>
                <TableCell>
                  <Badge
                    variant={p.estado === "activo" ? "default" : "destructive"}
                    className={
                      p.estado === "activo"
                        ? "bg-green-700 dark:bg-green-700"
                        : ""
                    }
                  >
                    {p.estado}
                  </Badge>
                </TableCell>
                {onVerTrazabilidad && (
                  <TableCell onClick={(e) => e.stopPropagation()}>
                    <Button
                      variant="ghost"
                      size="icon"
                      aria-label="Ver trazabilidad"
                      title="Ver trazabilidad"
                      onClick={() => onVerTrazabilidad(p.id)}
                    >
                      <GitBranch className="h-4 w-4" />
                    </Button>
                  </TableCell>
                )}
                {canDelete && (
                  <TableCell onClick={(e) => e.stopPropagation()}>
                    {p.estado === "activo" && (
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label="Eliminar pago"
                        onClick={() => onEliminar(p)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    )}
                  </TableCell>
                )}
              </TableRow>
            ))}
        {!isLoading && pagos.length === 0 && (
          <TableRow>
            <TableCell
              colSpan={8 + (onVerTrazabilidad ? 1 : 0) + (canDelete ? 1 : 0)}
              className="text-center text-muted-foreground py-8"
            >
              Sin pagos registrados
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}
