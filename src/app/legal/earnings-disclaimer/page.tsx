"use client";

export default function EarningsDisclaimerPage() {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <div className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-4xl font-bold mb-4" style={{ color: "var(--text-primary)" }}>
          Earnings Disclaimer
        </h1>
        <p className="text-sm mb-8" style={{ color: "var(--text-secondary)" }}>
          Last Updated: {new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}
        </p>

        <div className="prose prose-lg max-w-none" style={{ color: "var(--text-primary)" }}>
          <section className="mb-8 p-6 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
            <h2 className="text-2xl font-semibold mb-4">IMPORTANT: Please Read Carefully</h2>
            <p className="mb-4 font-bold text-lg" style={{ color: "var(--text-primary)" }}>
              INDIVIDUAL RESULTS MAY VARY. NO GUARANTEE OF SPECIFIC RESULTS.
            </p>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              All information, products, and services provided by Blitz are for educational and informational purposes only.
              We make no guarantees regarding income, earnings, or results from using our platform or any products, services,
              or strategies discussed or promoted through our platform.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">1. No Guarantee of Earnings</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Any earnings, revenue figures, or income examples mentioned on our platform or in user testimonials are:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li><strong>Not typical:</strong> These results are not typical and do not represent average earnings</li>
              <li><strong>Not guaranteed:</strong> There is no guarantee that you will achieve similar results</li>
              <li><strong>Illustrative only:</strong> Examples are provided for illustration purposes only</li>
              <li><strong>Dependent on many factors:</strong> Results depend on individual effort, skills, knowledge, and circumstances</li>
              <li><strong>Subject to market conditions:</strong> Results are influenced by market conditions beyond our control</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">2. Results May Vary</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Your results from using Blitz or any products promoted through our platform will vary and depend on many factors, including:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Your business experience and knowledge</li>
              <li>The time, effort, and resources you invest</li>
              <li>Your marketing skills and abilities</li>
              <li>The niche or market you choose</li>
              <li>Economic conditions and market demand</li>
              <li>Competition in your chosen field</li>
              <li>Your ability to implement strategies effectively</li>
              <li>Your dedication and consistency</li>
              <li>External factors beyond your control</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">3. No "Get Rich Quick" Claims</h2>
            <p className="mb-4 font-semibold" style={{ color: "var(--text-primary)" }}>
              Building a successful online business takes time, effort, and dedication.
            </p>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We do not promote or endorse "get rich quick" schemes. Anyone claiming you can earn substantial income
              quickly or easily is not being truthful. Success in affiliate marketing and online business requires:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Consistent effort over extended periods</li>
              <li>Continuous learning and skill development</li>
              <li>Investment of time and possibly money</li>
              <li>Patience and perseverance through challenges</li>
              <li>Adaptation to changing market conditions</li>
              <li>Professional execution of marketing strategies</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">4. Testimonials and Case Studies</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Any testimonials, case studies, or success stories shared on our platform:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Represent individual experiences and are not typical results</li>
              <li>Were achieved by individuals who may have unique skills, knowledge, or advantages</li>
              <li>May not reflect the average user's experience</li>
              <li>Should not be interpreted as a guarantee of earnings</li>
              <li>Are provided for informational purposes only</li>
              <li>May have been incentivized or compensated</li>
            </ul>
            <p className="mb-4 font-semibold" style={{ color: "var(--text-primary)" }}>
              TESTIMONIALS DO NOT REPRESENT TYPICAL RESULTS. YOUR RESULTS MAY BE BETTER, WORSE, OR THE SAME.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">5. Risk of Loss</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              There is a risk of loss in any business venture, including affiliate marketing:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>You may not earn any income from your efforts</li>
              <li>You may spend more on advertising and tools than you earn in commissions</li>
              <li>Your business may not be profitable</li>
              <li>Market conditions can change, affecting your earnings</li>
              <li>Products you promote may become discontinued or unavailable</li>
              <li>Affiliate networks may change commission structures or terms</li>
            </ul>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Only invest time and money that you can afford to lose. Do not quit your job or make financial decisions
              based solely on potential earnings from affiliate marketing.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">6. Use of AI and Automation Tools</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Blitz provides AI-powered content generation and automation tools. However:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>AI tools do not guarantee business success or earnings</li>
              <li>Generated content must be reviewed, edited, and customized</li>
              <li>Automation does not replace the need for strategy and effort</li>
              <li>Tools are only as effective as how you use them</li>
              <li>Success depends on your marketing skills, not just the tools</li>
              <li>Competition using similar tools may affect your results</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">7. Product Recommendations</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              When we recommend products, services, or strategies:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>We may earn affiliate commissions from your purchases</li>
              <li>We share our honest opinions based on our research and experience</li>
              <li>Products may work differently for different people</li>
              <li>We cannot guarantee the quality or effectiveness of third-party products</li>
              <li>You should conduct your own due diligence before purchasing</li>
              <li>Refund policies are determined by the product vendor, not Blitz</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">8. Educational Purpose Only</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              All information provided through Blitz is for educational and informational purposes only:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>We are not financial advisors, accountants, or attorneys</li>
              <li>Information should not be considered professional advice</li>
              <li>Consult with qualified professionals before making business decisions</li>
              <li>You are responsible for compliance with all applicable laws and regulations</li>
              <li>We do not provide tax, legal, or financial advice</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">9. Your Responsibility</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              By using Blitz, you acknowledge and agree that:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>You are solely responsible for your business decisions and results</li>
              <li>You will not hold Blitz liable for any financial losses</li>
              <li>You understand the risks involved in business and marketing</li>
              <li>You will conduct proper due diligence before investing time or money</li>
              <li>You will comply with all applicable laws, regulations, and guidelines</li>
              <li>You will not make false or misleading claims in your marketing</li>
              <li>You will include appropriate disclosures and disclaimers in your content</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">10. Actual Results Depend on You</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              The level of success you achieve depends entirely on:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li><strong>Your Effort:</strong> How much time and energy you dedicate</li>
              <li><strong>Your Skills:</strong> Your marketing, writing, and technical abilities</li>
              <li><strong>Your Investment:</strong> The resources you invest in your business</li>
              <li><strong>Your Learning:</strong> Your willingness to learn and improve</li>
              <li><strong>Your Persistence:</strong> Your ability to overcome challenges</li>
              <li><strong>Your Strategy:</strong> The effectiveness of your marketing approach</li>
              <li><strong>Your Market:</strong> The demand and competition in your niche</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">11. FTC Compliance</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              This disclaimer complies with Federal Trade Commission (FTC) requirements for:
            </p>
            <ul className="list-disc pl-6 mb-4 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Truth in advertising</li>
              <li>Income claims and representations</li>
              <li>Testimonial and endorsement guidelines</li>
              <li>Affiliate marketing disclosures</li>
            </ul>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              We are committed to operating ethically and in full compliance with all applicable regulations.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">12. Contact Information</h2>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              If you have questions about this Earnings Disclaimer, please contact us at:
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
              Summary Statement
            </h3>
            <p className="mb-4 font-bold" style={{ color: "var(--text-primary)" }}>
              ALL EARNINGS AND INCOME REPRESENTATIONS ARE ASPIRATIONAL ONLY.
            </p>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Your success is entirely dependent on your own effort, dedication, skills, and circumstances.
              We make no guarantees regarding your ability to earn income through our platform or any products,
              services, or strategies we discuss.
            </p>
            <p className="mb-4" style={{ color: "var(--text-secondary)" }}>
              Most people who use our platform or similar tools will not achieve substantial income. Those who do
              achieve success typically have invested significant time, effort, and resources into their businesses.
            </p>
            <p className="font-semibold" style={{ color: "var(--text-primary)" }}>
              THERE IS NO GUARANTEE THAT YOU WILL EARN ANY MONEY USING THE TECHNIQUES AND IDEAS PROVIDED.
              EXAMPLES IN TESTIMONIALS ARE EXCEPTIONAL RESULTS AND DON'T APPLY TO THE AVERAGE USER.
            </p>
          </section>

          <section className="mb-8 p-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <h3 className="text-lg font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
              Our Commitment
            </h3>
            <p style={{ color: "var(--text-secondary)" }}>
              While we cannot guarantee your earnings, we are committed to:
            </p>
            <ul className="list-disc pl-6 mt-2 space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>Providing high-quality tools and resources</li>
              <li>Being transparent and honest in all our communications</li>
              <li>Supporting our users with helpful guidance and best practices</li>
              <li>Maintaining compliance with all applicable regulations</li>
              <li>Continuously improving our platform to serve you better</li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}
