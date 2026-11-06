import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Lupira — Lupus Research & Screening Tool",
  description:
    "A research and educational tool that helps make sense of lupus (SLE) blood-test results and screens for neuropsychiatric lupus symptoms. Not a medical device — not for clinical decision-making.",
};

const NAV = [
  { href: "/", label: "Home" },
  { href: "/predict", label: "Check My Results" },
  { href: "/npsle", label: "Symptom Screening" },
  { href: "/about", label: "About the Research" },
];

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col font-sans">
        <header className="border-b border-border bg-white">
          <div className="mx-auto max-w-5xl px-6 py-4 flex items-center justify-between">
            <Link href="/" className="text-lg font-semibold text-primary">
              Lupira
            </Link>
            <nav className="flex gap-6 text-sm">
              {NAV.map((item) => (
                <Link key={item.href} href={item.href} className="text-foreground/70 hover:text-primary">
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="flex-1">{children}</main>
        <footer className="border-t border-border bg-card py-6">
          <div className="mx-auto max-w-5xl px-6 text-xs text-foreground/60">
            Lupira is a research tool and is not a medical device. It is not intended for clinical
            decision-making.
          </div>
        </footer>
      </body>
    </html>
  );
}
