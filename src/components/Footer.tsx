"use client";

import Link from "next/link";

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer
      className="border-t mt-auto pt-24"
      style={{
        borderColor: "var(--border-color)",
        background: "var(--bg-secondary)"
      }}
    >
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Company Info */}
          <div>
            <h3 className="font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
              Blitz
            </h3>
            <p className="text-sm mb-4" style={{ color: "var(--text-secondary)" }}>
              Streamlined marketing automation platform for affiliate marketers and product creators.
            </p>
            <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
              © {currentYear} Blitz. All rights reserved.
            </p>
          </div>

          {/* Legal Links */}
          <div>
            <h3 className="font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
              Legal
            </h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link
                  href="/legal/privacy-policy"
                  className="hover:underline"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link
                  href="/legal/terms"
                  className="hover:underline"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Terms & Conditions
                </Link>
              </li>
              <li>
                <Link
                  href="/legal/affiliate-disclosure"
                  className="hover:underline"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Affiliate Disclosure
                </Link>
              </li>
              <li>
                <Link
                  href="/legal/cookie-policy"
                  className="hover:underline"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Cookie Policy
                </Link>
              </li>
            </ul>
          </div>

          {/* Policies */}
          <div>
            <h3 className="font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
              Policies
            </h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link
                  href="/legal/earnings-disclaimer"
                  className="hover:underline"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Earnings Disclaimer
                </Link>
              </li>
              <li>
                <Link
                  href="/legal/refund-policy"
                  className="hover:underline"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Refund Policy
                </Link>
              </li>
            </ul>
          </div>

          {/* Contact & Resources */}
          <div>
            <h3 className="font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
              Contact
            </h3>
            <ul className="space-y-2 text-sm" style={{ color: "var(--text-secondary)" }}>
              <li>
                <a
                  href="mailto:support@blitz.app"
                  className="hover:underline"
                >
                  support@blitz.app
                </a>
              </li>
              <li>
                <a
                  href="mailto:legal@blitz.app"
                  className="hover:underline"
                >
                  legal@blitz.app
                </a>
              </li>
              <li>
                <a
                  href="mailto:privacy@blitz.app"
                  className="hover:underline"
                >
                  privacy@blitz.app
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div
          className="pt-6 border-t text-center text-xs"
          style={{
            borderColor: "var(--border-color)",
            color: "var(--text-secondary)"
          }}
        >
          <p className="mb-2">
            Blitz is committed to compliance with FTC guidelines, GDPR, CCPA, and affiliate network policies.
          </p>
          <p>
            By using this platform, you agree to our{" "}
            <Link href="/legal/terms" className="underline hover:text-blue-600">
              Terms & Conditions
            </Link>{" "}
            and{" "}
            <Link href="/legal/privacy-policy" className="underline hover:text-blue-600">
              Privacy Policy
            </Link>.
          </p>
        </div>
      </div>
    </footer>
  );
}
