# Slide-to-Video: 3-Step Workflow Plan (Updated with Campaign Intelligence)

## Overview
Create a streamlined workflow where users can generate images and immediately create slide videos from them in one cohesive process. Images are generated using campaign intelligence and user-selected keywords for maximum relevance.

---

## Step-by-Step Workflow

### **STEP 1: Generate Images**
**Trigger:** User selects "Slide-to-Video" mode

**UI Components:**
- "Generate Images for Slide Video" section
- Options:
  - **Number of images**: Dropdown (1-5 images)
  - **Image type**: Hero, Social, Ad, Product Shot, etc.
  - **Aspect ratio**: 16:9, 9:16, 1:1 (match video aspect ratio)
  - **Style**: Marketing, Educational, Social

**Campaign Intelligence Integration:**
- **Auto-generate prompt**: Pulls from campaign intelligence data
  - Extracts product name, category, key features
  - Analyzes competitor images and marketing angles
  - Combines with campaign's marketing angle (problem/solution, transformation, etc.)

- **User Keywords Selection** (Optional):
  - **Ingredients**: Extracted from intelligence (e.g., "Vitamin C", "Collagen", "Probiotics")
  - **Features**: From product specs (e.g., "Sugar-Free", "Organic", "Fast-Acting")
  - **Benefits**: From marketing research (e.g., "Anti-Aging", "Energy Boost", "Weight Loss")
  - Multi-select checkbox/tags interface
  - User can add custom keywords

- **Generated Prompt Preview**:
  - Auto-populated text area based on:
    - Campaign intelligence summary
    - Selected keywords
    - Image type and style
  - User can edit/modify the generated prompt
  - Shows character count and optimization tips

**Actions:**
- "Generate Images" button (calls existing image generation API)
- Shows progress/loading state with generation details
- On success: Images appear in a grid below

**Generated Images Display:**
- Grid showing all generated images (up to 5)
- Each image has:
  - Thumbnail (150px height)
  - Edit button (opens image editor)
  - Select checkbox (for video generation)
  - Delete button

---

### **STEP 2: Edit Images (Optional)**
**Trigger:** User clicks "Edit" button on any generated image

**UI Components:**
- Modal/overlay with image editor
- Tools available:
  - **Text overlay**: Add title, subtitle, or body text
  - **Position**: Drag text to position
  - **Style**: Font size, color, background
  - **Branding**: Add logo or watermark
  - **Filters**: Basic filters (brightness, contrast, etc.)

**Actions:**
- "Save Changes" → Updates the image
- "Cancel" → Closes without saving

**Implementation Options:**
1. **Simple**: Basic text overlay only
2. **Advanced**: Full image editor (like Canva)
3. **Hybrid**: Use existing image editing library

---

### **STEP 3: Select & Generate Video**
**Trigger:** User clicks "Continue to Video Generation"

**UI Components:**
- Image selection grid (only showing images from Step 1)
- Up to 2 images can be selected (PiAPI limit)
- Selected images highlighted
- Video settings:
  - Duration (5-10 seconds)
  - Style (Marketing, Educational, Social)
  - Aspect ratio (inherited from images)

**Actions:**
- "Generate Video" button
- Redirects to video library with success message

---

## Page Layout (Single Page)

```
┌─────────────────────────────────────────┐
│ Header: Generate Slide-to-Video         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ STEP 1: Generate Images                 │
│ ┌─────────────────────────────────────┐ │
│ │ Number of images: [5 ▼]             │ │
│ │ Image type: [Hero Image ▼]          │ │
│ │ Style: [Marketing ▼]                │ │
│ │                                     │ │
│ │ Campaign Intelligence:              │ │
│ │ ✓ Product: "Mitolyn"                │ │
│ │ ✓ Category: "Supplement"            │ │
│ │                                     │ │
│ │ Select Keywords:                    │ │
│ │ [Vitamin C] [Collagen] [Anti-Aging] │ │
│ │ [Energy Boost] [Organic]            │ │
│ │ [+ Add Custom]                      │ │
│ │                                     │ │
│ │ Generated Prompt:                   │ │
│ │ ┌─────────────────────────────────┐ │ │
│ │ │ "Professional hero image of...  │ │ │
│ │ │  [Edit Prompt] (245 chars)      │ │ │
│ │ └─────────────────────────────────┘ │ │
│ │                                     │ │
│ │ [Generate Images]                   │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Generated Images:                       │
│ [Grid of images with Edit/Select]      │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ STEP 2: Edit Images (Optional)          │
│ (Only shown when editing an image)      │
│ [Image editor modal/overlay]            │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ STEP 3: Select & Generate Video         │
│ ┌─────────────────────────────────────┐ │
│ │ Select up to 2 images:              │ │
│ │ [Grid with checkboxes]              │ │
│ │                                     │ │
│ │ Video Settings:                     │ │
│ │ Duration: [10s ▼]                   │ │
│ │ Style: [Marketing ▼]                │ │
│ │                                     │ │
│ │ [Generate Video]                    │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

## Technical Implementation

### **Backend Changes:**

1. **Campaign Intelligence Endpoint**
   - `/api/intelligence/campaign/{campaign_id}`
   - Returns compiled intelligence data including:
     - Product information (name, category, description)
     - Key ingredients/components
     - Features and specifications
     - Marketing benefits and angles
     - Competitor analysis insights

2. **Prompt Generation Service**
   - Creates optimized prompts from intelligence data
   - Combines selected keywords with base campaign data
   - Applies style and image type modifiers
   - Returns formatted prompt string

3. **Image Generation Endpoint** (already exists)
   - `/api/images/generate`
   - Returns array of generated images

4. **Image Storage**
   - Generated images saved to R2
   - Assigned to campaign
   - Get unique IDs for video generation

5. **Video Generation** (already exists)
   - `/api/video/generate`
   - Accepts `slides` parameter with image URLs

### **Frontend State Management:**

```typescript
interface SlideVideoState {
  // Step 1
  numImages: number;
  imageType: string;
  style: string;

  // Campaign Intelligence
  campaignIntelligence: {
    productName: string;
    category: string;
    ingredients: string[];
    features: string[];
    benefits: string[];
    description: string;
  } | null;

  // User Selections
  selectedKeywords: {
    ingredients: string[];
    features: string[];
    benefits: string[];
    custom: string[];
  };

  generatedPrompt: string;
  generatedImages: GeneratedImage[];

  // Step 2 (optional editing)
  editingImageId: string | null;

  // Step 3
  selectedImageIds: string[];
  videoSettings: {
    duration: number;
    style: string;
    aspectRatio: string;
  };
}
```

### **Prompt Generation Logic:**

```typescript
function generateImagePrompt(
  intelligence: CampaignIntelligence,
  keywords: SelectedKeywords,
  imageType: string,
  style: string
): string {
  const base = `${intelligence.productName} - ${intelligence.description}`;

  const selectedIngredients = keywords.ingredients.join(', ');
  const selectedFeatures = keywords.features.join(', ');
  const selectedBenefits = keywords.benefits.join(', ');
  const customKeywords = keywords.custom.join(', ');

  const keywordString = [
    selectedIngredients,
    selectedFeatures,
    selectedBenefits,
    customKeywords
  ].filter(Boolean).join(', ');

  const imageTypePrompt = {
    'Hero': 'Professional hero banner image',
    'Social': 'Social media square image',
    'Ad': 'Advertisement image with compelling visuals',
    'Product Shot': 'Clean product showcase'
  }[imageType] || 'Marketing image';

  const stylePrompt = {
    'Marketing': 'Professional, engaging marketing style',
    'Educational': 'Clean, informative educational style',
    'Social': 'Dynamic, eye-catching social media style'
  }[style] || 'Professional marketing style';

  return `${imageTypePrompt} of ${base}${keywordString ? ` featuring ${keywordString}` : ''}. ${stylePrompt}. High quality, professional photography style.`;
}
```

### **User Flow:**

```
User selects "Slide-to-Video"
    ↓
Step 1: Load campaign intelligence
    ↓
Display available keywords (ingredients, features, benefits)
    ↓
User selects keywords (optional)
    ↓
Auto-generate prompt based on intelligence + keywords
    ↓
User reviews/edits prompt (optional)
    ↓
Click "Generate Images"
    ↓
Images appear in grid
    ↓
(Optional) Edit any image
    ↓
Click "Continue to Video"
    ↓
Step 2: Select up to 2 images
    ↓
Configure video settings
    ↓
Click "Generate Video"
    ↓
Success! Redirect to video library
```

---

## Benefits

1. **Intelligent Image Generation**: Uses actual campaign data for relevant images
2. **User Control**: Keyword selection allows targeting specific aspects
3. **Time Saving**: Auto-generated prompts vs. manual writing
4. **Consistency**: Images align with campaign intelligence and messaging
5. **Flexibility**: Users can still edit prompts for fine-tuning
6. **Streamlined Workflow**: Everything in one place with campaign context

---

## Alternative: Multi-Page Flow

If single page is too complex:

**Page 1:** Generate Images (with intelligence-based prompts)
**Page 2:** Edit Images (if needed)
**Page 3:** Select & Generate Video

Each page has "Back" and "Next" buttons.

---

## Questions/Decisions Needed

1. **Image Editor Complexity**:
   - Simple text overlay only?
   - Or full editor (canva-like)?

2. **Keyword Extraction**:
   - Manual selection or auto-detect all available?
   - Limit number of selectable keywords?

3. **Prompt Customization**:
   - Allow full editing or only add/remove keywords?
   - Show prompt suggestions/optimization tips?

4. **Campaign Intelligence Scope**:
   - What intelligence data to include in prompt generation?
   - How to handle campaigns without compiled intelligence?

5. **Page Layout**:
   - Single page with sections?
   - Or separate pages?

6. **Edit Persistence**:
   - Save edited images back to library?
   - Or only use for video generation?

---

## Next Steps

1. Review this plan ✓
2. Decide on questions above
3. Implement backend intelligence endpoint (if not exists)
4. Create prompt generation service
5. Build frontend workflow with keyword selection
6. Test end-to-end flow with real campaign data
