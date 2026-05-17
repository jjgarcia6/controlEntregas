import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCurrency, formatDate } from "@/shared/utils/formatters";
import type { XmlPreviewType } from "../types/xml.types";

interface XmlPreviewProps {
  preview: XmlPreviewType;
}

export function XmlPreview({ preview }: XmlPreviewProps) {
  return (
    <div className="space-y-6">
      <div className="rounded-lg border p-4 text-sm">
        <div className="grid grid-cols-2 gap-x-8 gap-y-1">
          <div>
            <span className="text-muted-foreground">Emisor: </span>
            <span className="font-medium">{preview.razon_social_emisor}</span>
          </div>
          <div>
            <span className="text-muted-foreground">RUC emisor: </span>
            {preview.ruc_emisor}
          </div>
          <div>
            <span className="text-muted-foreground">Factura: </span>
            <span className="font-mono">{preview.numero_factura}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Fecha emisión: </span>
            {formatDate(preview.fecha_emision)}
          </div>
          <div>
            <span className="text-muted-foreground">Ambiente: </span>
            <span className={preview.ambiente === 2 ? "text-green-600 font-medium" : "text-yellow-600 font-medium"}>
              {preview.ambiente === 2 ? "Producción" : "Pruebas"}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">Moneda: </span>
            {preview.moneda}
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold mb-2">Ítems de la factura</h3>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Código</TableHead>
              <TableHead>Descripción</TableHead>
              <TableHead className="text-right">Cantidad</TableHead>
              <TableHead className="text-right">P. Unitario</TableHead>
              <TableHead className="text-right">IVA %</TableHead>
              <TableHead className="text-right">Total sin imp.</TableHead>
              <TableHead className="text-right">Peso unit.</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {preview.items.map((item, i) => (
              <TableRow key={i}>
                <TableCell className="font-mono text-xs">{item.codigo_principal}</TableCell>
                <TableCell>{item.descripcion}</TableCell>
                <TableCell className="text-right">{item.cantidad_documento}</TableCell>
                <TableCell className="text-right">{formatCurrency(item.precio_unitario)}</TableCell>
                <TableCell className="text-right">{item.tarifa_iva}%</TableCell>
                <TableCell className="text-right">{formatCurrency(item.precio_total_sin_imp)}</TableCell>
                <TableCell className="text-right">{item.peso_unitario}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="rounded-lg border p-4 text-sm">
        <h3 className="text-sm font-semibold mb-2">Totales</h3>
        <div className="grid grid-cols-2 gap-x-8 gap-y-1 max-w-xs">
          <span className="text-muted-foreground">Subtotal sin imp.:</span>
          <span className="text-right">{formatCurrency(preview.total_sin_impuestos)}</span>
          <span className="text-muted-foreground">Total descuento:</span>
          <span className="text-right">{formatCurrency(preview.total_descuento)}</span>
          <span className="text-muted-foreground">Subtotal gravado:</span>
          <span className="text-right">{formatCurrency(preview.subtotal_gravado)}</span>
          <span className="text-muted-foreground">IVA:</span>
          <span className="text-right">{formatCurrency(preview.valor_iva)}</span>
          <span className="text-muted-foreground font-semibold">Total:</span>
          <span className="text-right font-semibold">{formatCurrency(preview.importe_total)}</span>
        </div>
      </div>
    </div>
  );
}
