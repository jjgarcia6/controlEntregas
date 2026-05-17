import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import type { DestinatarioResponseType } from "@/features/destinatarios";
import { useCreateEntrega } from "../hooks/useCreateEntrega";
import type { EntregaItemRequestType } from "../types/entrega.types";
import { DestinatarioSelector } from "./DestinatarioSelector";
import { ProductoSelector } from "./ProductoSelector";

export function EntregaCreateContainer() {
  const navigate = useNavigate();
  const [destinatario, setDestinatario] = useState<DestinatarioResponseType | null>(null);
  const [items, setItems] = useState<EntregaItemRequestType[]>([]);

  const { mutate, isPending, errorMessage } = useCreateEntrega();

  const handleDestinatarioSelect = useCallback(
    (d: DestinatarioResponseType | null) => {
      setDestinatario(d);
    },
    [],
  );

  const handleItemsChange = useCallback((newItems: EntregaItemRequestType[]) => {
    setItems(newItems);
  }, []);

  const canSubmit = destinatario !== null && items.length > 0;

  const handleConfirmar = () => {
    if (!destinatario) return;
    mutate(
      { destinatario_id: destinatario.id, items },
      {
        onSuccess: (data) => {
          navigate(`/entregas/${data.id}`);
        },
      },
    );
  };

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h2 className="text-xl font-semibold mb-4">Nueva Entrega</h2>

        <div className="space-y-6">
          <section className="space-y-2">
            <h3 className="font-medium text-base">Destinatario</h3>
            <DestinatarioSelector onSelect={handleDestinatarioSelect} />
          </section>

          <section className="space-y-2">
            <h3 className="font-medium text-base">Productos a entregar</h3>
            <ProductoSelector onItemsChange={handleItemsChange} />
          </section>
        </div>
      </div>

      {errorMessage && (
        <p className="text-sm text-destructive bg-destructive/10 rounded px-3 py-2">
          {errorMessage}
        </p>
      )}

      <div className="flex gap-3">
        <Button
          onClick={handleConfirmar}
          disabled={!canSubmit || isPending}
        >
          {isPending ? "Procesando..." : "Confirmar Entrega"}
        </Button>
        <Button variant="outline" onClick={() => navigate("/entregas")}>
          Cancelar
        </Button>
      </div>
    </div>
  );
}
