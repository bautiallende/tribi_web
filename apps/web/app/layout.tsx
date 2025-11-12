import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

export const metadata: Metadata = {
  title: "Tribi - eSIM for Travelers",
  description: "Get connected worldwide with Tribi eSIM. Fast, secure, and affordable data plans for tourists.",
  keywords: "eSIM, travel, data, connectivity",
  openGraph: {
    title: "Tribi - eSIM for Travelers",
    description: "Get connected worldwide with Tribi eSIM",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta name="theme-color" content="#3b82f6" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect fill='%233b82f6' width='32' height='32' rx='4'/><text x='50%' y='50%' font-size='18' font-weight='bold' fill='white' text-anchor='middle' dominant-baseline='middle'>T</text></svg>" />
      </head>
      <body className="bg-white dark:bg-slate-950 text-foreground">
        <Navbar />
        <main className="min-h-screen">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}

