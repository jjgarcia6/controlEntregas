import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface KardexFiltersProps {
  onFilter: (fechaDesde?: string, fechaHasta?: string) => void;
}

export function KardexFilters({ onFilter }: KardexFiltersProps) {
  const [fechaDesde, setFechaDesde] = useState("");
  const [fechaHasta, setFechaHasta] = useState("");

  const handleFilter = () => {
    onFilter(fechaDesde || undefined, fechaHasta || undefined);
  };

  const handleClear = () => {
    setFechaDesde("");
    setFechaHasta("");
    onFilter(undefined, undefined);
  };

  return (
    <div className="flex flex-wrap items-end gap-4">
      <div className="space-y-1">
        <Label htmlFor="fecha-desde">Desde</Label>
        <Input
          id="fecha-desde"
          type="date"
          value={fechaDesde}
          onChange={(e) => setFechaDesde(e.target.value)}
          className="w-40"
        />
      </div>
      <div className="space-y-1">
        <Label htmlFor="fecha-hasta">Hasta</Label>
        <Input
          id="fecha-hasta"
          type="date"
          value={fechaHasta}
          onChange={(e) => setFechaHasta(e.target.value)}
          className="w-40"
        />
      </div>
      <Button onClick={handleFilter} variant="secondary">
        Filtrar
      </Button>
      {(fechaDesde || fechaHasta) && (
        <Button onClick={handleClear} variant="ghost" size="sm">
          Limpiar
        </Button>
      )}
    </div>
  );
}
