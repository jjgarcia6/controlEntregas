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
import type { DestinatarioResponseType } from "../types/destinatario.types";

interface DestinatariosListProps {
  destinatarios: DestinatarioResponseType[];
  onEdit: (destinatario: DestinatarioResponseType) => void;
  canEdit: boolean;
}

export function DestinatariosList({
  destinatarios,
  onEdit,
  canEdit,
}: DestinatariosListProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Tipo</TableHead>
          <TableHead>Identificación</TableHead>
          <TableHead>Nombre</TableHead>
          <TableHead>Teléfono</TableHead>
          {canEdit && <TableHead className="text-right">Acciones</TableHead>}
        </TableRow>
      </TableHeader>
      <TableBody>
        {destinatarios.map((d) => (
          <TableRow key={d.id}>
            <TableCell>
              <Badge variant="outline">
                {d.tipo_identificacion === "cedula" ? "Cédula" : "RUC"}
              </Badge>
            </TableCell>
            <TableCell className="font-mono">{d.identificacion}</TableCell>
            <TableCell className="font-medium">{d.nombre}</TableCell>
            <TableCell>{d.telefono}</TableCell>
            {canEdit && (
              <TableCell className="text-right">
                <Button size="sm" variant="ghost" onClick={() => onEdit(d)}>
                  Editar
                </Button>
              </TableCell>
            )}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
