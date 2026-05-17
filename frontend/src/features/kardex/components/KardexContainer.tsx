import { useState } from "react";

import { useFetchKardex } from "../hooks/useFetchKardex";
import { useFetchProductos } from "../hooks/useFetchProductos";
import { KardexFilters } from "./KardexFilters";
import { KardexMovimientos } from "./KardexMovimientos";
import { KardexProductosList } from "./KardexProductosList";

export function KardexContainer() {
  const [productoSeleccionadoId, setProductoSeleccionadoId] = useState<string | undefined>(
    undefined
  );
  const [fechaDesde, setFechaDesde] = useState<string | undefined>(undefined);
  const [fechaHasta, setFechaHasta] = useState<string | undefined>(undefined);
  const [page] = useState(1);

  const { data: productosData, isLoading: loadingProductos } = useFetchProductos();
  const { data: historialData, isLoading: loadingHistorial } = useFetchKardex(
    productoSeleccionadoId,
    page,
    20,
    fechaDesde,
    fechaHasta
  );

  const handleFilter = (desde?: string, hasta?: string) => {
    setFechaDesde(desde);
    setFechaHasta(hasta);
  };

  return (
    <div className="flex gap-6 h-[calc(100vh-8rem)] min-h-0">
      {/* Panel izquierdo — lista de productos */}
      <div className="w-72 shrink-0 flex flex-col min-h-0">
        <div className="mb-3">
          <h2 className="text-base font-semibold">Productos con Saldo</h2>
          <p className="text-xs text-muted-foreground mt-0.5">Selecciona un producto</p>
        </div>
        <div className="overflow-y-auto flex-1 rounded-md border">
          <KardexProductosList
            productos={productosData?.items ?? []}
            isLoading={loadingProductos}
            selectedId={productoSeleccionadoId}
            onSelectProducto={setProductoSeleccionadoId}
          />
        </div>
      </div>

      {/* Panel derecho — historial */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="mb-3">
          <h2 className="text-base font-semibold">Historial de movimientos</h2>
        </div>
        {productoSeleccionadoId ? (
          <div className="flex flex-col min-h-0 gap-3 flex-1">
            <KardexFilters onFilter={handleFilter} />
            <div className="overflow-y-auto flex-1 rounded-md border">
              <KardexMovimientos
                movimientos={historialData?.items ?? []}
                isLoading={loadingHistorial}
              />
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center rounded-md border border-dashed text-sm text-muted-foreground">
            Selecciona un producto para ver su historial
          </div>
        )}
      </div>
    </div>
  );
}
