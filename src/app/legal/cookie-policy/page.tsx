"use client";

export default function CookiePolicyPage() {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <div className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-4xl font-bold mb-4" style={{ color: "var(--text-primary)" }}>
          Cookie Policy
        </h1>
        <p className="text-sm mb-8" style={{ color: "var(--text-secondary)" }}>
          Last Updated: {new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}
        </p>

        <div className="prose prose-lg max-w-none" style={{ color: "var(--text-primary)" }}>
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">1. What Are Cookies?</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Cookies are small text files that are placed on your computer or mobile device when you visit a website.
              Cookies are widely used by website owners to make their websites work more efficiently, provide a better
              user experience, and provide reporting information.
            </p>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Cookies set by the website owner (in this case, Blitz) are called "first-party cookies." Cookies set by
              parties other than the website owner are called "third-party cookies." Third-party cookies enable features
              or functionality provided by third parties (e.g., analytics, advertising).
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">2. Why We Use Cookies</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Blitz uses cookies for several purposes:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li><strong>Essential Functionality:</strong> To enable core features like authentication and session management</li>
              <li><strong>Security:</strong> To protect your account and detect fraudulent activity</li>
              <li><strong>Preferences:</strong> To remember your settings and preferences (theme, language, etc.)</li>
              <li><strong>Analytics:</strong> To understand how visitors use our platform and identify areas for improvement</li>
              <li><strong>Performance:</strong> To monitor and improve the performance of our services</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">3. Types of Cookies We Use</h2>

            <h3 className="text-xl font-semibold mb-3 mt-6">3.1 Essential Cookies</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              These cookies are strictly necessary for the operation of our platform. They enable you to navigate
              the site and use its features. Without these cookies, services you have requested cannot be provided.
            </p>
            <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg mb-4">
              <table className="w-full" style={{ color: "var(--text-primary)" }}>
                <thead>
                  <tr>
                    <th className="text-left py-2">Cookie Name</th>
                    <th className="text-left py-2">Purpose</th>
                    <th className="text-left py-2">Duration</th>
                  </tr>
                </thead>
                <tbody style={{ color: "var(--text-secondary)" }}>
                  <tr>
                    <td className="py-2">auth_token</td>
                    <td className="py-2">User authentication</td>
                    <td className="py-2">Session/30 days</td>
                  </tr>
                  <tr>
                    <td className="py-2">session_id</td>
                    <td className="py-2">Session management</td>
                    <td className="py-2">Session</td>
                  </tr>
                  <tr>
                    <td className="py-2">csrf_token</td>
                    <td className="py-2">Security protection</td>
                    <td className="py-2">Session</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <h3 className="text-xl font-semibold mb-3 mt-6">3.2 Preference Cookies</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              These cookies allow our platform to remember information that changes the way the site behaves or looks,
              such as your preferred theme (light/dark mode) or the region you are in.
            </p>
            <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg mb-4">
              <table className="w-full" style={{ color: "var(--text-primary)" }}>
                <thead>
                  <tr>
                    <th className="text-left py-2">Cookie Name</th>
                    <th className="text-left py-2">Purpose</th>
                    <th className="text-left py-2">Duration</th>
                  </tr>
                </thead>
                <tbody style={{ color: "var(--text-secondary)" }}>
                  <tr>
                    <td className="py-2">theme</td>
                    <td className="py-2">Remember dark/light mode preference</td>
                    <td className="py-2">1 year</td>
                  </tr>
                  <tr>
                    <td className="py-2">language</td>
                    <td className="py-2">Remember language preference</td>
                    <td className="py-2">1 year</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <h3 className="text-xl font-semibold mb-3 mt-6">3.3 Analytics Cookies</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              These cookies help us understand how visitors interact with our platform by collecting and reporting
              information anonymously. This helps us improve our services.
            </p>
            <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg mb-4">
              <table className="w-full" style={{ color: "var(--text-primary)" }}>
                <thead>
                  <tr>
                    <th className="text-left py-2">Cookie Name</th>
                    <th className="text-left py-2">Purpose</th>
                    <th className="text-left py-2">Duration</th>
                  </tr>
                </thead>
                <tbody style={{ color: "var(--text-secondary)" }}>
                  <tr>
                    <td className="py-2">_ga</td>
                    <td className="py-2">Google Analytics - User identification</td>
                    <td className="py-2">2 years</td>
                  </tr>
                  <tr>
                    <td className="py-2">_ga_*</td>
                    <td className="py-2">Google Analytics - Session persistence</td>
                    <td className="py-2">2 years</td>
                  </tr>
                  <tr>
                    <td className="py-2">analytics_session</td>
                    <td className="py-2">Internal analytics tracking</td>
                    <td className="py-2">Session</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <h3 className="text-xl font-semibold mb-3 mt-6">3.4 Performance Cookies</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              These cookies collect information about how you use our platform (e.g., which pages you visit most often).
              This data is used to optimize the platform and make it easier for you to navigate.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">4. Third-Party Cookies</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              In addition to our own cookies, we may use various third-party cookies to report usage statistics
              and deliver content:
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">4.1 Vercel Analytics</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We use Vercel Analytics to monitor site performance and user experience. Vercel may set cookies to
              track page load times and other performance metrics.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">4.2 Stripe</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We use Stripe for payment processing. Stripe may set cookies for fraud detection and secure payment processing.
              See <a href="https://stripe.com/privacy" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Stripe's Privacy Policy</a> for more information.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">4.3 Content Delivery Networks (CDN)</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We use CDNs to deliver content faster and more reliably. These services may set cookies to optimize
              content delivery and performance.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">5. Local Storage and Session Storage</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              In addition to cookies, we use browser storage technologies such as:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li><strong>Local Storage:</strong> To store authentication tokens and user preferences</li>
              <li><strong>Session Storage:</strong> To store temporary data during your browsing session</li>
              <li><strong>IndexedDB:</strong> To store larger amounts of structured data for offline functionality</li>
            </ul>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              These technologies serve similar purposes to cookies and can be managed through your browser settings.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">6. How to Control Cookies</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              You have the right to decide whether to accept or reject cookies. You can exercise your cookie preferences by:
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">6.1 Browser Settings</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Most web browsers allow you to control cookies through their settings. You can usually find these settings
              in the "Options" or "Preferences" menu of your browser.
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li><strong>Chrome:</strong> Settings → Privacy and security → Cookies and other site data</li>
              <li><strong>Firefox:</strong> Settings → Privacy & Security → Cookies and Site Data</li>
              <li><strong>Safari:</strong> Preferences → Privacy → Cookies and website data</li>
              <li><strong>Edge:</strong> Settings → Cookies and site permissions → Cookies and site data</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">6.2 Opt-Out Links</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              You can opt-out of certain third-party cookies:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li><a href="https://tools.google.com/dlpage/gaoptout" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Google Analytics Opt-Out</a></li>
              <li><a href="http://www.aboutads.info/choices/" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Digital Advertising Alliance Opt-Out</a></li>
              <li><a href="http://www.youronlinechoices.eu/" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">European Interactive Digital Advertising Alliance</a></li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">6.3 Impact of Disabling Cookies</h3>
            <p className="mb-4 font-semibold" style={{ color: "var(--text-primary)" }}>
              Important: If you disable cookies, some features of our platform may not function properly.
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>You may not be able to log in or stay logged in</li>
              <li>Your preferences will not be saved</li>
              <li>Some features may not work as expected</li>
              <li>Your user experience may be degraded</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">7. Do Not Track Signals</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Some browsers include a "Do Not Track" (DNT) feature that signals to websites that you do not want to be tracked.
              Currently, there is no industry consensus on how to respond to DNT signals. At this time, we do not respond to
              DNT browser signals. However, you can control cookies through your browser settings as described above.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">8. GDPR Compliance (EU Users)</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              If you are located in the European Economic Area (EEA), you have specific rights under GDPR:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Right to access your personal data</li>
              <li>Right to rectify inaccurate data</li>
              <li>Right to erasure ("right to be forgotten")</li>
              <li>Right to restrict processing</li>
              <li>Right to data portability</li>
              <li>Right to object to processing</li>
              <li>Right to withdraw consent</li>
            </ul>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              For non-essential cookies, we will only use them with your explicit consent.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">9. CCPA Compliance (California Users)</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              If you are a California resident, you have specific rights under the California Consumer Privacy Act (CCPA):
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Right to know what personal information is collected</li>
              <li>Right to know if personal information is sold or shared</li>
              <li>Right to opt-out of the sale of personal information</li>
              <li>Right to deletion of personal information</li>
              <li>Right to non-discrimination for exercising CCPA rights</li>
            </ul>
            <p className="mb-4 font-semibold" style={{ color: "var(--text-primary)" }}>
              We do not sell your personal information.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">10. Updates to This Policy</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We may update this Cookie Policy from time to time to reflect:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Changes in our cookie practices</li>
              <li>Changes in cookie technology</li>
              <li>Changes in applicable laws and regulations</li>
              <li>Changes in our services or features</li>
            </ul>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We encourage you to review this Cookie Policy periodically. The "Last Updated" date at the top indicates
              when this policy was last revised.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">11. Contact Us</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              If you have questions about our use of cookies or this Cookie Policy, please contact us at:
            </p>
            <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg" style={{ borderColor: "var(--card-border)" }}>
              <p className="mb-2" style={{ color: "var(--text-primary)" }}>
                <strong>Email:</strong> privacy@blitz.app
              </p>
              <p className="mb-2" style={{ color: "var(--text-primary)" }}>
                <strong>Website:</strong> https://blitz-frontend-three.vercel.app
              </p>
            </div>
          </section>

          <section className="mb-8 mt-12 p-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <h3 className="text-lg font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
              Quick Summary
            </h3>
            <ul className="space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>✓ We use cookies to improve your experience and analyze site usage</li>
              <li>✓ Essential cookies are necessary for the platform to function</li>
              <li>✓ You can control cookies through your browser settings</li>
              <li>✓ Disabling cookies may affect site functionality</li>
              <li>✓ We do not sell your personal information</li>
              <li>✓ Third-party services may set their own cookies</li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}
