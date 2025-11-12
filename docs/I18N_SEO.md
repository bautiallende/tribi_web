# I18n and SEO Implementation Guide

## Overview

This document describes the internationalization (i18n) and SEO implementation for the Tribi web application using Next.js 14 App Router with `next-intl` and modern metadata APIs.

## Architecture

### i18n System

We use `next-intl` for i18n, which is optimized for Next.js App Router:

- **Locales**: English (`en`) and Spanish (`es`)
- **Storage**: Cookie-based (`NEXT_LOCALE` cookie with 1-year expiry)
- **Namespaces**: `common`, `home`, `plans`, `admin`
- **Server Components**: Translations loaded on the server for optimal performance

### File Structure

```
apps/web/
├── i18n/
│   └── config.ts              # next-intl configuration
├── locales/
│   ├── en/
│   │   ├── common.json        # Shared translations
│   │   ├── home.json          # Home page translations
│   │   ├── plans.json         # Plans page translations
│   │   └── admin.json         # Admin panel translations
│   └── es/
│       ├── common.json
│       ├── home.json
│       ├── plans.json
│       └── admin.json
├── components/
│   └── LanguageSwitcher.tsx   # Language toggle component
├── lib/
│   └── format.ts              # Locale-aware formatting utilities
├── middleware.ts              # Sets locale cookie
└── next.config.js             # next-intl plugin configuration
```

## Usage

### Using Translations in Components

#### Client Components

```tsx
'use client';

import { useTranslations } from 'next-intl';

export function MyComponent() {
  const t = useTranslations('common');
  
  return (
    <div>
      <h1>{t('welcome')}</h1>
      <button>{t('save')}</button>
    </div>
  );
}
```

#### Server Components

```tsx
import { useTranslations } from 'next-intl';
import { getTranslations } from 'next-intl/server';

export default async function Page() {
  const t = await getTranslations('home');
  
  return (
    <div>
      <h1>{t('hero.title')}</h1>
      <p>{t('hero.subtitle')}</p>
    </div>
  );
}
```

### Accessing Current Locale

```tsx
import { useLocale } from 'next-intl';

export function MyComponent() {
  const locale = useLocale(); // 'en' or 'es'
  
  // Use locale for conditional logic
  return <div>Current locale: {locale}</div>;
}
```

### Price Formatting

Use the `formatPrice` utility for locale-aware currency formatting:

```tsx
import { formatPrice } from '@/lib/format';
import { useLocale } from 'next-intl';

export function PriceDisplay({ amount }: { amount: number }) {
  const locale = useLocale();
  
  return <span>{formatPrice(amount, locale)}</span>;
  // en: "$19.99"
  // es: "$19.99" (USD format for Spanish)
}
```

### Data and Duration Formatting

```tsx
import { formatData, formatDuration } from '@/lib/format';
import { useLocale } from 'next-intl';

export function PlanDetails({ dataGB, days }: { dataGB: number; days: number }) {
  const locale = useLocale();
  
  return (
    <div>
      <p>Data: {formatData(dataGB, locale)}</p>
      <p>Duration: {formatDuration(days, locale)}</p>
    </div>
  );
}
```

## Namespace Structure

### `common.json`
Shared UI elements and common actions:
- Navigation labels
- Button labels (save, cancel, delete, edit)
- State messages (loading, error, success)
- Pagination controls

### `home.json`
Homepage content:
- Hero section
- Features list
- How it works steps

### `plans.json`
Plans page content:
- Search and filter labels
- Plan details
- Empty states
- Error messages

### `admin.json`
Admin panel content:
- Dashboard labels
- CRUD operations
- Form labels
- Success/error messages

## SEO Implementation

### Metadata API

We use Next.js 14 Metadata API for comprehensive SEO:

#### Root Layout (`app/layout.tsx`)

```tsx
export const metadata: Metadata = {
  metadataBase: new URL('https://tribi.app'),
  title: {
    default: "Tribi - Global eSIM for Travelers",
    template: "%s | Tribi"
  },
  description: "Stay connected worldwide...",
  openGraph: { /* OG tags */ },
  twitter: { /* Twitter cards */ },
  robots: { /* Crawler directives */ },
};
```

#### Page-Specific Metadata

```tsx
// app/plans/[iso2]/page.tsx
export async function generateMetadata({ params }): Promise<Metadata> {
  const country = await getCountry(params.iso2);
  
  return {
    title: `eSIM Plans for ${country.name}`,
    description: `Get affordable eSIM data plans for ${country.name}`,
    openGraph: {
      title: `${country.name} eSIM Plans`,
      images: [`/og/${country.iso2}.png`],
    },
  };
}
```

### robots.txt

Located at `app/robots.ts`:

```typescript
export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: ['/admin/', '/api/', '/account/'],
      },
    ],
    sitemap: 'https://tribi.app/sitemap.xml',
  };
}
```

- **Allow**: All public pages
- **Disallow**: Admin panel, API routes, user accounts

### sitemap.xml

Located at `app/sitemap.ts`:

```typescript
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const routes = ['', '/plans', '/auth'].map((route) => ({
    url: `https://tribi.app${route}`,
    lastModified: new Date().toISOString(),
    changeFrequency: 'daily',
    priority: route === '' ? 1.0 : 0.8,
  }));
  
  return routes;
}
```

### OpenGraph Images

Create OG images at:
- `/public/og-image.png` (default, 1200x630)
- `/public/og/[country-code].png` (country-specific)

## Accessibility

### Language Switcher

The `LanguageSwitcher` component includes:
- `aria-label` for screen readers
- `<label htmlFor>` for the select element
- `sr-only` class for visually hidden label
- `disabled` state with visual feedback
- Focus visible styles with `focus:ring-2`

```tsx
<label htmlFor="language-select" className="sr-only">
  {t('language')}
</label>
<select
  id="language-select"
  aria-label={t('language')}
  className="focus:outline-none focus:ring-2 focus:ring-indigo-500"
>
```

### Focus Styles

All interactive elements have visible focus indicators:

```css
focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent
```

### ARIA Labels

Add `aria-label` to icon buttons and inputs:

```tsx
<button aria-label="Toggle dark mode">
  <svg>...</svg>
</button>

<input aria-label="Search plans" placeholder="Search..." />
```

## Adding New Translations

### 1. Add to Translation Files

```json
// locales/en/plans.json
{
  "newFeature": {
    "title": "New Feature",
    "description": "Description text"
  }
}

// locales/es/plans.json
{
  "newFeature": {
    "title": "Nueva Funcionalidad",
    "description": "Texto descriptivo"
  }
}
```

### 2. Use in Component

```tsx
const t = useTranslations('plans');

return (
  <div>
    <h2>{t('newFeature.title')}</h2>
    <p>{t('newFeature.description')}</p>
  </div>
);
```

## Best Practices

### i18n

1. **Use Namespaces**: Organize translations by feature/page
2. **Nest Keys**: Use dot notation for hierarchical structure
3. **Complete Translations**: Ensure all keys exist in all locales
4. **Avoid Hardcoded Strings**: Extract all user-visible text
5. **Server Components**: Use `getTranslations()` for server components
6. **Client Components**: Use `useTranslations()` hook

### SEO

1. **Unique Titles**: Each page should have a unique title
2. **Meta Descriptions**: 150-160 characters, include key terms
3. **Structured Data**: Add JSON-LD for rich results (future)
4. **Image Alt Text**: Describe images for accessibility and SEO
5. **Semantic HTML**: Use `<h1>`, `<h2>`, etc. properly
6. **Internal Linking**: Link related content

### Performance

1. **Server Components**: Use for static content
2. **Dynamic Imports**: Lazy load translation namespaces if needed
3. **Cookie Storage**: Faster than client-side detection
4. **Static Generation**: Pre-render pages at build time

## Locale Detection Flow

```
1. User visits site
   ↓
2. Middleware checks NEXT_LOCALE cookie
   ↓
3. If cookie exists → use that locale
   If not → set default ('en') and create cookie
   ↓
4. Layout loads translations for current locale
   ↓
5. User changes language → Update cookie → Reload page
```

## Testing

### Manual Testing Checklist

- [ ] Language switcher works and persists
- [ ] All pages load in both languages
- [ ] Currency formatting displays correctly
- [ ] No untranslated strings visible
- [ ] Meta tags present in page source
- [ ] robots.txt accessible at `/robots.txt`
- [ ] sitemap.xml accessible at `/sitemap.xml`
- [ ] Focus indicators visible on all interactive elements
- [ ] Screen reader announces language selection

### TypeScript Type Checking

```bash
cd apps/web
npm run typecheck
```

### Build Test

```bash
cd apps/web
npm run build
```

## Troubleshooting

### Translations Not Loading

- Check cookie is set: DevTools → Application → Cookies
- Verify JSON syntax in locale files
- Ensure `i18n/config.ts` imports correct files
- Check middleware is running (no errors in console)

### Metadata Not Showing

- View page source (`Ctrl+U`) to verify tags
- Check `metadataBase` is set in root layout
- For dynamic pages, verify `generateMetadata` exports

### Build Errors

- Run `npm run typecheck` to find type errors
- Ensure all JSON files have valid syntax
- Check all imports resolve correctly

## Future Enhancements

- [ ] Add more locales (French, German, Portuguese)
- [ ] Implement URL-based locale routing (`/es/planes`)
- [ ] Add JSON-LD structured data for plans
- [ ] Generate dynamic OG images per country
- [ ] Implement locale-based currency (EUR, GBP, etc.)
- [ ] Add language auto-detection based on browser
- [ ] Create translation management workflow
- [ ] Add pluralization support for counts

## Resources

- [next-intl Documentation](https://next-intl-docs.vercel.app/)
- [Next.js Metadata API](https://nextjs.org/docs/app/building-your-application/optimizing/metadata)
- [Web Accessibility Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [OpenGraph Protocol](https://ogp.me/)
- [Schema.org](https://schema.org/)
