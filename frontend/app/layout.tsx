import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import { Footer } from "@/components/Chrome";
import Nav from "@/components/Nav";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist-sans" });

export const metadata: Metadata = {
  title: { default: "Maharashtra College Finder", template: "%s · Maharashtra College Finder" },
  description: "Compare your MHT-CET percentile with official historical CAP cutoffs for Maharashtra engineering colleges.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={geist.variable} data-scroll-behavior="smooth">
      <body className="min-h-screen bg-background font-sans text-navy antialiased">
        <Nav />
        {children}
        <Footer />
      </body>
    </html>
  );
}
