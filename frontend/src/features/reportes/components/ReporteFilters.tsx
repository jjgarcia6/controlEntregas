import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useFetchBancos } from "@/features/bancos/hooks/useFetchBancos";
import { useFetchProductos } from "@/features/kardex/hooks/useFetchProductos";
import { useFetchEntregas } from "@/features/entregas/hooks/useFetchEntregas";
import { type TipoReporte } from "../types/reporte.types";

interface ReporteFiltersProps {
  tipoActivo: TipoReporte;
  onSubmit: (filtros: Record<string, unknown>) => void;
}

export function ReporteFilters({ tipoActivo, onSubmit }: ReporteFiltersProps) {
  const [fechaDesde, setFechaDesde] = useState("");
  const [fechaHasta, setFechaHasta] = useState("");
  const [productoId, setProductoId] = useState("");
  const [codigoPrincipal, setCodigoPrincipal] = useState("");
  const [destinatarioId] = useState("");
  const [estado, setEstado] = useState<"" | "activa" | "eliminada">("");
  const [bancoId, setBancoId] = useState("");
  const [entregaId, setEntregaId] = useState("");

  const { data: productosData } = useFetchProductos(1, 200);
  const { data: bancos } = useFetchBancos();
  const { data: entregasData } = useFetchEntregas({}, 1, 200);

  function buildFiltros(): Record<string, unknown> {
    const base: Record<string, unknown> = {};
    if (fechaDesde) base.fecha_desde = fechaDesde;
    if (fechaHasta) base.fecha_hasta = fechaHasta;

    if (tipoActivo === "xmls") {
      if (codigoPrincipal) base.codigo_principal = codigoPrincipal;
    }
    if (tipoActivo === "kardex") {
      if (productoId) base.producto_id = productoId;
    }
    if (tipoActivo === "entregas") {
      if (destinatarioId) base.destinatario_id = destinatarioId;
      if (estado) base.estado = estado;
    }
    if (tipoActivo === "pagos") {
      if (bancoId) base.banco_id = bancoId;
      if (entregaId) base.entrega_id = entregaId;
    }
    return base;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit(buildFiltros());
  }

  const productoRequerido = tipoActivo === "kardex" && !productoId;

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-wrap items-end gap-4 rounded-lg border border-border bg-muted/20 p-4"
    >
      {/* Fecha desde/hasta — todos los tipos */}
      <div className="flex flex-col gap-1">
        <Label htmlFor="fecha_desde">Fecha desde</Label>
        <Input
          id="fecha_desde"
          type="date"
          value={fechaDesde}
          onChange={(e) => setFechaDesde(e.target.value)}
          className="w-40"
        />
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor="fecha_hasta">Fecha hasta</Label>
        <Input
          id="fecha_hasta"
          type="date"
          value={fechaHasta}
          onChange={(e) => setFechaHasta(e.target.value)}
          className="w-40"
        />
      </div>

      {/* XMLs: código principal */}
      {tipoActivo === "xmls" && (
        <div className="flex flex-col gap-1">
          <Label htmlFor="codigo_principal">Código producto</Label>
          <Input
            id="codigo_principal"
            value={codigoPrincipal}
            onChange={(e) => setCodigoPrincipal(e.target.value)}
            placeholder="Ej: PROD-001"
            className="w-40"
          />
        </div>
      )}

      {/* Kardex: producto_id (requerido) */}
      {tipoActivo === "kardex" && (
        <div className="flex flex-col gap-1">
          <Label htmlFor="producto_id">
            Producto <span className="text-destructive">*</span>
          </Label>
          <select
            id="producto_id"
            value={productoId}
            onChange={(e) => setProductoId(e.target.value)}
            required
            className="h-9 w-56 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring dark:bg-background"
          >
            <option value="">Seleccionar producto...</option>
            {productosData?.items.map((p) => (
              <option key={p.id} value={p.id}>
                {p.codigo_principal} — {p.descripcion}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Entregas: destinatario_id + estado */}
      {tipoActivo === "entregas" && (
        <>
          <div className="flex flex-col gap-1">
            <Label htmlFor="estado">Estado</Label>
            <select
              id="estado"
              value={estado}
              onChange={(e) =>
                setEstado(e.target.value as "" | "activa" | "eliminada")
              }
              className="h-9 w-36 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring dark:bg-background"
            >
              <option value="">Todos</option>
              <option value="activa">Activa</option>
              <option value="eliminada">Eliminada</option>
            </select>
          </div>
        </>
      )}

      {/* Pagos: banco_id + entrega_id */}
      {tipoActivo === "pagos" && (
        <>
          <div className="flex flex-col gap-1">
            <Label htmlFor="banco_id">Banco</Label>
            <select
              id="banco_id"
              value={bancoId}
              onChange={(e) => setBancoId(e.target.value)}
              className="h-9 w-48 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring dark:bg-background"
            >
              <option value="">Todos</option>
              {bancos?.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.nombre}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="entrega_id">Entrega</Label>
            <select
              id="entrega_id"
              value={entregaId}
              onChange={(e) => setEntregaId(e.target.value)}
              className="h-9 w-48 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring dark:bg-background"
            >
              <option value="">Todas</option>
              {entregasData?.items.map((e) => (
                <option key={e.id} value={e.id}>
                  Entrega #{e.numero}
                </option>
              ))}
            </select>
          </div>
        </>
      )}

      <Button type="submit" disabled={productoRequerido}>
        Consultar
      </Button>
    </form>
  );
}
