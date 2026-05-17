import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface XmlConfirmDialogProps {
  open: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  isPending: boolean;
}

export function XmlConfirmDialog({
  open,
  onConfirm,
  onCancel,
  isPending,
}: XmlConfirmDialogProps) {
  return (
    <Dialog open={open} onOpenChange={(o) => !o && onCancel()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Confirmar ingreso de XML</DialogTitle>
          <DialogDescription>
            ¿Confirmas el ingreso de esta factura al sistema? Se creará el registro
            y se actualizarán los productos correspondientes.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onCancel} disabled={isPending}>
            Cancelar
          </Button>
          <Button onClick={onConfirm} disabled={isPending}>
            {isPending ? "Procesando..." : "Confirmar ingreso"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
