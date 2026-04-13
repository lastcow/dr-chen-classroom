---
title: "Week 5 — Market Research & Digital Analytics"
description: "Methods and tools for conducting market research and measuring e-commerce performance: primary/secondary research, A/B testing, GA4, UTM tracking, heatmaps, SEO, social listening, NPS, cohort analysis, and attribution modeling. Mapped to CO3."
---

# Week 5 — Market Research & Digital Analytics

> **Course Outcome CO3** — Design and execute market research to support e-commerce decisions; collect, analyze, and interpret digital analytics data to optimize performance across the customer journey.

---

## Learning Objectives

By the end of this week you should be able to:

- [x] Distinguish primary and secondary research methods in digital commerce contexts
- [x] Design a survey instrument appropriate for an e-commerce research question
- [x] Explain A/B testing methodology, including statistical significance, sample size, and common pitfalls
- [x] Interpret core Google Analytics 4 metrics: sessions, users, bounce rate, engagement rate, conversion rate, and funnel analysis
- [x] Construct and explain UTM parameters for campaign tracking
- [x] Describe the capabilities and use cases of heatmap and session recording tools (Hotjar, Microsoft Clarity)
- [x] Apply basic keyword research methodology and interpret SEO metrics using industry tools
- [x] Identify and use social listening and competitive intelligence techniques
- [x] Calculate and interpret Net Promoter Score (NPS) and Customer Satisfaction Score (CSAT)
- [x] Explain cohort analysis and interpret a cohort retention table
- [x] Compare attribution models (first-touch, last-touch, linear, time-decay, data-driven) and their strategic implications

---

## 1. Primary and Secondary Research in Digital Commerce

### 1.1 The Research Hierarchy

All market research begins by distinguishing what you already know from what you need to find out, and how you'll find it.

**Secondary research** uses data that already exists — collected by someone else for a different primary purpose. **Primary research** generates new data specifically for your research question.

| Dimension | Secondary Research | Primary Research |
|-----------|-------------------|-----------------|
| Cost | Low (often free or subscription) | High (time, recruitment, incentives) |
| Speed | Fast | Slow |
| Specificity | Generalized | Tailored to your exact question |
| Control | No control over methodology | Full control |
| Recency | May be outdated | Current |
| Best for | Market sizing, benchmarking, trends | Specific customer insights, testing hypotheses |

### 1.2 Secondary Research Sources for E-Commerce

**Industry reports and market data**:
- **Statista**: Aggregates statistics from 22,500+ sources; e-commerce market sizing, benchmarks
- **eMarketer / Insider Intelligence**: US and global e-commerce forecasts; paid subscription but often cited freely
- **Nielsen / NielsenIQ**: Consumer panel data; retail market share; behavioral tracking
- **Forrester Research**: B2B and B2C digital commerce research; enterprise technology adoption
- **McKinsey Global Institute**: Macro-level digital economy analysis

**Government data sources**:
- **U.S. Census Bureau**: Quarterly E-Commerce Report; Annual Retail Trade Survey
- **Bureau of Labor Statistics (BLS)**: Consumer Expenditure Survey; industry employment data
- **Federal Trade Commission (FTC)**: Consumer complaint data; enforcement trends
- **OECD Digital Economy Outlook**: International comparative data

**Platform-provided data**:
- **Google Trends**: Search volume trends; geographic interest patterns; keyword seasonality
- **Facebook Audience Insights**: Demographic and interest profiles of Facebook users
- **Amazon Bestseller Lists**: Product category demand signals
- **Shopify Partners**: Annual merchant and consumer behavior reports

!!! tip "Secondary Research Best Practices"
    Always evaluate secondary data for:
    
    1. **Recency**: Data older than 2–3 years may not reflect current digital markets, which evolve rapidly
    2. **Methodology**: How was the data collected? Sample size? Geographic scope?
    3. **Source bias**: Industry association reports may be optimistic about their sector; competitor-funded research may be biased
    4. **Definition consistency**: "E-commerce" defined differently across reports (some include services; some only physical goods)

### 1.3 Primary Research Methods in E-Commerce

**Qualitative methods** (generate insights, hypotheses):

=== "User Interviews"
    In-depth conversations (30–60 minutes) with target users about their experiences, motivations, and pain points.

    **When to use**: Early-stage research to understand the "why" behind behaviors; generating hypotheses for quantitative testing; exploring unexpected findings from analytics data.

    **E-commerce application**: Interview 8–12 customers who abandoned their cart to understand the actual barriers — the analytics can tell you *when* they left, but only qualitative research can reveal *why*.

    **Tools**: Zoom, UserTesting.com, Respondent.io (recruiting platform)

=== "Usability Testing"
    Observing real users attempting specific tasks on a website or app, while thinking aloud.

    **When to use**: Evaluating a design before launch; diagnosing checkout friction; understanding navigation confusion.

    **5-user rule** (Nielsen/Norman): Testing with 5 users uncovers ~85% of usability problems. After 5, additional users reveal diminishing returns.

    **Moderated vs. unmoderated**: Moderated testing has a facilitator present; unmoderated (e.g., UserZoom, Maze) allows remote, asynchronous testing at lower cost.

=== "Focus Groups"
    Structured group discussions (6–10 participants) moderated to explore attitudes, perceptions, and reactions.

    **Strengths**: Group dynamics can surface ideas that individual interviews wouldn't; efficient for brand/concept testing.

    **Weaknesses**: Groupthink can suppress minority opinions; dominant participants can skew results; poor predictor of actual purchase behavior.

**Quantitative methods** (measure scale, patterns, statistical relationships):

- **Surveys / questionnaires**: See Section 1.4
- **A/B testing**: See Section 2
- **Analytics instrumentation**: See Section 3
- **Conjoint analysis**: Statistical technique to identify which product attributes consumers value most by analyzing tradeoff choices
- **Eye-tracking studies**: Hardware-based measurement of visual attention on page elements

### 1.4 Survey Design for E-Commerce

A well-designed survey is a powerful primary research tool. A poorly designed survey produces data that misleads decision-making.

**Core survey design principles**:

1. **Clarity**: Every question should be interpretable in exactly one way
2. **Neutrality**: Avoid leading questions ("How much did you enjoy our checkout experience?" presupposes enjoyment)
3. **Single topic per question**: Double-barreled questions ("Was the shipping fast and affordable?") cannot be analyzed cleanly
4. **Appropriate scales**: Likert scales (1–5 or 1–7) for attitude measurement; ensure scales are balanced with equal positive and negative options
5. **Order effects**: Put demographic questions last (reduces dropoff); put easy questions first to build completion momentum
6. **Length**: Completion rates drop precipitously after 7–10 minutes; target 3–5 minutes for unsolicited surveys

**E-commerce specific survey types**:

| Survey Type | Trigger | Key Metrics | Tool |
|-------------|---------|-------------|------|
| Post-purchase satisfaction | 1–3 days after delivery | CSAT, product satisfaction, shipping satisfaction | Klaviyo, Yotpo |
| Cart abandonment survey | Exit intent on cart page | Abandonment reason, unmet needs | Hotjar, Qualaroo |
| Net Promoter Score (NPS) | 30–90 days after purchase | NPS score, loyalty driver | Delighted, Medallia |
| New visitor survey | First visit, exit intent | Discovery channel, visit purpose, unmet needs | Hotjar Polls |
| Product page survey | Time on page trigger | Purchase barriers, missing information | Qualaroo |

!!! warning "Survey Response Bias"
    Online surveys suffer from multiple forms of response bias:

    - **Acquiescence bias**: Respondents tend to agree with statements regardless of content (counter with reverse-coded questions)
    - **Social desirability bias**: Respondents answer as they *think they should* behave, not how they do (use behavioral questions, not attitudinal when possible)
    - **Non-response bias**: People who respond may be systematically different from those who don't (especially unhappy customers who leave without responding)
    - **Recency bias**: Recent experiences are over-weighted vs. long-term satisfaction

---

## 2. A/B Testing Methodology

### 2.1 What Is A/B Testing?

**A/B testing** (also called **split testing**) is a controlled experiment in which a randomly selected portion of users sees version A (the control, typically the existing experience) and another randomly selected portion sees version B (the treatment, a modified version). By comparing outcomes between groups, you can measure the causal effect of the change.

```
All Visitors
    │
    ├──── 50% → Version A (Control)  ──→ Measure: Conversion Rate A
    │
    └──── 50% → Version B (Treatment) ──→ Measure: Conversion Rate B
    
    If B > A by a statistically significant amount → Ship version B
```

### 2.2 Why A/B Testing Matters

A/B testing is the gold standard for optimization because it establishes *causation* rather than just correlation. Without it, you might observe that customers who see a particular page element convert more — but you can't tell whether the element *caused* the conversion or whether those customers were already more likely to convert for unrelated reasons.

!!! success "The Impact of A/B Testing at Scale"
    Amazon, Google, and Microsoft run thousands of A/B tests simultaneously. Microsoft's Bing team has reported that their rigorous testing culture has identified changes that appeared positive in offline analysis but actually *hurt* revenue when tested live — and vice versa. Google runs over **10,000 A/B tests per year** on Google Search alone. The compound effect of many small, tested improvements is what drives consistent growth at mature digital platforms.

### 2.3 Statistical Significance

The most misunderstood concept in A/B testing is **statistical significance** — the probability that an observed difference between A and B reflects a true difference rather than random chance.

**Key concepts**:

```
p-value: The probability of observing the measured difference (or larger) 
         if the null hypothesis (no true difference) were true.

p < 0.05: Less than 5% probability the result is due to chance
          → "Statistically significant at the 95% confidence level"

p < 0.01: Less than 1% probability → 99% confidence

Confidence Interval (CI): The range within which the true value
likely falls with a specified probability.
"Version B converts 3.2% better than A (95% CI: 1.1% – 5.3%)"
```

**Sample size and test duration**:

One of the most common A/B testing mistakes is **stopping the test too early** when early results look good (or bad). Early fluctuations are normal; you need sufficient data to distinguish signal from noise.

```python
# Sample size estimation (simplified)
# Target: detect a 5% relative lift (e.g., 2.0% → 2.1% conversion rate)
# At 80% power and 95% significance

# Rule of thumb calculation:
# n = 16 × σ² / δ²
# Where σ² = baseline variance, δ = minimum detectable effect

# For conversion rates, using a calculator (e.g., Evan Miller's):
# Baseline: 2.0% conversion rate
# Minimum detectable effect: 10% relative lift = 0.2 percentage points
# Required sample per variant: ~38,000 visitors

# Always run tests for at least 2 full business cycle weeks
# to account for day-of-week effects
```

### 2.4 Common A/B Testing Pitfalls

| Pitfall | Description | Solution |
|---------|-------------|---------|
| **Peeking** | Stopping the test as soon as p < 0.05 is reached | Pre-determine sample size; use sequential testing methods |
| **Multiple comparisons** | Testing many variants simultaneously inflates false positive rate | Apply Bonferroni correction; limit variants |
| **Novelty effect** | New experiences show inflated results initially due to user curiosity | Run tests long enough for novelty to wear off |
| **Sample ratio mismatch** | Actual traffic split differs from intended split | Audit implementation; check for technical bugs |
| **Interference effects** | Users see both variants (e.g., logged-out vs. logged-in) | Use cookie-stable assignment; consider user-level randomization |
| **Local maximum trap** | Testing small variations never escapes a suboptimal design | Periodically conduct radical redesign tests |

### 2.5 What to Test in E-Commerce

High-impact areas for A/B testing, ranked by typical uplift potential:

1. **Checkout flow**: Reducing steps, removing form fields, offering guest checkout (often 10–20%+ conversion uplift)
2. **Free shipping threshold**: $25 vs. $35 vs. $50 vs. free (significant impact on AOV)
3. **Product page layout**: Hero image size, review placement, CTA button text/color/position
4. **Homepage value proposition**: Different headline copy, hero imagery
5. **Email subject lines**: Major impact on open rates (typically test batches before full send)
6. **Pricing display**: Charm pricing vs. round, bundle presentation, crossed-out original prices
7. **Trust signals placement**: Where trust seals, reviews, and guarantees appear

---

## 3. Google Analytics 4: Key Metrics and Features

### 3.1 GA4 vs. Universal Analytics

Google replaced **Universal Analytics (UA)** with **Google Analytics 4 (GA4)** as the default product in July 2023. GA4 represents a fundamental redesign:

| Dimension | Universal Analytics | Google Analytics 4 |
|-----------|--------------------|--------------------|
| **Data model** | Session-based | Event-based |
| **Cross-device tracking** | Limited | Built-in (Google Signals) |
| **Bounce rate** | % who leave after 1 page | Replaced by Engagement Rate |
| **Privacy** | Cookie-dependent | Cookieless-forward; consent mode |
| **Machine learning** | Limited | Extensively integrated (predictive audiences) |
| **Free vs. paid** | Free + GA 360 | Free + GA4 360 |
| **Reports** | Preset, rigid | Flexible exploration reports |

### 3.2 Core GA4 Metrics

=== "Traffic Metrics"
    **Users**: The count of unique individuals who visited the site in the period. GA4 distinguishes:
    - *New users*: First-ever visit from this device/account
    - *Returning users*: Previously visited

    **Sessions**: A period of continuous activity on the site (default timeout: 30 minutes of inactivity ends a session). One user can have multiple sessions.

    **Sessions per user**: Average number of sessions per user. Higher = more engaged returning audience.

    **Session source/medium**: Where the user came from:
    - `google / organic`: Non-paid Google Search
    - `google / cpc`: Paid Google Ads
    - `email / newsletter`: Email campaign
    - `(direct) / (none)`: Typed URL directly or unknown source

=== "Engagement Metrics"
    **Engagement Rate**: Percentage of sessions that were "engaged sessions" — sessions that lasted 10+ seconds, had 2+ pageviews, or had a conversion event. GA4's replacement for the bounce rate concept.

    **Bounce Rate** (available in GA4 but de-emphasized): Percentage of sessions that were *not* engaged sessions. Lower is generally better.

    !!! info "The Bounce Rate Nuance"
        A "high bounce rate" is not inherently bad. If someone Googles your business hours, finds them on your homepage in 5 seconds, and leaves — that's a successful zero-engagement session. Context matters enormously. Compare bounce rates by channel and landing page type, not just site-wide averages.

    **Average Engagement Time**: Time users spend actively (tab in focus) on the site. More meaningful than the old "average session duration."

    **Pages per session**: How many pages a user views in a session. High values suggest engaged exploration; very low values may indicate poor navigation.

=== "Conversion Metrics"
    **Conversions**: Any defined user action of value — a purchase, form submission, newsletter signup, or other goal. In GA4, any event can be marked as a conversion.

    **Conversion Rate**: `Conversions / Sessions` (or Users, depending on how configured). The most important single optimization metric.

    **E-commerce purchase revenue**: Total revenue from completed purchases. GA4 requires proper e-commerce tracking code implementation.

    **Average purchase revenue per user**: Total revenue divided by purchasing users. CLV proxy.

=== "Funnel Analysis"
    GA4's **Funnel Exploration** report allows you to define a sequence of steps in the purchase path and see what percentage of users complete each step:

    ```
    Step 1: Homepage view         100% (baseline)
    Step 2: Product page view      45%  (-55% dropped)
    Step 3: Add to cart            18%  (-27% dropped)
    Step 4: Begin checkout         12%  (-6% dropped)
    Step 5: Complete purchase       3%  (-9% dropped)
    
    Overall conversion rate: 3%
    Biggest drop: Homepage → Product page (opportunity: improve homepage CTA)
    ```

    Funnel analysis pinpoints where you are losing the most users and thus where optimization investment has the highest return.

### 3.3 UTM Parameters and Campaign Tracking

**UTM parameters** (Urchin Tracking Module, from Google's acquisition of Urchin in 2005) are tags appended to URLs that tell GA4 where traffic came from.

**The five UTM parameters**:

| Parameter | Required? | Description | Example |
|-----------|-----------|-------------|---------|
| `utm_source` | Required | The traffic source | `google`, `facebook`, `newsletter` |
| `utm_medium` | Required | The marketing medium/channel | `cpc`, `email`, `social`, `organic` |
| `utm_campaign` | Required | The specific campaign name | `spring_sale_2025`, `welcome_series` |
| `utm_content` | Optional | Differentiates ads/links within a campaign | `hero_cta_button`, `sidebar_banner` |
| `utm_term` | Optional | Keywords for paid search | `running+shoes+women` |

**Example tagged URL**:
```
https://www.yourstore.com/sale?utm_source=facebook&utm_medium=cpc
&utm_campaign=spring_sale_2025&utm_content=carousel_ad_v2
```

**Best practices**:
- Create a **UTM naming convention document** and enforce it organization-wide (inconsistent naming creates messy data: `Facebook`, `facebook`, and `FB` appear as three different sources)
- Always tag paid traffic; never tag organic or direct traffic (GA4 handles these automatically)
- Use a **UTM builder tool** (Google's Campaign URL Builder, or UTM.io) to avoid typos
- Tag all email links, social posts, and paid ad destination URLs

!!! warning "Common UTM Mistake"
    **Never** use UTM parameters on internal links (links from one page to another within your own site). This resets the session and attributes internal navigation as a new traffic source, corrupting your source/medium data.

---

## 4. Heatmaps and Session Recordings

### 4.1 What Heatmap Tools Reveal

**Heatmap tools** visually represent user behavior on a page using color gradients (hot = high activity, cool = low activity) for:

- **Click heatmaps**: Where users click (including "rage clicks" — repeated frustrated clicking on non-interactive elements)
- **Move heatmaps**: Where users move their mouse (correlated with visual attention)
- **Scroll heatmaps**: How far down the page users scroll before leaving

**Session recordings** capture anonymized video replays of individual user sessions, showing exactly what the user did — every click, scroll, mouse movement, and form interaction.

### 4.2 Hotjar

**Hotjar** (hotjar.com) is the most widely used behavior analytics platform:

- **Pricing**: Free tier (35 daily sessions); paid from $32/month (100 daily sessions)
- **Features**: Heatmaps, session recordings, surveys (on-site popups and polls), feedback widgets

**E-commerce use cases for Hotjar**:

| Insight Question | Hotjar Method |
|-----------------|---------------|
| Why are users not clicking the "Add to Cart" button? | Click heatmap on product page |
| What content above the fold gets the most attention? | Move heatmap on homepage |
| Are users seeing the shipping info section? | Scroll heatmap on product page |
| Why do users leave the checkout page at step 2? | Session recording filter for checkout exits |
| What's confusing users on the product page? | On-page poll: "Did you find the information you needed?" |

### 4.3 Microsoft Clarity

**Microsoft Clarity** (clarity.microsoft.com) is a free behavior analytics tool (no session limits):

- **Free**: Unlimited sessions, heatmaps, recordings
- **Unique features**: 
  - **Dead clicks**: Clicks that produce no action (elements that look clickable but aren't)
  - **Rage clicks**: Multiple rapid clicks indicating frustration
  - **Excessive scrolling**: Users scrolling up and down repeatedly, suggesting confusion
  - **Quick backs**: User navigated to a page then immediately left, suggesting the content wasn't what they expected

!!! tip "GA4 + Clarity Integration"
    Microsoft Clarity integrates directly with GA4 — you can filter Clarity session recordings by GA4 segments (e.g., "show me session recordings of users who added to cart but didn't purchase"). This combination of quantitative analytics (GA4) and qualitative behavior recording (Clarity) is extremely powerful for diagnosing conversion problems.

---

## 5. Keyword Research and SEO Basics

### 5.1 Why SEO Matters for E-Commerce

**Search Engine Optimization (SEO)** is the practice of optimizing web content to rank higher in organic (non-paid) search results. Organic search is one of the highest-quality and lowest-cost acquisition channels for e-commerce:

- 53% of all website traffic comes from organic search (BrightEdge, 2023)
- The top 3 organic results capture 54% of all clicks on a search results page
- Organic traffic has a **2–5× higher conversion rate** than paid traffic (lower intent mismatch)
- Once established, organic rankings provide traffic without per-click costs

### 5.2 Keyword Research Process

**Keyword research** identifies the specific search queries your target customers use, enabling you to create content that matches their intent.

**Step 1: Seed keyword generation**
Start with broad terms related to your products and business. For an online running shoe store:
- "running shoes"
- "trail running shoes"  
- "women's marathon shoes"

**Step 2: Expand using research tools**

=== "Google Search Console (Free)"
    **What it is**: Google's own data about how your site performs in Google Search.

    **Key features**:
    - Performance report: Queries that trigger your pages; impressions, clicks, click-through rate (CTR), average position
    - Coverage report: Indexed vs. not indexed pages; crawl errors
    - Core Web Vitals: Page speed and experience metrics

    **Unique value**: Shows real queries that real users typed before clicking your pages — not estimated data. Essential for identifying "quick win" keywords (ranked position 5–15 that could move to top 3 with optimization).

=== "SEMrush"
    **What it is**: Full-suite SEO and competitive intelligence platform.

    **Pricing**: Free limited version; paid from ~$129/month

    **Key features for e-commerce**:
    - **Keyword Magic Tool**: Enter a seed keyword; generates thousands of related keywords with search volume, difficulty, and CPC data
    - **Keyword Gap**: Compare your keyword rankings against competitors; identify keywords they rank for that you don't
    - **Position Tracking**: Monitor daily ranking changes for tracked keywords
    - **Site Audit**: Technical SEO crawl; finds errors, broken links, duplicate content

=== "Ahrefs"
    **What it is**: SEO toolset with the most comprehensive backlink database in the industry.

    **Pricing**: From ~$99/month (no free version beyond limited Webmaster Tools)

    **Key features for e-commerce**:
    - **Keywords Explorer**: Keyword research with "Keyword Difficulty" score, search volume, clicks data
    - **Site Explorer**: Analyze any domain's organic rankings and backlink profile
    - **Content Gap**: Find topics your competitors rank for that you don't
    - **Backlink analysis**: Critical for link-building strategy

**Step 3: Evaluate keywords**

| Metric | Definition | Target for New Sites |
|--------|-----------|----------------------|
| **Search volume** | Average monthly searches | Start with 100–1,000 volume niches |
| **Keyword difficulty (KD)** | How hard it is to rank (0–100) | Target KD < 30 initially |
| **Search intent** | What the user wants (informational / commercial / transactional) | Match content type to intent |
| **CPC** | Cost-per-click in paid search | High CPC = high commercial value |

### 5.3 Search Intent Framework

Understanding **search intent** is the most important keyword evaluation dimension:

| Intent Type | Description | Example Query | Content Type |
|-------------|-------------|---------------|--------------|
| **Informational** | Wants to learn | "how to choose running shoes" | Blog post, guide |
| **Navigational** | Wants a specific site | "Nike shoe store" | Brand pages |
| **Commercial investigation** | Comparing options before buying | "best running shoes for flat feet 2025" | Comparison page, reviews |
| **Transactional** | Ready to buy | "buy Brooks Adrenaline GTS 24" | Product page, category page |

!!! tip "Intent Mismatch Kills Rankings"
    If you create a blog post targeting a transactional keyword (users want a product page), Google will not rank your blog post well — and users who land on it will immediately leave. Always match your content format to the dominant search intent.

---

## 6. Social Listening and Competitive Intelligence

### 6.1 Social Listening

**Social listening** is the practice of monitoring digital channels for mentions of your brand, competitors, products, and relevant industry topics.

**What social listening reveals**:
- **Customer sentiment**: How do customers feel about your products and service?
- **Competitive intelligence**: What are customers saying about your competitors' weaknesses?
- **Emerging trends**: What topics are gaining traction in your category?
- **Crisis detection**: Identifying PR crises early before they escalate
- **Influencer identification**: Who talks about your category with authentic authority?

**Social listening tools**:

| Tool | Price | Best For |
|------|-------|---------|
| **Brandwatch** | $1,000+/month | Enterprise; deep historical data |
| **Sprout Social** | $249+/month | Mid-market; integrated social management |
| **Mention** | $29+/month | Small business; real-time mentions |
| **Talkwalker Alerts** | Free (basic) | Entry-level; email alerts for brand mentions |
| **Brand24** | $79+/month | SMB; good value for price |
| **Google Alerts** | Free | Basic; monitors Google-indexed web content |

**Conducting a social listening audit**:

1. Define keywords: Brand name + misspellings, product names, competitors, category terms
2. Set up monitoring across: Twitter/X, Reddit, Instagram, TikTok, Facebook, YouTube comments, review sites (Trustpilot, G2, Amazon reviews)
3. Track sentiment over time: Positive/negative/neutral ratios
4. Create response protocols: Who responds? In what timeframe? With what tone?

### 6.2 Competitive Intelligence Techniques

**Competitive intelligence (CI)** is the systematic process of gathering, analyzing, and using information about competitors.

=== "Digital Footprint Analysis"
    Examine publicly available digital signals:

    - **Website analysis**: Use BuiltWith.com to identify technology stack (what e-commerce platform, email tool, analytics, etc.)
    - **SEO analysis**: Use Ahrefs/SEMrush to see which keywords they rank for; their top-traffic pages; their backlink growth
    - **Paid advertising**: Use SimilarWeb, SpyFu, or Facebook Ad Library to see their ad creative and targeting
    - **Pricing monitoring**: Manual or automated price tracking (Prisync, Price2Spy)
    - **Job postings**: What roles are they hiring? Reveals strategic priorities (hiring AI engineers? Building a mobile app? Expanding internationally?)

=== "Customer Review Mining"
    Your competitors' customer reviews are a goldmine of intelligence:

    - What do customers praise? (Their strengths to match or exceed)
    - What do customers complain about? (Their weaknesses — your opportunity)
    - What features do customers request? (Unmet market needs)

    Systematically reading 50–100 recent reviews across Amazon, Trustpilot, and Google Reviews for competitors can generate more strategic insight than expensive market research.

=== "Social Media Monitoring"
    - Track competitor hashtags, post engagement rates, content themes
    - Identify which content formats get the most engagement for them
    - Monitor response time and tone in customer service interactions
    - Track follower growth trends (accelerating growth may signal a new campaign or product launch)

---

## 7. Customer Satisfaction Metrics

### 7.1 Net Promoter Score (NPS)

**Net Promoter Score (NPS)**, developed by Fred Reichheld at Bain & Company (2003), measures customer loyalty through a single question:

> *"On a scale of 0–10, how likely are you to recommend [Company/Product] to a friend or colleague?"*

**Scoring methodology**:

```
Responses 0-6 = Detractors (unhappy customers who may damage the brand)
Responses 7-8 = Passives (satisfied but not enthusiastic)
Responses 9-10 = Promoters (loyal enthusiasts who recommend actively)

NPS = % Promoters − % Detractors
Range: −100 to +100
```

**NPS benchmarks by industry** (Qualtrics XM Institute, 2023):

| Industry | Average NPS |
|----------|-------------|
| Online retail / e-commerce | 45 |
| Software (B2C) | 31 |
| Financial services | 34 |
| Healthcare | 38 |
| Airlines | 33 |

!!! info "NPS Limitations"
    NPS is the most widely used loyalty metric, but it has important limitations:
    
    - **Single question**: May miss nuance; doesn't diagnose *why* customers are satisfied or dissatisfied
    - **Industry variation**: A 45 NPS is excellent in insurance but mediocre in consumer electronics
    - **Implementation variation**: Different survey timing and channel produce very different scores; NPS isn't comparable across companies that measure differently
    - **Not predictive of churn in all cases**: Some research suggests NPS poorly predicts actual referral behavior

**NPS follow-up questions** dramatically increase the actionability of the metric:
- "What is the primary reason for your score?" (open text)
- "What could we do to improve your experience?" (open text for detractors)

### 7.2 Customer Satisfaction Score (CSAT)

**CSAT** measures satisfaction with a specific interaction or transaction (rather than overall loyalty like NPS).

**Standard CSAT question**:
> *"How satisfied were you with [specific interaction/product]?"*
> Response scale: Very Satisfied / Satisfied / Neutral / Dissatisfied / Very Dissatisfied

**Calculation**:
```
CSAT = (Number of Positive Responses / Total Responses) × 100

Where "positive" = Satisfied + Very Satisfied responses
```

**CSAT use cases in e-commerce**:

| Trigger | What It Measures | Benchmark |
|---------|-----------------|-----------|
| Post-delivery | Overall order satisfaction | 85%+ = good |
| Post-live chat | Chat support quality | 90%+ = good |
| Post-return processed | Returns experience | 80%+ = good |
| Post-purchase (7 days) | Product satisfaction | Varies by category |

**NPS vs. CSAT comparison**:

| Dimension | NPS | CSAT |
|-----------|-----|------|
| What it measures | Long-term loyalty / advocacy | Specific transaction satisfaction |
| Survey frequency | Periodic (quarterly/annually) | Post-interaction |
| Scale | 0–10 | 1–5 or custom |
| Best use | Strategic tracking; competitive benchmarking | Operational feedback; agent performance |

---

## 8. Cohort Analysis

### 8.1 What Is Cohort Analysis?

**Cohort analysis** groups users by a shared characteristic — typically the time period when they first purchased or registered — and tracks their behavior over subsequent periods. It is the most powerful tool for understanding customer retention and the long-term impact of acquisition channels and campaigns.

**Why cohort analysis matters**: Aggregate metrics can be misleading. If your month-over-month revenue is flat, you can't tell from the aggregate whether (a) customer quality is constant, (b) customers are churning faster but you're acquiring more to compensate, or (c) something else entirely. Cohort analysis separates these explanations.

### 8.2 Cohort Retention Table

```
          Month 0  Month 1  Month 2  Month 3  Month 4  Month 5
Jan cohort  100%     45%      28%      22%      18%      16%
Feb cohort  100%     42%      26%      21%      17%       —
Mar cohort  100%     48%      30%      24%       —        —
Apr cohort  100%     51%      33%       —        —        —
May cohort  100%     53%       —        —        —        —
```

**How to read the table**: 100% of customers in each cohort are active in Month 0 (their first purchase month). By Month 1, the January cohort has 45% retention — 55% of January customers did not make a second purchase in February. By Month 5, only 16% remain active.

**Key observations from this table**:
- **Recent cohorts (Apr, May) show higher Month 1 retention** (51–53% vs. 42–45%) — suggesting that a product change or marketing improvement is working
- The **biggest drop is Month 0 → Month 1** in all cohorts, which is typical; this is where the biggest retention opportunity lies (onboarding optimization)

### 8.3 Interpreting and Acting on Cohort Data

| Pattern | Interpretation | Action |
|---------|---------------|--------|
| Retention improving in recent cohorts | Recent changes (product, onboarding, messaging) are working | Continue and amplify those changes |
| Retention declining in recent cohorts | Product quality, market saturation, or acquisition quality issues | Investigate root cause; audit recent changes |
| High Month 0–1 drop, stable afterward | Onboarding / first purchase experience problem | Invest in post-purchase onboarding sequence |
| Good early retention, steep later drop | No long-term value driver | Introduce loyalty program; expand product line |
| Specific cohort outlier (e.g., holiday cohort lower retention) | Holiday buyers have different intent/loyalty profile | Separate holiday cohort from core customers in forecasting |

---

## 9. Funnel Visualization and Attribution Modeling

### 9.1 Funnel Visualization

**Funnel visualization** maps the percentage of users who complete each step in a defined conversion path. In GA4, this is done through the **Funnel Exploration** report.

**A full e-commerce funnel**:

```
                    Visitors       100,000
                        │
                        ▼
              Category page visits   48,000  (48%)
                        │
                        ▼
               Product page views    22,000  (22%)
                        │
                        ▼
                  Add to cart         7,000   (7%)
                        │
                        ▼
              Begin checkout          4,200   (4.2%)
                        │
                        ▼
          Enter payment information   2,800   (2.8%)
                        │
                        ▼
              Purchase complete       2,100   (2.1%)
```

**Reading the funnel**: The biggest percentage drop determines where to focus optimization effort. In this example, the Category → Product page transition loses 26 percentage points (54% of category visitors don't click into a product). This suggests either poor product imagery in category view, irrelevant product mix, or bad search intent match.

### 9.2 Attribution Modeling

**Attribution modeling** determines how to assign credit for a conversion across the multiple touchpoints a customer encountered before purchasing.

The challenge: A customer may:
1. See a Facebook ad → not purchase
2. Google the brand organically → not purchase
3. Receive an email → not purchase
4. Click a Google Shopping ad → purchase

Who gets credit? All four channels contributed. **Attribution models answer this question differently**.

=== "First-Touch Attribution"
    **100% of credit** goes to the first channel that introduced the customer to the brand.

    In the example: **Facebook ad** gets 100% credit.

    **Best for**: Understanding which channels are best at generating top-of-funnel awareness.

    **Weakness**: Ignores all channels that nurtured the customer from awareness to purchase.

=== "Last-Touch Attribution"
    **100% of credit** goes to the last channel the customer interacted with before converting.

    In the example: **Google Shopping** gets 100% credit.

    **Best for**: Understanding which channels most directly drive conversion decisions.

    **Weakness**: Ignores all awareness and consideration touchpoints. Tends to over-credit bottom-funnel channels (paid search, retargeting) and under-credit top-funnel channels (social media, content).

=== "Linear Attribution"
    Credit is **split equally** across all touchpoints.

    In the example: Each of the four channels (Facebook, organic Google, email, Google Shopping) gets **25% credit**.

    **Best for**: Getting a balanced view of all channels' contributions.

    **Weakness**: Treats all touches as equally valuable regardless of position or impact.

=== "Time-Decay Attribution"
    More credit is given to **more recent touchpoints**, with credit decaying exponentially for earlier touches.

    In the example: Google Shopping (most recent) gets most credit; Facebook (oldest) gets least.

    **Best for**: Short purchase cycles where recency is genuinely predictive of influence.

    **Weakness**: Undervalues awareness and top-of-funnel channels that start the journey.

=== "Data-Driven Attribution (DDA)"
    Uses **machine learning** to assign fractional credit based on which combinations of touchpoints actually correlate with conversion, using comparison between converting and non-converting paths.

    **Best for**: The most accurate picture of true channel contribution when sufficient data is available.

    **Requirement**: Typically requires ~600+ monthly conversions to generate statistically reliable models.

    **GA4 default**: Data-driven attribution is GA4's default model for conversion reporting (replacing the last-click default of UA).

### 9.3 Attribution in Practice

!!! warning "Attribution Is Never Perfect"
    All attribution models are simplifications. A customer who saw a TV ad, read a blog post, and then clicked a Google Search ad — the TV and blog post get no credit in any digital attribution model because they can't be tracked digitally. **Multi-touch attribution captures only the observable digital journey**, which is always incomplete.

    Marketing Mix Modeling (MMM) and incrementality testing are more rigorous (but more complex) methods to measure true channel impact.

**Choosing a model by decision type**:

| Decision | Recommended Model | Reason |
|----------|------------------|--------|
| Budget allocation across all channels | Data-driven or Linear | Need balanced view of all channel contributions |
| Evaluating a new top-funnel channel | First-touch or Linear | New channels need credit for starting journeys |
| Optimizing bottom-funnel conversion | Last-touch | Most directly measures close effectiveness |
| Understanding customer journey length | Full path / Cohort | Attribution models alone don't show journey complexity |

---

## Key Vocabulary

| Term | Definition |
|------|------------|
| **Primary research** | New data collected specifically to answer your research question |
| **Secondary research** | Existing data collected by others for different primary purposes |
| **A/B testing** | Controlled experiment comparing two versions of a web experience to measure causal effect on outcomes |
| **Statistical significance** | The probability that an observed result reflects a true effect rather than random chance |
| **p-value** | Probability of observing results this extreme if the null hypothesis (no effect) were true |
| **GA4** | Google Analytics 4 — Google's current web analytics platform, event-based model |
| **Session** | A period of continuous user activity on a website (default timeout: 30 minutes inactivity) |
| **Engagement rate** | % of sessions with 10+ seconds duration, 2+ pageviews, or a conversion event |
| **UTM parameters** | URL tags (source, medium, campaign, content, term) that identify traffic sources in analytics |
| **Heatmap** | Visual representation of user behavior patterns on a web page using color gradients |
| **Session recording** | Anonymized video replay of a user's complete interactions on a website |
| **Keyword difficulty (KD)** | SEO metric estimating how competitive it is to rank for a given keyword (0–100) |
| **Search intent** | The underlying goal behind a user's search query (informational/commercial/transactional) |
| **Social listening** | Monitoring digital channels for brand, competitor, and industry mentions |
| **NPS** | Net Promoter Score — % Promoters minus % Detractors on a 0–10 recommendation question |
| **CSAT** | Customer Satisfaction Score — % of respondents rating an interaction as satisfied or very satisfied |
| **Cohort analysis** | Tracking behavioral metrics over time for groups of users who share a common characteristic |
| **Funnel visualization** | Mapping user progression through a defined sequence of steps toward conversion |
| **First-touch attribution** | Assigns 100% of conversion credit to the first marketing touchpoint |
| **Last-touch attribution** | Assigns 100% of conversion credit to the final touchpoint before conversion |
| **Data-driven attribution** | ML-based model that distributes credit based on observed conversion path patterns |
| **Confidence interval** | Range within which the true value likely falls with a specified probability |

---

## Review Questions

!!! question "Week 5 Review Questions"

    1. **Design a research plan** for a DTC skincare brand that wants to understand why its 30-day customer retention rate is declining. Specify: (a) which secondary research sources you'd consult first and why, (b) one qualitative primary research method you'd use and how you'd recruit participants, and (c) one quantitative method you'd use to measure the problem. For each, state what specific question you're trying to answer.

    2. **Evaluate the following A/B test scenario**: An e-commerce team tests a new checkout page design. After 3 days, Version B shows a 12% higher conversion rate with p = 0.04. The team wants to immediately deploy Version B sitewide. Identify at least three methodological problems with this decision and explain what the team should do instead.

    3. **Interpret the following GA4 funnel data**: Homepage (100%) → Category page (52%) → Product page (31%) → Add to cart (9%) → Purchase (3.2%). Calculate the conversion rate at each step. Identify which step has the biggest relative drop. Propose two specific hypotheses for why that drop is occurring and describe how you would test each hypothesis.

    4. **A fashion startup** runs the following campaigns in one month and has 200 conversions. Using the attribution models framework, explain how first-touch, last-touch, and linear attribution would distribute credit across: 80 customers whose first touch was Instagram (but only 20 purchased directly from Instagram), 100 customers who came through email (40 purchased from email), and 80 customers who clicked a Google Shopping ad (140 purchased after a Google Shopping ad). Which model would make Instagram look most effective? Which would make Google Shopping look most effective? Which would you recommend for this startup and why?

    5. **Calculate the NPS** for a survey with 250 responses: 115 gave scores of 9–10, 75 gave scores of 7–8, and 60 gave scores of 0–6. Is this NPS above or below the e-commerce industry benchmark from Section 7.1? Design two follow-up actions the company should take based on this score, specifying which customer segment each action targets and what outcome it aims to improve.

---

## Further Reading

| Resource | Type | Notes |
|----------|------|-------|
| Kaushik, Avinash. *Web Analytics 2.0* (2010) | Book | Still the most practical book on web analytics strategy |
| Google Analytics 4 Documentation | Official docs | docs.google.com/analytics; complete GA4 reference |
| Baymard Institute — E-Commerce UX Research | Website | Extensive A/B test research and checkout optimization |
| Kohavi, Deng & Longbotham. "Online Randomized Controlled Experiments at Scale" *KDD 2013* | Academic paper | A/B testing at Microsoft scale; methodological deep dive |
| Reichheld, Fred. "The One Number You Need to Grow" *Harvard Business Review* (2003) | Article | Original NPS framework paper |
| Ahrefs Blog (ahrefs.com/blog) | Website | Practical SEO guides; keyword research tutorials |
| Google Search Console Help | Official docs | Complete GSC feature documentation |
| Think with Google (thinkwithgoogle.com) | Website | Consumer behavior research, ZMOT research, mobile data |
| Evan Miller's A/B Test Sample Size Calculator | Tool | evmill.com/ab-tool.html — required for experiment design |
| Hotjar Blog | Website | UX research and CRO best practices with case studies |

---

## Summary

Market research and digital analytics are the evidence base upon which all e-commerce strategy rests. The shift from intuition-driven to data-driven decision-making — enabled by the rich behavioral data that digital commerce generates — is one of the most significant competitive advantages available to modern businesses.

But data creates its own risks: the temptation to over-optimize for measurable metrics ("what gets measured gets managed") can cause under-investment in brand, customer relationships, and long-term equity that don't show up immediately in conversion rate dashboards. The most effective digital marketers combine quantitative rigor — A/B testing, cohort analysis, attribution modeling — with qualitative understanding of customer needs, motivations, and experiences. Neither alone is sufficient.

As you build your analytical toolkit, cultivate the habit of asking "why" before reaching for the "optimize" lever. The numbers tell you *what* is happening; your research skills help you understand *why* — and that understanding is what enables genuinely good decisions.

---

*[← Week 4 — Consumer Behavior & Digital Psychology](week04.md) | [Course Index](index.md)*
