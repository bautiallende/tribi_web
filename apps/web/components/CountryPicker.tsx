'use client'

import Link from 'next/link'
import { useState, useEffect, useRef } from 'react'
import { Input, Badge } from '@tribi/ui'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

interface Country {
  id: number
  iso2: string
  name: string
}

interface CountryPickerProps {
  onSelect: (country: Country) => void
}

export function CountryPicker({ onSelect }: CountryPickerProps) {
  const [search, setSearch] = useState('')
  const [countries, setCountries] = useState<Country[]>([])
  const [filteredCountries, setFilteredCountries] = useState<Country[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const searchRef = useRef<HTMLDivElement>(null)

  // Fetch all countries on mount
  useEffect(() => {
    const fetchCountries = async () => {
      try {
        setIsLoading(true)
        const response = await fetch(`${API_BASE}/api/countries`)
        if (response.ok) {
          const data = await response.json()
          setCountries(data)
        }
      } catch (error) {
        console.error('Failed to fetch countries:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchCountries()
  }, [])

  // Filter countries based on search input
  useEffect(() => {
    if (search.trim() === '') {
      setFilteredCountries([])
      setIsOpen(false)
    } else {
      const filtered = countries.filter(
        (country) =>
          country.name.toLowerCase().includes(search.toLowerCase()) ||
          country.iso2.toLowerCase().includes(search.toLowerCase())
      )
      setFilteredCountries(filtered)
      setIsOpen(true)
    }
  }, [search, countries])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelectCountry = (country: Country) => {
    setSearch(country.name)
    setIsOpen(false)
    onSelect(country)
  }

  return (
    <div ref={searchRef} className="relative w-full">
      <Input
        type="text"
        placeholder="Search for a country..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        onFocus={() => search && setIsOpen(true)}
        className="pr-10"
        aria-label="Search countries"
        aria-autocomplete="list"
        aria-expanded={isOpen}
      />

      {/* Search Icon */}
      <div className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground">
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-10 w-full mt-2 bg-white dark:bg-slate-900 border border-border rounded-lg shadow-lg max-h-80 overflow-y-auto animate-slide-up">
          {isLoading ? (
            <div className="px-4 py-8 text-center text-muted-foreground">Loading countries...</div>
          ) : filteredCountries.length > 0 ? (
            filteredCountries.map((country) => (
              <button
                key={country.id}
                onClick={() => handleSelectCountry(country)}
                className="w-full text-left px-4 py-3 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors border-b border-border last:border-b-0 focus-visible:outline-none focus-visible:bg-primary-50 dark:focus-visible:bg-primary-900/20"
                role="option"
                aria-selected={false}
              >
                <div className="font-medium text-foreground">{country.name}</div>
                <div className="text-xs text-muted-foreground">{country.iso2}</div>
              </button>
            ))
          ) : search.length > 0 ? (
            <div className="px-4 py-8 text-center text-muted-foreground">No countries found for "{search}"</div>
          ) : null}
        </div>
      )}
    </div>
  )
}
