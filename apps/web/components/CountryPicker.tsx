'use client'

import { Input } from '@tribi/ui'
import { useEffect, useRef, useState } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE
  ? process.env.NEXT_PUBLIC_API_BASE.replace(/\/$/, '')
  : undefined
const COUNTRIES_ENDPOINT = `${API_BASE ?? ''}/api/countries`

interface Country {
  id: number
  iso2: string
  name: string
}

interface CountryPickerProps {
  onSelect: (country: Country) => void
}

// Helper to get flag emoji from country code
const getFlagEmoji = (iso2: string): string => {
  const codePoints = iso2
    .toUpperCase()
    .split('')
    .map((char) => 127397 + char.charCodeAt(0))
  return String.fromCodePoint(...codePoints)
}

export function CountryPicker({ onSelect }: CountryPickerProps) {
  const [search, setSearch] = useState('')
  const [countries, setCountries] = useState<Country[]>([])
  const [filteredCountries, setFilteredCountries] = useState<Country[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const searchRef = useRef<HTMLDivElement>(null)

  // Fetch all countries on mount
  useEffect(() => {
    const fetchCountries = async () => {
      try {
        setIsLoading(true)
        console.log('🌍 Fetching countries from', COUNTRIES_ENDPOINT)
        const response = await fetch(COUNTRIES_ENDPOINT)
        console.log('🌍 Country response status:', response.status)
        if (!response.ok) {
          throw new Error(`Failed to load countries (${response.status})`)
        }

        const data: Country[] = await response.json()
        console.log('🌍 Countries loaded:', data.length, data[0])
        setCountries(data)
        setFilteredCountries(data)
        setErrorMessage('')
      } catch (error) {
        console.error('Failed to fetch countries:', error)
        setErrorMessage('Unable to load countries. Please try again.')
        setCountries([])
        setFilteredCountries([])
      } finally {
        setIsLoading(false)
      }
    }

    fetchCountries()
  }, [])

  // Filter countries based on search input
  useEffect(() => {
    const trimmed = search.trim()
    if (trimmed === '') {
      setFilteredCountries(countries)
      setIsOpen(countries.length > 0)
    } else {
      const lower = trimmed.toLowerCase()
      const filtered = countries.filter(
        (country) =>
          country.name.toLowerCase().includes(lower) ||
          country.iso2.toLowerCase().includes(lower)
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
    console.log('🧭 Country selected:', country)
    setSearch(country.name)
    setIsOpen(false)
    onSelect(country)
  }

  const handleSearchChange = (value: string) => {
    console.log('🔍 Country search query:', value)
    setSearch(value)
  }

  return (
    <div ref={searchRef} className="relative w-full">
      <div className="relative">
        <Input
          type="text"
          placeholder="🔍 Search for a country..."
          value={search}
          onChange={(e) => handleSearchChange(e.target.value)}
          onFocus={() => setIsOpen(filteredCountries.length > 0 && countries.length > 0)}
          className="pl-12 pr-4 text-lg h-14 shadow-md hover:shadow-lg transition-shadow"
          aria-label="Search countries"
          aria-autocomplete="list"
          aria-expanded={isOpen}
        />

        {/* Search Icon */}
        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-primary-500">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>

      {/* Dropdown */}
      {errorMessage && (
        <div className="absolute z-10 w-full mt-2 bg-red-50 border-2 border-red-200 rounded-xl shadow-xl p-4 text-red-700">
          {errorMessage}
        </div>
      )}

      {isOpen && !errorMessage && (
        <div className="absolute z-10 w-full mt-2 bg-white dark:bg-slate-900 border-2 border-gray-300 dark:border-gray-600 rounded-xl shadow-xl max-h-96 overflow-y-auto animate-slide-up">
          {isLoading ? (
            <div className="px-4 py-8 text-center text-gray-700 dark:text-gray-300">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
              <p className="mt-2">Loading countries...</p>
            </div>
          ) : filteredCountries.length > 0 ? (
            <>
              <div className="px-4 py-2 text-xs font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 border-b border-gray-300 dark:border-gray-600">
                {filteredCountries.length} {filteredCountries.length === 1 ? 'result' : 'results'}
              </div>
              {filteredCountries.map((country, index) => (
                <button
                  key={country.id}
                  onClick={() => handleSelectCountry(country)}
                  className="w-full text-left px-4 py-3 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-all duration-200 border-b border-gray-200 dark:border-gray-700 last:border-b-0 focus-visible:outline-none focus-visible:bg-primary-100 dark:focus-visible:bg-primary-900/30 group"
                  role="option"
                  aria-selected={false}
                  style={{ animationDelay: `${index * 30}ms` }}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-3xl group-hover:scale-110 transition-transform duration-200">
                      {getFlagEmoji(country.iso2)}
                    </span>
                    <div className="flex-1">
                      <div className="font-semibold text-gray-900 dark:text-gray-100 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                        {country.name}
                      </div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">{country.iso2}</div>
                    </div>
                    <svg className="w-5 h-5 text-gray-500 dark:text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </button>
              ))}
            </>
          ) : search.length > 0 ? (
            <div className="px-4 py-12 text-center">
              <div className="text-5xl mb-3">🌍</div>
              <p className="text-gray-900 dark:text-gray-100 font-medium">No countries found</p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Try searching for &ldquo;{search}&rdquo;</p>
            </div>
          ) : null}
        </div>
      )}
    </div>
  )
}