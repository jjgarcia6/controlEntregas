import { useState } from "react";

import { Button } from "@/components/ui/button";

import { useFetchXmls } from "../hooks/useFetchXmls";
import { XmlListTable } from "./XmlListTable";

const PAGE_SIZE = 20;

export function XmlListContainer() {
  const [page, setPage] = useState(1);
  const { data, isLoading, error } = useFetchXmls(page, PAGE_SIZE);

  if (isLoading) {
    return <div className="p-4 text-muted-foreground">Cargando XMLs...</div>;
  }

  if (error) {
    return (
      <div className="p-4 text-destructive">Error al cargar la lista de XMLs.</div>
    );
  }

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 1;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">XMLs ingresados</h2>
        <span className="text-sm text-muted-foreground">
          {data?.total ?? 0} registros
        </span>
      </div>

      <XmlListTable items={data?.items ?? []} />

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
          >
            Anterior
          </Button>
          <span className="text-sm text-muted-foreground">
            Página {page} de {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
          >
            Siguiente
          </Button>
        </div>
      )}
    </div>
  );
}
