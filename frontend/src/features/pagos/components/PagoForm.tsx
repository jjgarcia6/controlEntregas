import {
  Control,
  FormState,
  UseFormRegister,
  UseFormSetValue,
  useWatch,
} from "react-hook-form";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useFetchBancos } from "@/features/bancos";
import type { PagoRequestType } from "../types/pago.types";

const TIPO_CUENTA_OPTIONS = [
  { value: "corriente", label: "Cuenta Corriente" },
  { value: "ahorros", label: "Cuenta de Ahorros" },
  { value: "transferencia", label: "Transferencia" },
  { value: "cheque", label: "Cheque" },
  { value: "efectivo", label: "Efectivo" },
] as const;

interface PagoFormProps {
  register: UseFormRegister<PagoRequestType>;
  control: Control<PagoRequestType>;
  setValue: UseFormSetValue<PagoRequestType>;
  formState: FormState<PagoRequestType>;
}

export function PagoForm({
  register,
  control,
  setValue,
  formState,
}: PagoFormProps) {
  const { data: bancos = [] } = useFetchBancos();

  const bancoId = useWatch({ control, name: "banco_id" });
  const tipoCuenta = useWatch({ control, name: "tipo_cuenta" });

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <div className="flex flex-col gap-1">
        <Label htmlFor="numero_comprobante">N° Comprobante</Label>
        <Input
          id="numero_comprobante"
          placeholder="Ej. 001-001-000123456"
          {...register("numero_comprobante")}
          aria-invalid={!!formState.errors.numero_comprobante}
        />
        {formState.errors.numero_comprobante && (
          <p className="text-xs text-destructive">
            {formState.errors.numero_comprobante.message}
          </p>
        )}
      </div>

      <div className="flex flex-col gap-1">
        <Label htmlFor="fecha_pago">Fecha de Pago</Label>
        <Input
          id="fecha_pago"
          type="datetime-local"
          step="1"
          {...register("fecha_pago")}
          aria-invalid={!!formState.errors.fecha_pago}
        />
        {formState.errors.fecha_pago && (
          <p className="text-xs text-destructive">
            {formState.errors.fecha_pago.message}
          </p>
        )}
      </div>

      <div className="flex flex-col gap-1">
        <Label htmlFor="banco_id">Banco</Label>
        <Select
          value={bancoId}
          onValueChange={(v) =>
            setValue("banco_id", v, { shouldValidate: true })
          }
        >
          <SelectTrigger
            id="banco_id"
            aria-invalid={!!formState.errors.banco_id}
          >
            <SelectValue placeholder="Seleccione un banco" />
          </SelectTrigger>
          <SelectContent>
            {bancos.map((b) => (
              <SelectItem key={b.id} value={b.id}>
                {b.nombre}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {formState.errors.banco_id && (
          <p className="text-xs text-destructive">
            {formState.errors.banco_id.message}
          </p>
        )}
      </div>

      <div className="flex flex-col gap-1">
        <Label htmlFor="tipo_cuenta">Tipo de Cuenta</Label>
        <Select
          value={tipoCuenta}
          onValueChange={(v) =>
            setValue("tipo_cuenta", v as PagoRequestType["tipo_cuenta"], {
              shouldValidate: true,
            })
          }
        >
          <SelectTrigger id="tipo_cuenta">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {TIPO_CUENTA_OPTIONS.map((o) => (
              <SelectItem key={o.value} value={o.value}>
                {o.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex flex-col gap-1">
        <Label htmlFor="nombre_titular">Titular</Label>
        <Input
          id="nombre_titular"
          placeholder="Nombre del titular de la cuenta"
          {...register("nombre_titular")}
          aria-invalid={!!formState.errors.nombre_titular}
        />
        {formState.errors.nombre_titular && (
          <p className="text-xs text-destructive">
            {formState.errors.nombre_titular.message}
          </p>
        )}
      </div>

      <div className="flex flex-col gap-1">
        <Label htmlFor="valor_total">Valor Total ($)</Label>
        <Input
          id="valor_total"
          type="number"
          step="0.01"
          min="0.01"
          placeholder="0.00"
          {...register("valor_total", { valueAsNumber: true })}
          aria-invalid={!!formState.errors.valor_total}
        />
        {formState.errors.valor_total && (
          <p className="text-xs text-destructive">
            {formState.errors.valor_total.message}
          </p>
        )}
      </div>
    </div>
  );
}
