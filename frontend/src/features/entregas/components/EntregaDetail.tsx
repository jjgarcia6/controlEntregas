import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCurrency, formatDate } from "@/shared/utils/formatters";
import type { EntregaResponseType } from "../types/entrega.types";

interface EntregaDetailProps {
  entrega: EntregaResponseType;
  onEliminar: () => void;
  canDelete: boolean;
}

export function EntregaDetail({ entrega, onEliminar, canDelete }: EntregaDetailProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold">Entrega N° {entrega.numero}</h2>
            <Badge
              variant={entrega.estado === "activa" ? "default" : "destructive"}
              className={entrega.estado === "activa" ? "bg-green-500 dark:bg-green-600" : ""}
            >
              {entrega.estado}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">{formatDate(entrega.created_at)}</p>
        </div>

        {canDelete && entrega.estado === "activa" && (
          <Button variant="destructive" onClick={onEliminar}>
            Eliminar Entrega
          </Button>
        )}
      </div>

      <div className="grid grid-cols-2 gap-6 text-sm">
        <div className="space-y-1">
          <p className="font-medium text-muted-foreground">Destinatario</p>
          <p className="font-semibold">{entrega.snap_nombre}</p>
          <p className="font-mono text-xs">{entrega.snap_identificacion}</p>
          <p className="text-muted-foreground">{entrega.snap_direccion}</p>
          <p className="text-muted-foreground">{entrega.snap_telefono}</p>
        </div>

        <div className="space-y-1">
          <p className="font-medium text-muted-foreground">Totales</p>
          <p>
            Total:{" "}
            <span className="font-semibold">{formatCurrency(entrega.total_entrega)}</span>
          </p>
          <p>
            Saldo pendiente:{" "}
            <span className="font-semibold">{formatCurrency(entrega.saldo_pendiente)}</span>
          </p>
          {entrega.comentarios && (
            <p className="text-muted-foreground mt-2">{entrega.comentarios}</p>
          )}
        </div>
      </div>

      <div>
        <h3 className="font-medium mb-3">Ítems entregados</h3>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Producto</TableHead>
              <TableHead className="text-right">Cantidad</TableHead>
              <TableHead className="text-right">Peso Total</TableHead>
              <TableHead className="text-right">Costo Unitario</TableHead>
              <TableHead className="text-right">Costo Total</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {entrega.items.map((item) => (
              <TableRow key={item.id}>
                <TableCell>
                  <p className="font-medium text-sm">{item.descripcion}</p>
                  <p className="font-mono text-xs text-muted-foreground">{item.codigo_principal}</p>
                </TableCell>
                <TableCell className="text-right">{item.cantidad}</TableCell>
                <TableCell className="text-right">{item.peso_total} kg</TableCell>
                <TableCell className="text-right">
                  {formatCurrency(item.costo_unitario, 4)}
                </TableCell>
                <TableCell className="text-right font-medium">
                  {formatCurrency(item.costo_total)}
                </TableCell>
              </TableRow>
            ))}
            {entrega.items.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground py-6">
                  Sin ítems
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
