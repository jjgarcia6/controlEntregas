import { useState } from "react";

import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useFetchProductos } from "@/features/kardex";
import type { EntregaItemRequestType } from "../types/entrega.types";

interface ProductoSelectorProps {
  onItemsChange: (items: EntregaItemRequestType[]) => void;
}

const SKELETON_ROWS = 5;

export function ProductoSelector({ onItemsChange }: ProductoSelectorProps) {
  const { data, isLoading } = useFetchProductos(1, 100);
  const [cantidades, setCantidades] = useState<Record<string, string>>({});
  const [errores, setErrores] = useState<Record<string, string>>({});

  const handleCantidadChange = (
    productoId: string,
    saldoDisponible: number,
    value: string,
  ) => {
    setCantidades((prev) => ({ ...prev, [productoId]: value }));

    const num = parseFloat(value);
    if (value === "" || isNaN(num)) {
      setErrores((prev) => ({ ...prev, [productoId]: "" }));
      notifyParent({ ...cantidades, [productoId]: value }, data?.items ?? []);
      return;
    }

    if (num <= 0) {
      setErrores((prev) => ({ ...prev, [productoId]: "Debe ser mayor a 0" }));
    } else if (num > saldoDisponible) {
      setErrores((prev) => ({
        ...prev,
        [productoId]: `Máximo disponible: ${saldoDisponible}`,
      }));
    } else {
      setErrores((prev) => ({ ...prev, [productoId]: "" }));
    }

    notifyParent({ ...cantidades, [productoId]: value }, data?.items ?? []);
  };

  const notifyParent = (
    cantMap: Record<string, string>,
    productos: { id: string; saldo_cantidad: number }[],
  ) => {
    const items: EntregaItemRequestType[] = [];
    for (const [id, val] of Object.entries(cantMap)) {
      const num = parseFloat(val);
      const prod = productos.find((p) => p.id === id);
      if (!isNaN(num) && num > 0 && prod && num <= prod.saldo_cantidad) {
        items.push({ producto_id: id, cantidad: num });
      }
    }
    onItemsChange(items);
  };

  const productos = (data?.items ?? []).filter((p) => p.saldo_cantidad > 0);

  return (
    <div>
      <Table role="grid" aria-label="Productos disponibles para entrega">
        <TableHeader>
          <TableRow>
            <TableHead>Código</TableHead>
            <TableHead>Descripción</TableHead>
            <TableHead className="text-right">Saldo disponible</TableHead>
            <TableHead className="w-36">Cantidad a entregar</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading
            ? Array.from({ length: SKELETON_ROWS }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 4 }).map((__, j) => (
                    <TableCell key={j}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            : productos.map((p) => (
                <TableRow key={p.id}>
                  <TableCell className="font-mono text-xs">{p.codigo_principal}</TableCell>
                  <TableCell>{p.descripcion}</TableCell>
                  <TableCell className="text-right">{p.saldo_cantidad}</TableCell>
                  <TableCell>
                    <div>
                      <Input
                        type="number"
                        aria-label={`Cantidad para ${p.descripcion}`}
                        min={0}
                        max={p.saldo_cantidad}
                        step={0.0001}
                        value={cantidades[p.id] ?? ""}
                        onChange={(e) =>
                          handleCantidadChange(p.id, p.saldo_cantidad, e.target.value)
                        }
                        className={`w-28 ${errores[p.id] ? "border-destructive" : ""}`}
                        placeholder="0"
                      />
                      {errores[p.id] && (
                        <p className="text-xs text-destructive mt-1">{errores[p.id]}</p>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
          {!isLoading && productos.length === 0 && (
            <TableRow>
              <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                Sin productos con saldo disponible
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
      <p className="text-xs text-muted-foreground mt-2">
        Ingrese la cantidad solo para los productos que desea entregar. Precio FIFO calculado
        automáticamente.
      </p>
    </div>
  );
}
