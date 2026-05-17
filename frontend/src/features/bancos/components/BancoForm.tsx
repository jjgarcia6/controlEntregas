import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";

const bancoSchema = z.object({
  nombre: z.string().min(1, "El nombre es requerido").max(150),
});

type BancoValues = z.infer<typeof bancoSchema>;

interface BancoFormProps {
  defaultValues?: BancoValues;
  onSubmit: (values: BancoValues) => void;
  isPending: boolean;
  mode: "create" | "edit";
}

export function BancoForm({
  defaultValues,
  onSubmit,
  isPending,
  mode,
}: BancoFormProps) {
  const form = useForm<BancoValues>({
    resolver: zodResolver(bancoSchema),
    defaultValues: defaultValues ?? { nombre: "" },
  });

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="nombre"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Nombre del banco</FormLabel>
              <FormControl>
                <Input placeholder="Ej. Banco Pichincha" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit" className="w-full" disabled={isPending}>
          {isPending
            ? "Guardando..."
            : mode === "create"
            ? "Crear banco"
            : "Guardar cambios"}
        </Button>
      </form>
    </Form>
  );
}
