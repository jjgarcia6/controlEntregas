import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

import { useDesbloquearUsuario } from "../hooks/useDesbloquearUsuario";

interface DesbloquearButtonProps {
  usuarioId: string;
  nombre: string;
}

export function DesbloquearButton({
  usuarioId,
  nombre,
}: DesbloquearButtonProps) {
  const { mutate, isPending } = useDesbloquearUsuario();

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <button
          className="text-sm hover:underline disabled:opacity-50"
          disabled={isPending}
          aria-label={`Desbloquear ${nombre}`}
        >
          Desbloquear
        </button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>¿Desbloquear a {nombre}?</AlertDialogTitle>
          <AlertDialogDescription>
            Esto eliminará los intentos de login fallidos registrados para este
            usuario en los últimos 15 minutos.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <AlertDialogAction onClick={() => mutate(usuarioId)}>
            Desbloquear
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
