import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Retail Intelligencia",
  description: "Edge AI Retail Intelligence Operations Console",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
