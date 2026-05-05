import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "smart-receipt",
  description: "AI-powered receipt OCR and field extraction",
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
