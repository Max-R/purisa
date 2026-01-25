import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

interface PlatformFilterProps {
  platforms: string[]
  selected: string | null
  onChange: (platform: string | null) => void
  disabled?: boolean
}

export default function PlatformFilter({ platforms, selected, onChange, disabled = false }: PlatformFilterProps) {
  const handleChange = (value: string) => {
    onChange(value === 'all' ? null : value)
  }

  return (
    <Select
      value={selected || 'all'}
      onValueChange={handleChange}
      disabled={disabled}
    >
      <SelectTrigger className="w-[160px]">
        <SelectValue placeholder="All Platforms" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">All Platforms</SelectItem>
        {platforms.map((platform) => (
          <SelectItem key={platform} value={platform} className="capitalize">
            {platform.charAt(0).toUpperCase() + platform.slice(1)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
