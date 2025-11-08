"use client";

export default function RefundPolicyPage() {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <div className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-4xl font-bold mb-4" style={{ color: "var(--text-primary)" }}>
          Refund Policy
        </h1>
        <p className="text-sm mb-8" style={{ color: "var(--text-secondary)" }}>
          Last Updated: {new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}
        </p>

        <div className="prose prose-lg max-w-none" style={{ color: "var(--text-primary)" }}>
          <section className="mb-8 p-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <h2 className="text-2xl font-semibold mb-4">Our Commitment to Customer Satisfaction</h2>
            <p style={{ color: "var(--text-secondary)" }}>
              At Blitz, we are committed to providing high-quality services and ensuring customer satisfaction.
              This Refund Policy outlines the terms and conditions for requesting refunds on our subscription plans
              and services.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">1. Subscription Plans</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Blitz offers various subscription plans with different features and pricing. All subscriptions are:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Billed in advance on a recurring basis (monthly or annually)</li>
              <li>Auto-renewed unless canceled before the renewal date</li>
              <li>Non-transferable to other users</li>
              <li>Subject to our Terms & Conditions</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">2. Free Trial Period</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              If we offer a free trial period:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>You can cancel anytime during the trial without being charged</li>
              <li>Cancellation must occur before the trial end date to avoid charges</li>
              <li>After the trial ends, you will be automatically charged for your selected plan</li>
              <li>Free trials are limited to one per user</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">3. 30-Day Money-Back Guarantee</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We offer a 30-day money-back guarantee on all new subscriptions:
            </p>

            <h3 className="text-xl font-semibold mb-3 mt-6">3.1 Eligibility</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Available only for first-time purchases of a subscription plan</li>
              <li>Must be requested within 30 days of the original purchase date</li>
              <li>Not available for subscription renewals</li>
              <li>Limited to one refund per user</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">3.2 How to Request</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              To request a refund under our 30-day money-back guarantee:
            </p>
            <ol className="list-decimal pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Email us at <strong>support@blitz.app</strong> within 30 days of purchase</li>
              <li>Include your account email and reason for the refund request</li>
              <li>We will process your refund within 5-7 business days</li>
              <li>Refunds will be issued to the original payment method</li>
            </ol>

            <h3 className="text-xl font-semibold mb-3 mt-6">3.3 What Happens After Refund</h3>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Your subscription will be canceled immediately</li>
              <li>You will lose access to all premium features</li>
              <li>Your data will be retained for 30 days in case you change your mind</li>
              <li>After 30 days, your data may be deleted in accordance with our Privacy Policy</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">4. Subscription Renewals</h2>
            <p className="mb-4 font-semibold" style={{ color: "var(--text-primary)" }}>
              Subscription renewals are generally non-refundable.
            </p>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Once your subscription renews:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>The renewal fee is non-refundable</li>
              <li>You can cancel to prevent future renewals</li>
              <li>Cancellation takes effect at the end of the current billing period</li>
              <li>You will retain access to paid features until the end of your billing period</li>
            </ul>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              <strong>Exception:</strong> Refunds for renewals may be granted at our sole discretion in exceptional
              circumstances, such as technical errors or billing mistakes.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">5. Cancellation Policy</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              You can cancel your subscription at any time:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Log in to your account and go to Settings</li>
              <li>Navigate to Subscription or Billing section</li>
              <li>Click "Cancel Subscription"</li>
              <li>Confirm your cancellation</li>
            </ul>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              After cancellation:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>You will not be charged for future billing periods</li>
              <li>You retain access to paid features until the end of your current billing period</li>
              <li>Your account will automatically convert to a free plan (if available)</li>
              <li>You can reactivate your subscription at any time</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">6. Pro-Rated Refunds</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We do not offer pro-rated refunds for:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Partial billing periods</li>
              <li>Unused features or services</li>
              <li>Downgrading from a higher-tier plan</li>
              <li>Mid-month or mid-year cancellations</li>
            </ul>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              When you cancel, you will continue to have access to paid features for the remainder of your billing period.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">7. Exceptional Circumstances</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We may issue refunds outside of our standard policy in certain exceptional circumstances:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li><strong>Billing Errors:</strong> If you were charged incorrectly due to a technical error</li>
              <li><strong>Duplicate Charges:</strong> If you were charged multiple times for the same subscription</li>
              <li><strong>Service Outages:</strong> If our service was unavailable for extended periods</li>
              <li><strong>Unauthorized Charges:</strong> If charges were made without your authorization</li>
            </ul>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Such refunds are granted at our sole discretion and require documentation of the issue.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">8. Third-Party Products and Services</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              If you purchase third-party products or services through affiliate links on our platform:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Blitz is not responsible for those purchases</li>
              <li>Refund policies are determined by the third-party vendor</li>
              <li>You must contact the vendor directly for refund requests</li>
              <li>We do not process refunds for third-party products</li>
              <li>We may assist you in contacting the vendor but cannot guarantee refunds</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">9. Refund Processing Time</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Once a refund is approved:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>We process refunds within 5-7 business days</li>
              <li>Refunds are issued to the original payment method</li>
              <li>It may take an additional 5-10 business days for the refund to appear in your account</li>
              <li>Processing times vary by payment provider and financial institution</li>
              <li>You will receive an email confirmation when the refund is processed</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">10. Non-Refundable Items</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              The following are non-refundable:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Setup fees (if applicable)</li>
              <li>Custom development or consulting services</li>
              <li>Third-party service fees (Stripe processing fees, etc.)</li>
              <li>Addon features purchased separately</li>
              <li>Expired subscriptions or licenses</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">11. Chargebacks and Disputes</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              If you dispute a charge with your bank or credit card company:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Please contact us first to resolve the issue</li>
              <li>Chargebacks may result in immediate account suspension</li>
              <li>We reserve the right to dispute invalid chargebacks</li>
              <li>Account access will be restored if the chargeback is resolved in your favor</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">12. Changes to This Policy</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We reserve the right to modify this Refund Policy at any time:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Changes will be posted on this page with an updated "Last Updated" date</li>
              <li>Material changes will be communicated via email</li>
              <li>Continued use of the service constitutes acceptance of the updated policy</li>
              <li>Refund requests will be evaluated under the policy in effect at the time of purchase</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">13. Contact Us</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              For refund requests or questions about this policy, please contact us:
            </p>
            <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg" style={{ borderColor: "var(--card-border)" }}>
              <p className="mb-2" style={{ color: "var(--text-primary)" }}>
                <strong>Email:</strong> support@blitz.app
              </p>
              <p className="mb-2" style={{ color: "var(--text-primary)" }}>
                <strong>Subject Line:</strong> Refund Request - [Your Account Email]
              </p>
              <p className="mb-2" style={{ color: "var(--text-primary)" }}>
                <strong>Response Time:</strong> Within 1-2 business days
              </p>
            </div>
          </section>

          <section className="mb-8 mt-12 p-6 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
            <h3 className="text-lg font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
              Quick Summary
            </h3>
            <ul className="space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>✓ 30-day money-back guarantee on first-time purchases</li>
              <li>✓ Free trials can be canceled anytime without charge</li>
              <li>✓ Subscription renewals are generally non-refundable</li>
              <li>✓ Refunds processed within 5-7 business days</li>
              <li>✓ Cancel anytime to prevent future charges</li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}
