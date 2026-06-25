"use client";

import { Camera } from "lucide-react";
import { cn } from "@/lib/utils";

export function ProfileAvatar({
  name,
  imageUrl,
  preview,
  onFileSelect,
  className,
}: {
  name: string;
  imageUrl?: string | null;
  preview?: string | null;
  onFileSelect: (file: File) => void;
  className?: string;
}) {
  const initial = (name.trim()[0] ?? "?").toUpperCase();
  const src = preview ?? imageUrl;

  return (
    <div className={cn("flex flex-col items-center sm:items-start", className)}>
      <label className="group relative cursor-pointer">
        <div className="relative h-24 w-24 overflow-hidden rounded-2xl ring-2 ring-border ring-offset-2 ring-offset-background transition group-hover:ring-primary/40">
          {src ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={src} alt="" className="h-full w-full object-cover" />
          ) : (
            <div className="logo-gradient flex h-full w-full items-center justify-center text-2xl font-bold text-white">
              {initial}
            </div>
          )}
          <div className="absolute inset-0 flex items-center justify-center bg-background/60 opacity-0 transition group-hover:opacity-100">
            <Camera className="h-5 w-5 text-foreground" />
          </div>
        </div>
        <input
          type="file"
          accept="image/*"
          className="sr-only"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onFileSelect(file);
          }}
        />
      </label>
      <p className="mt-3 text-center text-xs text-muted sm:text-left">
        Foto de perfil <span className="text-foreground-secondary/70">(opcional)</span>
      </p>
    </div>
  );
}