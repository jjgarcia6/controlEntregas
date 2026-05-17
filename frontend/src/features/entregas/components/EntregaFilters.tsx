import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface FiltrosEntrega {
  destinatario_id?: string;
  estado?: "activa" | "eliminada" | undefined;
  fecha_desde?: string;
  fecha_hasta?: string;
}

interface EntregaFiltersProps {
  onFilter: (filtros: FiltrosEntrega) => void;
}

export function EntregaFilters({ onFilter }: EntregaFiltersProps) {
  const [identificacion, setIdentificacion] = useState("");
  const [estado, setEstado] = useState<"activa" | "eliminada" | "">("");
  const [fechaDesde, setFechaDesde] = useState("");
  const [fechaHasta, setFechaHasta] = useState("");

  const handleFiltrar = () => {
    onFilter({
      destinatario_id: identificacion || undefined,
      estado: (estado as "activa" | "eliminada") || undefined,
      fecha_desde: fechaDesde || undefined,
      fecha_hasta: fechaHasta || undefined,
    });
  };

  const handleLimpiar = () => {
    setIdentificacion("");
    setEstado("");
    setFechaDesde("");
    setFechaHasta("");
    onFilter({});
  };

  return (
    <div className="flex flex-wrap gap-4 items-end">
      <div className="space-y-1">
        <Label htmlFor="filtro-identificacion">Cédula / RUC</Label>
        <Input
          id="filtro-identificacion"
          aria-label="Filtrar por cédula o RUC del destinatario"
          value={identificacion}
          onChange={(e) => setIdentificacion(e.target.value)}
          placeholder="0912345678001"
          className="w-44"
        />
      </div>

      <div className="space-y-1">
        <Label htmlFor="filtro-estado">Estado</Label>
        <select
          id="filtro-estado"
          aria-label="Filtrar por estado"
          value={estado}
          onChange={(e) => setEstado(e.target.value as "activa" | "eliminada" | "")}
          className="flex h-9 w-36 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring dark:bg-background"
        >
          <option value="">Todos</option>
          <option value="activa">Activa</option>
          <option value="eliminada">Eliminada</option>
        </select>
      </div>

      <div className="space-y-1">
        <Label htmlFor="filtro-fecha-desde">Fecha desde</Label>
        <Input
          id="filtro-fecha-desde"
          aria-label="Filtrar desde fecha"
          type="date"
          value={fechaDesde}
          onChange={(e) => setFechaDesde(e.target.value)}
          className="w-40"
        />
      </div>

      <div className="space-y-1">
        <Label htmlFor="filtro-fecha-hasta">Fecha hasta</Label>
        <Input
          id="filtro-fecha-hasta"
          aria-label="Filtrar hasta fecha"
          type="date"
          value={fechaHasta}
          onChange={(e) => setFechaHasta(e.target.value)}
          className="w-40"
        />
      </div>

      <Button onClick={handleFiltrar}>Filtrar</Button>
      <Button variant="outline" onClick={handleLimpiar}>
        Limpiar filtros
      </Button>
    </div>
  );
}
