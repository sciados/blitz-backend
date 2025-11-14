# Frontend Changes Needed for URL Shortener & Developer Tier

## ✅ Completed
- **TypeScript Types Updated** (`src/lib/types.ts`)
  - Added `developer_tier`, `user_type`, `stripe_subscription_id` to `User` type
  - Added `affiliate_link`, `affiliate_link_short_code` to `Campaign` type
  - Added new types: `ShortenedLink`, `CreateShortLinkRequest`, `LinkAnalytics`

## 🔨 Required Frontend Changes

### 1. Campaign Form Updates

**File:** `src/app/(dashboard)/campaigns/new/page.tsx` or campaign creation component

**Changes Needed:**
- Add "Affiliate Link" input field (optional)
- Display hint: "Your affiliate URL will be automatically shortened for tracking"
- Show the generated short link after campaign creation
- Add copy-to-clipboard button for short link

**Example:**
```tsx
<div>
  <label>Affiliate Link (Optional)</label>
  <input
    type="url"
    name="affiliate_link"
    placeholder="https://example.com/your-affiliate-link"
  />
  <p className="text-sm text-gray-500">
    Your link will be automatically shortened to https://blitz.link/xxxxx
  </p>
</div>
```

### 2. Campaign Details Page Updates

**File:** `src/app/(dashboard)/campaigns/[id]/page.tsx`

**Changes Needed:**
- Display shortened link prominently if it exists
- Add "Copy Short Link" button with toast notification
- Show click statistics (total clicks, unique clicks)
- Add "View Analytics" button to see detailed click data
- Allow editing/adding affiliate link after creation

**Example UI Section:**
```tsx
{campaign.affiliate_link_short_code && (
  <div className="card p-6">
    <h3 className="font-semibold mb-2">Shortened Affiliate Link</h3>
    <div className="flex items-center gap-2">
      <code className="bg-gray-100 px-3 py-2 rounded flex-1">
        https://blitz.link/{campaign.affiliate_link_short_code}
      </code>
      <button onClick={() => copyToClipboard(shortUrl)}>
        Copy
      </button>
    </div>
    <div className="mt-4 grid grid-cols-2 gap-4">
      <div>
        <p className="text-sm text-gray-600">Total Clicks</p>
        <p className="text-2xl font-bold">{/* fetch from analytics */}</p>
      </div>
      <div>
        <p className="text-sm text-gray-600">Unique Clicks</p>
        <p className="text-2xl font-bold">{/* fetch from analytics */}</p>
      </div>
    </div>
  </div>
)}
```

### 3. Link Analytics Dashboard Component

**File:** `src/components/LinkAnalytics.tsx` (NEW)

**Features Needed:**
- Fetch analytics from `GET /api/links/{short_code}/analytics?days=30`
- Display clicks by date (line/bar chart)
- Display clicks by country (pie/bar chart)
- Display clicks by device (pie chart: mobile, tablet, desktop)
- Date range selector (7, 30, 90 days)
- Export analytics as CSV

**Tech Stack:**
- Use React Query for data fetching
- Use Recharts or Chart.js for visualizations
- Tailwind for styling

**Example:**
```tsx
"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/appClient";
import { LinkAnalytics } from "@/lib/types";
import { LineChart, Line, XAxis, YAxis, Tooltip } from "recharts";

export function LinkAnalyticsComponent({ shortCode }: { shortCode: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["linkAnalytics", shortCode],
    queryFn: async () =>
      (await api.get<LinkAnalytics>(`/api/links/${shortCode}/analytics?days=30`)).data,
  });

  if (isLoading) return <div>Loading analytics...</div>;

  return (
    <div className="space-y-6">
      <div>
        <h3>Clicks Over Time</h3>
        <LineChart data={data?.clicks_by_date} width={600} height={300}>
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="clicks" stroke="#8884d8" />
        </LineChart>
      </div>

      <div>
        <h3>Clicks by Country</h3>
        {/* Implement country breakdown */}
      </div>

      <div>
        <h3>Clicks by Device</h3>
        {/* Implement device breakdown */}
      </div>
    </div>
  );
}
```

### 4. Link Management Page

**File:** `src/app/(dashboard)/links/page.tsx` (NEW)

**Features Needed:**
- List all shortened links for user
- Filter by campaign
- Show click stats per link
- Toggle active/inactive status
- Delete links
- Create custom short links manually

**API Endpoints:**
- `GET /api/links` - List links
- `GET /api/links?campaign_id=123` - Filter by campaign
- `PATCH /api/links/{short_code}/toggle` - Toggle status
- `DELETE /api/links/{short_code}` - Delete link

### 5. User Profile - Developer Tier Badge

**File:** `src/components/Layout.tsx` or `src/app/(dashboard)/profile/page.tsx`

**Changes Needed:**
- Display developer tier badge if user has one
- Show tier benefits (product slots, features)
- Add "Upgrade Tier" button for product creators
- Link to Stripe subscription management if subscribed

**Example:**
```tsx
{user?.developer_tier && (
  <div className="flex items-center gap-2">
    <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
      {user.developer_tier === 'new' && '🌱 New Developer'}
      {user.developer_tier === 'verified' && '✅ Verified Developer'}
      {user.developer_tier === 'premium' && '⭐ Premium Developer'}
    </span>
  </div>
)}
```

### 6. Product Developer Analytics Dashboard

**File:** `src/app/(dashboard)/developer/analytics/page.tsx` (NEW)

**Features Needed:**
- Show products added by developer
- Product performance metrics:
  - Times used in campaigns
  - Content pieces generated
  - Active campaigns using product
- Quality scores
- Product approval status

**API Endpoints Needed (NOT YET CREATED IN BACKEND):**
- `GET /api/developer/products` - List developer's products
- `GET /api/developer/analytics` - Developer analytics summary
- `GET /api/developer/products/{id}/analytics` - Per-product analytics

**Note:** These backend endpoints don't exist yet and need to be created.

### 7. Navigation Menu Updates

**File:** `src/components/Layout.tsx`

**Changes Needed:**
- Add "Links" menu item for all users (to manage short links)
- Add "Developer Dashboard" menu item for product creators
- Show different menu items based on `user.user_type`

**Example:**
```tsx
// In navigation menu
{user?.user_type === 'product_creator' && (
  <Link href="/developer/dashboard">
    <span>Developer Dashboard</span>
  </Link>
)}

<Link href="/links">
  <span>Short Links</span>
</Link>
```

### 8. Content Preview - Show Short Links

**File:** Content generation/preview components

**Changes Needed:**
- When displaying generated content, highlight that affiliate URLs have been replaced
- Show both original and shortened URLs in metadata
- Add tooltip explaining click tracking

**Example:**
```tsx
<div className="bg-blue-50 border border-blue-200 p-3 rounded mb-4">
  <p className="text-sm text-blue-800">
    ℹ️ Affiliate URLs in this content have been automatically replaced with
    trackable short links (https://blitz.link/{campaign.affiliate_link_short_code})
  </p>
</div>
```

## 📊 Priority Order

1. **High Priority** (Core Functionality):
   - Campaign form affiliate link field
   - Display short link in campaign details with copy button
   - Basic click stats display

2. **Medium Priority** (Enhanced UX):
   - Link analytics dashboard with charts
   - Link management page
   - Navigation updates

3. **Low Priority** (Future Features):
   - Developer tier badge
   - Developer analytics dashboard (requires backend endpoints)
   - Advanced link management (custom slugs, UTM builder)

## 🎨 UI/UX Recommendations

1. **Copy-to-Clipboard Pattern:**
   ```tsx
   const copyToClipboard = (text: string) => {
     navigator.clipboard.writeText(text);
     toast.success("Copied to clipboard!");
   };
   ```

2. **Short Link Display:**
   - Use monospace font for links
   - Add visual indicator that link is shortened
   - Show original URL on hover/tooltip

3. **Analytics Charts:**
   - Use consistent color scheme across all charts
   - Add loading skeletons
   - Show "No data yet" state for new links

4. **Responsive Design:**
   - Charts should be responsive
   - Tables should be scrollable on mobile
   - Copy buttons should be accessible

## 🔧 Environment Variables

Add to `.env.local`:
```bash
# Short link domain (matches backend SHORT_LINK_DOMAIN)
NEXT_PUBLIC_SHORT_LINK_DOMAIN=https://blitz.link
```

## 📝 Help Content

Add to `src/config/helpContent.ts`:

```typescript
"/links": {
  title: "Manage Short Links",
  description: "View and manage all your shortened affiliate links with click tracking.",
  steps: [
    {
      number: 1,
      title: "View Your Links",
      description: "See all shortened links across all campaigns with click statistics.",
    },
    {
      number: 2,
      title: "Monitor Performance",
      description: "Click 'View Analytics' to see detailed click data by country and device.",
    },
    {
      number: 3,
      title: "Toggle Links",
      description: "Deactivate links you no longer want to track without deleting them.",
    },
  ],
  tips: [
    "Short links are automatically created when you add an affiliate link to a campaign",
    "Each click is tracked with device, location, and referrer data",
    "Use custom slugs for branded links (e.g., blitz.link/my-product)",
    "Inactive links return a 404 error - reactivate them anytime",
  ],
},

"/campaigns/[id]": {
  // Update existing campaign details help to mention short links
  tips: [
    // ... existing tips ...
    "Copy your short link to use in social media, emails, or anywhere you promote",
    "Monitor click analytics to see which channels drive the most traffic",
  ],
},
```

## 🚀 Next Steps

1. Start with campaign form updates (highest impact)
2. Add short link display to campaign details
3. Create basic analytics component
4. Build out link management page
5. Add developer tier features (lower priority)

Would you like me to implement any of these changes now?
