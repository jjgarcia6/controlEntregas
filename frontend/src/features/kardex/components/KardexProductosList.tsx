import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { ProductoConSaldoType } from "../types/kardex.types";

interface KardexProductosListProps {
  productos: ProductoConSaldoType[];
  isLoading: boolean;
  selectedId?: string;
  onSelectProducto: (id: string) => void;
}

const SKELETON_ROWS = 6;

export function KardexProductosList({
  productos,
  isLoading,
  selectedId,
  onSelectProducto,
}: KardexProductosListProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Código</TableHead>
          <TableHead>Descripción</TableHead>
          <TableHead className="text-right">Saldo</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {isLoading
          ? Array.from({ length: SKELETON_ROWS }).map((_, i) => (
              <TableRow key={i}>
                {Array.from({ length: 3 }).map((__, j) => (
                  <TableCell key={j}>
                    <Skeleton className="h-4 w-full" />
                  </TableCell>
                ))}
              </TableRow>
            ))
          : productos.map((p) => (
              <TableRow
                key={p.id}
                onClick={() => onSelectProducto(p.id)}
                className={`cursor-pointer hover:bg-muted/50 ${
                  p.id === selectedId ? "bg-muted" : ""
                }`}
              >
                <TableCell className="font-mono text-xs">{p.codigo_principal}</TableCell>
                <TableCell className="text-xs leading-tight">{p.descripcion}</TableCell>
                <TableCell className="text-right font-medium text-sm">
                  {p.saldo_cantidad}
                </TableCell>
              </TableRow>
            ))}
        {!isLoading && productos.length === 0 && (
          <TableRow>
            <TableCell colSpan={3} className="text-center text-muted-foreground py-8">
              Sin productos registrados
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}
