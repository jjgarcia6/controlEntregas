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

import { useSearchDestinatario } from "../hooks/useSearchDestinatario";
import type { DestinatarioResponseType } from "../types/destinatario.types";

const createSchema = z.object({
  identificacion: z.string().min(10).max(13),
  nombre: z.string().min(1).max(255),
  direccion: z.string().min(1),
  telefono: z.string().min(1).max(20),
  email: z.string().email().optional().or(z.literal("")),
});

const editSchema = z.object({
  nombre: z.string().min(1).max(255).optional(),
  direccion: z.string().min(1).optional(),
  telefono: z.string().min(1).max(20).optional(),
  email: z.string().email().optional().or(z.literal("")),
});

type CreateValues = z.infer<typeof createSchema>;
type EditValues = z.infer<typeof editSchema>;

interface DestinatarioFormCreateProps {
  mode: "create";
  onSubmit: (values: CreateValues) => void;
  isPending: boolean;
}

interface DestinatarioFormEditProps {
  mode: "edit";
  defaultValues: Partial<DestinatarioResponseType>;
  onSubmit: (values: EditValues) => void;
  isPending: boolean;
}

type DestinatarioFormProps =
  | DestinatarioFormCreateProps
  | DestinatarioFormEditProps;

function CreateForm({
  onSubmit,
  isPending,
}: DestinatarioFormCreateProps) {
  const form = useForm<CreateValues>({
    resolver: zodResolver(createSchema),
    defaultValues: {
      identificacion: "",
      nombre: "",
      direccion: "",
      telefono: "",
      email: "",
    },
  });

  const identificacion = form.watch("identificacion");
  const { refetch, isFetching } = useSearchDestinatario(identificacion);

  const handleIdBlur = async () => {
    if (identificacion.length >= 10) {
      const { data } = await refetch();
      if (data) {
        form.setValue("nombre", data.nombre);
        form.setValue("direccion", data.direccion);
        form.setValue("telefono", data.telefono);
        form.setValue("email", data.email ?? "");
      }
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="identificacion"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Cédula / RUC</FormLabel>
              <FormControl>
                <Input
                  placeholder="0000000000"
                  {...field}
                  onBlur={handleIdBlur}
                />
              </FormControl>
              {isFetching && (
                <p className="text-xs text-muted-foreground">Buscando...</p>
              )}
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="nombre"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Nombre / Razón social</FormLabel>
              <FormControl>
                <Input placeholder="Nombre completo" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="direccion"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Dirección</FormLabel>
              <FormControl>
                <Input placeholder="Dirección" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="telefono"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Teléfono</FormLabel>
              <FormControl>
                <Input placeholder="09XXXXXXXX" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email (opcional)</FormLabel>
              <FormControl>
                <Input type="email" placeholder="contacto@empresa.com" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit" className="w-full" disabled={isPending}>
          {isPending ? "Guardando..." : "Crear destinatario"}
        </Button>
      </form>
    </Form>
  );
}

function EditForm({
  defaultValues,
  onSubmit,
  isPending,
}: DestinatarioFormEditProps) {
  const form = useForm<EditValues>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      nombre: defaultValues.nombre ?? "",
      direccion: defaultValues.direccion ?? "",
      telefono: defaultValues.telefono ?? "",
      email: defaultValues.email ?? "",
    },
  });

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="nombre"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Nombre / Razón social</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="direccion"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Dirección</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="telefono"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Teléfono</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email (opcional)</FormLabel>
              <FormControl>
                <Input type="email" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit" className="w-full" disabled={isPending}>
          {isPending ? "Guardando..." : "Guardar cambios"}
        </Button>
      </form>
    </Form>
  );
}

export function DestinatarioForm(props: DestinatarioFormProps) {
  if (props.mode === "create") return <CreateForm {...props} />;
  return <EditForm {...props} />;
}
