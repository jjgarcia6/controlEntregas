import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/authStore";
import { useFetchEntregas } from "../hooks/useFetchEntregas";
import { EntregaFilters } from "./EntregaFilters";
import { EntregasList } from "./EntregasList";

interface FiltrosEntrega {
  destinatario_id?: string;
  estado?: "activa" | "eliminada";
  fecha_desde?: string;
  fecha_hasta?: string;
}

export function EntregasContainer() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [filtros, setFiltros] = useState<FiltrosEntrega>({});
  const [page] = useState(1);

  const { data, isLoading } = useFetchEntregas(filtros, page);

  const canCreate = user?.rol === "admin" || user?.rol === "operador";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Entregas</h2>
        {canCreate && (
          <Button onClick={() => navigate("/entregas/nueva")}>Nueva Entrega</Button>
        )}
      </div>

      <EntregaFilters onFilter={setFiltros} />

      <EntregasList
        entregas={data?.items ?? []}
        isLoading={isLoading}
        onVerDetalle={(id) => navigate(`/entregas/${id}`)}
      />
    </div>
  );
}
