import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { XmlItemPendienteType } from "../hooks/useFetchXmlPendientes";
import type { KardexIngresoItemType } from "../types/kardex.types";

interface XmlItemSelectorProps {
  items: XmlItemPendienteType[];
  onConfirm: (seleccion: KardexIngresoItemType[]) => void;
  isPending?: boolean;
}

interface RowState {
  checked: boolean;
  cantidad: number;
  error: string | null;
}

export function XmlItemSelector({ items, onConfirm, isPending = false }: XmlItemSelectorProps) {
  const [rows, setRows] = useState<Record<string, RowState>>(() =>
    Object.fromEntries(
      items.map((item) => [
        item.id,
        { checked: false, cantidad: item.cantidad_pendiente, error: null },
      ])
    )
  );

  const handleCheck = (id: string, checked: boolean) => {
    setRows((prev) => ({ ...prev, [id]: { ...prev[id], checked } }));
  };

  const handleCantidad = (id: string, value: string, max: number) => {
    const num = Number(value);
    let error: string | null = null;
    if (!Number.isFinite(num) || num < 1) {
      error = "Mín. 1";
    } else if (num > max) {
      error = `Máx. ${max}`;
    }
    setRows((prev) => ({ ...prev, [id]: { ...prev[id], cantidad: num, error } }));
  };

  const handleConfirm = () => {
    const seleccion: KardexIngresoItemType[] = Object.entries(rows)
      .filter(([, row]) => row.checked && row.error === null)
      .map(([id, row]) => ({ xml_item_id: id, cantidad: row.cantidad }));
    if (seleccion.length > 0) {
      onConfirm(seleccion);
    }
  };

  const hasValidSelection = Object.entries(rows).some(
    ([, row]) => row.checked && row.error === null
  );

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-10">
              <span className="sr-only">Seleccionar</span>
            </TableHead>
            <TableHead>Código</TableHead>
            <TableHead>Descripción</TableHead>
            <TableHead className="text-right">Doc.</TableHead>
            <TableHead className="text-right">Ingresado</TableHead>
            <TableHead className="text-right">Pendiente</TableHead>
            <TableHead className="w-32">Cantidad a ingresar</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((item) => {
            const row = rows[item.id];
            return (
              <TableRow key={item.id} className={row?.checked ? "bg-muted/40" : ""}>
                <TableCell>
                  <input
                    type="checkbox"
                    aria-label={`Seleccionar ${item.descripcion}`}
                    checked={row?.checked ?? false}
                    onChange={(e) => handleCheck(item.id, e.target.checked)}
                    className="h-4 w-4 rounded border-input accent-primary"
                  />
                </TableCell>
                <TableCell className="font-mono text-xs">{item.codigo_principal}</TableCell>
                <TableCell>{item.descripcion}</TableCell>
                <TableCell className="text-right">{item.cantidad_documento}</TableCell>
                <TableCell className="text-right">{item.cantidad_ingresada}</TableCell>
                <TableCell className="text-right font-medium">{item.cantidad_pendiente}</TableCell>
                <TableCell>
                  <div className="space-y-1">
                    <Input
                      type="number"
                      min={1}
                      max={item.cantidad_pendiente}
                      step="any"
                      value={row?.cantidad ?? item.cantidad_pendiente}
                      disabled={!row?.checked}
                      aria-describedby={row?.error ? `error-${item.id}` : undefined}
                      onChange={(e) =>
                        handleCantidad(item.id, e.target.value, item.cantidad_pendiente)
                      }
                      className="h-8 text-sm"
                    />
                    {row?.error && (
                      <p id={`error-${item.id}`} className="text-xs text-destructive">
                        {row.error}
                      </p>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
      <Button onClick={handleConfirm} disabled={!hasValidSelection || isPending}>
        {isPending ? "Ingresando..." : "Confirmar ingreso"}
      </Button>
    </div>
  );
}
