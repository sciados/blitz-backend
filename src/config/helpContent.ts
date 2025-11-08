// Centralized help content configuration for all pages
// This provides context-sensitive help in the right sidebar
//
// ⚠️ IMPORTANT: Every new page MUST have help content added here!
//
// When creating a new page:
// 1. Add a new entry to the helpContent object below
// 2. Use the page route as the key (e.g., "/your-page")
// 3. Include: title, description, steps (3-6), and tips (3-5)
// 4. For dynamic routes, use pattern syntax (e.g., "/campaigns/[id]")
//
// See CLAUDE.md for complete documentation and templates

export type HelpContent = {
  title: string;
  description: string;
  steps?: {
    number: number;
    title: string;
    description: string;
  }[];
  tips?: string[];
  links?: {
    label: string;
    href: string;
  }[];
};

export const helpContent: Record<string, HelpContent> = {
  // Dashboard
  "/dashboard": {
    title: "Dashboard Overview",
    description: "Your central hub with quick access to key features. Dashboard content varies based on your account type (Product Developer or Affiliate Marketer).",
    steps: [
      {
        number: 1,
        title: "Product Developers",
        description: "Access Product Library to add your products, and use Product Analytics to track how affiliates are promoting them.",
      },
      {
        number: 2,
        title: "Affiliate Marketers",
        description: "Create campaigns, browse the Product Library, generate content, and track your marketing performance.",
      },
      {
        number: 3,
        title: "Quick Navigation",
        description: "Click any card to navigate directly to that feature. The dashboard shows only the features relevant to your account type.",
      },
      {
        number: 4,
        title: "Getting Started Guide",
        description: "Check the 'Getting Started' section at the bottom for helpful tips and next steps.",
      },
    ],
    tips: [
      "Your dashboard is personalized based on whether you're a Product Developer or Affiliate Marketer",
      "Product Developers see: Product Library, Product Analytics, Settings",
      "Affiliate Marketers see: Campaigns, Content, Intelligence, Compliance, Analytics",
      "All users can access the Product Library - it's the shared marketplace",
      "Check your account type badge in the left sidebar (purple for Product Developers, blue for Affiliate Marketers)",
    ],
  },

  // Campaigns List
  "/campaigns": {
    title: "Campaign Management",
    description: "Create and manage your affiliate marketing campaigns. Each campaign represents a product you're promoting.",
    steps: [
      {
        number: 1,
        title: "Create Your First Campaign",
        description: "Click 'Create Campaign' and fill in the basic information about the product you're promoting.",
      },
      {
        number: 2,
        title: "Add Product Details",
        description: "Include the sales page URL, affiliate network, keywords, and product description.",
      },
      {
        number: 3,
        title: "Review and Edit",
        description: "Click on any campaign card or the Edit button to view details and make changes.",
      },
      {
        number: 4,
        title: "Generate Content",
        description: "Once your campaign is set up, use it to generate marketing content and intelligence.",
      },
    ],
    tips: [
      "Use descriptive campaign names to easily identify them later",
      "Add relevant keywords to improve content generation",
      "Keep product descriptions detailed but concise",
      "Update campaign status as you progress through your workflow",
    ],
  },

  // Campaign Details
  "/campaigns/[id]": {
    title: "Campaign Details",
    description: "View and manage all aspects of your campaign, from basic information to generated content.",
    steps: [
      {
        number: 1,
        title: "Review Campaign Info",
        description: "Check all campaign details including product URL, keywords, and description.",
      },
      {
        number: 2,
        title: "Update Campaign Status",
        description: "Change status between Draft, Active, Paused, or Completed as your campaign progresses.",
      },
      {
        number: 3,
        title: "Edit Campaign Details",
        description: "Click the Edit button to update campaign information (Note: URL and affiliate network cannot be changed).",
      },
      {
        number: 4,
        title: "Generate Intelligence",
        description: "Use 'Compile Intelligence' to analyze the sales page and extract key information.",
      },
      {
        number: 5,
        title: "Create Content",
        description: "Generate marketing content based on your campaign and intelligence data.",
      },
      {
        number: 6,
        title: "Check Compliance",
        description: "Verify your content meets FTC guidelines and affiliate network requirements.",
      },
    ],
    tips: [
      "Set status to 'Active' when you're ready to start promoting",
      "Generate intelligence before creating content for better results",
      "Always run compliance checks before publishing content",
      "Use 'Paused' status for seasonal campaigns",
    ],
  },

  // Content
  "/content": {
    title: "Content Management",
    description: "Create, edit, and manage all your marketing content in one place.",
    steps: [
      {
        number: 1,
        title: "Select a Campaign",
        description: "Choose which campaign you want to create content for.",
      },
      {
        number: 2,
        title: "Choose Content Type",
        description: "Select the type of content you need (email, blog post, social media, etc.).",
      },
      {
        number: 3,
        title: "Generate Content",
        description: "Let AI generate content based on your campaign intelligence and parameters.",
      },
      {
        number: 4,
        title: "Review and Edit",
        description: "Review the generated content and make any necessary adjustments.",
      },
      {
        number: 5,
        title: "Run Compliance Check",
        description: "Ensure your content meets all legal and network requirements before publishing.",
      },
    ],
    tips: [
      "Generate multiple variations to test what works best",
      "Always customize AI-generated content to add your personal touch",
      "Run compliance checks before publishing",
      "Track which content performs best for future reference",
    ],
  },

  // Intelligence
  "/intelligence": {
    title: "Campaign Intelligence",
    description: "View compiled intelligence data including product information, market analysis, and marketing insights for your campaigns.",
    steps: [
      {
        number: 1,
        title: "Select a Campaign",
        description: "Use the dropdown at the top to select a campaign. Campaigns with intelligence data show a ✓ checkmark.",
      },
      {
        number: 2,
        title: "Review Product Information",
        description: "View extracted product features, benefits, and descriptions from the sales page.",
      },
      {
        number: 3,
        title: "Analyze Market Data",
        description: "Study the target audience profiles, pain points, and market positioning insights.",
      },
      {
        number: 4,
        title: "Use Marketing Intelligence",
        description: "Review marketing hooks, angles, CTAs, and testimonials to inform your content strategy.",
      },
      {
        number: 5,
        title: "Check Sales Page Analysis",
        description: "View the extracted headline, subheadline, and key messaging from the original sales page.",
      },
    ],
    tips: [
      "Intelligence data is automatically compiled when adding products to the Product Library",
      "Use the pain points and benefits to create more resonant marketing copy",
      "Reference marketing hooks and angles when generating campaign content",
      "The raw data view at the bottom shows the complete intelligence structure",
      "Campaigns without intelligence show '(No intelligence data)' in the dropdown",
    ],
  },

  // Compliance
  "/compliance": {
    title: "Compliance Management",
    description: "Ensure all your marketing content meets FTC guidelines and affiliate network requirements.",
    steps: [
      {
        number: 1,
        title: "Select Content to Check",
        description: "Choose the content piece you want to verify for compliance.",
      },
      {
        number: 2,
        title: "Run Compliance Scan",
        description: "The system will check for required disclosures, claims verification, and network policies.",
      },
      {
        number: 3,
        title: "Review Issues",
        description: "Check any flagged issues or warnings that need attention.",
      },
      {
        number: 4,
        title: "Make Corrections",
        description: "Fix any compliance issues and re-run the check.",
      },
      {
        number: 5,
        title: "Approve Content",
        description: "Once all checks pass, mark the content as compliant and ready to publish.",
      },
    ],
    tips: [
      "Always include proper affiliate disclosures",
      "Avoid making unsubstantiated claims",
      "Check compliance before publishing any content",
      "Stay updated on FTC guidelines and network policies",
      "Different networks may have different requirements",
    ],
  },

  // Analytics
  "/analytics": {
    title: "Analytics & Performance",
    description: "Track campaign performance, content effectiveness, and ROI metrics.",
    steps: [
      {
        number: 1,
        title: "Select Time Period",
        description: "Choose the date range you want to analyze.",
      },
      {
        number: 2,
        title: "Review Campaign Performance",
        description: "Check which campaigns are performing best.",
      },
      {
        number: 3,
        title: "Analyze Content Metrics",
        description: "See which content types and variations are most effective.",
      },
      {
        number: 4,
        title: "Identify Trends",
        description: "Look for patterns to inform future campaign strategies.",
      },
    ],
    tips: [
      "Compare performance across different campaigns",
      "Track conversion rates and ROI",
      "Identify top-performing content for replication",
      "Use data to optimize your marketing strategy",
    ],
  },

  // Settings
  "/settings": {
    title: "Account Settings",
    description: "Manage your account preferences, API keys, and system configuration.",
    steps: [
      {
        number: 1,
        title: "Update Profile",
        description: "Keep your account information up to date.",
      },
      {
        number: 2,
        title: "Configure Preferences",
        description: "Set your default options for content generation and compliance checks.",
      },
      {
        number: 3,
        title: "Manage API Keys",
        description: "Add or update API keys for AI services and affiliate networks.",
      },
      {
        number: 4,
        title: "Set Notification Preferences",
        description: "Choose how and when you want to receive notifications.",
      },
    ],
    tips: [
      "Keep your API keys secure and rotate them regularly",
      "Set up notification preferences to stay informed",
      "Configure default compliance rules for your networks",
      "Review your settings periodically",
    ],
  },

  // Product Developer Analytics
  "/product-analytics": {
    title: "Product Developer Analytics",
    description: "Track how affiliates are promoting your products and monitor affiliate performance across your product line.",
    steps: [
      {
        number: 1,
        title: "Review Affiliate Performance",
        description: "Check which affiliates are promoting your products and how much traffic they're driving.",
      },
      {
        number: 2,
        title: "Analyze Product Metrics",
        description: "See which products are getting the most promotion and generating the most clicks.",
      },
      {
        number: 3,
        title: "Monitor the Leaderboard",
        description: "Track top-performing affiliates and identify your best partners in the affiliate leaderboard.",
      },
      {
        number: 4,
        title: "Track Click-Through Rates",
        description: "Monitor total clicks vs unique visitors to understand traffic quality from each affiliate.",
      },
    ],
    tips: [
      "Top affiliates deserve special attention - consider reaching out to them with exclusive offers",
      "Monitor unique click rates to identify high-quality traffic sources",
      "Products with many campaigns but low clicks might need better marketing materials",
      "Use the affiliate leaderboard to create performance-based incentive programs",
      "Track which products attract the most affiliates to inform future product development",
    ],
  },
};

// Helper function to get help content by pathname
export function getHelpContent(pathname: string): HelpContent | undefined {
  // Try exact match first
  if (helpContent[pathname]) {
    return helpContent[pathname];
  }

  // Try pattern matching for dynamic routes
  if (pathname.startsWith("/campaigns/") && pathname !== "/campaigns") {
    return helpContent["/campaigns/[id]"];
  }

  // Add more pattern matches as needed for other dynamic routes

  return undefined;
}
