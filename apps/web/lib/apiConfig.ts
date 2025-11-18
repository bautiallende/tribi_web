/**
 * Shared API configuration for all web API calls
 * Ensures consistent API_BASE usage across the application
 */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") ||
  "http://localhost:8000";

/**
 * Build a full API URL from a path
 * @param path - API path (with or without leading slash)
 * @returns Full URL to the backend API endpoint
 */
export const apiUrl = (path: string): string =>
  `${API_BASE}${path.startsWith("/") ? path : "/" + path}`;

/**
 * Fetch wrapper with improved error handling for JSON responses
 * @param url - Full URL or path (will be converted to full URL if path)
 * @param options - Fetch options
 * @returns Response data as JSON
 */
export async function apiFetch<T = any>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const fullUrl = url.startsWith("http") ? url : apiUrl(url);

  console.log(`🌐 API Request: ${options?.method || "GET"} ${fullUrl}`);

  const response = await fetch(fullUrl, {
    ...options,
    credentials: options?.credentials || "include",
  });

  const contentType = response.headers.get("content-type") || "";
  const text = await response.text();

  // Log response for debugging
  console.log(`📥 API Response: ${response.status} ${response.statusText}`);
  console.log(`📄 Content-Type: ${contentType}`);

  if (!response.ok) {
    console.error(`❌ API Error ${response.status}:`, text.slice(0, 500));

    // Try to parse as JSON for error details
    if (contentType.includes("application/json")) {
      try {
        const errorData = JSON.parse(text);
        throw new Error(
          errorData.detail ||
            errorData.message ||
            `Request failed: ${response.status}`
        );
      } catch (parseError) {
        throw new Error(
          `Request failed: ${response.status} ${response.statusText}`
        );
      }
    }

    throw new Error(
      `Request failed: ${response.status} ${response.statusText}`
    );
  }

  // Ensure we got JSON back
  if (!contentType.includes("application/json")) {
    console.error("❌ Expected JSON but got:", contentType);
    console.error("Response text (first 200 chars):", text.slice(0, 200));
    throw new Error(`Expected JSON response but got ${contentType}`);
  }

  try {
    const data = JSON.parse(text);
    console.log(`✅ API Success:`, data);
    return data;
  } catch (parseError) {
    console.error("❌ Failed to parse JSON:", parseError);
    console.error("Response text:", text.slice(0, 500));
    throw new Error("Failed to parse response as JSON");
  }
}
