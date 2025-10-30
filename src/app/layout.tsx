// app/layout.tsx
import "src/app/globals.css";
import { ThemeProvider } from "src/contexts/ThemeContext";
import { Providers } from "src/components/Providers";
import Layout from "src/components/Layout"; // default import

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <ThemeProvider>
            <Layout>{children}</Layout>
          </ThemeProvider>
        </Providers>
      </body>
    </html>
  );
}
