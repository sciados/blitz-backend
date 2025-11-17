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

  // Content Hub
  "/content": {
    title: "Content Generation Hub",
    description: "Central hub for generating AI-powered marketing content. Choose between text or image generation based on your needs.",
    steps: [
      {
        number: 1,
        title: "Select Your Campaign",
        description: "Choose the campaign you want to generate content for. All generated content will use your campaign's intelligence data.",
      },
      {
        number: 2,
        title: "Choose Content Type",
        description: "Select Text Content for articles, emails, videos, social posts, landing pages, and ads. Select Image Content for marketing visuals.",
      },
      {
        number: 3,
        title: "Configure Settings",
        description: "In the next screen, configure specific settings like tone, length, style, or aspect ratio based on your content type.",
      },
      {
        number: 4,
        title: "Generate Content",
        description: "AI will create content using your campaign's intelligence data (product info, target audience, marketing hooks, etc.).",
      },
      {
        number: 5,
        title: "Refine and Export",
        description: "Review, edit, regenerate, or download your content. All content is saved to your library for future use.",
      },
    ],
    tips: [
      "Always select a campaign first - content quality depends on campaign intelligence",
      "Use Text Content for copywriting (emails, articles, scripts)",
      "Use Image Content for visual marketing assets",
      "Generated content uses your campaign's product info, audience insights, and marketing angles",
      "All content is automatically saved to your library",
    ],
  },

  // Text Content Generation
  "/content/text": {
    title: "Text Content Generation",
    description: "Create, edit, and manage all your marketing text content with automatic compliance checking.",
    steps: [
      {
        number: 1,
        title: "Verify Campaign",
        description: "Your selected campaign is shown at the top. Content will use this campaign's intelligence data.",
      },
      {
        number: 2,
        title: "Choose Content Type",
        description: "Select the type of content you need (article, email, video script, social post, landing page, ad copy).",
      },
      {
        number: 3,
        title: "Set Parameters",
        description: "Choose marketing angle (problem/solution, transformation, etc.), tone (professional, casual), and length.",
      },
      {
        number: 4,
        title: "Generate Content",
        description: "Click Generate to create AI-powered content with automatic FTC compliance checking.",
      },
      {
        number: 5,
        title: "Review and Fix Compliance",
        description: "Check compliance score, fix any issues with 'Fix Compliance' button, then copy or download your content.",
      },
    ],
    tips: [
      "Generate multiple variations to test what works best",
      "Always run compliance checks before publishing",
      "Use 'Fix Compliance' button to automatically correct FTC issues",
      "Email sequences generate multiple emails in one click",
      "Track which content performs best for future reference",
    ],
  },

  // Image Content Generation
  "/content/images": {
    title: "AI Image Generation",
    description: "Generate professional marketing images using rotating AI platforms with your campaign intelligence data.",
    steps: [
      {
        number: 1,
        title: "Verify Campaign",
        description: "Your selected campaign is shown at the top. Images will be generated using this campaign's intelligence data.",
      },
      {
        number: 2,
        title: "Choose Image Type",
        description: "Select the type of image: hero images, product shots, social media graphics, ad creatives, email headers, blog features, infographics, or comparison images.",
      },
      {
        number: 3,
        title: "Pick Style and Aspect Ratio",
        description: "Choose artistic style (photorealistic, artistic, minimalist, etc.) and aspect ratio (1:1 for Instagram, 16:9 for YouTube, 9:16 for Stories).",
      },
      {
        number: 4,
        title: "Generate Image",
        description: "Click Generate to create your image. The system rotates through multiple AI providers to optimize cost and quality.",
      },
      {
        number: 5,
        title: "Download or Regenerate",
        description: "Download images you like or regenerate to get a different result. All images are saved to your library.",
      },
    ],
    tips: [
      "Images are generated using your campaign intelligence for better relevance",
      "Leave custom prompt blank to auto-generate from campaign data",
      "Use different aspect ratios for different platforms",
      "Regenerate images to try different AI providers and styles",
      "Download high-res images directly from the library",
      "All generated images include provider, model, and cost information",
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

  // Profile
  "/profile": {
    title: "User Profile",
    description: "Manage your account information, upload a profile image, view your statistics, and configure security settings.",
    steps: [
      {
        number: 1,
        title: "Edit Your Profile",
        description: "Click 'Edit Profile' to update your full name and upload a profile image.",
      },
      {
        number: 2,
        title: "Upload Profile Image",
        description: "Click 'Choose image file' to select a photo (JPG, PNG, GIF, or WebP, max 5MB). Preview appears instantly, then click 'Upload' to save.",
      },
      {
        number: 3,
        title: "View Your Statistics",
        description: "Scroll down to see user-type-specific statistics. Product Developers see product and affiliate metrics, while Affiliate Marketers see campaign and content stats.",
      },
      {
        number: 4,
        title: "Review Account Security",
        description: "Check the Account Security section to manage your password and view active sessions.",
      },
    ],
    tips: [
      "Profile images appear in the header dropdown and throughout the platform",
      "Recommended image size is 400x400px for best results",
      "Your account type (Product Developer or Affiliate Marketer) determines which statistics you see",
      "Profile information is visible to other users when you collaborate on campaigns",
      "Keep your email up to date as it's used for important notifications",
    ],
  },

  // Products
  "/products": {
    title: "Product Library",
    description: "Browse available products to promote, or add your own products for affiliates to discover. The Product Library is the central marketplace connecting Product Developers and Affiliate Marketers.",
    steps: [
      {
        number: 1,
        title: "Browse Available Products",
        description: "Scroll through product cards to find items you want to promote. Click any card to view full details.",
      },
      {
        number: 2,
        title: "View Product Details",
        description: "Click a product card to open the details panel showing description, category, commission info, and marketing intelligence.",
      },
      {
        number: 3,
        title: "Create Campaign (Affiliates)",
        description: "In the product details panel, click 'Create Campaign' to start promoting that product with pre-filled information.",
      },
      {
        number: 4,
        title: "Add Your Products (Developers)",
        description: "Product Developers can add their own products by clicking 'Add Product' and filling in product details, pricing, and commission structure.",
      },
    ],
    tips: [
      "Use the search bar to find products by name or category",
      "Filter by commission type (recurring vs one-time) to match your promotion strategy",
      "Products with compiled intelligence provide better marketing insights",
      "Look for products with high commission rates and proven conversion rates",
      "Product Developers: detailed product information helps affiliates promote more effectively",
      "Creating a campaign from the Product Library auto-fills product details",
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
