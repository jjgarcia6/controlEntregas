import { useState } from "react";
import { toast } from "sonner";

import { useFetchXmls } from "@/features/xmls";
import { useIngresarItems } from "../hooks/useIngresarItems";
import { useFetchXmlPendientes } from "../hooks/useFetchXmlPendientes";
import type { KardexIngresoItemType } from "../types/kardex.types";
import { XmlItemSelector } from "./XmlItemSelector";

export function KardexIngresoContainer() {
  const [xmlId, setXmlId] = useState<string | undefined>(undefined);

  const { data: xmlsList, isLoading: isLoadingXmls } = useFetchXmls(1, 100);
  const { data: pendientes, isLoading: isLoadingItems, error: fetchError } = useFetchXmlPendientes(xmlId);
  const ingresarMutation = useIngresarItems();

  const handleConfirm = (seleccion: KardexIngresoItemType[]) => {
    if (!xmlId) return;
    ingresarMutation.mutate(
      { xmlId, body: { items: seleccion } },
      {
        onSuccess: () => {
          toast.success("Ítems ingresados al Kardex correctamente");
          setXmlId(undefined);
        },
      }
    );
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <h2 className="text-xl font-semibold">XML Pendientes de Ingreso al Kardex</h2>

      <div className="max-w-lg">
        <label className="text-sm font-medium mb-1 block">Seleccionar XML</label>
        <select
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
          value={xmlId ?? ""}
          onChange={(e) => setXmlId(e.target.value || undefined)}
          disabled={isLoadingXmls}
        >
          <option value="">
            {isLoadingXmls ? "Cargando XMLs..." : "— Seleccione un XML —"}
          </option>
          {xmlsList?.items.map((xml) => (
            <option key={xml.id} value={xml.id}>
              {xml.numero_factura} · {xml.razon_social_emisor} · {new Date(xml.fecha_emision).toLocaleDateString("es-EC")}
            </option>
          ))}
        </select>
      </div>

      {ingresarMutation.errorMessage && (
        <p className="text-sm text-destructive">{ingresarMutation.errorMessage}</p>
      )}

      {fetchError && (
        <p className="text-sm text-destructive">Error al cargar ítems pendientes</p>
      )}

      {isLoadingItems && (
        <p className="text-sm text-muted-foreground">Cargando ítems...</p>
      )}

      {pendientes && pendientes.length === 0 && (
        <p className="text-sm text-muted-foreground">
          Ingreso completo — este XML no tiene ítems pendientes.
        </p>
      )}

      {pendientes && pendientes.length > 0 && (
        <XmlItemSelector
          items={pendientes}
          onConfirm={handleConfirm}
          isPending={ingresarMutation.isPending}
        />
      )}
    </div>
  );
}
