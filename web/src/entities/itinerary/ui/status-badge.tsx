import type { StatusCategory } from "../model/schema";
import { STATUS_LABELS } from "../lib/format";

import { Badge } from "@/shared/ui/badge";

const TONES = {
  confirmed: "success",
  waitlisted: "warning",
  requested: "warning",
  cancelled: "danger",
  unknown: "neutral",
} as const satisfies Record<StatusCategory, string>;

interface StatusBadgeProps {
  category: StatusCategory;
  code: string;
  description: string | null;
}

export function StatusBadge({ category, code, description }: StatusBadgeProps) {
  const label = category === "unknown" ? (description ?? code) : STATUS_LABELS[category];
  return (
    <Badge tone={TONES[category]} title={description ? `${code} · ${description}` : code}>
      {label}
    </Badge>
  );
}
