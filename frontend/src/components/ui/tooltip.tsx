"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

function TooltipProvider({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}

function Tooltip({ children }: { children: React.ReactNode }) {
  return <div className="relative inline-flex group/tooltip">{children}</div>
}

function TooltipTrigger({
  children,
  asChild,
  ...props
}: React.ComponentProps<"div"> & { asChild?: boolean }) {
  return <div {...props}>{children}</div>
}

function TooltipContent({
  className,
  children,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="tooltip-content"
      className={cn(
        "absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50 hidden group-hover/tooltip:block",
        "rounded-md bg-popover px-3 py-1.5 text-xs text-popover-foreground shadow-md border border-border whitespace-nowrap",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider }
