"use client";

import { apiUrl } from "@/lib/apiConfig";
import { Badge, Button, Select, Skeleton, useToast } from "@tribi/ui";
import { useCallback, useEffect, useMemo, useState } from "react";

interface AnalyticsTopPlan {
  plan_id: number | null;
  name: string | null;
  payments: number;
  revenue_minor_units: number;
  data_gb: number | null;
  duration_days: number | null;
}

interface AnalyticsOverviewResponse {
  total_signups: number;
  checkout_started: number;
  payments: number;
  activations: number;
  revenue_minor_units: number;
  conversion_rate: number;
  signup_to_payment: number;
  activation_rate: number;
  average_order_value_minor_units: number;
  top_plans: AnalyticsTopPlan[];
}

interface AnalyticsTimeseriesPoint {
  date: string;
  user_signup: number;
  checkout_started: number;
  payment_succeeded: number;
  esim_activated: number;
  revenue_minor_units: number;
}

interface AnalyticsTimeseriesResponse {
  points: AnalyticsTimeseriesPoint[];
}

interface AnalyticsProjectionResponse {
  revenue_next_days_minor_units: number;
  signups_next_days: number;
  avg_daily_revenue_minor_units: number;
  avg_daily_signups: number;
  growth_rate: number;
  notes?: string | null;
}

const eventFilters = [
  { label: "Signups", value: "user_signup" },
  { label: "Checkout", value: "checkout_started" },
  { label: "Payments", value: "payment_succeeded" },
  { label: "Activations", value: "esim_activated" },
];

const quickRanges = [
  { label: "Last 7 days", days: 7 },
  { label: "30 days", days: 30 },
  { label: "90 days", days: 90 },
];

const projectionWindowOptions = [7, 14, 30];
const projectionHorizonOptions = [7, 14, 21];

const defaultRangeDays = 30;

const getAuthHeaders = (): HeadersInit => {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("auth_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const toDateInput = (date: Date) => date.toISOString().slice(0, 10);

const floorDate = (daysAgo: number) => {
  const date = new Date();
  date.setDate(date.getDate() - daysAgo);
  return date;
};

const formatCurrency = (minor: number) => {
  const value = (minor || 0) / 100;
  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 2,
    }).format(value);
  } catch {
    return `$${value.toFixed(2)}`;
  }
};

const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

const formatDateLabel = (value: string) => {
  try {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
    }).format(new Date(value));
  } catch {
    return value;
  }
};

export default function AnalyticsDashboardPage() {
  const { showToast } = useToast();
  const [overview, setOverview] = useState<AnalyticsOverviewResponse | null>(
    null,
  );
  const [timeseries, setTimeseries] = useState<AnalyticsTimeseriesPoint[]>([]);
  const [projections, setProjections] =
    useState<AnalyticsProjectionResponse | null>(null);
  const [rangeStart, setRangeStart] = useState(() =>
    toDateInput(floorDate(defaultRangeDays - 1)),
  );
  const [rangeEnd, setRangeEnd] = useState(() => toDateInput(new Date()));
  const [selectedEvents, setSelectedEvents] = useState<string[]>([]);
  const [windowDays, setWindowDays] = useState(14);
  const [horizonDays, setHorizonDays] = useState(7);
  const [loadingMetrics, setLoadingMetrics] = useState(true);
  const [loadingProjections, setLoadingProjections] = useState(true);

  const toggleEvent = (value: string) => {
    setSelectedEvents((prev) =>
      prev.includes(value)
        ? prev.filter((item) => item !== value)
        : [...prev, value],
    );
  };

  const applyQuickRange = (days: number) => {
    setRangeStart(toDateInput(floorDate(days - 1)));
    setRangeEnd(toDateInput(new Date()));
  };

  const buildDateParam = (date: string, endOfDay = false) => {
    const suffix = endOfDay ? "T23:59:59.000Z" : "T00:00:00.000Z";
    return new Date(`${date}${suffix}`).toISOString();
  };

  const fetchAnalytics = useCallback(async () => {
    setLoadingMetrics(true);
    try {
      const params = new URLSearchParams({
        start_date: buildDateParam(rangeStart),
        end_date: buildDateParam(rangeEnd, true),
      });
      selectedEvents.forEach((event) => params.append("event_types", event));

      const [overviewRes, timeseriesRes] = await Promise.all([
        fetch(apiUrl(`/admin/analytics/overview?${params.toString()}`), {
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            ...getAuthHeaders(),
          },
        }),
        fetch(apiUrl(`/admin/analytics/timeseries?${params.toString()}`), {
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            ...getAuthHeaders(),
          },
        }),
      ]);

      if (!overviewRes.ok) {
        const error = await overviewRes.json().catch(() => ({}));
        throw new Error(error.detail || "Unable to load analytics overview");
      }

      if (!timeseriesRes.ok) {
        const error = await timeseriesRes.json().catch(() => ({}));
        throw new Error(error.detail || "Unable to load timeseries data");
      }

      const overviewData: AnalyticsOverviewResponse = await overviewRes.json();
      const timeseriesData: AnalyticsTimeseriesResponse =
        await timeseriesRes.json();
      setOverview(overviewData);
      setTimeseries(timeseriesData.points || []);
    } catch (error: any) {
      console.error(error);
      showToast(error.message || "Failed to load analytics", "error");
      setOverview(null);
      setTimeseries([]);
    } finally {
      setLoadingMetrics(false);
    }
  }, [rangeStart, rangeEnd, selectedEvents, showToast]);

  const fetchProjections = useCallback(async () => {
    setLoadingProjections(true);
    try {
      const params = new URLSearchParams({
        window_days: windowDays.toString(),
        horizon_days: horizonDays.toString(),
      });

      const response = await fetch(
        apiUrl(`/admin/analytics/projections?${params.toString()}`),
        {
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            ...getAuthHeaders(),
          },
        },
      );

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || "Unable to load projections");
      }

      const data: AnalyticsProjectionResponse = await response.json();
      setProjections(data);
    } catch (error: any) {
      console.error(error);
      showToast(error.message || "Failed to load projections", "error");
      setProjections(null);
    } finally {
      setLoadingProjections(false);
    }
  }, [windowDays, horizonDays, showToast]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  useEffect(() => {
    fetchProjections();
  }, [fetchProjections]);

  const maxRevenue = useMemo(() => {
    if (!timeseries.length) return 0;
    return Math.max(...timeseries.map((point) => point.revenue_minor_units));
  }, [timeseries]);

  const summaryCards = [
    {
      label: "Signups",
      value: overview?.total_signups ?? 0,
      description: "New users created",
    },
    {
      label: "Checkout",
      value: overview?.checkout_started ?? 0,
      description: "Orders initiated",
    },
    {
      label: "Payments",
      value: overview?.payments ?? 0,
      description:
        formatPercent(overview?.conversion_rate ?? 0) + " checkout → pay",
    },
    {
      label: "Activations",
      value: overview?.activations ?? 0,
      description:
        formatPercent(overview?.activation_rate ?? 0) + " payment → eSIM",
    },
    {
      label: "Revenue",
      value: formatCurrency(overview?.revenue_minor_units ?? 0),
      description: `AOV ${formatCurrency(
        overview?.average_order_value_minor_units ?? 0,
      )}`,
    },
  ];

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <p className="text-sm uppercase tracking-wide text-blue-600">
          Analytics
        </p>
        <h1 className="text-3xl font-bold text-gray-900">
          Funnel metrics & revenue projections
        </h1>
        <p className="text-gray-600">
          Monitor the full journey from signup to eSIM activation. Adjust the
          date range or focus on specific events to debug drops in conversion.
        </p>
      </header>

      <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Start date
            </label>
            <input
              type="date"
              value={rangeStart}
              onChange={(event) => setRangeStart(event.target.value)}
              className="mt-1 w-40 rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              End date
            </label>
            <input
              type="date"
              value={rangeEnd}
              max={toDateInput(new Date())}
              onChange={(event) => setRangeEnd(event.target.value)}
              className="mt-1 w-40 rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none"
            />
          </div>
          <div className="flex flex-wrap items-end gap-2">
            {quickRanges.map((range) => (
              <Button
                key={range.days}
                onClick={() => applyQuickRange(range.days)}
                className="rounded-full border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 transition hover:border-blue-500 hover:text-blue-600"
              >
                {range.label}
              </Button>
            ))}
          </div>
        </div>

        <div className="mt-6">
          <p className="text-sm font-medium text-gray-700">Event filters</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {eventFilters.map((event) => {
              const active = selectedEvents.includes(event.value);
              return (
                <button
                  key={event.value}
                  onClick={() => toggleEvent(event.value)}
                  className={`rounded-full border px-3 py-1 text-sm font-medium transition ${
                    active
                      ? "border-blue-500 bg-blue-50 text-blue-600"
                      : "border-gray-200 text-gray-600 hover:border-blue-200"
                  }`}
                >
                  {event.label}
                  {active && <span className="ml-1">×</span>}
                </button>
              );
            })}
            {!selectedEvents.length && (
              <Badge variant="outline" className="text-gray-500">
                Showing all events
              </Badge>
            )}
          </div>
        </div>
      </section>

      <section>
        {loadingMetrics ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            {Array.from({ length: 5 }).map((_, index) => (
              <Skeleton key={index} className="h-32 w-full" />
            ))}
          </div>
        ) : overview ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            {summaryCards.map((card) => (
              <div
                key={card.label}
                className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm"
              >
                <p className="text-sm font-medium text-gray-500">
                  {card.label}
                </p>
                <p className="mt-2 text-3xl font-bold text-gray-900">
                  {card.value}
                </p>
                <p className="mt-1 text-sm text-gray-500">{card.description}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-gray-300 bg-white p-8 text-center text-gray-500">
            No analytics found for the selected window.
          </div>
        )}
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm lg:col-span-2">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                Revenue trend
              </h2>
              <p className="text-sm text-gray-500">
                Daily revenue stacked by the selected range
              </p>
            </div>
            <Badge variant="primary">
              {timeseries.length} {timeseries.length === 1 ? "day" : "days"}
            </Badge>
          </div>
          {loadingMetrics ? (
            <Skeleton className="mt-6 h-64 w-full" />
          ) : timeseries.length ? (
            <div className="mt-6 flex h-64 items-end gap-2 overflow-x-auto">
              {timeseries.map((point) => {
                const height = maxRevenue
                  ? Math.max(4, (point.revenue_minor_units / maxRevenue) * 100)
                  : 4;
                return (
                  <div
                    key={point.date}
                    className="flex flex-col items-center text-xs text-gray-500"
                  >
                    <div className="flex h-48 w-4 items-end">
                      <div
                        className="w-full rounded-full bg-gradient-to-t from-blue-600 via-blue-400 to-blue-200"
                        style={{ height: `${height}%` }}
                      />
                    </div>
                    <span className="mt-2 font-medium text-gray-800">
                      {formatCurrency(point.revenue_minor_units)}
                    </span>
                    <span>{formatDateLabel(point.date)}</span>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="mt-4 text-sm text-gray-500">
              Waiting for revenue data in the selected window.
            </p>
          )}
          {!loadingMetrics && timeseries.length > 0 && (
            <div className="mt-6 overflow-auto">
              <table className="min-w-full text-left text-sm">
                <thead>
                  <tr className="text-gray-500">
                    <th className="pb-2">Date</th>
                    <th className="pb-2">Signups</th>
                    <th className="pb-2">Checkout</th>
                    <th className="pb-2">Payments</th>
                    <th className="pb-2">Activations</th>
                    <th className="pb-2">Revenue</th>
                  </tr>
                </thead>
                <tbody>
                  {timeseries.map((point) => (
                    <tr
                      key={`row-${point.date}`}
                      className="border-t text-gray-800"
                    >
                      <td className="py-2">{formatDateLabel(point.date)}</td>
                      <td>{point.user_signup}</td>
                      <td>{point.checkout_started}</td>
                      <td>{point.payment_succeeded}</td>
                      <td>{point.esim_activated}</td>
                      <td>{formatCurrency(point.revenue_minor_units)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                Next-week outlook
              </h2>
              <p className="text-sm text-gray-500">
                Moving average projections
              </p>
            </div>
            <Badge variant="outline">Beta</Badge>
          </div>

          <div className="mt-4 space-y-4 text-sm">
            <label className="block text-gray-600">Historical window</label>
            <Select
              value={windowDays.toString()}
              onChange={(event) => setWindowDays(Number(event.target.value))}
            >
              {projectionWindowOptions.map((value) => (
                <option value={value} key={`window-${value}`}>
                  {value} days
                </option>
              ))}
            </Select>
            <label className="block text-gray-600">Projection horizon</label>
            <Select
              value={horizonDays.toString()}
              onChange={(event) => setHorizonDays(Number(event.target.value))}
            >
              {projectionHorizonOptions.map((value) => (
                <option value={value} key={`horizon-${value}`}>
                  Next {value} days
                </option>
              ))}
            </Select>
          </div>

          {loadingProjections ? (
            <Skeleton className="mt-6 h-40 w-full" />
          ) : projections ? (
            <div className="mt-6 space-y-3">
              <div>
                <p className="text-sm text-gray-500">Forecast revenue</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {formatCurrency(projections.revenue_next_days_minor_units)}
                </p>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Projected signups</p>
                  <p className="text-xl font-semibold text-gray-900">
                    {Math.round(projections.signups_next_days)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">Growth vs. first day</p>
                  <p
                    className={`text-xl font-semibold ${
                      projections.growth_rate >= 0
                        ? "text-green-600"
                        : "text-red-600"
                    }`}
                  >
                    {formatPercent(projections.growth_rate)}
                  </p>
                </div>
              </div>
              <div className="rounded-lg bg-gray-50 p-3 text-sm text-gray-600">
                {projections.notes ||
                  "Moving average across the selected window."}
              </div>
            </div>
          ) : (
            <p className="mt-6 text-sm text-gray-500">
              Not enough historical data to compute projections.
            </p>
          )}
        </div>
      </section>

      <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Top performing plans
            </h2>
            <p className="text-sm text-gray-500">
              Sorted by revenue this window
            </p>
          </div>
          {overview?.top_plans?.length ? (
            <Badge variant="primary">{overview.top_plans.length} plans</Badge>
          ) : null}
        </div>
        {loadingMetrics ? (
          <Skeleton className="mt-6 h-32 w-full" />
        ) : overview?.top_plans?.length ? (
          <div className="mt-6 overflow-auto">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="text-gray-500">
                  <th className="pb-2">Plan</th>
                  <th className="pb-2">Payments</th>
                  <th className="pb-2">Revenue</th>
                  <th className="pb-2">Data</th>
                  <th className="pb-2">Duration</th>
                </tr>
              </thead>
              <tbody>
                {overview.top_plans.map((plan) => (
                  <tr
                    key={`plan-${plan.plan_id}`}
                    className="border-t text-gray-800"
                  >
                    <td className="py-2 font-medium">
                      {plan.name || `Plan #${plan.plan_id ?? "N/A"}`}
                    </td>
                    <td>{plan.payments}</td>
                    <td>{formatCurrency(plan.revenue_minor_units)}</td>
                    <td>{plan.data_gb ? `${plan.data_gb} GB` : "—"}</td>
                    <td>
                      {plan.duration_days ? `${plan.duration_days} days` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="mt-6 text-sm text-gray-500">
            No paid orders were recorded for the selected window.
          </p>
        )}
      </section>
    </div>
  );
}
