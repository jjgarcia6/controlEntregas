import { useRef, useState } from "react";

import { Button } from "@/components/ui/button";

interface XmlUploaderProps {
  onFileSelected: (file: File) => void;
  onClear?: () => void;
  disabled?: boolean;
}

export function XmlUploader({ onFileSelected, onClear, disabled }: XmlUploaderProps) {
  const [fileName, setFileName] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
      onFileSelected(file);
    }
  };

  const handleClear = () => {
    setFileName(null);
    if (inputRef.current) {
      inputRef.current.value = "";
    }
    onClear?.();
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="outline"
          disabled={disabled}
          onClick={() => inputRef.current?.click()}
        >
          Seleccionar archivo XML
        </Button>
        {fileName && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={disabled}
            onClick={handleClear}
          >
            Limpiar
          </Button>
        )}
      </div>
      <input
        ref={inputRef}
        type="file"
        accept=".xml"
        className="hidden"
        onChange={handleChange}
        disabled={disabled}
      />
      {fileName && (
        <p className="text-sm text-muted-foreground">{fileName}</p>
      )}
    </div>
  );
}
