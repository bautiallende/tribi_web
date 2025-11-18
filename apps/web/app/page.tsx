'use client'

import { CountryPicker } from '@/components/CountryPicker'
import { Badge } from '@tribi/ui'
import Link from 'next/link'
import { useRouter } from 'next/navigation'


interface Country {
  id: number
  iso2: string
  name: string
}

export default function Home() {
  const router = useRouter()

  const handleCountrySelect = (country: Country) => {
    router.push(`/plans/${country.iso2}`)
  }

  const steps = [
    {
      number: '1',
      title: 'Choose Country',
      description: 'Select your destination from our list of 100+ countries',
      icon: '🌍',
    },
    {
      number: '2',
      title: 'Pick a Plan',
      description: 'Choose from flexible data plans with coverage from local carriers',
      icon: '📱',
    },
    {
      number: '3',
      title: 'Activate eSIM',
      description: 'Get your eSIM activation code instantly and enjoy connectivity',
      icon: '✨',
    },
  ]

  const popularCarriers = [
    { name: 'Vodafone', code: 'VODAFONE' },
    { name: 'Orange', code: 'ORANGE' },
    { name: 'Deutsche Telekom', code: 'TELEKOM' },
    { name: 'Swisscom', code: 'SWISSCOM' },
    { name: 'KPN', code: 'KPN' },
    { name: 'Proximus', code: 'PROXIMUS' },
  ]

  const trustPoints = [
    { label: '100+ Countries', value: 'Global Coverage' },
    { label: '24/7 Support', value: 'Always Available' },
    { label: '99.8% Uptime', value: 'Reliable Service' },
    { label: '50K+ Travelers', value: 'Trusted Community' },
  ]

  return (
    <main className="w-full">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-32 sm:pt-32 sm:pb-40">
        {/* Background Gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary-50 via-white to-accent-50 dark:from-primary-900/20 dark:via-slate-950 dark:to-accent-900/20" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-accent-200/20 dark:bg-accent-900/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-primary-200/20 dark:bg-primary-900/10 rounded-full blur-3xl" />

        {/* Content */}
        <div className="container-max relative z-10">
          <div className="text-center space-y-6 mb-12">
            {/* Badge */}
            <div className="flex justify-center">
              <Badge variant="primary" className="px-4 py-2 text-xs md:text-sm">
                ✨ Introducing Tribi - Travel Connected
              </Badge>
            </div>

            {/* Main Heading */}
            <div className="space-y-4">
              <h1 className="gradient-text text-5xl md:text-7xl font-bold leading-tight">
                Stay Connected Everywhere
              </h1>
              <p className="text-lg md:text-2xl text-gray-700 dark:text-gray-300 max-w-3xl mx-auto">
                Get instant eSIM coverage in 100+ countries. No roaming fees. No surprises. Just seamless connectivity.
              </p>
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
              <button className="group px-8 py-3 md:px-10 md:py-4 bg-gradient-to-r from-primary-600 via-primary-600 to-primary-700 hover:from-primary-700 hover:via-primary-600 hover:to-primary-600 text-white rounded-xl font-semibold transition-all shadow-lg hover:shadow-2xl hover:scale-105 active:scale-95 relative overflow-hidden">
                <span className="relative z-10 flex items-center justify-center gap-2">
                  Get Started Now
                  <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </span>
                <div className="absolute inset-0 bg-gradient-to-r from-accent-500 to-primary-600 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
              </button>
              <Link
                href="#how-it-works"
                className="group px-8 py-3 md:px-10 md:py-4 border-2 border-primary-300 dark:border-primary-700 text-primary-700 dark:text-primary-300 rounded-xl font-semibold hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-all hover:border-primary-500 dark:hover:border-primary-500 hover:scale-105 active:scale-95 flex items-center justify-center gap-2"
              >
                Learn More
                <svg className="w-5 h-5 group-hover:translate-y-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </Link>
            </div>
          </div>

          {/* Country Picker Card */}
                    <div className="bg-white dark:bg-slate-800 rounded-3xl shadow-2xl p-8 border-2 border-gray-300 dark:border-gray-600 hover:border-primary-300 dark:hover:border-primary-700 transition-all duration-300">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Where are you traveling?</h2>
            </div>
            <CountryPicker onSelect={handleCountrySelect} />
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-4 flex items-center gap-2">
              <svg className="w-4 h-4 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Search by country name or code to see available plans</span>
            </p>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-20 sm:py-32 bg-slate-50 dark:bg-slate-900/50">
        <div className="container-max">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4 text-gray-900 dark:text-white">How It Works</h2>
            <p className="text-lg text-gray-700 dark:text-gray-300 max-w-2xl mx-auto">
              Get connected in just 3 simple steps
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {steps.map((step, index) => (
              <div key={index} className="relative group">
                {/* Connection Line (hidden on mobile) */}
                {index < steps.length - 1 && (
                  <div className="hidden md:block absolute top-16 left-full w-full h-0.5 bg-gradient-to-r from-primary-300 to-transparent dark:from-primary-700 -z-10"></div>
                )}

                {/* Card */}
                <div className="bg-white dark:bg-slate-800 border-2 border-gray-300 dark:border-gray-600 rounded-2xl p-8 h-full hover:shadow-2xl hover:border-primary-300 dark:hover:border-primary-700 transition-all duration-300 hover:-translate-y-2 relative">
                  {/* Icon */}
                  <div className="text-5xl mb-4 group-hover:scale-110 transition-transform duration-300">{step.icon}</div>

                  {/* Number Badge */}
                  <div className="absolute top-4 right-4 w-12 h-12 rounded-full bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
                    <span className="font-bold text-white text-lg">{step.number}</span>
                  </div>

                  {/* Content */}
                  <h3 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">{step.title}</h3>
                  <p className="text-gray-700 dark:text-gray-300">{step.description}</p>
                </div>

                {/* Arrow (hidden on last item) */}
                {index < steps.length - 1 && (
                  <div className="hidden md:flex absolute top-1/2 -right-4 -translate-y-1/2 text-primary-300">
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Popular Carriers Section */}
      <section className="py-20 sm:py-32">
        <div className="container-max">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4 text-gray-900 dark:text-white">Trusted by Major Carriers</h2>
            <p className="text-lg text-gray-700 dark:text-gray-300">
              We partner with the world&apos;s leading telecommunications networks
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
            {popularCarriers.map((carrier, index) => (
              <div key={index} className="flex items-center justify-center p-6 bg-slate-50 dark:bg-slate-900 border-2 border-gray-300 dark:border-gray-600 rounded-xl hover:shadow-md hover:border-primary-200 dark:hover:border-primary-800 transition-all">
                <div className="text-center">
                  <div className="text-3xl mb-2">📡</div>
                  <p className="font-semibold text-sm text-gray-900 dark:text-white">{carrier.name}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Trust Section */}
      <section className="py-20 sm:py-32 bg-gradient-to-r from-primary-600 to-accent-600 text-white">
        <div className="container-max">
          <h2 className="text-4xl md:text-5xl font-bold text-center mb-16">Why Choose Tribi?</h2>

          <div className="grid md:grid-cols-4 gap-8">
            {trustPoints.map((point, index) => (
              <div key={index} className="text-center">
                <div className="text-5xl font-bold mb-2 opacity-80">{point.label}</div>
                <p className="text-white/90">{point.value}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="py-20 sm:py-32 bg-slate-50 dark:bg-slate-900/50">
        <div className="container-max text-center">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 text-gray-900 dark:text-white">Ready to Travel Connected?</h2>
          <p className="text-lg text-gray-700 dark:text-gray-300 max-w-2xl mx-auto mb-8">
            Join thousands of travelers who&apos;ve already ditched expensive roaming plans
          </p>
          <button className="px-10 py-4 bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 text-white rounded-lg font-semibold transition-all shadow-lg hover:shadow-xl hover:scale-105 active:scale-95">
            Explore Plans Now
          </button>
        </div>
      </section>
    </main>
  )
}