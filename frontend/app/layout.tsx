import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/ui/ThemeProvider";
import { GridDataProvider } from "@/lib/GridDataProvider";

export const metadata: Metadata = {
  title: "GridPulse — Smart Energy Grid Monitoring",
  description: "Smart Energy Grid Monitoring & Predictive Failure Analytics",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <GridDataProvider>{children}</GridDataProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
