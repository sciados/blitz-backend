// app/layout.tsx
import "src/app/globals.css";
import { ThemeProvider } from "src/contexts/ThemeContext";
import Layout from "src/components/Layout"; // default import

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <ThemeProvider>
          <Layout>{children}</Layout>
        </ThemeProvider>
      </body>
    </html>
  );
}
