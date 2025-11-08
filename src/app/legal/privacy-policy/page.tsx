"use client";

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <div className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-4xl font-bold mb-4" style={{ color: "var(--text-primary)" }}>
          Privacy Policy
        </h1>
        <p className="text-sm mb-8" style={{ color: "var(--text-secondary)" }}>
          Last Updated: {new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}
        </p>

        <div className="prose prose-lg max-w-none" style={{ color: "var(--text-primary)" }}>
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">1. Introduction</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Welcome to Blitz ("we," "our," or "us"). We are committed to protecting your personal information and your right to privacy.
              This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our marketing automation platform.
            </p>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              By using Blitz, you agree to the collection and use of information in accordance with this policy.
              If you do not agree with our policies and practices, please do not use our service.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">2. Information We Collect</h2>

            <h3 className="text-xl font-semibold mb-3 mt-6">2.1 Personal Information</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We collect personal information that you voluntarily provide to us when you:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Register for an account (email address, full name)</li>
              <li>Use our services (campaign data, product URLs, affiliate links)</li>
              <li>Subscribe to our newsletter or marketing communications</li>
              <li>Contact us for support or inquiries</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">2.2 Automatically Collected Information</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              When you access our platform, we automatically collect certain information, including:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Log data (IP address, browser type, operating system)</li>
              <li>Usage data (pages visited, time spent, features used)</li>
              <li>Device information (device type, unique device identifiers)</li>
              <li>Cookies and similar tracking technologies (see our Cookie Policy)</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">2.3 Third-Party Data</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We may collect information about products and URLs you submit for analysis. This data is processed to provide
              you with marketing intelligence and campaign optimization services.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">3. How We Use Your Information</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We use your information for the following purposes:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li><strong>Provide and Maintain Services:</strong> To operate and maintain your account and provide platform features</li>
              <li><strong>Improve Our Platform:</strong> To understand how users interact with our service and make improvements</li>
              <li><strong>Communicate With You:</strong> To send updates, security alerts, and support messages</li>
              <li><strong>Marketing:</strong> To send promotional communications (you can opt-out at any time)</li>
              <li><strong>Analytics:</strong> To analyze usage patterns and optimize performance</li>
              <li><strong>Compliance:</strong> To comply with legal obligations and enforce our terms</li>
              <li><strong>AI Processing:</strong> To generate marketing content and product intelligence using AI services</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">4. Information Sharing and Disclosure</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We do not sell your personal information. We may share your information in the following circumstances:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li><strong>Service Providers:</strong> With third-party vendors who perform services on our behalf (hosting, analytics, AI processing)</li>
              <li><strong>Business Transfers:</strong> In connection with a merger, acquisition, or sale of assets</li>
              <li><strong>Legal Requirements:</strong> When required by law or to protect our rights and safety</li>
              <li><strong>With Your Consent:</strong> When you explicitly authorize us to share specific information</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">Third-Party Services We Use:</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Anthropic Claude AI (for content generation and intelligence compilation)</li>
              <li>Vercel (hosting and deployment)</li>
              <li>Railway (backend infrastructure)</li>
              <li>Stripe (payment processing for subscriptions)</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">5. Data Security</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We implement appropriate technical and organizational security measures to protect your personal information, including:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Encryption of data in transit and at rest</li>
              <li>Secure authentication using JWT tokens</li>
              <li>Regular security assessments and updates</li>
              <li>Access controls and data minimization practices</li>
            </ul>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              However, no method of transmission over the Internet is 100% secure. While we strive to protect your information,
              we cannot guarantee absolute security.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">6. Data Retention</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We retain your personal information for as long as necessary to:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Provide our services to you</li>
              <li>Comply with legal obligations</li>
              <li>Resolve disputes and enforce agreements</li>
            </ul>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              When you delete your account, we will delete or anonymize your personal information within 30 days,
              except where we are required to retain it for legal purposes.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">7. Your Privacy Rights</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Depending on your location, you may have the following rights:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li><strong>Access:</strong> Request a copy of the personal information we hold about you</li>
              <li><strong>Correction:</strong> Request correction of inaccurate or incomplete information</li>
              <li><strong>Deletion:</strong> Request deletion of your personal information</li>
              <li><strong>Portability:</strong> Request transfer of your data to another service</li>
              <li><strong>Objection:</strong> Object to processing of your information for certain purposes</li>
              <li><strong>Restriction:</strong> Request restriction of processing in certain circumstances</li>
              <li><strong>Withdraw Consent:</strong> Withdraw consent for marketing communications at any time</li>
            </ul>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              To exercise these rights, please contact us at the email address provided in Section 12.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">8. Cookies and Tracking Technologies</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We use cookies and similar tracking technologies to track activity on our platform and store certain information.
              For detailed information about the cookies we use and your choices, please see our{" "}
              <a href="/legal/cookie-policy" className="text-blue-600 hover:underline">Cookie Policy</a>.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">9. International Data Transfers</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Your information may be transferred to and processed in countries other than your country of residence.
              These countries may have data protection laws that differ from those in your country.
              We ensure appropriate safeguards are in place to protect your information in accordance with this Privacy Policy.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">10. Children's Privacy</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Our service is not intended for children under the age of 18. We do not knowingly collect personal information
              from children under 18. If you are a parent or guardian and believe your child has provided us with personal information,
              please contact us, and we will delete such information.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">11. Changes to This Privacy Policy</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We may update this Privacy Policy from time to time. We will notify you of any changes by:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Posting the new Privacy Policy on this page</li>
              <li>Updating the "Last Updated" date at the top</li>
              <li>Sending you an email notification for material changes</li>
            </ul>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Your continued use of our platform after changes are posted constitutes your acceptance of the updated policy.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">12. Contact Us</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              If you have questions or concerns about this Privacy Policy or our privacy practices, please contact us at:
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
              GDPR Compliance (For EU Users)
            </h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              If you are a resident of the European Economic Area (EEA), you have additional rights under the General Data Protection
              Regulation (GDPR). Our lawful basis for processing your personal information includes:
            </p>
            <ul className="list-disc pl-6 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li><strong>Consent:</strong> You have given clear consent for us to process your personal information</li>
              <li><strong>Contract:</strong> Processing is necessary to fulfill our contract with you</li>
              <li><strong>Legal Obligation:</strong> Processing is necessary to comply with the law</li>
              <li><strong>Legitimate Interests:</strong> Processing is in our legitimate interests and does not override your rights</li>
            </ul>
          </section>

          <section className="mb-8 p-6 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
            <h3 className="text-lg font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
              CCPA Compliance (For California Users)
            </h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              If you are a California resident, you have specific rights under the California Consumer Privacy Act (CCPA):
            </p>
            <ul className="list-disc pl-6 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Right to know what personal information is collected, used, shared, or sold</li>
              <li>Right to delete personal information held by us</li>
              <li>Right to opt-out of sale of personal information (we do not sell personal information)</li>
              <li>Right to non-discrimination for exercising your CCPA rights</li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}
