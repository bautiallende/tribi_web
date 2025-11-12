import { MetadataRoute } from 'next'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = 'https://tribi.app';
  
  // Static routes
  const routes = ['', '/plans', '/auth'].map((route) => ({
    url: `${baseUrl}${route}`,
    lastModified: new Date().toISOString(),
    changeFrequency: 'daily' as const,
    priority: route === '' ? 1.0 : 0.8,
  }));

  // TODO: Fetch dynamic routes from API (countries)
  // For now, return static routes
  
  return routes;
}
