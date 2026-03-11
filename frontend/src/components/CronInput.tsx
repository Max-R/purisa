/**
 * Cron expression input with preset buttons and human-readable description.
 */
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

interface CronInputProps {
  value: string
  onChange: (cron: string) => void
}

const PRESETS: { label: string; cron: string }[] = [
  { label: 'Every hour', cron: '0 * * * *' },
  { label: 'Every 6h', cron: '0 */6 * * *' },
  { label: 'Every 12h', cron: '0 */12 * * *' },
  { label: 'Daily midnight', cron: '0 0 * * *' },
  { label: 'Weekdays 9am', cron: '0 9 * * 1-5' },
]

const DESCRIPTIONS: Record<string, string> = {
  '0 * * * *': 'Every hour on the hour',
  '0 */6 * * *': 'Every 6 hours',
  '0 */12 * * *': 'Every 12 hours',
  '0 0 * * *': 'Daily at midnight',
  '0 9 * * 1-5': 'Weekdays at 9:00 AM',
  '0 */2 * * *': 'Every 2 hours',
  '0 */3 * * *': 'Every 3 hours',
  '0 */4 * * *': 'Every 4 hours',
  '0 */8 * * *': 'Every 8 hours',
  '0 6 * * *': 'Daily at 6:00 AM',
  '0 12 * * *': 'Daily at noon',
  '0 18 * * *': 'Daily at 6:00 PM',
  '0 0 * * 0': 'Weekly on Sunday at midnight',
  '0 0 * * 1': 'Weekly on Monday at midnight',
  '0 0 1 * *': 'Monthly on the 1st at midnight',
}

function describeCron(cron: string): string {
  return DESCRIPTIONS[cron] || 'Custom schedule'
}

export default function CronInput({ value, onChange }: CronInputProps) {
  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="0 */6 * * *"
          className="flex-1 px-3 py-2 border rounded-md bg-background text-sm font-mono focus:outline-none focus:ring-2 focus:ring-ring"
        />
        {value && (
          <Badge variant="secondary" className="self-center whitespace-nowrap">
            {describeCron(value)}
          </Badge>
        )}
      </div>

      <div className="flex flex-wrap gap-1.5">
        {PRESETS.map((preset) => (
          <Button
            key={preset.cron}
            type="button"
            variant={value === preset.cron ? 'default' : 'outline'}
            size="sm"
            className="text-xs h-7"
            onClick={() => onChange(preset.cron)}
          >
            {preset.label}
          </Button>
        ))}
      </div>
    </div>
  )
}
