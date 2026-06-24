import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Customer Support System",
  description: "LangGraph customer support portal with human escalation dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
