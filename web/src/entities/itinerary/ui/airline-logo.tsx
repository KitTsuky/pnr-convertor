import { useState } from "react";

import { apiUrl } from "@/shared/api/api-url";
import { cn } from "@/shared/lib/cn";

interface AirlineLogoProps {
  code: string;
  name: string;
  logoUrl: string | null;
  className?: string;
}

export function AirlineLogo({ code, name, logoUrl, className }: AirlineLogoProps) {
  const [failed, setFailed] = useState(false);

  // Logos are drawn for light backgrounds: a white plate keeps them readable in dark mode.
  if (logoUrl && !failed) {
    return (
      <span className={cn("inline-flex h-8 items-center rounded-md bg-white px-1.5", className)}>
        <img
          src={apiUrl(logoUrl)}
          alt={name}
          loading="lazy"
          decoding="async"
          className="h-5 w-auto max-w-24 object-contain"
          onError={() => {
            setFailed(true);
          }}
        />
      </span>
    );
  }
  return (
    <span
      role="img"
      aria-label={name}
      className={cn(
        "inline-flex size-8 items-center justify-center rounded-md bg-muted font-mono text-xs font-semibold",
        className,
      )}
    >
      {code}
    </span>
  );
}
