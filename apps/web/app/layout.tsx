import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import {NextIntlClientProvider} from 'next-intl';
import {getLocale, getMessages} from 'next-intl/server';

export const metadata: Metadata = {
  metadataBase: new URL('https://tribi.app'),
  title: {
    default: "Tribi - Global eSIM for Travelers",
    template: "%s | Tribi"
  },
  description: "Stay connected worldwide with instant eSIM activation. No roaming fees, no SIM swaps. Get affordable data plans for 150+ countries.",
  keywords: ["eSIM", "travel", "data", "connectivity", "roaming", "international", "mobile data", "travelers"],
  authors: [{ name: "Tribi" }],
  creator: "Tribi",
  publisher: "Tribi",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  openGraph: {
    title: "Tribi - Global eSIM for Travelers",
    description: "Stay connected worldwide with instant eSIM activation. No roaming fees, no SIM swaps.",
    url: "https://tribi.app",
    siteName: "Tribi",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Tribi eSIM",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Tribi - Global eSIM for Travelers",
    description: "Stay connected worldwide with instant eSIM activation",
    images: ["/og-image.png"],
    creator: "@tribi",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    google: "google-site-verification-code",
    yandex: "yandex-verification-code",
  },
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const locale = await getLocale();
  const messages = await getMessages();

  return (
    <html lang={locale} suppressHydrationWarning>
      <head>
        <meta name="theme-color" content="#3b82f6" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect fill='%233b82f6' width='32' height='32' rx='4'/><text x='50%' y='50%' font-size='18' font-weight='bold' fill='white' text-anchor='middle' dominant-baseline='middle'>T</text></svg>" />
      </head>
      <body className="bg-white dark:bg-slate-950 text-foreground">
        <NextIntlClientProvider messages={messages}>
          <Navbar />
          <main className="min-h-screen">
            {children}
          </main>
          <Footer />
        </NextIntlClientProvider>
      </body>
    </html>
  );
}

