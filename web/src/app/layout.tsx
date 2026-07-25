import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import "katex/dist/katex.min.css";
import { MyRuntimeProvider } from "@/lib/runtime-provider";
import { Nav } from "@/components/nav";
import { siteConfig } from "@/lib/site-config";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: siteConfig.title,
  description: siteConfig.description,
};

/**
 * Lock the mobile viewport so the app behaves like a fixed-shell app, not a
 * zoomable document: `userScalable: false` + `maximumScale: 1` disable the
 * accidental two-finger pinch-zoom that made the whole page "float"; `device-width`
 * + `initialScale: 1` pin the layout to the device; `viewportFit: "cover"` lets the
 * shell extend under notches/safe areas. Combined with `overscroll-behavior: none`
 * (globals.css) and the per-drawer scroll lock, the page no longer drifts.
 */
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-dvh antialiased`}
    >
      <body className="flex h-full flex-col">
        <MyRuntimeProvider>
          <Nav />
          <div className="min-h-0 flex-1">{children}</div>
        </MyRuntimeProvider>
      </body>
    </html>
  );
}
