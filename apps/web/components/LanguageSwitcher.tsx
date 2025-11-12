'use client';

import { useTransition } from 'react';
import { useLocale, useTranslations } from 'next-intl';

export default function LanguageSwitcher() {
  const t = useTranslations('common');
  const locale = useLocale();
  const [isPending, startTransition] = useTransition();

  function onSelectChange(newLocale: string) {
    startTransition(() => {
      // Set cookie
      document.cookie = `NEXT_LOCALE=${newLocale}; path=/; max-age=${365 * 24 * 60 * 60}`;
      // Reload page to apply new locale
      window.location.reload();
    });
  }

  return (
    <div className="relative">
      <label htmlFor="language-select" className="sr-only">
        {t('language')}
      </label>
      <select
        id="language-select"
        aria-label={t('language')}
        value={locale}
        onChange={(e) => onSelectChange(e.target.value)}
        disabled={isPending}
        className="appearance-none bg-transparent border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-2 pr-10 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <option value="en">{t('english')}</option>
        <option value="es">{t('spanish')}</option>
      </select>
      <svg
        className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    </div>
  );
}
