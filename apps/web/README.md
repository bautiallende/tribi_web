# Tribi Web App

Modern, vibrant eSIM marketplace built with Next.js 14, TypeScript, Tailwind CSS, and Shadcn components.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ (recommended 20.x)
- npm or yarn
- Environment variables set (see `.env.example`)

### Installation

```bash
# Install dependencies
npm install

# Set environment variables
cat > .env.local << EOF
NEXT_PUBLIC_API_BASE=http://localhost:8000
EOF

# Run development server
npm run dev

# Open browser
open http://localhost:3000
```

### Build for Production

```bash
# Type check
npm run typecheck

# Lint code
npm run lint

# Build
npm run build

# Start server
npm start
```

## 📁 Project Structure

```
apps/web/
├── app/                    # Next.js 14 App Router
│   ├── page.tsx           # Home page (hero + country picker)
│   ├── layout.tsx         # Global layout with Navbar + Footer
│   ├── globals.css        # Global styles & design tokens
│   ├── auth/              # Authentication pages
│   ├── account/           # User profile & orders
│   ├── checkout/          # Payment & eSIM activation
│   ├── plans/[iso2]/      # Dynamic plans page with filters
│   └── health/            # Health check endpoint
├── components/            # Reusable React components
│   ├── Navbar.tsx        # Navigation with dark mode toggle
│   ├── Footer.tsx        # Footer with links & social
│   └── CountryPicker.tsx # Autocomplete country selector
├── next.config.js        # Next.js configuration
├── tailwind.config.ts    # Tailwind CSS configuration
├── tsconfig.json         # TypeScript configuration
├── package.json          # Dependencies & scripts
└── README.md            # This file
```

## 🎨 Design System

See `docs/STYLEGUIDE.md` for comprehensive design documentation including:

- **Color Palette**: Primary (Blue→Purple), Accent (Green→Teal)
- **Typography**: Inter (body), Plus Jakarta Sans (headings)
- **Components**: Button, Card, Badge, Input, Select, Skeleton
- **Layout Patterns**: Container, Glass morphism, Gradients
- **Animations**: Fade in, Slide up, Pulse glow, Float
- **Dark Mode**: CSS classes and hooks
- **Accessibility**: WCAG AA compliant

### Quick Design Reference

```tsx
// Colors
className="text-primary-600 bg-accent-100 dark:bg-accent-900"

// Spacing & Radius
className="p-6 rounded-2xl"

// Typography
className="text-5xl md:text-7xl font-bold"  // Hero title
className="text-base text-muted-foreground"  // Body

// Components
import { Button, Card, Badge, Input, Select, Skeleton } from '@tribi/ui'

// Layout
className="container-max"  // Max width container with padding
className="glass"          // Glassmorphism effect

// Gradients
className="gradient-text"  // Primary → Accent gradient text
className="bg-gradient-to-r from-primary-600 to-accent-600"

// Dark mode
className="dark:bg-slate-900 dark:text-white"
```

## 🔑 Environment Variables

```bash
# API Configuration
NEXT_PUBLIC_API_BASE=http://localhost:8000  # Backend API URL

# Optional - for production builds
NEXT_PUBLIC_APP_URL=https://tribi.app
```

## 📱 Pages & Features

### 🏠 Home (/)

- **Hero Section**: Brand messaging with gradient text
- **Country Picker**: Autocomplete search with icons
- **How It Works**: 3-step process explanation
- **Trusted Carriers**: Partner logos grid
- **Social Proof**: Stats about Tribi
- **CTAs**: Multiple conversion points

### 🔐 Auth (/auth)

- **OTP-based Login**: Email → Code verification
- **2-step Flow**: Request code, then verify
- **JWT Storage**: Token saved to localStorage (future: httpOnly)
- **Error Handling**: User-friendly messages
- **Auto-redirect**: To /account on success

### 👤 Account (/account)

- **Profile Display**: Current user information
- **Order Management**: List of past orders with status
- **eSIM Codes**: Activation codes with copy button
- **Logout**: Clear token and redirect

### 🛒 Plans (/plans/[iso2])

- **Dynamic Routes**: One page per country
- **Grid Layout**: Responsive card layout
- **Filters Sidebar**:
  - Price range slider
  - Data volume slider
  - Minimum days input
  - Sort options (price, data)
- **Loading States**: Skeleton cards while fetching
- **Empty State**: Friendly message when no results
- **Plan Cards**: Show price, data, duration with badges

### 💳 Checkout (/checkout?order_id=123)

- **Order Review**: Summary of selected plan
- **MOCK Payment**: Instant payment simulation
- **eSIM Activation**: Generate activation code
- **Success Flow**: Display code with copy button
- **Error Handling**: Validation if order not ready

## 🧪 Testing

### Run Type Checker

```bash
npm run typecheck
```

### Run Linter

```bash
npm run lint
```

### E2E Tests (Playwright)

```bash
# Install Playwright (one-time)
npm install -D @playwright/test

# Run tests
npx playwright test

# Run in headed mode (see browser)
npx playwright test --headed

# Run specific test file
npx playwright test e2e/home.spec.ts
```

### E2E Test Examples

**Home → Plans Flow:**
```typescript
test('user can search country and view plans', async ({ page }) => {
  await page.goto('/')
  await page.fill('[placeholder="Search for a country"]', 'Spain')
  await page.click('text=Spain')
  await expect(page).toHaveURL('/plans/es')
  await expect(page.locator('[data-testid="plan-card"]')).toHaveCount(expect.any(Number))
})
```

**Plans → Filter Flow:**
```typescript
test('user can filter plans by price', async ({ page }) => {
  await page.goto('/plans/es')
  await page.fill('input[name="maxPrice"]', '15')
  const cards = page.locator('[data-testid="plan-card"]')
  const count = await cards.count()
  expect(count).toBeLessThan(10)
})
```

## 🚀 Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard
NEXT_PUBLIC_API_BASE=https://api.tribi.app
```

### Docker

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY . .
RUN npm ci && npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

```bash
docker build -t tribi-web .
docker run -p 3000:3000 tribi-web
```

## 📊 Performance Targets

- **Lighthouse Score**: ≥ 90 (Performance, Best Practices, SEO)
- **First Contentful Paint (FCP)**: < 1.5s
- **Largest Contentful Paint (LCP)**: < 2.5s
- **Cumulative Layout Shift (CLS)**: < 0.1
- **Core Web Vitals**: All green

### Optimization Tips

1. **Image Optimization**: Use `next/image`
```tsx
import Image from 'next/image'
<Image src="..." alt="..." width={400} height={300} />
```

2. **Code Splitting**: Use dynamic imports
```tsx
import dynamic from 'next/dynamic'
const Component = dynamic(() => import('./Component'))
```

3. **Prefetching**: Links prefetch automatically
```tsx
<Link href="/plans/es" prefetch>Plans</Link>
```

4. **Lazy Loading**: Lazyload images and sections
```tsx
<img src="..." loading="lazy" />
```

## 🎯 Development Commands

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Type check
npm run typecheck

# Lint code
npm run lint

# Format code (if configured)
npm run format

# Clean build artifacts
npm run clean
```

## 🔗 API Integration

### Base URL

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'
```

### Endpoints Used

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/countries` | GET | List all countries |
| `/api/plans?country={iso2}` | GET | Get plans for country |
| `/auth/request-code` | POST | Request OTP code |
| `/auth/verify` | POST | Verify OTP code |
| `/auth/me` | GET | Get current user |
| `/orders` | POST | Create order |
| `/orders/mine` | GET | Get user's orders |
| `/payments/create` | POST | Create payment |
| `/esims/activate` | POST | Activate eSIM |

### Example: Fetch Plans

```typescript
const response = await fetch(`${API_BASE}/api/plans?country=es`, {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
  },
})
const plans = await response.json()
```

### Example: Create Order

```typescript
const response = await fetch(`${API_BASE}/orders`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  },
  body: JSON.stringify({
    plan_id: 1,
    currency: 'USD',
  }),
})
const order = await response.json()
```

## 🐛 Debugging

### Enable Verbose Logging

```typescript
// In browser console
localStorage.setItem('DEBUG', '*')
```

### Check Network Requests

1. Open DevTools (F12)
2. Go to Network tab
3. Perform action
4. Check request headers and response

### Debug Middleware

```bash
# Set debug environment
DEBUG=* npm run dev
```

### TypeScript Errors

```bash
npm run typecheck
```

## 📚 Documentation

- **Design System**: See `docs/STYLEGUIDE.md`
- **Architecture**: See `docs/ARCHITECTURE.md`
- **Testing Guide**: See `docs/TESTING.md`
- **API Examples**: See `docs/API_EXAMPLES.md`

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and test locally
3. Run linter: `npm run lint`
4. Run typecheck: `npm run typecheck`
5. Commit: `git commit -am 'feat: add my feature'`
6. Push: `git push origin feature/my-feature`
7. Open PR and wait for review

### Commit Convention

```
feat: add new feature
fix: fix bug
docs: update documentation
style: formatting changes
refactor: code reorganization
test: add tests
chore: maintenance
```

## 📄 License

MIT

## 👥 Support

For issues or questions:
1. Check existing issues on GitHub
2. Create new issue with detailed description
3. Include steps to reproduce
4. Attach screenshots if applicable

---

**Version**: 1.0.0  
**Last Updated**: November 12, 2025  
**Maintainer**: Frontend Team
