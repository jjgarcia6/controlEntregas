import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useAuthStore } from "@/store/authStore";

import { useCreateDestinatario } from "../hooks/useCreateDestinatario";
import { useFetchDestinatarios } from "../hooks/useFetchDestinatarios";
import { useUpdateDestinatario } from "../hooks/useUpdateDestinatario";
import type { DestinatarioResponseType } from "../types/destinatario.types";
import { DestinatarioForm } from "./DestinatarioForm";
import { DestinatariosList } from "./DestinatariosList";

type DialogMode =
  | { type: "none" }
  | { type: "create" }
  | { type: "edit"; destinatario: DestinatarioResponseType };

export function DestinatariosContainer() {
  const { data: destinatarios = [], isLoading } = useFetchDestinatarios();
  const createMutation = useCreateDestinatario();
  const updateMutation = useUpdateDestinatario();
  const [dialog, setDialog] = useState<DialogMode>({ type: "none" });

  const user = useAuthStore((s) => s.user);
  const canEdit = user?.rol === "admin" || user?.rol === "operador";

  const closeDialog = () => setDialog({ type: "none" });

  if (isLoading) {
    return (
      <div className="p-4 text-muted-foreground">
        Cargando destinatarios...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Destinatarios</h2>
        {canEdit && (
          <Button onClick={() => setDialog({ type: "create" })}>
            Nuevo destinatario
          </Button>
        )}
      </div>

      <DestinatariosList
        destinatarios={destinatarios}
        onEdit={(d) => setDialog({ type: "edit", destinatario: d })}
        canEdit={canEdit}
      />

      <Dialog
        open={dialog.type === "create"}
        onOpenChange={(open) => !open && closeDialog()}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nuevo destinatario</DialogTitle>
          </DialogHeader>
          <DestinatarioForm
            mode="create"
            isPending={createMutation.isPending}
            onSubmit={(values) =>
              createMutation.mutate(
                {
                  ...values,
                  email: values.email || null,
                },
                {
                  onSuccess: () => {
                    toast.success("Destinatario creado");
                    closeDialog();
                  },
                  onError: (e) =>
                    toast.error(e instanceof Error ? e.message : "Error"),
                }
              )
            }
          />
        </DialogContent>
      </Dialog>

      {dialog.type === "edit" && (
        <Dialog open onOpenChange={(open) => !open && closeDialog()}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Editar destinatario</DialogTitle>
            </DialogHeader>
            <DestinatarioForm
              mode="edit"
              defaultValues={dialog.destinatario}
              isPending={updateMutation.isPending}
              onSubmit={(values) =>
                updateMutation.mutate(
                  {
                    id: dialog.destinatario.id,
                    ...values,
                    email: values.email || null,
                  },
                  {
                    onSuccess: () => {
                      toast.success("Destinatario actualizado");
                      closeDialog();
                    },
                    onError: (e) =>
                      toast.error(e instanceof Error ? e.message : "Error"),
                  }
                )
              }
            />
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
