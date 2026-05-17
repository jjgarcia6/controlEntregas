import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";

import { useConfirmXml } from "../hooks/useConfirmXml";
import { usePreviewXml } from "../hooks/usePreviewXml";
import type { XmlPreviewType } from "../types/xml.types";
import { XmlConfirmDialog } from "./XmlConfirmDialog";
import { XmlPreview } from "./XmlPreview";
import { XmlUploader } from "./XmlUploader";

export function XmlIngresoContainer() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<XmlPreviewType | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const previewMutation = usePreviewXml();
  const confirmMutation = useConfirmXml();

  const handleFileSelected = (f: File) => {
    setFile(f);
    setPreview(null);
    setErrorMsg(null);
  };

  const handleClear = () => {
    setFile(null);
    setPreview(null);
    setErrorMsg(null);
  };

  const handlePreview = () => {
    if (!file) return;
    setErrorMsg(null);
    previewMutation.mutate(file, {
      onSuccess: (data) => setPreview(data),
      onError: (e) => {
        if (axios.isAxiosError(e)) {
          const msg = e.response?.data?.detail as string | undefined;
          setErrorMsg(msg ?? "Error al procesar el XML.");
        } else if (e instanceof Error) {
          setErrorMsg(`Error al procesar el XML: ${e.message}`);
        } else {
          setErrorMsg("Error inesperado al procesar el XML.");
        }
      },
    });
  };

  const handleConfirm = () => {
    if (!file) return;
    confirmMutation.mutate(file, {
      onSuccess: () => {
        toast.success("XML ingresado correctamente");
        navigate("/xml/lista");
      },
      onError: (e) => {
        setShowConfirm(false);
        if (axios.isAxiosError(e)) {
          const status = e.response?.status;
          const msg = e.response?.data?.detail as string | undefined;
          if (status === 409) {
            setErrorMsg("Este XML ya fue ingresado anteriormente (clave de acceso duplicada).");
          } else if (status === 400) {
            setErrorMsg(msg ?? "El archivo no es una factura SRI válida.");
          } else {
            setErrorMsg(msg ?? "Error al confirmar el ingreso.");
          }
        } else {
          setErrorMsg("Error inesperado al confirmar el ingreso.");
        }
      },
    });
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <h2 className="text-xl font-semibold">Ingreso de XML SRI</h2>

      <div className="space-y-4">
        <XmlUploader
          onFileSelected={handleFileSelected}
          onClear={handleClear}
          disabled={previewMutation.isPending || confirmMutation.isPending}
        />

        {!preview && (
          <Button
            onClick={handlePreview}
            disabled={!file || previewMutation.isPending}
          >
            {previewMutation.isPending ? "Procesando..." : "Vista previa"}
          </Button>
        )}

        {errorMsg && (
          <p className="text-sm text-destructive">{errorMsg}</p>
        )}

        {preview && (
          <div className="space-y-4">
            <XmlPreview preview={preview} />
            <Button
              onClick={() => setShowConfirm(true)}
              disabled={confirmMutation.isPending}
            >
              Confirmar ingreso
            </Button>
          </div>
        )}
      </div>

      <XmlConfirmDialog
        open={showConfirm}
        onConfirm={handleConfirm}
        onCancel={() => setShowConfirm(false)}
        isPending={confirmMutation.isPending}
      />
    </div>
  );
}
