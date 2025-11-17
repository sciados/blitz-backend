"use client";

export default function AffiliateDisclosurePage() {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <div className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-4xl font-bold mb-4" style={{ color: "var(--text-primary)" }}>
          Affiliate Disclosure
        </h1>
        <p className="text-sm mb-8" style={{ color: "var(--text-secondary)" }}>
          Last Updated: {new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}
        </p>

        <div className="prose prose-lg max-w-none" style={{ color: "var(--text-primary)" }}>
          <section className="mb-8 p-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <h2 className="text-2xl font-semibold mb-4">FTC Disclosure Statement</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              In compliance with the Federal Trade Commission (FTC) guidelines concerning the use of endorsements and
              testimonials in advertising, we are required to inform you of the relationship between Blitz and the
              products, services, or companies that we recommend, review, or promote.
            </p>
            <p className="mb-4 font-semibold" style={{ color: "var(--text-primary)" }}>
              This website and the content generated through our platform may contain affiliate links and sponsored content.
              When you click on affiliate links and make a purchase, we may receive a commission at no additional cost to you.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">1. What Are Affiliate Links?</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Affiliate links are special tracking URLs that allow us to earn a commission when you purchase a product
              or service after clicking on our link. These links do not affect the price you pay – you pay the same amount
              whether you use our affiliate link or go directly to the merchant's website.
            </p>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Example: If we recommend a product and you click our affiliate link and make a purchase, we may earn a
              commission from that sale. This helps support our platform and allows us to continue providing valuable
              content and services to our users.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">2. Our Relationship with Affiliate Networks</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Blitz partners with various affiliate networks and programs, including but not limited to:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>ClickBank</li>
              <li>JVZoo</li>
              <li>ShareASale</li>
              <li>Amazon Associates</li>
              <li>Commission Junction (CJ Affiliate)</li>
              <li>Impact</li>
              <li>Rakuten Advertising</li>
              <li>And other affiliate networks</li>
            </ul>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              When our users promote products from these networks, we may also earn commissions on those promotions.
              We provide tools to help our users comply with FTC guidelines and affiliate network policies.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">3. Our Commitment to Transparency</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We are committed to transparency and honesty in all our recommendations and promotions:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li><strong>Clear Disclosures:</strong> We clearly disclose when content contains affiliate links</li>
              <li><strong>Honest Reviews:</strong> We provide honest opinions and will never recommend products solely for commission</li>
              <li><strong>Actual Experience:</strong> We strive to review and recommend products we have personally researched or used</li>
              <li><strong>No False Claims:</strong> We do not make exaggerated or misleading claims about products</li>
              <li><strong>User Benefit First:</strong> We prioritize providing value to our users over earning commissions</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">4. Commission Structure</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              The commissions we earn vary depending on the affiliate program and product:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li><strong>Percentage-Based:</strong> Some programs pay a percentage of the sale (e.g., 10%, 30%, 50%)</li>
              <li><strong>Fixed Amount:</strong> Some programs pay a fixed dollar amount per sale</li>
              <li><strong>Recurring:</strong> Some programs pay ongoing commissions for subscription-based products</li>
              <li><strong>Performance Bonuses:</strong> Some programs offer additional bonuses for high-performing affiliates</li>
            </ul>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              The commission we earn does not influence the price you pay. You pay the same price whether you purchase
              through our affiliate link or directly from the merchant.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">5. Product Recommendations and Reviews</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              When we recommend or review products:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>We may earn a commission if you purchase through our links</li>
              <li>Our opinions are our own and not influenced by commission rates</li>
              <li>We provide balanced reviews highlighting both pros and cons</li>
              <li>We disclose any material connections or sponsorships</li>
              <li>We update reviews if our opinions change over time</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">6. User-Generated Content</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Blitz is a platform that enables our users to create marketing content and campaigns. When our users
              create content using our platform:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Users are responsible for their own affiliate disclosures</li>
              <li>We provide compliance tools to help users meet FTC requirements</li>
              <li>Users must ensure their content complies with all applicable laws</li>
              <li>We are not responsible for user-generated content or claims</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">7. No Guarantees of Results</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              It is important to understand that:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>We do not guarantee specific results from using recommended products</li>
              <li>Results vary based on individual circumstances, effort, and other factors</li>
              <li>Past performance does not guarantee future results</li>
              <li>Testimonials and examples do not represent typical results</li>
              <li>You should conduct your own research before making purchase decisions</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">8. Medical and Financial Disclaimers</h2>

            <h3 className="text-xl font-semibold mb-3 mt-6">8.1 Medical Disclaimer</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              If we promote health-related products:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>We are not medical professionals and do not provide medical advice</li>
              <li>Information is for educational purposes only</li>
              <li>Consult with a healthcare provider before using health products</li>
              <li>Products are not intended to diagnose, treat, cure, or prevent any disease</li>
              <li>Individual results may vary</li>
            </ul>

            <h3 className="text-xl font-semibold mb-3 mt-6">8.2 Financial Disclaimer</h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              If we promote financial or business opportunity products:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>We are not financial advisors and do not provide financial advice</li>
              <li>Information is for educational purposes only</li>
              <li>Consult with a financial professional before making investment decisions</li>
              <li>We do not guarantee income or earnings</li>
              <li>Results depend on individual effort, skill, and market conditions</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">9. Third-Party Products and Services</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              When we link to third-party products or services:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>We are not responsible for the content, policies, or practices of third-party websites</li>
              <li>Third-party products are sold by independent merchants</li>
              <li>Refund policies are set by the merchant, not by Blitz</li>
              <li>Customer service issues should be directed to the merchant</li>
              <li>We may receive compensation for referrals but are not liable for product quality</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">10. Sponsored Content</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              From time to time, we may publish sponsored content or receive compensation for featuring specific products:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Sponsored content will be clearly labeled as "Sponsored," "Ad," or "Paid Partnership"</li>
              <li>Sponsors do not dictate our editorial opinions or content</li>
              <li>We only promote products we believe provide value to our audience</li>
              <li>Sponsorship does not influence our honest assessment of products</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">11. Updates to This Disclosure</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We may update this Affiliate Disclosure from time to time to reflect:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Changes in our affiliate partnerships</li>
              <li>Updates to FTC guidelines</li>
              <li>Changes in our business practices</li>
              <li>New affiliate networks or programs</li>
            </ul>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              The "Last Updated" date at the top of this page indicates when this disclosure was last revised.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">12. Questions and Contact</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              If you have questions about our affiliate relationships or this disclosure, please contact us at:
            </p>
            <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg" style={{ borderColor: "var(--card-border)" }}>
              <p className="mb-2" style={{ color: "var(--text-primary)" }}>
                <strong>Email:</strong> disclosure@blitz.app
              </p>
              <p className="mb-2" style={{ color: "var(--text-primary)" }}>
                <strong>Website:</strong> https://blitz-frontend-three.vercel.app
              </p>
            </div>
          </section>

          <section className="mb-8 mt-12 p-6 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
            <h3 className="text-lg font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
              Your Trust Matters to Us
            </h3>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We value your trust and are committed to maintaining transparent relationships with our users.
              We will always disclose our affiliate relationships and provide honest, unbiased information to help
              you make informed decisions.
            </p>
            <p style={{ color: "var(--text-secondary)" }}>
              Thank you for supporting Blitz by using our affiliate links. Your purchases help us continue providing
              valuable content and services at no cost to you.
            </p>
          </section>

          <section className="mb-8 p-6 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
            <h3 className="text-lg font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
              FTC Compliance Statement
            </h3>
            <p style={{ color: "var(--text-secondary)" }}>
              This affiliate disclosure complies with the Federal Trade Commission's 16 CFR Part 255: "Guides Concerning
              the Use of Endorsements and Testimonials in Advertising." We are committed to operating with full transparency
              and in compliance with all applicable regulations governing affiliate marketing and endorsements.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
