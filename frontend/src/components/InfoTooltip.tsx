/**
 * Reusable info tooltip component.
 *
 * Renders a small ⓘ icon that shows help text on hover.
 * Uses shadcn Tooltip backed by @radix-ui/react-tooltip.
 */
import { Info } from 'lucide-react'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

interface InfoTooltipProps {
  text: string
  side?: 'top' | 'bottom' | 'left' | 'right'
}

export default function InfoTooltip({ text, side = 'top' }: InfoTooltipProps) {
  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            className="inline-flex items-center justify-center h-4 w-4 rounded-full text-muted-foreground hover:text-foreground transition-colors"
            aria-label="More info"
          >
            <Info className="h-3.5 w-3.5" />
          </button>
        </TooltipTrigger>
        <TooltipContent side={side} className="max-w-xs text-sm">
          {text}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
