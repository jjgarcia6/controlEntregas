import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { BancoResponseType } from "../types/banco.types";

interface BancosListProps {
  bancos: BancoResponseType[];
  onEdit: (banco: BancoResponseType) => void;
  canEdit: boolean;
}

export function BancosList({ bancos, onEdit, canEdit }: BancosListProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Nombre</TableHead>
          {canEdit && <TableHead className="text-right">Acciones</TableHead>}
        </TableRow>
      </TableHeader>
      <TableBody>
        {bancos.map((b) => (
          <TableRow key={b.id}>
            <TableCell className="font-medium">{b.nombre}</TableCell>
            {canEdit && (
              <TableCell className="text-right">
                <Button size="sm" variant="ghost" onClick={() => onEdit(b)}>
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
