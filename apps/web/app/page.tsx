import Link from 'next/link'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold">Tribi</h1>
      <Link href="/health" className="mt-4 text-blue-500">
        Go to Health Page
      </Link>
    </main>
  )
}