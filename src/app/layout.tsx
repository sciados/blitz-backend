import { ThemeProvider } from "src/contexts/ThemeContext";
import "./globals.css";

export const metadata = {
  title: "Blitz SaaS",
  description: "Affiliate Marketing Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
