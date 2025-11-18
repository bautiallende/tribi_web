"use client"

import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
    Skeleton,
} from "@tribi/ui"
import Link from "next/link"
import { useParams, useRouter } from "next/navigation"
import { useEffect, useMemo, useState } from "react"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000"

type PlanSnapshot = {
	name?: string
	description?: string
	data_gb?: number
	duration_days?: number
	price_minor_units?: number
	currency?: string
	country_name?: string
}

type EsimProfile = {
	id: number
	status: string
	activation_code?: string | null
	iccid?: string | null
	qr_payload?: string | null
	instructions?: string | null
	plan_snapshot?: PlanSnapshot | null
}

type Order = {
	id: number
	status: string
	currency: string
	amount_minor_units: number
	amount_major: string
	created_at: string
	plan_snapshot?: PlanSnapshot | null
	esim_profile?: EsimProfile | null
}

const statusStyles: Record<string, string> = {
	created: "bg-amber-100 text-amber-800 border border-amber-200",
	paid: "bg-emerald-100 text-emerald-800 border border-emerald-200",
	failed: "bg-rose-100 text-rose-800 border border-rose-200",
	refunded: "bg-slate-200 text-slate-700 border border-slate-300",
}

const formatDateTime = (value?: string) => {
	if (!value) {
		return "—"
	}
	const date = new Date(value)
	if (Number.isNaN(date.getTime())) {
		return value
	}
	return date.toLocaleString()
}

export default function OrderDetailPage() {
	const params = useParams()
	const router = useRouter()
	const orderIdParam = params?.orderId as string | undefined
	const orderId = orderIdParam ? Number(orderIdParam) : NaN

	const [token, setToken] = useState<string | null>(null)
	const [order, setOrder] = useState<Order | null>(null)
	const [isLoading, setIsLoading] = useState(true)
	const [error, setError] = useState<string | null>(null)
	const [isActivating, setIsActivating] = useState(false)
	const [activationMessage, setActivationMessage] = useState<string | null>(null)

	useEffect(() => {
		if (Number.isNaN(orderId)) {
			setError("Invalid order id provided")
			setIsLoading(false)
			return
		}

		const storedToken =
			typeof window !== "undefined" ? window.localStorage.getItem("auth_token") : null

		if (!storedToken) {
			router.push("/auth")
			return
		}

		setToken(storedToken)
	}, [orderId, router])

	useEffect(() => {
		const fetchOrder = async () => {
			if (!token || Number.isNaN(orderId)) {
				return
			}

			try {
				setIsLoading(true)
				setError(null)

				const response = await fetch(`${API_BASE}/api/orders/mine`, {
					headers: {
						Authorization: `Bearer ${token}`,
					},
				})

				if (!response.ok) {
					throw new Error("Unable to fetch orders for current user")
				}

				const orders: Order[] = await response.json()
				const found = orders.find((item) => item.id === orderId)

				if (!found) {
					setError("Order not found for your account")
					setOrder(null)
					return
				}

				setOrder(found)
			} catch (err) {
				const message = err instanceof Error ? err.message : "Unexpected error"
				setError(message)
			} finally {
				setIsLoading(false)
			}
		}

		fetchOrder()
	}, [token, orderId])

	const planSnapshot = useMemo(() => {
		return order?.plan_snapshot || order?.esim_profile?.plan_snapshot || null
	}, [order])

	const canActivateEsim = useMemo(() => {
		if (!order || order.status !== "paid") {
			return false
		}

		if (!order.esim_profile) {
			return true
		}

		return order.esim_profile.status === "pending_activation"
	}, [order])

	const handleActivateEsim = async () => {
		if (!token || !order) {
			return
		}

		if (!canActivateEsim) {
			setActivationMessage("Order must be paid before activating the eSIM")
			return
		}

		try {
			setIsActivating(true)
			setActivationMessage(null)

			const response = await fetch(`${API_BASE}/api/esims/activate`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
					Authorization: `Bearer ${token}`,
				},
				body: JSON.stringify({ order_id: order.id }),
			})

			if (!response.ok) {
				const payload = await response.json().catch(() => ({ detail: "Failed to activate" }))
				throw new Error(payload.detail || "Failed to activate eSIM")
			}

			const updatedEsim: EsimProfile = await response.json()
			setOrder((prev) => (prev ? { ...prev, esim_profile: updatedEsim } : prev))
			setActivationMessage("✅ eSIM activated successfully")
		} catch (err) {
			const message = err instanceof Error ? err.message : "Activation failed"
			setActivationMessage(message)
		} finally {
			setIsActivating(false)
		}
	}

	const renderStatusBadge = (status: string) => {
		const normalized = status?.toLowerCase()
		const style = statusStyles[normalized] || "bg-slate-100 text-slate-700"
		return (
			<span className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-semibold capitalize ${style}`}>
				{normalized || "unknown"}
			</span>
		)
	}

	return (
		<main className="min-h-screen bg-slate-50 dark:bg-slate-900">
			<div className="container-max py-10">
				<div className="mb-8 flex items-center gap-3 text-sm text-primary-600">
					<Link href="/" className="inline-flex items-center gap-2 hover:text-primary-700">
						<svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
						</svg>
						Home
					</Link>
					<span>/</span>
					<Link href="/plans" className="hover:text-primary-700">
						Plans
					</Link>
					<span>/</span>
					<span className="font-semibold text-primary-800">Order #{orderIdParam}</span>
				</div>

				<div className="space-y-8">
					{isLoading ? (
						<Card className="rounded-3xl border border-border bg-white p-8 shadow-sm">
							<Skeleton className="mb-6 h-10 w-1/3" />
							<Skeleton className="mb-4 h-6 w-1/2" />
							<Skeleton className="h-48 w-full" />
						</Card>
					) : error ? (
						<Card className="rounded-3xl border border-rose-200 bg-rose-50 p-8 text-rose-800">
							<CardHeader>
								<CardTitle className="text-2xl font-semibold">Unable to load order</CardTitle>
								<CardDescription className="text-rose-700">{error}</CardDescription>
							</CardHeader>
							<CardContent>
								<p className="text-sm text-rose-700">
									Double-check the order link or visit your <Link href="/account" className="font-semibold underline">account dashboard</Link> to choose a different order.
								</p>
							</CardContent>
						</Card>
					) : order ? (
						<>
							<Card className="rounded-3xl border border-border bg-white p-8 shadow-sm">
								<CardHeader className="space-y-3">
									<div className="flex flex-wrap items-center justify-between gap-4">
										<div>
											<p className="text-sm text-muted-foreground">Order ID</p>
											<CardTitle className="text-4xl font-bold text-foreground">#{order.id}</CardTitle>
										</div>
										{renderStatusBadge(order.status)}
									</div>
									<CardDescription className="text-base text-muted-foreground">
										Created on {formatDateTime(order.created_at)} • Total charged {order.amount_major} {order.currency}
									</CardDescription>
								</CardHeader>

								<CardContent className="grid gap-8 md:grid-cols-2">
									<div className="space-y-6">
										<div>
											<h3 className="text-lg font-semibold text-foreground">Plan Details</h3>
											{planSnapshot ? (
												<ul className="mt-4 space-y-3 text-sm text-muted-foreground">
													<li className="flex items-center justify-between border-b border-border pb-2">
														<span className="font-medium text-foreground">Plan</span>
														<span>{planSnapshot.name}</span>
													</li>
													<li className="flex items-center justify-between border-b border-border pb-2">
														<span className="font-medium text-foreground">Data</span>
														<span>
															{planSnapshot.data_gb ? `${planSnapshot.data_gb} GB` : "—"}
														</span>
													</li>
													<li className="flex items-center justify-between border-b border-border pb-2">
														<span className="font-medium text-foreground">Duration</span>
														<span>{planSnapshot.duration_days} days</span>
													</li>
													<li className="flex items-center justify-between">
														<span className="font-medium text-foreground">Destination</span>
														<span>{planSnapshot.country_name ?? "—"}</span>
													</li>
												</ul>
											) : (
												<p className="mt-2 text-sm text-muted-foreground">
													Plan snapshot is unavailable. Please contact support if this persists.
												</p>
											)}
										</div>

										<div>
											<h3 className="text-lg font-semibold text-foreground">Payment Summary</h3>
											<div className="mt-4 rounded-2xl border border-border bg-slate-50 p-4 text-sm">
												<div className="flex items-center justify-between">
													<span className="text-muted-foreground">Amount</span>
													<span className="text-lg font-semibold text-foreground">
														{order.amount_major} {order.currency}
													</span>
												</div>
												<div className="mt-2 flex items-center justify-between text-muted-foreground">
													<span>Minor units</span>
													<span>{order.amount_minor_units}</span>
												</div>
											</div>
										</div>
									</div>

									<div className="space-y-6">
										<div>
											<h3 className="text-lg font-semibold text-foreground">eSIM Status</h3>
											<div className="mt-4 rounded-2xl border border-border bg-slate-50 p-4">
												{order.esim_profile ? (
													<div className="space-y-3 text-sm">
														<div className="flex items-center justify-between">
															<span className="text-muted-foreground">Status</span>
															{renderStatusBadge(order.esim_profile.status)}
														</div>
														<div className="flex items-center justify-between">
															<span className="text-muted-foreground">Activation code</span>
															<span className="font-mono text-sm text-foreground">
																{order.esim_profile.activation_code || "—"}
															</span>
														</div>
														<div className="flex items-center justify-between">
															<span className="text-muted-foreground">ICCID</span>
															<span className="font-mono text-sm text-foreground">
																{order.esim_profile.iccid || "—"}
															</span>
														</div>
														{order.esim_profile.instructions && (
															<p className="rounded-xl bg-white/70 p-3 text-muted-foreground">
																{order.esim_profile.instructions}
															</p>
														)}
													</div>
												) : (
													<p className="text-sm text-muted-foreground">
														Your eSIM profile will be generated right after checkout.
													</p>
												)}

												<button
													onClick={handleActivateEsim}
													disabled={!canActivateEsim || isActivating}
													className="mt-6 w-full rounded-xl bg-primary-600 px-4 py-3 text-center text-sm font-semibold text-white transition hover:bg-primary-700 disabled:cursor-not-allowed disabled:bg-primary-300"
												>
													{isActivating ? "Activating..." : "Activate eSIM"}
												</button>
												{activationMessage && (
													<p className="mt-3 text-center text-sm text-muted-foreground">{activationMessage}</p>
												)}
											</div>
										</div>
									</div>
								</CardContent>

								<CardFooter className="flex flex-wrap items-center justify-between gap-4 border-t border-border pt-6 text-sm text-muted-foreground">
									<span>
										Need help with this order? Contact support with the reference <strong>#{order.id}</strong>.
									</span>
									<div className="flex gap-3">
										<Link
											href="/checkout"
											className="rounded-lg border border-border px-4 py-2 font-medium text-foreground hover:bg-slate-100"
										>
											Back to checkout
										</Link>
										<Link
											href="/account"
											className="rounded-lg bg-primary-600 px-4 py-2 font-medium text-white hover:bg-primary-700"
										>
											Go to dashboard
										</Link>
									</div>
								</CardFooter>
							</Card>
						</>
					) : null}
				</div>
			</div>
		</main>
	)
}
