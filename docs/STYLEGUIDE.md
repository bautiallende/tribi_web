# Tribi Design System & Style Guide

## Overview

Tribi uses a modern, vibrant, and youth-oriented design system built with Tailwind CSS and custom design tokens. This guide documents our color palette, typography, components, and usage patterns.

## Design Philosophy

- **Modern**: Clean, minimalist interfaces with subtle animations
- **Vibrant**: Bold gradient colors that stand out
- **Youthful**: Fast-paced, energetic feel suitable for travelers
- **Accessible**: WCAG AA compliant, keyboard navigable, semantic HTML

---

## Color Palette

### Primary Colors (Blue → Purple Gradient)

Used for primary actions, focus states, and primary UI elements.

```
Primary-50:   hsl(240 100% 96%)   - Lightest background
Primary-100:  hsl(240 89% 94%)
Primary-200:  hsl(240 85% 89%)
Primary-300:  hsl(240 75% 80%)    - Hover states
Primary-400:  hsl(240 64% 69%)
Primary-500:  hsl(240 58% 52%)    - Main brand color ⭐
Primary-600:  hsl(240 72% 42%)    - Default button
Primary-700:  hsl(240 80% 32%)    - Hover button
Primary-800:  hsl(240 85% 22%)
Primary-900:  hsl(240 90% 12%)    - Darkest variant
```

**Usage:**
- Primary CTAs (buttons, links)
- Navigation active states
- Focus indicators
- Primary brand elements

### Accent Colors (Green → Teal Gradient)

Used for secondary actions, success states, and highlights.

```
Accent-50:    hsl(160 84% 96%)    - Lightest background
Accent-100:   hsl(160 81% 93%)
Accent-200:   hsl(160 77% 86%)
Accent-300:   hsl(160 71% 76%)    - Hover states
Accent-400:   hsl(160 65% 63%)
Accent-500:   hsl(160 59% 52%)    - Main accent color ⭐
Accent-600:   hsl(160 68% 42%)
Accent-700:   hsl(160 75% 32%)
Accent-800:   hsl(160 80% 22%)
Accent-900:   hsl(160 85% 12%)
```

**Usage:**
- Success states
- Secondary CTAs
- Accent highlights
- Badges

### Semantic Colors

```
Success:      #10b981 (Green)      - Confirmations, paid orders
Warning:      #f59e0b (Amber)      - Caution, pending states
Destructive:  #ef4444 (Red)        - Errors, deletions
Info:         #3b82f6 (Blue)       - Information alerts
```

---

## Typography

### Font Families

```css
/* Inter: Body text, UI elements */
--font-sans: 'Inter', system-ui, sans-serif;

/* Plus Jakarta Sans: Headings, display text */
--font-display: 'Plus Jakarta Sans', sans-serif;
```

### Scale

```
H1:  5rem    (80px)  - Large hero titles
H2:  3rem    (48px)  - Section titles
H3:  1.875rem (30px) - Subsection titles
Body: 1rem   (16px)  - Main text
Small: 0.875rem (14px) - Secondary text
Tiny: 0.75rem  (12px) - Helper text, badges
```

### Font Weights

```
Display (Headings):
  - Bold:     700
  - Semibold: 600
  - Medium:   500

Body (Paragraphs):
  - Regular:  400
  - Medium:   500
  - Semibold: 600
```

### Usage

```tsx
// Heading
<h1 className="text-5xl md:text-7xl font-bold">Main Title</h1>

// Body
<p className="text-base md:text-lg text-muted-foreground">Description</p>

// Small
<span className="text-xs text-muted-foreground">Helper text</span>
```

---

## Design Tokens

### Border Radius

```
xs:      calc(--radius * 0.5)  = 4px
sm:      calc(--radius * 0.75) = 6px
DEFAULT: var(--radius)         = 8px
md:      calc(--radius * 1.5)  = 12px
lg:      calc(--radius * 2)    = 16px
```

**Usage:**
- `rounded-xs`: Tight borders (small icons, chips)
- `rounded-sm`: Small elements (inputs, badges)
- `rounded`: Default components (cards, buttons)
- `rounded-md`: Larger containers (modals, panels)
- `rounded-lg`: Full sections (hero backgrounds)

### Shadows

```
Shadow-xs:  0 1px 2px 0 rgba(0,0,0, 0.05)
Shadow-sm:  0 1px 3px 0 rgba(0,0,0, 0.1)
Shadow:     0 4px 6px -1px rgba(0,0,0, 0.1)     ⭐ Default
Shadow-md:  0 10px 15px -3px rgba(0,0,0, 0.1)
Shadow-lg:  0 20px 25px -5px rgba(0,0,0, 0.1)
Shadow-xl:  0 25px 50px -12px rgba(0,0,0, 0.25)
```

**Usage:**
- `shadow-xs`: Subtle elevation
- `shadow-sm`: Light cards
- `shadow`: Default cards, buttons
- `shadow-md`: Elevated modals
- `shadow-lg`: Floating elements
- `shadow-xl`: Maximum elevation

### Spacing Scale

Based on `1rem = 16px`:

```
0    = 0px
1    = 4px
2    = 8px
3    = 12px
4    = 16px
6    = 24px
8    = 32px
12   = 48px
16   = 64px
20   = 80px
24   = 96px
32   = 128px
```

---

## Components

### Button

```tsx
// Primary (CTA)
<button className="px-8 py-3 bg-gradient-to-r from-primary-600 to-primary-700 
                   hover:from-primary-700 hover:to-primary-800 text-white 
                   rounded-lg font-semibold transition-all shadow-lg hover:shadow-xl">
  Click me
</button>

// Secondary
<button className="px-8 py-3 border-2 border-primary-300 text-primary-700
                   hover:bg-primary-50 transition-colors rounded-lg font-semibold">
  Secondary
</button>

// Ghost
<button className="px-4 py-2 text-primary-600 hover:bg-primary-50 
                   transition-colors rounded-md font-medium">
  Ghost
</button>
```

**Sizes:**
- `px-3 py-2` - Small (32px height)
- `px-4 py-2.5` - Medium (36px height)
- `px-8 py-3` - Large (44px height)
- `px-10 py-4` - Extra Large (48px height)

### Card

```tsx
import { Card } from '@tribi/ui'

<Card className="p-6">
  <h3>Card Title</h3>
  <p>Card content</p>
</Card>
```

### Badge

```tsx
import { Badge } from '@tribi/ui'

<Badge variant="default">Default</Badge>
<Badge variant="primary">Primary</Badge>
<Badge variant="accent">Accent</Badge>
<Badge variant="success">Success</Badge>
<Badge variant="warning">Warning</Badge>
<Badge variant="destructive">Error</Badge>
<Badge variant="outline">Outline</Badge>
```

### Input

```tsx
import { Input } from '@tribi/ui'

<Input 
  type="text" 
  placeholder="Enter text..."
  className="w-full"
/>
```

### Select

```tsx
import { Select } from '@tribi/ui'

<Select>
  <option>Option 1</option>
  <option>Option 2</option>
</Select>
```

### Skeleton (Loading State)

```tsx
import { Skeleton } from '@tribi/ui'

// Card skeleton
<div className="space-y-2">
  <Skeleton className="h-12 w-full" />
  <Skeleton className="h-4 w-3/4" />
  <Skeleton className="h-4 w-1/2" />
</div>
```

---

## Layout Patterns

### Container with Max-Width

```tsx
// Utility class
<div className="container-max">
  Content
</div>

// Equivalent
<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  Content
</div>
```

### Glass Morphism

```tsx
<div className="glass p-8 rounded-2xl">
  Frosted glass effect
</div>

// Classes:
// backdrop-blur-md, bg-white/30 dark:bg-slate-900/30
// border border-white/20 dark:border-white/10
```

### Gradient Text

```tsx
<h1 className="gradient-text text-5xl font-bold">
  Colored Text
</h1>

// Gradient: from primary-600 to accent-600
```

### Responsive Grid

```tsx
{/* 1 col mobile, 2 col tablet, 3 col desktop */}
<div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
  <div>Item 1</div>
  <div>Item 2</div>
  <div>Item 3</div>
</div>
```

---

## Dark Mode

Dark mode is enabled with the `dark` class on the `<html>` element.

### Color Adjustments

```tsx
<div className="bg-white dark:bg-slate-950">
  Light background in light mode, dark background in dark mode
</div>

<p className="text-black dark:text-white">
  Text automatically inverts
</p>
```

### Detecting Dark Mode

```tsx
const isDark = document.documentElement.classList.contains('dark')
```

### Toggle Implementation

```tsx
function DarkModeToggle() {
  const [isDark, setIsDark] = useState(false)
  
  const toggle = () => {
    document.documentElement.classList.toggle('dark')
    setIsDark(!isDark)
  }
  
  return <button onClick={toggle}>Toggle Dark Mode</button>
}
```

---

## Animations

### Fade In

```tsx
<div className="animate-fade-in">
  Fades in on mount
</div>
```

### Slide Up

```tsx
<div className="animate-slide-up">
  Slides up on mount
</div>
```

### Pulse Glow

```tsx
<div className="animate-pulse-glow">
  Pulsing glow animation
</div>
```

### Float

```tsx
<div className="animate-float">
  Floating animation
</div>
```

### Custom Timing

```tsx
<div className="transition-all duration-300 ease-out">
  Custom transition
</div>
```

---

## Accessibility

### Focus Indicators

```tsx
// Visible focus ring
<button className="focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2">
  Focus me
</button>
```

### Keyboard Navigation

```tsx
// All interactive elements must be keyboard accessible
<button />        // Natural ✅
<div role="button" tabIndex={0}>  // With role ✅
<span>Not focusable</span>        // Missing role ❌
```

### Semantic HTML

```tsx
// Good
<nav>Navigation links</nav>
<main>Main content</main>
<footer>Footer links</footer>
<h1>Page Title</h1>

// Avoid
<div>Navigation links</div>
<div>Main content</div>
<div>Footer links</div>
<div className="text-2xl font-bold">Page Title</div>
```

### Labels

```tsx
// Always label inputs
<label htmlFor="email">Email:</label>
<input id="email" type="email" />

// Or use aria-label
<input aria-label="Search" type="text" />
```

---

## Performance Tips

1. **Lazy Load Images**
   ```tsx
   <img src="..." loading="lazy" />
   ```

2. **Use Next Image Component**
   ```tsx
   import Image from 'next/image'
   <Image src="..." alt="..." width={400} height={300} />
   ```

3. **Code Splitting**
   ```tsx
   const Component = dynamic(() => import('./Component'), {
     loading: () => <Skeleton />,
   })
   ```

4. **Prefetch Links**
   ```tsx
   <Link href="/plans/[iso2]" prefetch>
     Plans
   </Link>
   ```

---

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile: iOS 12+, Android 8+

---

## Variables Configuration

Edit `apps/web/app/globals.css` to customize:

```css
:root {
  --color-primary-500: 240 58% 52%;    /* Main brand color */
  --color-accent-500: 160 59% 52%;     /* Accent color */
  --radius: 8px;                       /* Border radius */
  --font-sans: 'Inter', sans-serif;   /* Body font */
}
```

---

## Usage Examples

### Hero Section

```tsx
<section className="relative overflow-hidden pt-32 pb-40">
  <div className="absolute inset-0 bg-gradient-to-br from-primary-50 to-accent-50" />
  <div className="container-max relative z-10 text-center space-y-6">
    <h1 className="gradient-text text-7xl font-bold">Title</h1>
    <p className="text-xl text-muted-foreground max-w-2xl mx-auto">Description</p>
    <button className="px-10 py-4 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-semibold">
      CTA
    </button>
  </div>
</section>
```

### Feature Cards Grid

```tsx
<div className="grid md:grid-cols-3 gap-8">
  {features.map((feature) => (
    <div key={feature.id} className="bg-white border border-border rounded-2xl p-8 hover:shadow-lg transition-shadow">
      <div className="text-5xl mb-4">{feature.icon}</div>
      <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
      <p className="text-muted-foreground">{feature.description}</p>
    </div>
  ))}
</div>
```

### Form Section

```tsx
<form className="space-y-6 max-w-md mx-auto">
  <div>
    <label className="block text-sm font-medium mb-2">Email</label>
    <Input type="email" placeholder="you@example.com" />
  </div>
  <button className="w-full px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-semibold">
    Submit
  </button>
</form>
```

---

## Questions or Issues?

For design system questions or to propose changes:
1. Check this guide first
2. Review existing components
3. Open an issue with design system tag
4. Follow the PR template when submitting changes
