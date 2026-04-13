---
title: "Week 6 — B2C Strategy, UX Design & Conversion Optimization"
description: "B2C e-commerce strategy, customer acquisition channels, UX design principles, checkout optimization, CRO methodology, and SEO techniques for ITEC 442."
---

# Week 6 — B2C Strategy, UX Design & Conversion Optimization

> **Course Objectives:** CO1 (Evaluate e-commerce business models and strategies), CO3 (Apply user experience and design principles to e-commerce systems)

---

## Learning Objectives

- [x] Construct a B2C e-commerce strategy framework aligned with business goals
- [x] Compare customer acquisition channels by CAC, scalability, and intent
- [x] Calculate and interpret the CAC-to-CLV ratio for business viability
- [x] Apply Fitts's Law, Hick's Law, and visual hierarchy to interface design
- [x] Design information architecture and navigation systems for e-commerce sites
- [x] Optimize product pages, shopping carts, and checkout flows for conversion
- [x] Implement a systematic CRO (Conversion Rate Optimization) methodology
- [x] Configure email marketing automation sequences
- [x] Implement SEO best practices and structured data markup for product pages
- [x] Evaluate Core Web Vitals and their measurable impact on revenue

---

## 1. B2C E-Commerce Strategy Framework

### 1.1 Defining B2C Strategy

Business-to-Consumer (B2C) e-commerce strategy is the deliberate plan by which a company acquires, converts, and retains individual consumers through digital channels. Unlike B2B strategy — which focuses on long-term contract relationships and multi-stakeholder buying processes — B2C strategy must optimize for volume, speed, and emotional resonance.

A complete B2C strategy integrates four interdependent pillars:

| Pillar | Focus | Key Metrics |
|--------|-------|-------------|
| **Acquisition** | Drawing qualified visitors to the site | CAC, traffic volume, channel mix |
| **Conversion** | Turning visitors into paying customers | CVR, add-to-cart rate, checkout completion |
| **Retention** | Encouraging repeat purchase and loyalty | CLV, repeat purchase rate, NPS |
| **Expansion** | Increasing average order value and cross-sell | AOV, upsell rate, basket size |

!!! tip "The Leaky Bucket Analogy"
    Think of your e-commerce funnel as a bucket. Acquisition pours water in; poor UX, slow pages, and friction in checkout are the holes. Before pouring in more water (spending on ads), plug the holes first. A 1% improvement in CVR typically costs far less than a 1% increase in traffic.

### 1.2 The E-Commerce Flywheel

Amazon popularized the *flywheel* concept — a self-reinforcing cycle in which lower prices attract more customers, more customers attract more sellers, more sellers increase selection, better selection drives more traffic, and scale reduces costs enabling lower prices again.

For a mid-market B2C retailer, the flywheel looks slightly different:

```
Better UX → Higher Conversion
        ↓
More Revenue → More Inventory Choice
        ↓
More Choice → Better SEO Rankings
        ↓
More Traffic → Better UX (from data)
```

### 1.3 Market Positioning in B2C

Effective B2C positioning answers three questions:

1. **Who** is the target customer (ICP — Ideal Customer Profile)?
2. **What** unique value does the brand deliver?
3. **Why** should the customer choose this brand over alternatives?

Positioning strategies include:
- **Price leadership** (Wish, AliExpress) — compete on lowest cost
- **Differentiation** (Warby Parker, Allbirds) — compete on unique product or brand identity
- **Niche focus** (Chewy for pets, REI for outdoor) — serve a specific segment exceptionally well
- **Convenience** (Amazon Prime, Instacart) — compete on speed, selection, and ease

---

## 2. Customer Acquisition Channels

### 2.1 Channel Overview and Economics

No single acquisition channel suits every business. The optimal mix depends on product category, margin, target demographic, and stage of growth. The table below summarizes each major channel.

| Channel | Avg. CAC Range | Time to Results | Scalability | Intent Level |
|---------|---------------|-----------------|-------------|--------------|
| SEO (Organic) | $10–$50 | 3–12 months | High | High |
| SEM / PPC | $20–$200+ | Days | Very High | Very High |
| Social (Paid) | $15–$100 | Days | High | Medium |
| Email Marketing | $1–$10 | Days | Medium | High |
| Affiliate | 5–30% commission | Weeks | High | Medium–High |
| Influencer | $30–$500+ | Weeks | Medium | Medium |
| Content Marketing | $5–$40 | 6–18 months | High | Medium |

### 2.2 Search Engine Optimization (SEO)

SEO for e-commerce operates at multiple levels:

=== "Technical SEO"
    - **Crawlability:** XML sitemaps submitted to Google Search Console; `robots.txt` allowing product and category pages
    - **Indexability:** Canonical tags on paginated category pages; `noindex` on duplicate thin pages
    - **Site structure:** Flat architecture (≤3 clicks from homepage to any product)
    - **Core Web Vitals:** LCP < 2.5s, FID/INP < 200ms, CLS < 0.1
    - **Schema markup:** Product, BreadcrumbList, Review, Organization schemas

=== "On-Page SEO"
    - Unique, keyword-rich title tags (50–60 characters): `{Product Name} | {Category} | {Brand}`
    - Meta descriptions with CTAs (150–160 characters)
    - H1 containing primary keyword
    - Image alt text describing product (not just "img001.jpg")
    - Unique product descriptions (avoid manufacturer boilerplate)
    - Internal linking from blog/content to product pages

=== "Off-Page SEO"
    - Link earning through PR, digital partnerships, and reviews
    - Branded mentions (Google uses co-citation signals)
    - Guest posting on industry publications
    - Product syndication on niche directories

!!! info "E-Commerce SEO Fact"
    According to BrightEdge (2023), organic search drives **53% of all website traffic** on average across e-commerce sites. Despite this, many brands dramatically under-invest in SEO relative to paid search.

### 2.3 Search Engine Marketing (SEM) / PPC

Pay-Per-Click advertising on Google and Microsoft Ads offers immediate visibility for high-intent commercial searches.

**Key PPC concepts:**

- **Quality Score (QS):** Google's 1–10 rating based on expected CTR, ad relevance, and landing page experience. Higher QS lowers cost-per-click (CPC).
- **Ad Rank:** `Bid × QS × Expected Impact of Extensions`
- **ROAS (Return on Ad Spend):** Revenue ÷ Ad Spend. A ROAS of 4× means $4 revenue per $1 spent.
- **Shopping Campaigns / Performance Max:** Google's product listing ads (PLAs) show product images, prices, and store names. They require a properly optimized Google Merchant Center feed.

**Campaign structure best practice:**

```
Account
├── Brand Campaign (protect branded traffic)
├── Competitor Campaign (intercept competitor searches)
├── Category Campaigns (broad product categories)
│   └── Ad Groups by subcategory
│       └── Responsive Search Ads
└── Shopping / PMax Campaign
    └── Asset Groups by product category
```

### 2.4 Social Media Advertising

=== "Meta (Facebook/Instagram)"
    - Largest social commerce platform by ad revenue
    - **Campaign Objective options:** Awareness, Traffic, Engagement, Leads, Sales
    - **Pixel tracking:** `fbq('track', 'Purchase', {value: 29.99, currency: 'USD'});`
    - **Custom Audiences:** Retarget cart abandoners, past purchasers, email list
    - **Lookalike Audiences:** 1–5% similarity to seed audience
    - Strong for visual products: fashion, beauty, home décor

=== "TikTok Ads"
    - Fastest-growing social commerce platform
    - **In-Feed Ads:** Native video ads in For You Page
    - **TikTok Shop:** In-app product catalog and checkout
    - Particularly effective for Gen Z and Millennial demographics
    - UGC-style creative significantly outperforms polished production

=== "Pinterest Ads"
    - High purchase intent: 85% of weekly Pinners have made a purchase from a Pin
    - Strong for home, fashion, food, DIY categories
    - **Shopping Ads:** Catalog-based ads linked to product pages
    - **Idea Pins:** Shoppable content pins

### 2.5 Email Marketing

Email consistently delivers the highest ROI of any digital channel — **$36–$42 per dollar spent** according to Litmus (2023).

**List building strategies:**
- Exit-intent popups with discount incentive
- Post-purchase opt-in for loyalty programs
- Content upgrades (size guides, lookbooks)
- SMS-to-email cross-promotion

**Segmentation variables:** purchase history, browse behavior, geography, engagement tier (active/lapsed/churned), demographics, acquisition source.

### 2.6 Affiliate and Influencer Marketing

**Affiliate marketing** operates on a performance basis — affiliates earn a commission (typically 3–15% for physical goods) for each sale they refer. Major affiliate networks include:
- **ShareASale / Awin** — general merchandise
- **CJ Affiliate** — large brands
- **Amazon Associates** — universal product links
- **Impact.com** — SaaS-style affiliate management

**Influencer marketing** tiers:

| Tier | Followers | Avg. Engagement | Best Use Case |
|------|-----------|-----------------|---------------|
| Nano | 1K–10K | 5–8% | Hyper-local, authentic |
| Micro | 10K–100K | 3–6% | Niche audiences |
| Macro | 100K–1M | 1–3% | Broad awareness |
| Mega/Celebrity | 1M+ | 0.5–1.5% | Mass brand awareness |

---

## 3. CAC vs. CLV — The Unit Economics of E-Commerce

### 3.1 Calculating Customer Acquisition Cost

$$\text{CAC} = \frac{\text{Total Marketing \& Sales Spend}}{\text{Number of New Customers Acquired}}$$

!!! warning "Common CAC Mistakes"
    - Including retained-customer marketing spend in the numerator
    - Forgetting to include salaries of marketing/sales staff
    - Using a channel-level CAC without blended CAC for full-picture health
    - Not distinguishing paid CAC from organic (blended) CAC

**Example:** A DTC brand spent $120,000 on paid ads, $18,000 on agency fees, and $12,000 in affiliate commissions in Q1, acquiring 1,500 new customers.

$$\text{CAC} = \frac{\$120,000 + \$18,000 + \$12,000}{1,500} = \$100$$

### 3.2 Calculating Customer Lifetime Value

$$\text{CLV} = \text{AOV} \times \text{Purchase Frequency} \times \text{Customer Lifespan}$$

Or using a margin-adjusted formula:

$$\text{CLV} = \frac{\text{AOV} \times \text{Gross Margin} \times \text{Purchase Frequency}}{1 - \text{Retention Rate} + \frac{\text{Discount Rate}}{\text{Purchase Frequency}}}$$

**Example:** AOV = $75, gross margin = 45%, purchases per year = 3, retention rate = 60%, discount rate = 10%.

$$\text{CLV} = \frac{75 \times 0.45 \times 3}{1 - 0.60 + \frac{0.10}{3}} \approx \frac{101.25}{0.433} \approx \$234$$

### 3.3 The CLV:CAC Ratio

The **CLV:CAC ratio** is the single most important unit economics metric for e-commerce health.

| Ratio | Interpretation | Action |
|-------|---------------|--------|
| < 1:1 | Losing money on every customer | Stop acquisition; fix fundamentals |
| 1:1 – 2:1 | Barely viable; slow payback | Optimize CRO and retention first |
| 3:1 | Healthy benchmark | Invest in scaling acquisition |
| 5:1+ | Strong; potentially under-investing | Increase acquisition spend |

**Payback Period:**
$$\text{Payback Period (months)} = \frac{\text{CAC}}{\text{Monthly Revenue per Customer} \times \text{Gross Margin}}$$

!!! success "Industry Benchmarks"
    - SaaS target: 3:1 CLV:CAC with < 12 month payback
    - E-commerce target: 3:1+ CLV:CAC with < 6 month payback
    - Subscription e-commerce: 4:1+ due to high churn risk in early months

---

## 4. UX Design Principles for E-Commerce

### 4.1 Fitts's Law

Formulated by Paul Fitts in 1954, **Fitts's Law** predicts the time required to move a pointer to a target:

$$T = a + b \log_2 \left(\frac{D}{W} + 1\right)$$

Where:
- *T* = movement time
- *D* = distance to the target
- *W* = width (size) of the target
- *a* and *b* are empirical constants

**E-commerce implications:**
- **Add to Cart** buttons should be large (≥44px touch target per Apple HIG) and high-contrast
- Place primary CTAs in locations users naturally reach (e.g., below product title on mobile, not after a long description)
- Avoid placing destructive actions (Remove, Cancel) near primary positive actions
- Navigation items used frequently should be larger and closer to the user's starting position (top-left, bottom tab bar on mobile)

### 4.2 Hick's Law

**Hick's Law** states that decision time increases logarithmically with the number of choices:

$$RT = a + b \log_2(n+1)$$

Where *n* is the number of choices presented.

**E-commerce implications:**
- Limit top navigation to 5–7 categories (Miller's Law: 7±2 items in working memory)
- Use progressive disclosure: show 12–24 products per page; paginate or infinite scroll rather than dumping 200 SKUs
- Filter/facet systems help — but only when they reduce the effective choice set the user perceives
- One primary CTA per page section (avoid competing "Buy Now," "Add to Cart," "Save for Later," and "Get Quote" all at the same visual level)

### 4.3 Visual Hierarchy

Visual hierarchy guides the user's eye in a deliberate sequence using:

| Principle | Technique | E-Commerce Application |
|-----------|-----------|------------------------|
| **Size** | Larger elements draw attention first | Product images dominate; price prominent |
| **Color** | Contrast and saturation create emphasis | CTA buttons in high-contrast accent color |
| **Position** | Top-left and top-center scanned first (F-pattern) | Logo, search, cart in header |
| **Whitespace** | Space around elements increases perceived importance | Generous padding around Add to Cart |
| **Typography** | Weight and scale create text hierarchy | H1 product name, large price, body description |
| **Motion** | Animation draws the eye (use sparingly) | Cart count increment, hover states |

### 4.4 Information Architecture and Navigation Design

**Information Architecture (IA)** is the structural design of shared information environments. For e-commerce, IA governs how products are organized, labeled, and navigated.

**Faceted Classification vs. Hierarchical Taxonomy:**

=== "Hierarchical Taxonomy"
    Best for smaller catalogs with clear parent-child relationships.
    ```
    Clothing → Men's → Shirts → Dress Shirts
                              → Casual Shirts
                    → Pants → Chinos
                            → Jeans
    ```
    - Simple to navigate
    - Products belong to one category
    - Difficult for products that span multiple categories

=== "Faceted Classification"
    Best for large catalogs. Users can filter by multiple orthogonal attributes simultaneously.
    ```
    Product attributes (facets):
    - Category: Shirts | Pants | Shoes
    - Size: XS | S | M | L | XL
    - Color: Black | White | Blue | Red
    - Brand: Nike | Adidas | Puma
    - Price: $0–$50 | $50–$100 | $100+
    - Customer Rating: ★★★★☆ and above
    ```
    - Enables cross-category discovery
    - Requires robust metadata on all products
    - Presents deduplication and URL canonicalization challenges

**Navigation patterns:**

- **Mega-menu:** Best for large category trees; shows subcategories on hover/click
- **Hamburger menu:** Standard on mobile; reduces visible navigation
- **Breadcrumb trail:** Critical for SEO and wayfinding deep in the taxonomy
- **Sticky header with search:** Users should never lose access to search
- **Predictive search / autocomplete:** Reduces friction; should handle typos and synonyms

!!! tip "Card Sorting for IA Validation"
    Before building navigation, conduct **card sorting studies** with 15–30 users. Give participants cards with product category names and ask them to group them logically. Tools: Optimal Workshop, UserZoom, Maze. Open card sorting reveals users' mental models; closed card sorting validates a proposed structure.

---

## 5. Product Page Optimization

### 5.1 Product Images

Product imagery is the single largest conversion driver on a product page. Research by Etsy (2022) found that image quality is the #1 factor in purchase decisions for 90% of online shoppers.

**Image requirements:**
- Minimum 1000×1000px to enable zoom functionality
- White background primary shot + lifestyle shots + detail shots + scale shot + 360° or video
- Mobile: touch-swipeable image gallery with dot pagination
- WebP format with JPEG fallback; lazy loading for below-the-fold images
- Average 6–8 images per product significantly outperforms 1–3 images

**Video:** Product video on the page increases conversion by 64–85% (Retail Dive). Short (15–30s) autoplay (muted) demos are most effective.

### 5.2 Product Descriptions

A product description must answer three questions:
1. **What is it?** — Clear, specific headline and first sentence
2. **What does it do for me?** — Benefits over features
3. **Why should I trust this?** — Materials, certifications, social proof

**F-A-B framework:**
- **Feature:** 100% merino wool
- **Advantage:** Naturally temperature-regulating and odor-resistant
- **Benefit:** Stay comfortable through a 12-hour travel day without worrying about smell

**SEO-integrated description structure:**
```html
<h1>Men's Merino Wool Travel Shirt</h1>
<p class="short-desc">Lightweight, wrinkle-resistant...</p>
<div class="accordion">
  <h3>Features & Benefits</h3>
  <h3>Materials & Care</h3>
  <h3>Sizing Guide</h3>
  <h3>Shipping & Returns</h3>
</div>
```

### 5.3 Social Proof

Social proof is one of Cialdini's six principles of influence and a critical conversion lever.

| Social Proof Type | Implementation | Avg. CVR Lift |
|------------------|----------------|---------------|
| Star ratings (aggregate) | 4.2 ★ (847 reviews) near product title | +15–20% |
| Review count | "847 verified reviews" | +10% |
| Photo reviews | Customer-uploaded images in review section | +25% |
| "X people viewed this today" | Real-time social activity | +8–12% |
| "Only 3 left" (scarcity) | Inventory-triggered urgency | +14–20% |
| Press mentions | "As seen in Forbes, Oprah" | +5–8% |
| Certifications | "Certified B-Corp", "USDA Organic" | Category-dependent |

!!! warning "Dark Patterns to Avoid"
    Fabricating scarcity ("Only 1 left!" when 500 are in stock), fake countdown timers, or manufactured "X people bought this today" messages are deceptive and may violate FTC guidelines. The FTC has taken action against companies using fake urgency since 2021. Build real urgency from real data.

### 5.4 Call-to-Action Design

The Add to Cart / Buy Now button is the most important UI element on a product page.

**CTA best practices:**
- **Color:** Use a color not used elsewhere on the page (reserved exclusively for primary CTAs)
- **Label:** Action-oriented ("Add to Cart" performs better than "Buy"); "Add to Bag" beats "Add to Cart" in fashion
- **Size:** Minimum 44×44px (iOS HIG), ideally 48×56px on mobile
- **Position:** Visible without scrolling on ≥80% of target devices (above the fold)
- **Sticky CTA bar:** On mobile, a fixed bottom bar with price + Add to Cart increases conversion on long product pages

---

## 6. Checkout Flow Optimization

### 6.1 Shopping Cart Design

The cart is the last staging area before purchase commitment. Cart abandonment averages **70.19%** across e-commerce (Baymard Institute, 2023).

**Cart design principles:**
- Show thumbnail image, product name, variant (size/color), quantity (editable), unit price, and subtotal
- Provide an order summary with shipping estimate and taxes before checkout begins
- Display trust badges (SSL seal, return policy, secure checkout) in the cart
- Show progress toward free shipping threshold: "Add $12.47 more for FREE shipping!"
- Cross-sell/upsell in cart should be subtle and relevant — avoid disrupting purchase momentum

### 6.2 Checkout Flow Architecture

=== "One-Page Checkout"
    All checkout steps (contact, shipping, payment) on a single scrollable page.
    
    **Pros:**
    - Reduced perceived effort (user can see the whole form at once)
    - Fewer HTTP requests / page loads
    - Better for simple orders (single item, known address)
    
    **Cons:**
    - Can feel overwhelming on mobile
    - Harder to implement address validation and payment method switching
    
    **Best for:** Single-product stores, subscription boxes, donation flows

=== "Multi-Step Checkout"
    Checkout broken into 2–4 distinct steps with a progress indicator.
    
    **Typical steps:**
    1. Cart Review
    2. Contact & Shipping Information
    3. Shipping Method Selection
    4. Payment & Order Review
    
    **Pros:**
    - Less cognitive load per screen
    - Clear progress indication reduces anxiety
    - Easier to implement conditional logic (address → available shipping methods)
    
    **Cons:**
    - Each step is an opportunity to abandon
    - Requires proper state management (don't lose form data on back navigation)
    
    **Best for:** Complex orders, multi-item carts, international shipping, B2B checkout

=== "Accelerated Checkout"
    Express lanes that bypass the full checkout:
    - **Shop Pay / PayPal Express / Apple Pay / Google Pay:** Pre-fill shipping and payment from stored credentials
    - **One-click reorder:** Repeat customers bypass all steps
    - **Auto-fill:** Browser/Google autofill reduces keystrokes
    
    Baymard research shows **26% of US adults have abandoned checkout because "the checkout process was too long/complicated."** Accelerated checkout directly addresses this.

### 6.3 Guest Checkout

Forcing account creation before purchase is the **#1 checkout abandonment cause** (Baymard, 2023 — cited by 26% of abandoners).

**Best practice:** Offer guest checkout as the default primary path. After order confirmation, prompt: "Create an account to track your order and save for next time" — at this point, you already have their email and shipping address; they only need to set a password.

**Account creation conversion on post-purchase confirmation pages:** 40–60% opt-in rate versus 10–20% if required at checkout entry.

### 6.4 Form Design Best Practices

| Principle | Implementation | Why It Matters |
|-----------|---------------|----------------|
| Inline validation | Validate field on blur, not on submit | Reduces re-submission friction |
| Smart defaults | Auto-detect country from IP; pre-populate state | Fewer required keystrokes |
| Input types | `type="tel"` for phone, `type="email"` for email | Correct keyboard on mobile |
| Autocomplete attributes | `autocomplete="shipping address-line1"` | Enables browser/Google autofill |
| Single-column layout | Stack fields vertically on mobile | Reduces horizontal scrolling |
| Clear error messages | "Please enter a valid ZIP code (5 digits)" | Actionable, not generic |
| Card field formatting | Auto-format 4444 5555 6666 7777; auto-advance field | Reduces errors |

---

## 7. Conversion Rate Optimization (CRO) Methodology

### 7.1 The CRO Process

CRO is not random A/B testing. It is a systematic, evidence-based methodology:

```
1. RESEARCH (Quantitative + Qualitative)
      ↓
2. HYPOTHESIS GENERATION
      ↓
3. PRIORITIZATION (ICE / PIE Score)
      ↓
4. EXPERIMENT DESIGN
      ↓
5. IMPLEMENTATION
      ↓
6. ANALYSIS & STATISTICAL VALIDATION
      ↓
7. ITERATION
```

### 7.2 Quantitative Research Tools

- **Google Analytics 4 / Adobe Analytics:** Funnel analysis, drop-off points, segment behavior
- **Heatmaps (Hotjar, Microsoft Clarity):** Click maps, scroll maps, attention maps
- **Session Recordings:** Watch real user sessions to identify confusion and friction
- **Form Analytics:** Which fields cause abandonment, re-entry, or hesitation

### 7.3 Qualitative Research Tools

- **User interviews:** 5 moderated sessions reveal ~85% of major usability issues (Nielsen Norman)
- **Usability testing:** Task completion rates, time on task, error rates
- **On-site surveys (Hotjar Surveys, Qualaroo):** "What stopped you from completing your purchase today?"
- **Customer support ticket analysis:** Recurring questions indicate confusing UX

### 7.4 Hypothesis Prioritization

The **ICE Score** framework prioritizes experiments:

$$\text{ICE Score} = \frac{\text{Impact} + \text{Confidence} + \text{Ease}}{3}$$

Where each dimension is rated 1–10:
- **Impact:** If this test wins, how significantly will it move the primary metric?
- **Confidence:** How confident are we this will be a positive change (based on data)?
- **Ease:** How easy is it to implement and run this test?

### 7.5 Statistical Validity in A/B Testing

!!! danger "Invalid A/B Test Practices"
    - **Peeking:** Stopping a test as soon as you see significant results (inflates false positive rate)
    - **Running multiple variations without correction:** Use Bonferroni correction for multi-variant tests
    - **Insufficient sample size:** Calculate required sample size BEFORE running the test
    - **Not separating test segments:** New vs. returning users may respond differently

**Minimum detectable effect (MDE) calculation:**

For a baseline CVR of 3%, to detect a 0.5% absolute improvement (to 3.5%) with 80% power and 95% confidence:

- Required visitors per variant: ~19,000
- At 1,000 daily visitors (50/50 split): ~38 days needed

Use tools like Evan Miller's A/B test calculator or Optimizely's calculator.

---

## 8. Email Marketing Automation

### 8.1 Welcome Series

The welcome series is the highest-ROI email sequence. Subscribers are most engaged in the first 72 hours.

**5-Email Welcome Structure:**

| Email | Timing | Subject | Goal |
|-------|--------|---------|------|
| #1 — Welcome | Immediately | "Welcome! Here's your 10% off" | Deliver incentive, brand intro |
| #2 — Brand Story | +1 day | "Why we started [Brand]" | Build emotional connection |
| #3 — Best Sellers | +3 days | "Our most-loved products" | Drive first purchase |
| #4 — Social Proof | +5 days | "See what customers are saying" | Overcome objections |
| #5 — Urgency | +7 days | "Your discount expires tomorrow" | Convert fence-sitters |

### 8.2 Abandoned Cart Series

Average recovery rate: **5–15% of abandoned carts** with a 3-email sequence.

**Timing and content:**

```
Email 1: 1 hour after abandonment
  Subject: "You left something behind..."
  Content: Cart contents with images, soft CTA "Return to your cart"
  
Email 2: 24 hours after abandonment
  Subject: "Still thinking it over? Here's why customers love us"
  Content: Social proof + cart contents + gentle urgency
  
Email 3: 72 hours after abandonment
  Subject: "Last chance — items selling fast"
  Content: Scarcity signal + optional small incentive (5–10% off)
  Note: Only include discount in final email to avoid training customers to abandon carts for discounts
```

### 8.3 Post-Purchase Sequence

Post-purchase emails achieve **40–50% open rates** (vs. 20% industry average) because customers are engaged and expecting communication.

```
T+0: Order confirmation (transactional)
T+1 day: "Your order is being packed" (shipping prep)
T+3 days: Shipping confirmation with tracking link
T+1 day after delivery: Product care tips / how-to content
T+7 days after delivery: Review request ("How did we do?")
T+30 days: Cross-sell / replenishment ("Time for a refill?")
T+90 days: Win-back / "We miss you"
```

---

## 9. SEO, Structured Data & Core Web Vitals

### 9.1 Structured Data Markup (Schema.org)

Structured data in JSON-LD format enables **rich results** in Google SERPs — star ratings, price, availability — dramatically increasing CTR.

**Product schema example:**

```json
{
  "@context": "https://schema.org/",
  "@type": "Product",
  "name": "Men's Merino Wool Travel Shirt",
  "image": [
    "https://example.com/photos/shirt-front.jpg",
    "https://example.com/photos/shirt-back.jpg"
  ],
  "description": "Lightweight, wrinkle-resistant merino wool shirt for travel.",
  "sku": "MWT-SHIRT-001",
  "brand": {
    "@type": "Brand",
    "name": "TrailBlazer Co."
  },
  "offers": {
    "@type": "Offer",
    "url": "https://example.com/products/merino-travel-shirt",
    "priceCurrency": "USD",
    "price": "89.95",
    "priceValidUntil": "2025-12-31",
    "itemCondition": "https://schema.org/NewCondition",
    "availability": "https://schema.org/InStock"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.6",
    "reviewCount": "847"
  }
}
```

### 9.2 Core Web Vitals and Conversion Impact

Google's Core Web Vitals are both a ranking signal and a conversion driver.

| Metric | Full Name | Good Threshold | Poor Threshold | CVR Impact |
|--------|-----------|---------------|----------------|------------|
| **LCP** | Largest Contentful Paint | ≤ 2.5s | > 4s | Deloitte: 0.1s faster → +1% CVR |
| **INP** | Interaction to Next Paint | ≤ 200ms | > 500ms | Slow interactions cause rage clicks |
| **CLS** | Cumulative Layout Shift | ≤ 0.1 | > 0.25 | Layout shift causes mis-taps |

**Google/Deloitte study (2020):** 0.1 second improvement in mobile load time led to 8.4% increase in conversions for retail and 10.1% for travel.

**Page speed optimization techniques:**
- Image optimization: WebP, responsive `srcset`, lazy loading
- Critical CSS inlining; defer non-critical JS
- CDN for static assets (Cloudflare, Fastly, AWS CloudFront)
- HTTP/2 or HTTP/3 multiplexing
- Server-side rendering or static site generation for product pages
- Browser caching with long TTLs; cache-busting via content hashing

---

## Key Vocabulary

| Term | Definition |
|------|-----------|
| **CAC** | Customer Acquisition Cost — total spend to acquire one new customer |
| **CLV / LTV** | Customer Lifetime Value — total net profit attributed to a customer over the relationship |
| **CVR** | Conversion Rate — percentage of visitors who complete a desired action |
| **AOV** | Average Order Value — average revenue per transaction |
| **ROAS** | Return on Ad Spend — revenue generated per dollar of advertising spend |
| **Fitts's Law** | Movement time to a target increases with distance and decreases with target size |
| **Hick's Law** | Decision time increases logarithmically with the number of choices |
| **CRO** | Conversion Rate Optimization — systematic process for increasing conversion rates |
| **A/B Testing** | Randomized controlled experiment comparing two variants of a page/element |
| **MDE** | Minimum Detectable Effect — smallest improvement an A/B test is designed to detect |
| **Core Web Vitals** | Google's user experience metrics: LCP, INP, CLS |
| **Schema.org** | Vocabulary for structured data markup to enable rich search results |
| **LCP** | Largest Contentful Paint — time for the largest visible element to load |
| **ICE Score** | Impact × Confidence × Ease — experiment prioritization framework |
| **Faceted Navigation** | Multi-attribute filtering system for large product catalogs |

---

## Review Questions

!!! question "Week 6 Review Questions"

    1. **A DTC apparel brand spends $80,000/month on all marketing and acquires 500 new customers/month. Their AOV is $65, gross margin is 40%, purchase frequency is 2.5×/year, and customer retention rate is 55%. Calculate the CAC, CLV, and CLV:CAC ratio. Is the business viable? What actions would you recommend?**

    2. **You are redesigning a product page for a mid-range camera. Apply Fitts's Law and Hick's Law to explain three specific design decisions you would make regarding the Add to Cart button and product variant selection. How would you test whether your decisions improved conversion?**

    3. **Compare one-page checkout vs. multi-step checkout from a UX and conversion standpoint. Under what specific circumstances would you recommend each approach? What data would you gather to make this decision for a new e-commerce client?**

    4. **An e-commerce site has a 2.1% conversion rate. A CRO hypothesis test is designed to detect a 0.3% absolute improvement with 95% confidence and 80% power. The site receives 2,400 daily visitors. Explain the statistical concepts of statistical significance and test power, calculate the approximate test duration, and describe what happens if the test is stopped early when significance is first reached.**

    5. **Explain how each of the three Core Web Vitals (LCP, INP, CLS) directly impacts e-commerce conversion rates with a specific example for each. Then propose four technical optimizations to improve LCP on a product page that loads a large hero image.**

---

## Further Reading

- Baymard Institute. (2023). *E-Commerce UX Research*. [baymard.com/research](https://baymard.com/research) — Industry-leading UX and checkout research with over 90,000 hours of studies
- Nielsen Norman Group. (2023). *E-Commerce User Experience*. [nngroup.com](https://www.nngroup.com) — Foundational UX research reports
- Google Web.dev. (2024). *Core Web Vitals*. [web.dev/vitals](https://web.dev/vitals) — Official Google CWV documentation
- Eisenberg, B., & Eisenberg, J. (2006). *Call to Action: Secret Formulas to Improve Online Results*. Thomas Nelson.
- Cialdini, R. B. (2006). *Influence: The Psychology of Persuasion*. Harper Business.
- Kaushik, A. (2010). *Web Analytics 2.0*. Sybex. — Foundational analytics strategy text
- Google. (2023). *Structured Data Documentation*. [developers.google.com/search/docs/appearance/structured-data](https://developers.google.com/search/docs/appearance/structured-data)

---

[← Week 5](week05.md) | [Course Index](index.md) | [Week 7 →](week07.md)
