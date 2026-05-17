import { Badge } from "@/components/ui/badge";
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
import type { EntregaListItemType } from "../types/entrega.types";

interface EntregasListProps {
  entregas: EntregaListItemType[];
  isLoading: boolean;
  onVerDetalle: (id: string) => void;
}

const SKELETON_ROWS = 5;

export function EntregasList({ entregas, isLoading, onVerDetalle }: EntregasListProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>N°</TableHead>
          <TableHead>Identificación</TableHead>
          <TableHead>Destinatario</TableHead>
          <TableHead>Fecha</TableHead>
          <TableHead className="text-right">Total</TableHead>
          <TableHead className="text-right">Saldo Pendiente</TableHead>
          <TableHead>Estado</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {isLoading
          ? Array.from({ length: SKELETON_ROWS }).map((_, i) => (
              <TableRow key={i}>
                {Array.from({ length: 7 }).map((__, j) => (
                  <TableCell key={j}>
                    <Skeleton className="h-4 w-full" />
                  </TableCell>
                ))}
              </TableRow>
            ))
          : entregas.map((e) => (
              <TableRow
                key={e.id}
                onClick={() => onVerDetalle(e.id)}
                className="cursor-pointer hover:bg-muted/50"
              >
                <TableCell className="font-mono text-sm font-medium">{e.numero}</TableCell>
                <TableCell className="font-mono text-xs">{e.snap_identificacion}</TableCell>
                <TableCell>{e.snap_nombre}</TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {formatDate(e.created_at)}
                </TableCell>
                <TableCell className="text-right">{formatCurrency(e.total_entrega)}</TableCell>
                <TableCell className="text-right">{formatCurrency(e.saldo_pendiente)}</TableCell>
                <TableCell>
                  <Badge
                    variant={e.estado === "activa" ? "default" : "destructive"}
                    className={
                      e.estado === "activa"
                        ? "bg-green-500 dark:bg-green-600"
                        : ""
                    }
                  >
                    {e.estado}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
        {!isLoading && entregas.length === 0 && (
          <TableRow>
            <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
              Sin entregas registradas
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}
