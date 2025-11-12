import {getRequestConfig} from 'next-intl/server';
import {cookies} from 'next/headers';

export default getRequestConfig(async () => {
  // Get locale from cookie or default to 'en'
  const cookieStore = cookies();
  const locale = cookieStore.get('NEXT_LOCALE')?.value || 'en';

  return {
    locale,
    messages: {
      common: (await import(`../locales/${locale}/common.json`)).default,
      home: (await import(`../locales/${locale}/home.json`)).default,
      plans: (await import(`../locales/${locale}/plans.json`)).default,
      admin: (await import(`../locales/${locale}/admin.json`)).default,
    }
  };
});
