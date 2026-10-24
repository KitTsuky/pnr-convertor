import { zodResolver } from "@hookform/resolvers/zod";
import { LoaderCircle, Sparkles } from "lucide-react";
import { useId, type KeyboardEvent } from "react";
import { Controller, useForm } from "react-hook-form";

import { GDS_LABELS, gdsSchema } from "@/entities/itinerary";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import { Textarea } from "@/shared/ui/textarea";

import { SAMPLE_PNR } from "../lib/sample-pnr";
import {
  AUTO_DETECT,
  convertFormSchema,
  DEFAULT_VALUES,
  type ConvertFormValues,
} from "../model/form-schema";

interface ConvertPnrFormProps {
  onSubmit: (values: ConvertFormValues) => void;
  onReset?: () => void;
  isPending: boolean;
}

export function ConvertPnrForm({ onSubmit, onReset, isPending }: ConvertPnrFormProps) {
  const id = useId();
  const {
    register,
    control,
    handleSubmit,
    reset,
    setValue,
    formState: { errors },
  } = useForm<ConvertFormValues>({
    resolver: zodResolver(convertFormSchema),
    defaultValues: DEFAULT_VALUES,
  });
  const submit = handleSubmit(onSubmit);

  const submitOnShortcut = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
      event.preventDefault();
      void submit();
    }
  };

  return (
    <form
      noValidate
      onSubmit={(event) => {
        void submit(event);
      }}
      className="flex flex-col gap-5"
      aria-label="Convert a PNR"
    >
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <Label htmlFor={`${id}-pnr`}>PNR</Label>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => {
              setValue("pnr", SAMPLE_PNR, { shouldValidate: true });
            }}
          >
            <Sparkles aria-hidden />
            Try an example
          </Button>
        </div>
        <Textarea
          id={`${id}-pnr`}
          rows={12}
          wrap="off"
          spellCheck={false}
          autoComplete="off"
          placeholder="Paste the PNR exactly as your GDS displays it…"
          className="min-h-56 resize-y overflow-x-auto font-mono text-xs leading-relaxed whitespace-pre"
          aria-invalid={errors.pnr ? true : undefined}
          aria-describedby={errors.pnr ? `${id}-pnr-error` : `${id}-pnr-hint`}
          onKeyDown={submitOnShortcut}
          {...register("pnr")}
        />
        {errors.pnr ? (
          <p id={`${id}-pnr-error`} className="text-xs text-danger">
            {errors.pnr.message}
          </p>
        ) : (
          <p id={`${id}-pnr-hint`} className="text-xs text-muted-foreground">
            Amadeus, Sabre, Galileo, Worldspan or Apollo. Ctrl/⌘ + Enter converts.
          </p>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-2">
          <Label htmlFor={`${id}-gds`}>Format</Label>
          <Controller
            control={control}
            name="gds"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger id={`${id}-gds`} onBlur={field.onBlur}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={AUTO_DETECT}>Auto-detect</SelectItem>
                  {gdsSchema.options.map((gds) => (
                    <SelectItem key={gds} value={gds}>
                      {GDS_LABELS[gds]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor={`${id}-date`}>Displayed on</Label>
          <Input
            id={`${id}-date`}
            type="date"
            aria-invalid={errors.referenceDate ? true : undefined}
            aria-describedby={`${id}-date-hint`}
            {...register("referenceDate")}
          />
          <p id={`${id}-date-hint`} className="text-xs text-muted-foreground">
            {errors.referenceDate?.message ?? "Optional. Sets the year of dates like 15MAR."}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button type="submit" disabled={isPending} className="flex-1">
          {isPending && <LoaderCircle className="animate-spin" aria-hidden />}
          Convert
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => {
            reset(DEFAULT_VALUES);
            onReset?.();
          }}
        >
          Clear
        </Button>
      </div>
    </form>
  );
}
