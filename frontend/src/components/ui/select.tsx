"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

function Select({
  value,
  onValueChange,
  children,
}: {
  value?: string
  onValueChange?: (value: string) => void
  children: React.ReactNode
}) {
  return (
    <SelectContext.Provider value={{ value: value ?? "", onValueChange: onValueChange ?? (() => {}) }}>
      {children}
    </SelectContext.Provider>
  )
}

interface SelectContextValue {
  value: string
  onValueChange: (value: string) => void
}

const SelectContext = React.createContext<SelectContextValue>({ value: "", onValueChange: () => {} })

function SelectTrigger({
  className,
  children,
  ...props
}: React.ComponentProps<"button">) {
  return (
    <button
      data-slot="select-trigger"
      className={cn(
        "flex items-center justify-between gap-1.5 rounded-lg border border-input bg-transparent px-3 py-2 text-sm h-9 min-w-[100px] outline-none",
        className
      )}
      {...props}
    >
      {children}
      <svg className="w-4 h-4 text-muted-foreground shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    </button>
  )
}

function SelectValue({ placeholder }: { placeholder?: string }) {
  const ctx = React.useContext(SelectContext)
  return <span className="truncate">{ctx.value || placeholder || ""}</span>
}

function SelectContent({
  className,
  children,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="select-content"
      className={cn(
        "absolute mt-1 z-50 min-w-[8rem] overflow-hidden rounded-lg bg-popover text-popover-foreground shadow-md border border-border p-1",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

function SelectItem({
  className,
  value,
  children,
  ...props
}: React.ComponentProps<"button"> & { value: string }) {
  const ctx = React.useContext(SelectContext)
  const isActive = ctx.value === value

  return (
    <button
      className={cn(
        "relative flex w-full cursor-pointer items-center rounded-md py-1.5 px-2 text-sm outline-none hover:bg-accent hover:text-accent-foreground",
        isActive && "bg-accent text-accent-foreground",
        className
      )}
      onClick={() => ctx.onValueChange(value)}
      {...props}
    >
      {children}
    </button>
  )
}

// Wrapper that implements dropdown behavior
function SelectRoot({
  value,
  onValueChange,
  children,
}: {
  value?: string
  onValueChange?: (value: string) => void
  children: React.ReactNode
}) {
  const [open, setOpen] = React.useState(false)
  const ref = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  return (
    <Select value={value} onValueChange={(v) => { onValueChange?.(v); setOpen(false) }}>
      <div ref={ref} className="relative">
        {React.Children.map(children, (child) => {
          if (!React.isValidElement(child)) return child
          if ((child.type as { displayName?: string })?.displayName === "SelectTrigger" || child.type === SelectTrigger) {
            return React.cloneElement(child as React.ReactElement<{onClick?: () => void}>, { onClick: () => setOpen(!open) })
          }
          if ((child.type as { displayName?: string })?.displayName === "SelectContent" || child.type === SelectContent) {
            return open ? child : null
          }
          return child
        })}
      </div>
    </Select>
  )
}

export { SelectRoot as Select, SelectTrigger, SelectValue, SelectContent, SelectItem }
