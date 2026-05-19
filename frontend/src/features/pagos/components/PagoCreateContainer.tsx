import { useCallback, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { useCreatePago } from "../hooks/useCreatePago";
import {
  pagoRequestSchema,
  type PagoItemRequestType,
  type PagoRequestType,
} from "../types/pago.types";
import { EntregaDistribucion } from "./EntregaDistribucion";
import { PagoForm } from "./PagoForm";

export function PagoCreateContainer() {
  const navigate = useNavigate();
  const { mutate, isPending, errorMessage } = useCreatePago();

  const [distribuciones, setDistribuciones] = useState<PagoItemRequestType[]>(
    [],
  );
  const now = new Date();
  const defaultFechaPago = new Date(
    now.getTime() - now.getTimezoneOffset() * 60000,
  )
    .toISOString()
    .slice(0, 16);

  const form = useForm<PagoRequestType>({
    resolver: zodResolver(pagoRequestSchema),
    defaultValues: {
      numero_comprobante: "",
      fecha_pago: defaultFechaPago,
      banco_id: "",
      tipo_cuenta: "transferencia",
      nombre_titular: "",
      valor_total: 0,
      distribuciones: [],
    },
  });

  const valorTotal = useWatch({ control: form.control, name: "valor_total" });

  const sumaAplicada = distribuciones.reduce(
    (acc, d) => acc + (d.monto_aplicado || 0),
    0,
  );
  const valorTotalNum = Number(valorTotal) || 0;
  const diferencia = Math.round((valorTotalNum - sumaAplicada) * 100) / 100;
  const cuadra =
    diferencia === 0 && distribuciones.length > 0 && valorTotalNum > 0;

  const handleDistribucionChange = useCallback(
    (items: PagoItemRequestType[]) => {
      setDistribuciones(items);
      form.setValue("distribuciones", items, { shouldValidate: true });
    },
    [form],
  );

  function handleSubmit() {
    form.handleSubmit((formData) => {
      mutate(formData, {
        onSuccess: (data) => {
          navigate(`/pagos/${data.id}`);
        },
      });
    })();
  }

  return (
    <div className="space-y-8 max-w-3xl">
      <h2 className="text-xl font-semibold">Nuevo Pago</h2>

      <section className="space-y-4">
        <h3 className="font-medium text-base border-b pb-1">
          Datos del comprobante
        </h3>
        <PagoForm
          register={form.register}
          control={form.control}
          setValue={form.setValue}
          formState={form.formState}
        />
      </section>

      <section className="space-y-4">
        <h3 className="font-medium text-base border-b pb-1">
          Distribución entre entregas
        </h3>
        <EntregaDistribucion
          distribuciones={distribuciones}
          valorTotal={valorTotalNum}
          onChange={handleDistribucionChange}
        />
      </section>

      {errorMessage && (
        <p className="text-sm text-destructive bg-destructive/10 rounded px-3 py-2">
          {errorMessage}
        </p>
      )}

      <div className="flex gap-3">
        <Button onClick={handleSubmit} disabled={!cuadra || isPending}>
          {isPending ? "Procesando..." : "Confirmar Pago"}
        </Button>
        <Button variant="outline" onClick={() => navigate("/pagos")}>
          Cancelar
        </Button>
      </div>
    </div>
  );
}
