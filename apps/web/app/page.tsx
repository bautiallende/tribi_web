'use client'

import Link from 'next/link'
import { useState, useEffect, useRef } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

interface Country {
  id: number
  iso2: string
  name: string
}

export default function Home() {
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
    // Navigate to plans page
    window.location.href = `/plans/${country.iso2}`
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold">Tribi</h1>
          <Link href="/account" className="text-blue-500 hover:underline text-sm">
            My Account
          </Link>
        </div>
        
        <h2 className="text-2xl font-semibold text-center mb-6 text-gray-700">Find eSIM Plans</h2>

        <div ref={searchRef} className="relative">
          <input
            type="text"
            placeholder="Search countries..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onFocus={() => search && setIsOpen(true)}
            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
          />

          {isOpen && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-64 overflow-y-auto">
              {isLoading ? (
                <div className="px-4 py-3 text-gray-500">Loading countries...</div>
              ) : filteredCountries.length > 0 ? (
                filteredCountries.map((country) => (
                  <button
                    key={country.id}
                    onClick={() => handleSelectCountry(country)}
                    className="w-full text-left px-4 py-3 hover:bg-blue-100 transition-colors border-b last:border-b-0"
                  >
                    <span className="font-semibold">{country.name}</span>
                    <span className="text-gray-500 ml-2">({country.iso2})</span>
                  </button>
                ))
              ) : (
                <div className="px-4 py-3 text-gray-500">No countries found</div>
              )}
            </div>
          )}
        </div>

        <div className="mt-8 text-center">
          <Link href="/health" className="text-blue-500 hover:underline">
            Health Check
          </Link>
        </div>
      </div>
    </main>
  )
}