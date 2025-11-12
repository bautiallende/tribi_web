'use client'

import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useState, useEffect } from 'react'
import { Button, Card } from '@tribi/ui'

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
  const [country, setCountry] = useState<Country | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedPlan, setSelectedPlan] = useState<number | null>(null)
  const [isCreatingOrder, setIsCreatingOrder] = useState(false)

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

  const handleSelectPlan = async (plan: Plan) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
    
    if (!token) {
      // Redirect to auth if not logged in
      router.push('/auth')
      return
    }

    setSelectedPlan(plan.id)
    setIsCreatingOrder(true)

    try {
      // Create order
      const orderResponse = await fetch(`${API_BASE}/orders`, {
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

      if (!orderResponse.ok) {
        const errorData = await orderResponse.json()
        throw new Error(errorData.detail || 'Failed to create order')
      }

      const order = await orderResponse.json()
      
      // Redirect to checkout
      router.push(`/checkout?order_id=${order.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create order')
      setSelectedPlan(null)
    } finally {
      setIsCreatingOrder(false)
    }
  }

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link href="/" className="text-blue-500 hover:underline mb-4 inline-block">
            ← Back to Search
          </Link>
          {country ? (
            <>
              <h1 className="text-4xl font-bold mb-2">{country.name}</h1>
              <p className="text-gray-600">Available eSIM Plans</p>
            </>
          ) : (
            <h1 className="text-4xl font-bold mb-2">eSIM Plans</h1>
          )}
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-12">
            <p className="text-gray-500">Loading plans...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Plans Grid */}
        {!isLoading && !error && (
          <div>
            {plans.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {plans.map((plan) => (
                  <div
                    key={plan.id}
                    className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
                  >
                    <div className="flex justify-between items-start mb-4">
                      <h3 className="text-xl font-semibold text-gray-800">{plan.name}</h3>
                      <span className="text-2xl font-bold text-blue-600">
                        ${plan.price_usd}
                      </span>
                    </div>

                    <div className="space-y-3 mb-4">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Data</span>
                        <span className="font-semibold">
                          {plan.is_unlimited ? 'Unlimited' : `${plan.data_gb}GB`}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Duration</span>
                        <span className="font-semibold">{plan.duration_days} days</span>
                      </div>
                      {plan.description && (
                        <div className="text-sm text-gray-700 pt-2 border-t">
                          {plan.description}
                        </div>
                      )}
                    </div>

                    <button 
                      onClick={() => handleSelectPlan(plan)}
                      disabled={isCreatingOrder && selectedPlan === plan.id}
                      className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 rounded-lg transition-colors disabled:opacity-50"
                    >
                      {isCreatingOrder && selectedPlan === plan.id ? 'Creating Order...' : 'Select Plan'}
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-500 text-lg">No plans available for this country yet.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  )
}
