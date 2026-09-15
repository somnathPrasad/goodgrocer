import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "Goodgrocer · Store desk",
  description: "Manage your neighbourhood store",
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
