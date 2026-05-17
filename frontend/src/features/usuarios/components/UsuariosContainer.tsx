import { useState } from "react";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

import { useCreateUsuario } from "../hooks/useCreateUsuario";
import { useDeleteUsuario } from "../hooks/useDeleteUsuario";
import { useFetchUsuarios } from "../hooks/useFetchUsuarios";
import { useUpdatePassword } from "../hooks/useUpdatePassword";
import { useUpdateUsuario } from "../hooks/useUpdateUsuario";
import type { UsuarioResponseType } from "../types/usuario.types";
import { UsuarioForm } from "./UsuarioForm";
import { UsuariosList } from "./UsuariosList";

type DialogMode =
  | { type: "none" }
  | { type: "create" }
  | { type: "edit"; usuario: UsuarioResponseType }
  | { type: "password"; usuario: UsuarioResponseType }
  | { type: "deactivate"; usuario: UsuarioResponseType };

const passwordSchema = z.object({ nueva_password: z.string().min(8) });

export function UsuariosContainer() {
  const { data: usuarios = [], isLoading } = useFetchUsuarios();
  const createMutation = useCreateUsuario();
  const updateMutation = useUpdateUsuario();
  const passwordMutation = useUpdatePassword();
  const deleteMutation = useDeleteUsuario();

  const [dialog, setDialog] = useState<DialogMode>({ type: "none" });
  const [newPassword, setNewPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");

  const closeDialog = () => {
    setDialog({ type: "none" });
    setNewPassword("");
    setPasswordError("");
  };

  if (isLoading) {
    return <div className="p-4 text-muted-foreground">Cargando usuarios...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Usuarios</h2>
        <Button onClick={() => setDialog({ type: "create" })}>
          Nuevo usuario
        </Button>
      </div>

      <UsuariosList
        usuarios={usuarios}
        onEdit={(u) => setDialog({ type: "edit", usuario: u })}
        onChangePassword={(u) => setDialog({ type: "password", usuario: u })}
        onDeactivate={(u) => setDialog({ type: "deactivate", usuario: u })}
      />

      {/* Create dialog */}
      <Dialog
        open={dialog.type === "create"}
        onOpenChange={(open) => !open && closeDialog()}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nuevo usuario</DialogTitle>
          </DialogHeader>
          <UsuarioForm
            mode="create"
            isPending={createMutation.isPending}
            onSubmit={(values) =>
              createMutation.mutate(values, {
                onSuccess: () => {
                  toast.success("Usuario creado");
                  closeDialog();
                },
                onError: (e) =>
                  toast.error(e instanceof Error ? e.message : "Error"),
              })
            }
          />
        </DialogContent>
      </Dialog>

      {/* Edit dialog */}
      {dialog.type === "edit" && (
        <Dialog open onOpenChange={(open) => !open && closeDialog()}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Editar usuario</DialogTitle>
            </DialogHeader>
            <UsuarioForm
              mode="edit"
              isPending={updateMutation.isPending}
              defaultValues={{
                email: dialog.usuario.email,
                nombre: dialog.usuario.nombre,
                rol: dialog.usuario.rol,
              }}
              onSubmit={(values) =>
                updateMutation.mutate(
                  { id: dialog.usuario.id, ...values },
                  {
                    onSuccess: () => {
                      toast.success("Usuario actualizado");
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

      {/* Change password dialog */}
      {dialog.type === "password" && (
        <Dialog open onOpenChange={(open) => !open && closeDialog()}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Cambiar contraseña</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <Input
                type="password"
                placeholder="Nueva contraseña (mínimo 8 caracteres)"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
              {passwordError && (
                <p className="text-sm text-destructive">{passwordError}</p>
              )}
              <Button
                className="w-full"
                disabled={passwordMutation.isPending}
                onClick={() => {
                  const result = passwordSchema.safeParse({
                    nueva_password: newPassword,
                  });
                  if (!result.success) {
                    setPasswordError("Mínimo 8 caracteres");
                    return;
                  }
                  passwordMutation.mutate(
                    {
                      id: dialog.usuario.id,
                      nueva_password: newPassword,
                    },
                    {
                      onSuccess: () => {
                        toast.success("Contraseña actualizada");
                        closeDialog();
                      },
                      onError: (e) =>
                        toast.error(
                          e instanceof Error ? e.message : "Error"
                        ),
                    }
                  );
                }}
              >
                {passwordMutation.isPending ? "Guardando..." : "Cambiar contraseña"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Deactivate confirmation dialog */}
      {dialog.type === "deactivate" && (
        <Dialog open onOpenChange={(open) => !open && closeDialog()}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Desactivar usuario</DialogTitle>
            </DialogHeader>
            <p className="text-sm text-muted-foreground">
              ¿Está seguro de que desea desactivar a{" "}
              <strong>{dialog.usuario.nombre}</strong>? Esta acción puede
              revertirse desde la base de datos.
            </p>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={closeDialog}>
                Cancelar
              </Button>
              <Button
                variant="destructive"
                disabled={deleteMutation.isPending}
                onClick={() =>
                  deleteMutation.mutate(dialog.usuario.id, {
                    onSuccess: () => {
                      toast.success("Usuario desactivado");
                      closeDialog();
                    },
                    onError: (e) =>
                      toast.error(e instanceof Error ? e.message : "Error"),
                  })
                }
              >
                {deleteMutation.isPending ? "Desactivando..." : "Desactivar"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
