"use client";

import Link from "next/link";

export default function AdminDashboard() {
  return (
    <div>
      <h2 className="mb-8 text-3xl font-bold text-gray-900">Dashboard</h2>
      
      <div className="grid gap-6 md:grid-cols-3">
        {/* Countries Card */}
        <Link
          href="/admin/countries"
          className="group block rounded-lg border border-gray-200 bg-white p-6 shadow-sm transition hover:border-blue-500 hover:shadow-md"
        >
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-xl font-semibold text-gray-900">Countries</h3>
            <svg
              className="h-8 w-8 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <p className="text-gray-600">
            Manage countries and their ISO2 codes
          </p>
          <div className="mt-4 flex items-center text-sm font-medium text-blue-600 group-hover:text-blue-700">
            Manage
            <svg
              className="ml-2 h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5l7 7-7 7"
              />
            </svg>
          </div>
        </Link>

        {/* Carriers Card */}
        <Link
          href="/admin/carriers"
          className="group block rounded-lg border border-gray-200 bg-white p-6 shadow-sm transition hover:border-blue-500 hover:shadow-md"
        >
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-xl font-semibold text-gray-900">Carriers</h3>
            <svg
              className="h-8 w-8 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0"
              />
            </svg>
          </div>
          <p className="text-gray-600">
            Manage mobile network carriers
          </p>
          <div className="mt-4 flex items-center text-sm font-medium text-blue-600 group-hover:text-blue-700">
            Manage
            <svg
              className="ml-2 h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5l7 7-7 7"
              />
            </svg>
          </div>
        </Link>

        {/* Plans Card */}
        <Link
          href="/admin/plans"
          className="group block rounded-lg border border-gray-200 bg-white p-6 shadow-sm transition hover:border-blue-500 hover:shadow-md"
        >
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-xl font-semibold text-gray-900">Plans</h3>
            <svg
              className="h-8 w-8 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <p className="text-gray-600">
            Manage eSIM data plans and pricing
          </p>
          <div className="mt-4 flex items-center text-sm font-medium text-blue-600 group-hover:text-blue-700">
            Manage
            <svg
              className="ml-2 h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5l7 7-7 7"
              />
            </svg>
          </div>
        </Link>
      </div>

      {/* Quick Stats */}
      <div className="mt-12">
        <h3 className="mb-4 text-xl font-semibold text-gray-900">Quick Info</h3>
        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <p className="text-gray-600">
            Welcome to the Tribi Admin Panel. Use the sections above to manage
            catalog data.
          </p>
          <ul className="mt-4 space-y-2 text-sm text-gray-600">
            <li className="flex items-center">
              <svg
                className="mr-2 h-5 w-5 text-green-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
              All actions support search and pagination
            </li>
            <li className="flex items-center">
              <svg
                className="mr-2 h-5 w-5 text-green-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
              Changes are reflected immediately with optimistic updates
            </li>
            <li className="flex items-center">
              <svg
                className="mr-2 h-5 w-5 text-green-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
              Validation is enforced on both frontend and backend
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
