import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import apiClient from "@/api/client";
import {
  usuarioDesbloqueoSchema,
  type UsuarioDesbloqueoType,
} from "../types/usuario.types";

export function useDesbloquearUsuario() {
  const queryClient = useQueryClient();

  return useMutation<UsuarioDesbloqueoType, Error, string>({
    mutationFn: async (usuarioId: string) => {
      const { data } = await apiClient.post(
        `/usuarios/${usuarioId}/desbloquear`,
      );
      return usuarioDesbloqueoSchema.parse(data);
    },
    onSuccess: (data) => {
      toast.success(
        data.intentos_eliminados > 0
          ? `Usuario desbloqueado. ${data.intentos_eliminados} intento(s) eliminado(s).`
          : "Usuario no tenía intentos fallidos registrados.",
      );
      queryClient.invalidateQueries({ queryKey: ["usuarios"] });
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error ? error.message : "Error al desbloquear";
      toast.error(message);
    },
  });
}
