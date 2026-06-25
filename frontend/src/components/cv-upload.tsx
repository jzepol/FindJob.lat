"use client";

import { useRef, useState } from "react";
import { CheckCircle2, FileText, Loader2, Sparkles, Upload, X } from "lucide-react";
import { uploadCv } from "@/lib/auth";
import { cn } from "@/lib/utils";

const MAX_MB = 5;
const ACCEPT = ".pdf,.txt,application/pdf,text/plain";

function basename(name: string): string {
  const normalized = name.replace(/\\/g, "/");
  const parts = normalized.split("/");
  return parts[parts.length - 1] || name;
}

function looksLikeWindowsPath(value: string): boolean {
  return /^[a-zA-Z]:\\/.test(value) || value.startsWith("file://");
}

function fileFromDrop(e: React.DragEvent): File | null {
  const transfer = e.dataTransfer;
  if (transfer.files.length > 0) {
    const candidate = transfer.files[0];
    if (candidate.size > 0) return candidate;
  }

  for (const item of Array.from(transfer.items ?? [])) {
    if (item.kind !== "file") continue;
    const candidate = item.getAsFile();
    if (candidate && candidate.size > 0) return candidate;
  }

  return null;
}

function pathOnlyFromDrop(e: React.DragEvent): string | null {
  const raw =
    e.dataTransfer.getData("text/uri-list") ||
    e.dataTransfer.getData("text/plain") ||
    e.dataTransfer.getData("text");
  const line = raw.split(/\r?\n/).find((part) => part.trim())?.trim();
  if (!line || !looksLikeWindowsPath(line)) return null;
  return line.replace(/^file:\/\/\/?/i, "");
}

function normalizeUploadFile(file: File): File {
  const cleanName = basename(file.name);
  if (!cleanName || cleanName === file.name) return file;
  return new File([file], cleanName, { type: file.type, lastModified: file.lastModified });
}

type CvUploadProps = {
  cvText: string;
  onCvChange: (text: string) => void;
  onUploaded?: (result: {
    filename: string;
    chars: number;
    karmaGained: number;
    parsedBy: string;
    embeddingReady: boolean;
    summary: string | null;
    skills: string[];
    headline: string | null;
    fullName: string | null;
  }) => void;
  onError?: (message: string) => void;
};

export function CvUpload({ cvText, onCvChange, onUploaded, onError }: CvUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  async function processFile(rawFile: File) {
    const file = normalizeUploadFile(rawFile);
    const ext = basename(file.name).split(".").pop()?.toLowerCase();
    if (!ext || !["pdf", "txt"].includes(ext)) {
      onError?.("Solo aceptamos archivos PDF o TXT.");
      return;
    }
    if (file.size === 0) {
      onError?.(
        "No pudimos leer el archivo (llegó vacío). Usá «Seleccionar archivo» en lugar de arrastrar desde el Explorador de Windows.",
      );
      return;
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      onError?.(`El archivo supera ${MAX_MB} MB.`);
      return;
    }

    setUploading(true);
    try {
      const result = await uploadCv(file);
      setFileName(result.filename);
      onCvChange(result.cv_text);
      onUploaded?.({
        filename: result.filename,
        chars: result.chars,
        karmaGained: result.karma_gained,
        parsedBy: result.parsed_by,
        embeddingReady: result.embedding_ready,
        summary: result.summary,
        skills: result.skills_extracted,
        headline: result.headline_extracted,
        fullName: result.full_name_extracted,
      });
    } catch (err) {
      onError?.(err instanceof Error ? err.message : "Error al subir el CV");
      return;
    } finally {
      setUploading(false);
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);

    const file = fileFromDrop(e);
    if (file) {
      processFile(file);
      return;
    }

    const droppedPath = pathOnlyFromDrop(e);
    if (droppedPath) {
      onError?.(
        "No podemos abrir archivos por ruta. Hacé clic en «Seleccionar archivo» y elegí tu PDF desde Descargas.",
      );
      return;
    }

    onError?.("No se detectó ningún archivo. Probá con «Seleccionar archivo».");
  }

  const hasCv = cvText.trim().length > 50;

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={cn(
          "relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-12 transition-all sm:py-14",
          uploading && "pointer-events-none opacity-70",
          dragOver
            ? "border-primary bg-primary/5 shadow-glow"
            : hasCv
              ? "border-primary/30 bg-primary/5"
              : "border-border-strong bg-surface-2/30 hover:border-primary/30",
        )}
      >
        {uploading ? (
          <>
            <Loader2 className="mb-4 h-10 w-10 animate-spin text-primary" />
            <p className="font-display font-semibold text-foreground">Procesando tu CV...</p>
            <p className="mt-1 text-sm text-muted">Extracción de texto y preparación para matching</p>
          </>
        ) : hasCv ? (
          <>
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/15 ring-1 ring-primary/25">
              <CheckCircle2 className="h-7 w-7 text-primary" />
            </div>
            <p className="font-display font-semibold text-foreground">CV cargado</p>
            <p className="mt-1 flex items-center gap-1.5 text-sm text-muted">
              <FileText className="h-3.5 w-3.5" />
              {fileName ?? "cv.txt"} · {cvText.length.toLocaleString("es-AR")} caracteres
            </p>
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="btn-ghost mt-5 text-sm"
            >
              Reemplazar archivo
            </button>
          </>
        ) : (
          <>
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 ring-1 ring-primary/20">
              <Upload className="h-6 w-6 text-primary" />
            </div>
            <p className="font-display font-semibold text-foreground">Arrastrá tu CV acá</p>
            <p className="mt-1.5 text-sm text-muted">PDF o TXT · máx. {MAX_MB} MB</p>
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="btn-primary mt-6"
            >
              Seleccionar archivo
            </button>
          </>
        )}

        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) processFile(file);
            e.target.value = "";
          }}
        />
      </div>

      {hasCv && (
        <div>
          <div className="mb-2 flex items-center justify-between">
            <p className="text-sm font-medium text-foreground">Vista previa editable</p>
            <button
              type="button"
              onClick={() => {
                onCvChange("");
                setFileName(null);
              }}
              className="inline-flex items-center gap-1 text-xs text-muted transition hover:text-danger"
            >
              <X className="h-3 w-3" />
              Quitar CV
            </button>
          </div>
          <textarea
            value={cvText}
            onChange={(e) => onCvChange(e.target.value)}
            rows={10}
            className="input-field resize-y font-mono text-xs leading-relaxed"
            placeholder="El texto extraído aparecerá acá..."
          />
          <p className="mt-2 flex items-start gap-1.5 text-xs text-muted">
            <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
            Podés editar el texto; al guardar el perfil se actualiza el embedding para matching con
            ofertas.
          </p>
        </div>
      )}
    </div>
  );
}