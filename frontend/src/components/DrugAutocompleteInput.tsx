import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { fdaApi } from '../services/api'

type DrugAutocompleteInputProps = {
  id: string
  value: string
  onChange: (value: string) => void
  onSelect?: (value: string) => void
  placeholder?: string
  className?: string
}

export function DrugAutocompleteInput({
  id,
  value,
  onChange,
  onSelect,
  placeholder,
  className = '',
}: DrugAutocompleteInputProps) {
  const [debouncedValue, setDebouncedValue] = useState(value)
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedValue(value.trim())
    }, 250)

    return () => window.clearTimeout(timer)
  }, [value])

  const { data: suggestions = [], isFetching } = useQuery({
    queryKey: ['drug-suggestions', debouncedValue],
    queryFn: () => fdaApi.suggestDrugs(debouncedValue, 8),
    enabled: debouncedValue.length >= 2,
    staleTime: 10 * 60 * 1000,
  })

  const showSuggestions = isOpen && value.trim().length >= 2 && suggestions.length > 0

  const chooseSuggestion = (name: string) => {
    onChange(name)
    onSelect?.(name)
    setIsOpen(false)
  }

  return (
    <div className={`relative ${className}`}>
      <input
        id={id}
        type="text"
        value={value}
        onChange={(event) => {
          onChange(event.target.value)
          setIsOpen(true)
        }}
        onFocus={() => setIsOpen(true)}
        onBlur={() => window.setTimeout(() => setIsOpen(false), 120)}
        placeholder={placeholder}
        className="input-field w-full pr-9"
        autoComplete="off"
      />
      <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
        {isFetching ? (
          <div className="h-4 w-4 animate-spin rounded-full border-b-2 border-primary-600"></div>
        ) : (
          <Search className="h-4 w-4" />
        )}
      </div>

      {showSuggestions && (
        <div className="absolute z-30 mt-1 max-h-72 w-full overflow-y-auto rounded-lg border border-gray-200 bg-white shadow-lg">
          {suggestions.map((suggestion) => (
            <button
              key={`${suggestion.kind}-${suggestion.name}`}
              type="button"
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => chooseSuggestion(suggestion.name)}
              className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left hover:bg-gray-50"
            >
              <span className="min-w-0">
                <span className="block truncate text-sm font-medium text-gray-900">
                  {suggestion.name}
                </span>
                <span className="block text-xs capitalize text-gray-500">
                  {suggestion.kind}
                </span>
              </span>
              <span className="shrink-0 rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                {suggestion.label_count}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
