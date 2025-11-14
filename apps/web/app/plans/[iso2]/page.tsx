'use client'

import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useState, useEffect } from 'react'
import { Card, Badge, Skeleton, Input, Select } from '@tribi/ui'

interface Plan {
  id: number
  name: string
  data_gb: string
  duration_days: number
  price_usd: string
  description: string
  is_unlimited: boolean
  country_id: number
  carrier_id: number
}

interface Country {
  id: number
  iso2: string
  name: string
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export default function PlansPage() {
  const params = useParams()
  const router = useRouter()
  const iso2 = params?.iso2 as string

  const [plans, setPlans] = useState<Plan[]>([])
  const [filteredPlans, setFilteredPlans] = useState<Plan[]>([])
  const [country, setCountry] = useState<Country | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedPlan, setSelectedPlan] = useState<number | null>(null)
  const [isCreatingOrder, setIsCreatingOrder] = useState(false)

  // Filter states
  const [maxPrice, setMaxPrice] = useState(100)
  const [maxData, setMaxData] = useState(50)
  const [minDays, setMinDays] = useState(1)
  const [sortBy, setSortBy] = useState<'price-asc' | 'price-desc' | 'data-desc'>('price-asc')

  // Fetch data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true)
        setError(null)

        // Fetch country info
        const countryResponse = await fetch(`${API_BASE}/api/countries?q=${iso2}`)
        if (countryResponse.ok) {
          const countryData = await countryResponse.json()
          if (countryData.length > 0) {
            setCountry(countryData[0])
          }
        }

        // Fetch plans for this country
        const plansResponse = await fetch(`${API_BASE}/api/plans?country=${iso2}`)
        if (plansResponse.ok) {
          const plansData = await plansResponse.json()
          setPlans(plansData)
        }
      } catch (err) {
        setError('Failed to load plans')
        console.error(err)
      } finally {
        setIsLoading(false)
      }
    }

    if (iso2) {
      fetchData()
    }
  }, [iso2])

  // Apply filters
  useEffect(() => {
    let result = plans.filter((plan) => {
      const price = parseFloat(plan.price_usd)
      const data = plan.is_unlimited ? Infinity : parseFloat(plan.data_gb)
      return price <= maxPrice && data <= maxData && plan.duration_days >= minDays
    })

    // Sort
    if (sortBy === 'price-asc') {
      result.sort((a, b) => parseFloat(a.price_usd) - parseFloat(b.price_usd))
    } else if (sortBy === 'price-desc') {
      result.sort((a, b) => parseFloat(b.price_usd) - parseFloat(a.price_usd))
    } else if (sortBy === 'data-desc') {
      result.sort((a, b) => {
        const aData = a.is_unlimited ? Infinity : parseFloat(a.data_gb)
        const bData = b.is_unlimited ? Infinity : parseFloat(b.data_gb)
        return bData - aData
      })
    }

    setFilteredPlans(result)
  }, [plans, maxPrice, maxData, minDays, sortBy])

  const handleSelectPlan = async (plan: Plan) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null

    if (!token) {
      router.push('/auth')
      return
    }

    setSelectedPlan(plan.id)
    setIsCreatingOrder(true)

    try {
      console.log('🛒 Creating order for plan:', plan.id);
      const orderResponse = await fetch(`${API_BASE}/api/orders`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          plan_id: plan.id,
          currency: 'USD',
        }),
      })

      console.log('📥 Order response:', orderResponse.status);

      if (!orderResponse.ok) {
        const errorData = await orderResponse.json()
        throw new Error(errorData.detail || 'Failed to create order')
      }

      const order = await orderResponse.json()
      router.push(`/checkout?order_id=${order.id}`)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create order')
      setSelectedPlan(null)
    } finally {
      setIsCreatingOrder(false)
    }
  }

  const maxPrice_global = plans.length > 0 ? Math.max(...plans.map((p) => parseFloat(p.price_usd))) : 100
  const maxData_global = plans.length > 0 ? Math.max(...plans.filter((p) => !p.is_unlimited).map((p) => parseFloat(p.data_gb))) : 50

  return (
    <main className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <div className="container-max py-12">
        {/* Header */}
        <div className="mb-12">
          <Link href="/" className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 mb-6 font-medium transition-colors">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Search
          </Link>

          {country ? (
            <>
              <h1 className="text-5xl md:text-6xl font-bold mb-3 text-foreground">{country.name}</h1>
              <p className="text-lg text-muted-foreground">Available eSIM Plans</p>
            </>
          ) : (
            <h1 className="text-5xl md:text-6xl font-bold mb-3">eSIM Plans</h1>
          )}
        </div>

        <div className="grid lg:grid-cols-4 gap-8">
          {/* Filters Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-border sticky top-24 space-y-6">
              <div>
                <h3 className="font-semibold text-foreground mb-3">Filters</h3>
                <button
                  onClick={() => {
                    setMaxPrice(maxPrice_global)
                    setMaxData(maxData_global)
                    setMinDays(1)
                    setSortBy('price-asc')
                  }}
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                >
                  Reset Filters
                </button>
              </div>

              {/* Sort */}
              <div>
                <label className="block text-sm font-medium mb-2 text-foreground">Sort by</label>
                <Select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="w-full"
                >
                  <option value="price-asc">Price: Low to High</option>
                  <option value="price-desc">Price: High to Low</option>
                  <option value="data-desc">Data: Most to Least</option>
                </Select>
              </div>

              {/* Price Range */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-sm font-medium text-foreground">Max Price</label>
                  <span className="text-sm font-semibold text-primary-600">${maxPrice}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max={maxPrice_global}
                  step="5"
                  value={maxPrice}
                  onChange={(e) => setMaxPrice(Number(e.target.value))}
                  className="w-full accent-primary-600"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>$0</span>
                  <span>${maxPrice_global}</span>
                </div>
              </div>

              {/* Data Volume */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-sm font-medium text-foreground">Max Data</label>
                  <span className="text-sm font-semibold text-accent-600">{maxData}GB</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max={maxData_global}
                  step="1"
                  value={maxData}
                  onChange={(e) => setMaxData(Number(e.target.value))}
                  className="w-full accent-accent-600"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>0GB</span>
                  <span>{maxData_global}GB</span>
                </div>
              </div>

              {/* Min Duration */}
              <div>
                <label className="block text-sm font-medium mb-2 text-foreground">Min. Days</label>
                <Input
                  type="number"
                  min="1"
                  max="365"
                  value={minDays}
                  onChange={(e) => setMinDays(Math.max(1, Number(e.target.value)))}
                />
              </div>

              {/* Results Count */}
              <div className="pt-4 border-t border-border">
                <p className="text-sm text-muted-foreground">
                  Showing <span className="font-semibold text-foreground">{filteredPlans.length}</span> of{' '}
                  <span className="font-semibold text-foreground">{plans.length}</span> plans
                </p>
              </div>
            </div>
          </div>

          {/* Plans Grid */}
          <div className="lg:col-span-3">
            {isLoading ? (
              // Loading Skeletons
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} className="space-y-4">
                    <Skeleton className="h-48 w-full rounded-2xl" />
                  </div>
                ))}
              </div>
            ) : error ? (
              // Error State
              <div className="bg-destructive/10 border border-destructive/20 rounded-2xl p-8 text-center">
                <p className="text-destructive font-medium mb-2">Failed to load plans</p>
                <p className="text-sm text-muted-foreground">{error}</p>
              </div>
            ) : filteredPlans.length > 0 ? (
              // Plans Grid
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {filteredPlans.map((plan) => (
                  <Card key={plan.id} className="overflow-hidden border border-border hover:shadow-lg transition-all group cursor-pointer">
                    <div className="p-6 space-y-4">
                      {/* Header */}
                      <div className="flex justify-between items-start gap-4">
                        <div className="flex-1">
                          <h3 className="text-xl font-semibold text-foreground group-hover:text-primary-600 transition-colors">{plan.name}</h3>
                          <p className="text-sm text-muted-foreground mt-1">{plan.description}</p>
                        </div>
                        <div className="text-right">
                          <div className="text-3xl font-bold gradient-text">${plan.price_usd}</div>
                          <p className="text-xs text-muted-foreground mt-1">per plan</p>
                        </div>
                      </div>

                      {/* Specs */}
                      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border">
                        {/* Data */}
                        <div>
                          <p className="text-xs text-muted-foreground font-medium mb-1">Data</p>
                          <div className="flex items-baseline gap-1">
                            <span className="text-lg font-semibold text-accent-600">
                              {plan.is_unlimited ? '∞' : plan.data_gb}
                            </span>
                            {!plan.is_unlimited && <span className="text-xs text-muted-foreground">GB</span>}
                          </div>
                        </div>

                        {/* Duration */}
                        <div>
                          <p className="text-xs text-muted-foreground font-medium mb-1">Duration</p>
                          <div className="flex items-baseline gap-1">
                            <span className="text-lg font-semibold text-primary-600">{plan.duration_days}</span>
                            <span className="text-xs text-muted-foreground">days</span>
                          </div>
                        </div>
                      </div>

                      {/* Badges */}
                      <div className="flex flex-wrap gap-2 pt-2">
                        {plan.is_unlimited && <Badge variant="accent">Unlimited Data</Badge>}
                        {parseFloat(plan.price_usd) < 10 && <Badge variant="success">Budget Friendly</Badge>}
                        {plan.duration_days >= 30 && <Badge variant="primary">Long Duration</Badge>}
                      </div>

                      {/* CTA Button */}
                      <button
                        onClick={() => handleSelectPlan(plan)}
                        disabled={isCreatingOrder && selectedPlan === plan.id}
                        className="w-full mt-4 px-4 py-3 bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 text-white font-semibold rounded-lg transition-all disabled:opacity-50 active:scale-95"
                      >
                        {isCreatingOrder && selectedPlan === plan.id ? (
                          <span className="inline-flex items-center gap-2">
                            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                            </svg>
                            Creating Order...
                          </span>
                        ) : (
                          'Select Plan'
                        )}
                      </button>
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              // Empty State
              <div className="bg-slate-100 dark:bg-slate-800 rounded-2xl p-12 text-center">
                <div className="text-5xl mb-4">📭</div>
                <h3 className="text-xl font-semibold text-foreground mb-2">No plans found</h3>
                <p className="text-muted-foreground mb-6">
                  Try adjusting your filters or check back soon for new plans
                </p>
                <button
                  onClick={() => {
                    setMaxPrice(maxPrice_global)
                    setMaxData(maxData_global)
                    setMinDays(1)
                  }}
                  className="inline-flex px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors"
                >
                  Reset Filters
                </button>
              </div>
            )}

            {/* Results Info */}
            {!isLoading && !error && (
              <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <p className="text-sm text-blue-900 dark:text-blue-100">
                  💡 <span className="font-medium">Tip:</span> Use the filters on the left to narrow down by price, data, or duration. All plans include local carrier coverage.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  )
}
