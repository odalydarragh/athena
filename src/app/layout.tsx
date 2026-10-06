import type { ReactNode } from "react";
import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";
import "./globals.css";

const sans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-sans",
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "DocuMDR — Continuous Regulatory Integration",
  description:
    "Developer-first compiler of IEC 62304, ISO 14971, EU MDR, and EU AI Act draft technical files from git metadata.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en-IE">
      <body className={`${sans.className} ${sans.variable} ${mono.variable}`}>
        {children}
        <footer className="site wrap">
          DocuMDR compiles draft documentation only. It is not a notified body, does not issue CE
          marking, and is not a medical device.{" "}
          <a href="/privacy">Privacy</a> · <a href="/terms">Terms</a> · <a href="/dpa">DPA</a> ·{" "}
          <a href="/cookies">Cookies</a>
        </footer>
      </body>
    </html>
  );
}
