'use client'

import { useEffect, useState } from 'react'

export default function Health() {
  const [status, setStatus] = useState('loading...')

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then((res) => res.json())
      .then((data) => setStatus(data.status))
      .catch(() => setStatus('error'))
  }, [])

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold">Backend Status</h1>
      <p className="mt-4">{status}</p>
    </main>
  )
}
