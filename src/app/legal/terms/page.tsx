"use client";

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <div className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-4xl font-bold mb-4" style={{ color: "var(--text-primary)" }}>
          Terms & Conditions
        </h1>
        <p className="text-sm mb-8" style={{ color: "var(--text-secondary)" }}>
          Last Updated: {new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}
        </p>

        <div className="prose prose-lg max-w-none" style={{ color: "var(--text-primary)" }}>
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">1. Agreement to Terms</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              By accessing or using Blitz ("the Service"), you agree to be bound by these Terms & Conditions ("Terms").
              If you do not agree to these Terms, you may not access or use the Service.
            </p>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We reserve the right to update or modify these Terms at any time without prior notice. Your continued use
              of the Service following any changes constitutes acceptance of those changes.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">2. Description of Service</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Blitz is a marketing automation platform that provides:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Campaign management tools for affiliate marketers</li>
              <li>AI-powered content generation for marketing materials</li>
              <li>Product intelligence compilation and research</li>
              <li>Compliance checking for FTC and affiliate network guidelines</li>
              <li>Analytics and performance tracking</li>
              <li>URL shortening and click tracking</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">3. Account Registration and Security</h2>

            <h3 className="text-xl font-semibold mb-3 mt-6">3.1 Account Creation</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              To use certain features of the Service, you must register for an account. You agree to:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Provide accurate, current, and complete information during registration</li>
              <li>Maintain and promptly update your account information</li>
              <li>Keep your password secure and confidential</li>
              <li>Notify us immediately of any unauthorized account access</li>
              <li>Accept responsibility for all activities under your account</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">3.2 Account Eligibility</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              You must be at least 18 years old to use this Service. By using the Service, you represent that you are
              at least 18 years of age and have the legal capacity to enter into these Terms.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">3.3 Account Termination</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We reserve the right to suspend or terminate your account at any time, with or without notice, for:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Violation of these Terms</li>
              <li>Fraudulent, abusive, or illegal activity</li>
              <li>Non-payment of fees (if applicable)</li>
              <li>Extended periods of inactivity</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">4. Acceptable Use Policy</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              You agree NOT to use the Service to:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Violate any applicable laws or regulations</li>
              <li>Infringe on intellectual property rights of others</li>
              <li>Transmit harmful, offensive, or unlawful content</li>
              <li>Engage in spam, phishing, or fraudulent activities</li>
              <li>Attempt to gain unauthorized access to our systems</li>
              <li>Interfere with or disrupt the Service or servers</li>
              <li>Use automated tools to access the Service without permission</li>
              <li>Promote illegal products, services, or activities</li>
              <li>Create content that violates FTC guidelines or advertising regulations</li>
              <li>Resell or redistribute the Service without authorization</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">5. Intellectual Property Rights</h2>

            <h3 className="text-xl font-semibold mb-3 mt-6">5.1 Our Content</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              The Service, including its original content, features, and functionality, is owned by Blitz and is protected
              by international copyright, trademark, and other intellectual property laws. You may not copy, modify,
              distribute, sell, or lease any part of our Service without our explicit permission.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">5.2 Your Content</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              You retain ownership of content you create using the Service ("User Content"). By using the Service, you grant us:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>A non-exclusive license to use, store, and process your content to provide the Service</li>
              <li>Permission to use AI services to analyze and generate content based on your inputs</li>
              <li>The right to create anonymized, aggregated data for analytics and service improvement</li>
            </ul>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              You are solely responsible for your User Content and must ensure you have all necessary rights and permissions.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">5.3 AI-Generated Content</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Content generated by our AI services is provided "as is" for your use. You are responsible for:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Reviewing and editing AI-generated content before publication</li>
              <li>Ensuring compliance with applicable laws and regulations</li>
              <li>Verifying accuracy and appropriateness of content</li>
              <li>Adding required disclosures and disclaimers</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">6. Payment Terms</h2>

            <h3 className="text-xl font-semibold mb-3 mt-6">6.1 Pricing</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Certain features of the Service may require payment of fees. Current pricing is available on our website.
              We reserve the right to change our pricing at any time with 30 days' notice to active subscribers.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">6.2 Subscriptions</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Subscription fees are billed in advance on a recurring basis (monthly or annually). Subscriptions automatically
              renew unless canceled before the renewal date. No refunds are provided for partial subscription periods.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">6.3 Payment Processing</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Payments are processed by Stripe, a third-party payment processor. By providing payment information,
              you authorize us to charge your payment method for all fees incurred.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">6.4 Late Payments</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              If payment fails, we may suspend or terminate your access to paid features until payment is received.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">7. Disclaimers and Limitations of Liability</h2>

            <h3 className="text-xl font-semibold mb-3 mt-6">7.1 Service "As Is"</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
              INCLUDING BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">7.2 No Guarantee of Results</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We do not guarantee that:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>The Service will meet your specific requirements</li>
              <li>The Service will be uninterrupted, timely, secure, or error-free</li>
              <li>AI-generated content will be accurate, complete, or suitable for your purposes</li>
              <li>Use of the Service will result in any particular business outcomes or revenue</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">7.3 Limitation of Liability</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              TO THE MAXIMUM EXTENT PERMITTED BY LAW, BLITZ AND ITS AFFILIATES, OFFICERS, DIRECTORS, EMPLOYEES, OR AGENTS
              SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING
              LOSS OF PROFITS, DATA, OR OTHER INTANGIBLE LOSSES, RESULTING FROM:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Your use or inability to use the Service</li>
              <li>Unauthorized access to or alteration of your data</li>
              <li>Statements or conduct of third parties on the Service</li>
              <li>Any other matter relating to the Service</li>
            </ul>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              IN NO EVENT SHALL OUR TOTAL LIABILITY EXCEED THE AMOUNT YOU PAID US IN THE TWELVE (12) MONTHS PRIOR TO THE CLAIM.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">8. Indemnification</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              You agree to indemnify, defend, and hold harmless Blitz and its affiliates from any claims, losses, damages,
              liabilities, and expenses (including legal fees) arising from:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Your use of the Service</li>
              <li>Your User Content</li>
              <li>Your violation of these Terms</li>
              <li>Your violation of any rights of another party</li>
              <li>Your violation of applicable laws or regulations</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">9. Third-Party Links and Services</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              The Service may contain links to third-party websites or integrate with third-party services.
              We are not responsible for the content, privacy policies, or practices of third-party sites or services.
              Your use of third-party services is at your own risk.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">10. Affiliate Marketing Compliance</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              If you use the Service for affiliate marketing, you agree to:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Comply with all FTC guidelines and regulations</li>
              <li>Include proper affiliate disclosures in all promotional content</li>
              <li>Comply with the terms and conditions of affiliate networks you join</li>
              <li>Not make false or misleading claims about products</li>
              <li>Not engage in deceptive marketing practices</li>
            </ul>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Our compliance checking tools are provided as a convenience only. You are solely responsible for ensuring
              your content complies with all applicable laws and regulations.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">11. Data Privacy</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Your use of the Service is also governed by our{" "}
              <a href="/legal/privacy-policy" className="text-blue-600 hover:underline">Privacy Policy</a>, which is
              incorporated into these Terms by reference. Please review our Privacy Policy to understand how we collect,
              use, and protect your information.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">12. Dispute Resolution</h2>

            <h3 className="text-xl font-semibold mb-3 mt-6">12.1 Governing Law</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              These Terms shall be governed by and construed in accordance with the laws of the jurisdiction in which
              Blitz operates, without regard to its conflict of law provisions.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">12.2 Arbitration</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Any disputes arising from these Terms or your use of the Service shall be resolved through binding arbitration,
              except that either party may seek injunctive relief in court for intellectual property infringement or
              unauthorized access to the Service.
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">12.3 Class Action Waiver</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              You agree that disputes will be resolved on an individual basis only and not as part of a class action,
              consolidated, or representative proceeding.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">13. Modifications to the Service</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We reserve the right to modify, suspend, or discontinue any part of the Service at any time, with or without
              notice. We will not be liable to you or any third party for any modification, suspension, or discontinuation
              of the Service.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">14. Severability</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              If any provision of these Terms is found to be invalid or unenforceable, the remaining provisions shall
              continue in full force and effect. The invalid or unenforceable provision shall be replaced with a valid
              provision that most closely matches the intent of the original provision.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">15. Entire Agreement</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              These Terms, together with our Privacy Policy and any other legal notices published by us on the Service,
              constitute the entire agreement between you and Blitz regarding your use of the Service and supersede all
              prior agreements and understandings.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">16. Contact Information</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              If you have questions about these Terms, please contact us at:
            </p>
            <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg" style={{ borderColor: "var(--card-border)" }}>
              <p className="mb-2" style={{ color: "var(--text-primary)" }}>
                <strong>Email:</strong> legal@blitz.app
              </p>
              <p className="mb-2" style={{ color: "var(--text-primary)" }}>
                <strong>Website:</strong> https://blitz-frontend-three.vercel.app
              </p>
            </div>
          </section>

          <section className="mb-8 mt-12 p-6 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
            <h3 className="text-lg font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
              Important Notice
            </h3>
            <p style={{ color: "var(--text-secondary)" }}>
              By using Blitz, you acknowledge that you have read, understood, and agree to be bound by these Terms & Conditions.
              If you do not agree to these Terms, you must discontinue use of the Service immediately.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
