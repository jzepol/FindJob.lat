import Image from "next/image";
import Link from "next/link";
import { cn } from "@/lib/utils";

type LogoProps = {
  size?: number;
  showText?: boolean;
  className?: string;
};

export function Logo({ size = 32, showText = true, className }: LogoProps) {
  return (
    <Link href="/" className={cn("flex items-center gap-2.5", className)}>
      <Image
        src="/android-chrome-192x192.png"
        alt="Findjob.lat"
        width={size}
        height={size}
        className="shrink-0 rounded-xl"
        priority
      />
      {showText && (
        <span className="font-display text-lg font-bold tracking-tight">
          Findjob<span className="text-primary">.lat</span>
        </span>
      )}
    </Link>
  );
}