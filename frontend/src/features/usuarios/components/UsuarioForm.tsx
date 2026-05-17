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

const createSchema = z.object({
  email: z.string().email("Email inválido"),
  password: z.string().min(8, "Mínimo 8 caracteres"),
  nombre: z.string().min(1, "El nombre es requerido").max(150),
  rol: z.enum(["admin", "operador", "lectura"]),
});

const editSchema = z.object({
  email: z.string().email("Email inválido").optional(),
  nombre: z.string().min(1).max(150).optional(),
  rol: z.enum(["admin", "operador", "lectura"]).optional(),
});

type CreateValues = z.infer<typeof createSchema>;
type EditValues = z.infer<typeof editSchema>;

interface UsuarioFormCreateProps {
  mode: "create";
  onSubmit: (values: CreateValues) => void;
  isPending: boolean;
}

interface UsuarioFormEditProps {
  mode: "edit";
  defaultValues: EditValues;
  onSubmit: (values: EditValues) => void;
  isPending: boolean;
}

type UsuarioFormProps = UsuarioFormCreateProps | UsuarioFormEditProps;

export function UsuarioForm(props: UsuarioFormProps) {
  const isCreate = props.mode === "create";

  const form = useForm<CreateValues>({
    resolver: zodResolver(isCreate ? createSchema : editSchema),
    defaultValues: isCreate
      ? { email: "", password: "", nombre: "", rol: "operador" }
      : { ...(props as UsuarioFormEditProps).defaultValues, password: "" },
  });

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(props.onSubmit as (v: CreateValues) => void)}
        className="space-y-4"
      >
        <FormField
          control={form.control}
          name="nombre"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Nombre</FormLabel>
              <FormControl>
                <Input placeholder="Nombre completo" {...field} />
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
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" placeholder="usuario@empresa.com" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        {isCreate && (
          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Contraseña</FormLabel>
                <FormControl>
                  <Input type="password" placeholder="Mínimo 8 caracteres" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        )}
        <FormField
          control={form.control}
          name="rol"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Rol</FormLabel>
              <FormControl>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  {...field}
                >
                  <option value="admin">Admin</option>
                  <option value="operador">Operador</option>
                  <option value="lectura">Lectura</option>
                </select>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit" className="w-full" disabled={props.isPending}>
          {props.isPending
            ? "Guardando..."
            : isCreate
            ? "Crear usuario"
            : "Guardar cambios"}
        </Button>
      </form>
    </Form>
  );
}
