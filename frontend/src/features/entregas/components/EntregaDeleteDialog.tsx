import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface EntregaDeleteDialogProps {
  isOpen: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  pagosBlockers?: string[];
}

export function EntregaDeleteDialog({
  isOpen,
  onConfirm,
  onCancel,
  pagosBlockers = [],
}: EntregaDeleteDialogProps) {
  const isBlocked = pagosBlockers.length > 0;

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onCancel()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Eliminar entrega</DialogTitle>
          <DialogDescription>
            {isBlocked
              ? "No se puede eliminar esta entrega porque tiene pagos activos asociados."
              : "¿Está seguro que desea eliminar esta entrega? Esta acción revertirá el stock en el Kardex."}
          </DialogDescription>
        </DialogHeader>

        {isBlocked && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Pagos bloqueantes:</p>
            <ul className="text-sm text-destructive list-disc list-inside space-y-1">
              {pagosBlockers.map((comprobante, i) => (
                <li key={i}>{comprobante}</li>
              ))}
            </ul>
            <p className="text-sm text-muted-foreground">
              Elimine los pagos indicados antes de eliminar la entrega.
            </p>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>
            {isBlocked ? "Cerrar" : "Cancelar"}
          </Button>
          {!isBlocked && (
            <Button variant="destructive" onClick={onConfirm}>
              Confirmar eliminación
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
