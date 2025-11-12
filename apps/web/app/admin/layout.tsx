"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [isAuthorized, setIsAuthorized] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function checkAuth() {
      try {
        // Check if user is authenticated
        const response = await fetch("http://localhost:8000/auth/me", {
          credentials: "include",
        });

        if (!response.ok) {
          // Not authenticated - redirect to login
          router.push("/auth/login?redirect=/admin");
          return;
        }

        const user = await response.json();

        // Check if user is admin by trying to access admin endpoint
        const adminCheckResponse = await fetch(
          "http://localhost:8000/admin/countries?page=1&page_size=1",
          {
            credentials: "include",
          }
        );

        if (adminCheckResponse.status === 403) {
          // Authenticated but not admin
          setError("Access denied. Admin privileges required.");
          setIsAuthorized(false);
          return;
        }

        if (!adminCheckResponse.ok) {
          setError("Failed to verify admin access.");
          setIsAuthorized(false);
          return;
        }

        // User is admin
        setIsAuthorized(true);
      } catch (err) {
        console.error("Admin auth check error:", err);
        setError("Network error. Please try again.");
        setIsAuthorized(false);
      }
    }

    checkAuth();
  }, [router]);

  // Loading state
  if (isAuthorized === null) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="text-gray-600">Verifying admin access...</p>
        </div>
      </div>
    );
  }

  // Not authorized
  if (!isAuthorized) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="max-w-md rounded-lg bg-white p-8 shadow-lg">
          <div className="mb-4 flex justify-center">
            <svg
              className="h-16 w-16 text-red-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <h1 className="mb-2 text-center text-2xl font-bold text-gray-900">
            Access Denied
          </h1>
          <p className="mb-6 text-center text-gray-600">
            {error || "You do not have permission to access this area."}
          </p>
          <div className="flex gap-3">
            <button
              onClick={() => router.push("/")}
              className="flex-1 rounded-lg bg-gray-200 px-4 py-2 font-medium text-gray-700 hover:bg-gray-300"
            >
              Go Home
            </button>
            <button
              onClick={() => router.push("/auth/login")}
              className="flex-1 rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
            >
              Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Authorized - render admin interface
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="border-b bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
            <button
              onClick={() => router.push("/")}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Back to Site →
            </button>
          </div>
        </div>
      </div>
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {children}
      </div>
    </div>
  );
}
