import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  useSearchDestinatario,
  useCreateDestinatario,
  DestinatarioForm,
} from "@/features/destinatarios";
import type { DestinatarioResponseType } from "@/features/destinatarios";

interface DestinatarioSelectorProps {
  onSelect: (destinatario: DestinatarioResponseType | null) => void;
}

export function DestinatarioSelector({ onSelect }: DestinatarioSelectorProps) {
  const [identificacion, setIdentificacion] = useState("");
  const [debouncedId, setDebouncedId] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);

  const { data, isFetching, error, refetch } = useSearchDestinatario(debouncedId);
  const createMutation = useCreateDestinatario();

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedId(identificacion.trim());
    }, 400);
    return () => clearTimeout(timer);
  }, [identificacion]);

  useEffect(() => {
    if (debouncedId.length >= 10) {
      void refetch();
      setShowCreateForm(false);
    } else {
      onSelect(null);
      setShowCreateForm(false);
    }
  }, [debouncedId, refetch, onSelect]);

  useEffect(() => {
    if (data) {
      onSelect(data);
      setShowCreateForm(false);
    } else if (error) {
      onSelect(null);
    }
  }, [data, error, onSelect]);

  const handleChange = (value: string) => {
    setIdentificacion(value);
    if (!value.trim()) {
      onSelect(null);
      setShowCreateForm(false);
    }
  };

  const handleCreate = (values: {
    identificacion: string;
    nombre: string;
    direccion: string;
    telefono: string;
    email?: string;
  }) => {
    createMutation.mutate(values, {
      onSuccess: (nuevo) => {
        toast.success("Destinatario creado correctamente");
        onSelect(nuevo);
        setShowCreateForm(false);
      },
    });
  };

  const notFound = !isFetching && !!error && debouncedId.length >= 10;

  return (
    <div className="space-y-3">
      <div className="space-y-1">
        <Label htmlFor="destinatario-id">Cédula / RUC del destinatario</Label>
        <Input
          id="destinatario-id"
          aria-label="Cédula o RUC del destinatario"
          value={identificacion}
          onChange={(e) => handleChange(e.target.value)}
          placeholder="0912345678001"
          className="w-64"
        />
      </div>

      {isFetching && (
        <p className="text-sm text-muted-foreground">Buscando destinatario...</p>
      )}

      {data && !showCreateForm && (
        <div className="rounded-md border border-border p-3 bg-muted/30 text-sm space-y-1">
          <p className="font-medium">{data.nombre}</p>
          <p className="text-muted-foreground">{data.direccion}</p>
          <p className="text-muted-foreground">{data.telefono}</p>
        </div>
      )}

      {notFound && !showCreateForm && (
        <div className="flex items-center gap-3">
          <p className="text-sm text-destructive">Destinatario no encontrado</p>
          <button
            type="button"
            className="text-sm text-primary underline underline-offset-2 hover:opacity-80"
            onClick={() => setShowCreateForm(true)}
          >
            Crear destinatario
          </button>
        </div>
      )}

      {showCreateForm && (
        <div className="space-y-3 max-w-md">
          <Separator />
          <p className="text-sm font-medium">Nuevo destinatario</p>
          <DestinatarioForm
            mode="create"
            onSubmit={handleCreate}
            isPending={createMutation.isPending}
          />
          {createMutation.isError && (
            <p className="text-sm text-destructive">
              {createMutation.error?.message ?? "Error al crear destinatario"}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
