import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { UsuarioResponseType } from "../types/usuario.types";

interface UsuariosListProps {
  usuarios: UsuarioResponseType[];
  onEdit: (usuario: UsuarioResponseType) => void;
  onChangePassword: (usuario: UsuarioResponseType) => void;
  onDeactivate: (usuario: UsuarioResponseType) => void;
}

const rolLabels: Record<string, string> = {
  admin: "Admin",
  operador: "Operador",
  lectura: "Lectura",
};

export function UsuariosList({
  usuarios,
  onEdit,
  onChangePassword,
  onDeactivate,
}: UsuariosListProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Nombre</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>Rol</TableHead>
          <TableHead>Estado</TableHead>
          <TableHead className="text-right">Acciones</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {usuarios.map((u) => (
          <TableRow key={u.id}>
            <TableCell className="font-medium">{u.nombre}</TableCell>
            <TableCell>{u.email}</TableCell>
            <TableCell>
              <Badge variant="outline">{rolLabels[u.rol] ?? u.rol}</Badge>
            </TableCell>
            <TableCell>
              <Badge variant={u.is_active ? "default" : "secondary"}>
                {u.is_active ? "Activo" : "Inactivo"}
              </Badge>
            </TableCell>
            <TableCell className="text-right space-x-1">
              <Button size="sm" variant="ghost" onClick={() => onEdit(u)}>
                Editar
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => onChangePassword(u)}
              >
                Contraseña
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="text-destructive hover:text-destructive"
                onClick={() => onDeactivate(u)}
              >
                Desactivar
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
