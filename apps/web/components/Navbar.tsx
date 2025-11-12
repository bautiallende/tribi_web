'use client'

import Link from 'next/link'
import { useState } from 'react'
import { Button } from '@tribi/ui'
import LanguageSwitcher from './LanguageSwitcher'

export function Navbar() {
  const [isDarkMode, setIsDarkMode] = useState(false)

  const toggleDarkMode = () => {
    const html = document.documentElement
    if (isDarkMode) {
      html.classList.remove('dark')
    } else {
      html.classList.add('dark')
    }
    setIsDarkMode(!isDarkMode)
  }

  return (
    <nav className="sticky top-0 z-50 w-full bg-white/80 dark:bg-slate-950/80 backdrop-blur-md border-b border-border">
      <div className="container-max">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <div className="w-8 h-8 bg-gradient-to-r from-primary-600 to-accent-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">T</span>
            </div>
            <span className="font-display font-bold text-xl hidden sm:inline">Tribi</span>
          </Link>

          {/* Center - Navigation Links */}
          <div className="hidden md:flex items-center gap-8">
            <Link href="/" className="text-sm font-medium hover:text-primary transition-colors">
              Home
            </Link>
            <a href="/#how-it-works" className="text-sm font-medium hover:text-primary transition-colors">
              How it works
            </a>
            <a href="/#popular" className="text-sm font-medium hover:text-primary transition-colors">
              Plans
            </a>
          </div>

          {/* Right - Controls */}
          <div className="flex items-center gap-4">
            {/* Language Switcher */}
            <LanguageSwitcher />

            {/* Dark Mode Toggle */}
            <button
              onClick={toggleDarkMode}
              className="p-2 rounded-md hover:bg-muted transition-colors"
              aria-label="Toggle dark mode"
            >
              {isDarkMode ? (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.707.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zm5.657-9.193a1 1 0 00-1.414 0l-.707.707A1 1 0 005.05 6.464l.707-.707a1 1 0 011.414-1.414zM5 8a1 1 0 100-2H4a1 1 0 100 2h1z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </button>

            {/* My Account CTA */}
            <Link href="/account" className="hidden sm:inline-flex px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-md font-medium text-sm transition-colors" aria-label="My Account">
              My Account
            </Link>

            {/* Mobile Account Icon */}
            <Link href="/account" className="md:hidden p-2 hover:bg-muted rounded-md transition-colors" aria-label="Account">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
              </svg>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
}
