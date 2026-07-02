import type { Metadata } from "next";
import { Inter, Plus_Jakarta_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-plus-jakarta",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "HackLaunch AI — Multi-Agent Hackathon GTM Platform",
    template: "%s | HackLaunch AI",
  },
  description:
    "Transform your hackathon idea into a complete launch package in minutes. AI-powered brand, content, marketing, emails, and execution plans.",
  keywords: ["hackathon", "AI", "GTM", "launch", "multi-agent", "event planning"],
  authors: [{ name: "HackLaunch AI Team" }],
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://hacklaunch.ai",
    title: "HackLaunch AI",
    description: "AI-powered hackathon GTM platform",
    siteName: "HackLaunch AI",
  },
  twitter: {
    card: "summary_large_image",
    title: "HackLaunch AI",
    description: "AI-powered hackathon GTM platform",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${inter.variable} ${plusJakarta.variable} ${jetbrainsMono.variable}`}
    >
      <body className="bg-dark-500 text-surface-50 antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
