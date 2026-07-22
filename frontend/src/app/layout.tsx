import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import "./globals.css"
import { DarkModeProvider } from "@/lib/dark-mode"
import { TopBar } from "@/components/layout/top-bar"

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
})

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
})

export const metadata: Metadata = {
  title: "ScreenSorts",
  description: "AI-Powered Semantic Screenshot Search Engine",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var dark = localStorage.getItem('screensorts_dark');
                  var preferDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                  if (dark === 'true' || (dark === null && preferDark)) {
                    document.documentElement.classList.add('dark');
                  }
                } catch(e) {}
              })();
            `,
          }}
        />
      </head>
      <body className="flex min-h-full flex-col bg-background text-foreground">
        <DarkModeProvider>
          <TopBar />
          <main className="flex-1">{children}</main>
        </DarkModeProvider>
      </body>
    </html>
  )
}
