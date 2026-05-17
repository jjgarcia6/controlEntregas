import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { Skeleton } from "@/components/ui/skeleton";
import { useAuthStore } from "@/store/authStore";
import { useFetchEntregaDetail } from "../hooks/useFetchEntregaDetail";
import { useDeleteEntrega } from "../hooks/useDeleteEntrega";
import { EntregaDetail } from "./EntregaDetail";
import { EntregaDeleteDialog } from "./EntregaDeleteDialog";

export function EntregaDetailContainer() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data, isLoading } = useFetchEntregaDetail(id);
  const { mutate: eliminar, pagosBlockers } = useDeleteEntrega();

  const canDelete = user?.rol === "admin" || user?.rol === "operador";

  const handleEliminar = () => {
    setDialogOpen(true);
  };

  const handleConfirmEliminar = () => {
    if (!id) return;
    eliminar(id, {
      onSuccess: () => {
        setDialogOpen(false);
        navigate("/entregas");
      },
      onError: () => {
        // pagosBlockers are set by the hook; keep dialog open to show them
      },
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (!data) {
    return (
      <p className="text-muted-foreground">Entrega no encontrada.</p>
    );
  }

  return (
    <>
      <EntregaDetail
        entrega={data}
        onEliminar={handleEliminar}
        canDelete={canDelete}
      />

      <EntregaDeleteDialog
        isOpen={dialogOpen}
        onConfirm={handleConfirmEliminar}
        onCancel={() => setDialogOpen(false)}
        pagosBlockers={pagosBlockers}
      />
    </>
  );
}
