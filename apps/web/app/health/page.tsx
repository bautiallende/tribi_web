async function getHealth() {
  const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/health`)
  // The return value is *not* serialized
  // You can return Date, Map, Set, etc.
 
  if (!res.ok) {
    // This will activate the closest `error.js` Error Boundary
    throw new Error('Failed to fetch data')
  }
 
  return res.json()
}
 
export default async function HealthPage() {
  const data = await getHealth()
 
  return (
    <main>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </main>
  )
}
