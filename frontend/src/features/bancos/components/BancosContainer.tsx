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

import { useCreateBanco } from "../hooks/useCreateBanco";
import { useFetchBancos } from "../hooks/useFetchBancos";
import { useUpdateBanco } from "../hooks/useUpdateBanco";
import type { BancoResponseType } from "../types/banco.types";
import { BancoForm } from "./BancoForm";
import { BancosList } from "./BancosList";

type DialogMode =
  | { type: "none" }
  | { type: "create" }
  | { type: "edit"; banco: BancoResponseType };

export function BancosContainer() {
  const { data: bancos = [], isLoading } = useFetchBancos();
  const createMutation = useCreateBanco();
  const updateMutation = useUpdateBanco();
  const [dialog, setDialog] = useState<DialogMode>({ type: "none" });

  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.rol === "admin";
  const canCreate = user?.rol === "admin" || user?.rol === "operador";

  const closeDialog = () => setDialog({ type: "none" });

  if (isLoading) {
    return <div className="p-4 text-muted-foreground">Cargando bancos...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Bancos</h2>
        {canCreate && (
          <Button onClick={() => setDialog({ type: "create" })}>
            Nuevo banco
          </Button>
        )}
      </div>

      <BancosList
        bancos={bancos}
        onEdit={(b) => setDialog({ type: "edit", banco: b })}
        canEdit={isAdmin}
      />

      <Dialog
        open={dialog.type === "create"}
        onOpenChange={(open) => !open && closeDialog()}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nuevo banco</DialogTitle>
          </DialogHeader>
          <BancoForm
            mode="create"
            isPending={createMutation.isPending}
            onSubmit={(values) =>
              createMutation.mutate(values, {
                onSuccess: () => {
                  toast.success("Banco creado");
                  closeDialog();
                },
                onError: (e) =>
                  toast.error(e instanceof Error ? e.message : "Error"),
              })
            }
          />
        </DialogContent>
      </Dialog>

      {dialog.type === "edit" && (
        <Dialog open onOpenChange={(open) => !open && closeDialog()}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Editar banco</DialogTitle>
            </DialogHeader>
            <BancoForm
              mode="edit"
              defaultValues={{ nombre: dialog.banco.nombre }}
              isPending={updateMutation.isPending}
              onSubmit={(values) =>
                updateMutation.mutate(
                  { id: dialog.banco.id, ...values },
                  {
                    onSuccess: () => {
                      toast.success("Banco actualizado");
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
