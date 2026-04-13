---
title: "Week 7 — B2B E-Commerce & Company-Centric Models"
description: "B2B vs B2C differences, company-centric e-commerce models, electronic procurement, EDI standards, supplier relationship management, and B2B marketplaces for ITEC 442."
---

# Week 7 — B2B E-Commerce & Company-Centric Models

> **Course Objective:** CO4 (Analyze B2B e-commerce models and procurement systems)

---

## Learning Objectives

- [x] Differentiate B2B from B2C e-commerce across buying process, pricing, and technology dimensions
- [x] Classify company-centric B2B models: sell-side, buy-side, and trading communities
- [x] Explain the architecture and workflow of electronic procurement systems
- [x] Describe EDI standards (X12 and EDIFACT) and modern API-based alternatives
- [x] Evaluate major B2B platforms: SAP Ariba, Coupa, Alibaba, Amazon Business
- [x] Analyze supplier relationship management (SRM) and vendor portal design
- [x] Explain RFP processes, reverse auctions, and dynamic pricing in B2B
- [x] Apply account-based marketing (ABM) principles to B2B customer acquisition
- [x] Examine real-world cases: Boeing supplier portal and Walmart Supplier Connect

---

## 1. B2B vs. B2C E-Commerce: Fundamental Differences

### 1.1 Market Scale

B2B e-commerce is substantially larger than B2C by transaction volume. According to Statista (2023), global B2B e-commerce was estimated at **$20.4 trillion** — approximately 5× the size of global B2C e-commerce. In the United States alone, US Census Bureau data shows B2B e-commerce at $2.6 trillion annually versus B2C at approximately $1.1 trillion.

Despite this scale, B2B e-commerce has historically lagged B2C in digital sophistication. The pandemic dramatically accelerated B2B digital transformation: McKinsey (2022) found that 65% of B2B companies now offer full self-serve digital purchasing, up from 13% in 2016.

### 1.2 Buying Process Comparison

The B2B buying process is fundamentally different from B2C in complexity, duration, and stakeholder involvement.

| Dimension | B2C | B2B |
|-----------|-----|-----|
| **Decision Makers** | 1–2 people | 6–10+ (Gartner avg: 6.8) |
| **Purchase Cycle** | Minutes to days | Weeks to years |
| **Average Order Value** | $50–$500 | $5,000–$500,000+ |
| **Buying Motivation** | Emotional + rational | Primarily rational + ROI-driven |
| **Price Transparency** | Listed publicly | Negotiated, contract-based |
| **Repeat Purchases** | Occasional | Regular/contractual |
| **Payment Terms** | Immediate (credit card) | Net-30/60/90, purchase orders |
| **Returns** | Self-service | Contractual RMA process |
| **Customization** | Limited (size/color) | Deep (specs, configurations) |

### 1.3 Decision-Making Units (DMU)

The **Decision-Making Unit** (DMU) in B2B purchasing consists of multiple roles, each with different priorities:

| Role | Also Called | Primary Concern | Influence Stage |
|------|------------|-----------------|-----------------|
| **Initiator** | — | Identifies the need | Problem recognition |
| **User** | End user | Usability, efficiency | Specification |
| **Influencer** | Technical evaluator | Features, compatibility | Evaluation |
| **Decider** | Budget owner | ROI, total cost of ownership | Selection |
| **Buyer** | Procurement | Price, terms, compliance | Negotiation |
| **Gatekeeper** | IT/Legal/Security | Risk, compliance, integration | Throughout |
| **Approver** | C-Suite | Strategic fit, risk | Final approval |

!!! info "Implication for B2B Digital Commerce"
    A B2B e-commerce platform must provide different information and tools for each DMU member. Technical documentation for the Influencer, ROI calculators for the Decider, compliance certifications for the Gatekeeper, and contract/pricing portals for the Buyer — all within the same platform.

### 1.4 Contract Purchasing and Volume Pricing

B2B commerce is built on contractual relationships that define:

- **Master Service Agreement (MSA):** Overarching terms of engagement
- **Statement of Work (SOW):** Specific deliverables and pricing for a project
- **Blanket Purchase Order:** Pre-authorization for recurring purchases up to a set amount
- **Volume Discount Tiers:** Quantity-based pricing schedules (often called "price books")

**Price book example:**

```
Product: Industrial Bearing Assembly (SKU: IBA-2234)
List Price: $142.00

Volume Pricing:
  1–49 units:     $142.00 (list)
  50–249 units:   $127.80 (10% off)
  250–999 units:  $113.60 (20% off)
  1000+ units:    $99.40  (30% off)

Contract Price (TechCorp Account #4521): $108.00 flat
  (Contract valid 2024-01-01 through 2024-12-31)
```

---

## 2. Company-Centric B2B E-Commerce Models

### 2.1 Sell-Side Models

A **sell-side** B2B e-commerce model is built and operated by a seller to serve its business customers. The seller controls the platform, catalog, and buyer experience.

**Characteristics:**
- Single seller, multiple buyers
- Seller-centric product catalog and configuration
- Buyer-specific pricing, catalogs, and approval workflows
- Integration with seller's ERP (SAP, Oracle, Microsoft Dynamics)

**Examples:**
- **Grainger.com:** Industrial supplies portal allowing businesses to set up cost centers, approval workflows, and purchase order management
- **Dell Technologies B2B Portal:** Configured product bundles, leasing options, and volume pricing for enterprise customers
- **W.W. Grainger, RS Components, MSC Industrial Direct**

```
Sell-Side Architecture:

[Buyer Company] ──→ [Seller Web Portal] ──→ [Seller ERP/OMS]
     ↑                    │                       │
  Purchase Order      Product Catalog         Inventory
  Approval Logic      Buyer-Specific Price    Fulfillment
  Cost Centers        Quote Management        Invoicing
```

!!! tip "Competitive Advantage of Sell-Side Portals"
    By embedding business customers deeply in a sell-side portal — with their approved vendor lists, cost center codes, GL account mapping, and approval workflows — sellers create significant switching costs. Customers who have configured a portal extensively are unlikely to migrate to a competitor.

### 2.2 Buy-Side Models

A **buy-side** model is built and operated by a buyer (large organization) to manage procurement from multiple suppliers. The buyer controls the platform and mandates supplier participation.

**Characteristics:**
- Single buyer, multiple suppliers
- Buyer-controlled catalog (hosted or punch-out)
- Enforces corporate procurement policies, budgets, and approval hierarchies
- Reduces "maverick spending" — purchases outside approved channels

**Examples:**
- **Walmart Supplier Connect** (see Section 6.2)
- **Boeing Supplier Portal** (see Section 6.1)
- **US Federal Government SAM.gov and GSA Advantage**

```
Buy-Side Architecture:

[Supplier A] ──┐
[Supplier B] ──┼──→ [Buyer Procurement Portal] ──→ [Buyer ERP]
[Supplier C] ──┘          │
                    Approved Catalogs
                    Purchase Orders
                    Invoice Processing
                    Contract Compliance
```

### 2.3 Trading Communities and Exchanges

A **trading community** (also called a B2B marketplace or exchange) is a neutral third-party platform connecting many buyers with many sellers in a specific industry or category.

**Types of trading communities:**

=== "Vertical Exchanges"
    Industry-specific platforms serving a defined sector.
    - **Covisint** (automotive suppliers) — legacy example
    - **Global Healthcare Exchange (GHX)** — medical supplies
    - **Agora** — agricultural commodities
    - **E2open** — global trade and logistics
    
    Advantages: Pre-existing industry relationships; standardized data schemas; regulatory compliance built in.

=== "Horizontal Exchanges"
    Cross-industry platforms serving a functional category (e.g., MRO, office supplies, logistics).
    - **Amazon Business** — horizontal MRO and office
    - **Alibaba B2B** — global sourcing across all categories
    - **ThomasNet** — US industrial manufacturing

=== "Consortium Exchanges"
    Built by a group of large companies in the same industry to serve their shared supply base.
    - **Elemica** (chemicals) — founded by BASF, Dow, DuPont
    - **Exostar** (aerospace/defense) — Lockheed, BAE, Raytheon

---

## 3. Electronic Procurement Systems

### 3.1 E-Procurement Overview

**Electronic procurement (e-procurement)** is the use of digital systems to automate and manage the purchase of goods and services according to defined business rules. E-procurement encompasses the full **Purchase-to-Pay (P2P)** cycle.

```
P2P Cycle:

Requisition → Approval → Purchase Order → Receipt → Invoice → Payment
    ↑              ↑            ↑             ↑         ↑         ↑
  Catalog      Workflow      EDI/API      3-Way      OCR/EDI   EFT/ACH
  Browse       Engine        Send         Match      Capture   Payment
```

**Key benefits of e-procurement:**
- Eliminates paper requisitions and manual PO creation
- Enforces approved vendor lists and contract pricing
- Reduces cycle time (PO-to-delivery) by 50–70%
- Provides spend visibility across all categories
- Reduces "off-contract" or "maverick" spending by 15–40%
- Enables 3-way matching: PO quantity = Receiving confirmation = Invoice quantity

### 3.2 Catalog Management

B2B procurement platforms support two catalog models:

=== "Hosted Catalog"
    Supplier product data and pricing is imported into the buyer's procurement system.
    
    **Data exchange format:** cXML (Commerce XML) or custom spreadsheet import
    
    ```xml
    <!-- Example cXML Catalog Item -->
    <Item ParentIndex="1" ItemIndex="1">
      <ItemID>
        <SupplierPartID>IBA-2234</SupplierPartID>
      </ItemID>
      <ItemDetail>
        <UnitPrice>
          <Money currency="USD">108.00</Money>
        </UnitPrice>
        <Description xml:lang="en">
          Industrial Bearing Assembly, 2.234" OD
        </Description>
        <UnitOfMeasure>EA</UnitOfMeasure>
        <Classification domain="UNSPSC">31171500</Classification>
      </ItemDetail>
    </Item>
    ```
    
    **Pros:** Full buyer control; offline browsing possible; fast search
    **Cons:** Catalog goes stale; supplier must push updates; large catalog = complex data management

=== "Punch-Out Catalog"
    Buyer's procurement system sends the user to the supplier's own website. When items are added to cart and "punched back," the shopping cart data returns as a cXML PurchaseRequisition to the buyer's system.
    
    **Flow:**
    ```
    1. User clicks supplier in procurement system
    2. System sends PunchOutSetupRequest (cXML) to supplier
    3. Supplier authenticates and opens their website in browser
    4. User shops on supplier site with buyer-specific pricing
    5. User clicks "Send to Requisition"
    6. Supplier sends PunchOutOrderMessage (cXML) back to buyer
    7. Requisition appears in buyer's system for approval
    ```
    
    **Pros:** Supplier maintains catalog; always current pricing/availability; rich buying experience
    **Cons:** Requires supplier technical integration; dependent on supplier site uptime

### 3.3 Purchase Order Management

A **Purchase Order (PO)** is a legally binding commercial document issued by a buyer to a seller. In electronic procurement:

| Field | Description | Example |
|-------|-------------|---------|
| PO Number | Unique identifier | PO-2024-018847 |
| Vendor Code | Supplier identifier in buyer's ERP | VEND-00421 |
| Buyer Entity | Legal entity making purchase | Acme Corp, Chicago Division |
| Ship-To Address | Delivery location | 1400 Industrial Pkwy, Chicago, IL |
| Line Items | Item code, description, qty, unit price | IBA-2234 × 100 @ $108.00 |
| Payment Terms | Net payment agreement | Net-30 |
| PO Total | Sum of all line items + taxes | $10,800.00 |
| Delivery Date | Required by date | 2024-03-15 |

---

## 4. RFP, Auctions, and Dynamic Pricing in B2B

### 4.1 Request for Proposal (RFP)

An **RFP (Request for Proposal)** is a structured document inviting suppliers to propose solutions to a defined business need. E-procurement platforms automate the RFP process:

**RFP lifecycle:**
1. **Requirements Definition:** Buyer defines scope, specifications, evaluation criteria, timeline
2. **Supplier Invitation:** Select qualified vendors from approved list or open market
3. **Q&A Period:** Suppliers submit clarifying questions; responses shared with all participants
4. **Proposal Submission:** Suppliers submit technical and commercial proposals
5. **Evaluation & Scoring:** Weighted scoring matrix (price, quality, delivery, certifications)
6. **Negotiation:** One-on-one negotiation with shortlisted suppliers
7. **Award & Contract:** Selected supplier notified; contract executed in CLM system

**RFP scoring matrix example:**

| Criterion | Weight | Supplier A Score | Supplier B Score |
|-----------|--------|-----------------|-----------------|
| Price / TCO | 35% | 88 → 30.8 pts | 76 → 26.6 pts |
| Quality / Certifications | 25% | 92 → 23.0 pts | 95 → 23.75 pts |
| Delivery Lead Time | 20% | 80 → 16.0 pts | 85 → 17.0 pts |
| Financial Stability | 10% | 90 → 9.0 pts | 88 → 8.8 pts |
| References / Track Record | 10% | 95 → 9.5 pts | 90 → 9.0 pts |
| **Total** | **100%** | **88.3** | **85.15** |

### 4.2 Reverse Auctions

A **reverse auction** inverts the traditional auction model: buyers post requirements, and multiple suppliers compete by bidding prices downward. The lowest bid (meeting quality requirements) wins.

!!! info "Reverse Auction Mechanics"
    - **Duration:** Typically 30–90 minutes for the live bidding phase
    - **Visibility:** Suppliers see their rank but not competitors' specific prices
    - **Lots:** Large procurement events may have hundreds of line items (lots) auctioned simultaneously
    - **Reserve Price:** Buyer may set a maximum acceptable price (invisible to suppliers)
    - **Savings:** FreeMarkets (now Jaggaer) documented average savings of **15–25%** vs. traditional RFQ in early deployments

**When reverse auctions are appropriate:**
- Commodity goods with clear specifications (steel, packaging materials, logistics lanes)
- Multiple qualified suppliers exist and can genuinely compete
- Total spend is large enough to justify supplier effort
- Relationship is primarily transactional (not strategic partnership)

**When to avoid reverse auctions:**
- Sole-source or preferred strategic suppliers
- Complex services where quality differentiation is high
- Situations where price pressure will compromise supplier financial health
- Industries where safety-critical components require extensive supplier audits

### 4.3 Dynamic Pricing in B2B

B2B pricing was historically static (annual price books renegotiated yearly). Modern e-procurement platforms enable **dynamic B2B pricing** based on:

- Real-time raw material cost inputs (e.g., steel, copper, oil-based feedstocks)
- Demand signals: order volume, urgency, buyer relationship tier
- Competitive intelligence: market index data
- Inventory position: overstocked items discounted; constrained items priced up
- Contract terms: within-contract caps prevent gaming

---

## 5. Technology Platforms: SAP Ariba and Coupa

### 5.1 SAP Ariba

**SAP Ariba** is the world's largest B2B procurement network and platform, with over 6.2 million supplier connections across 190 countries (2023). Acquired by SAP in 2012, Ariba provides:

**Core modules:**
- **Ariba Sourcing:** RFP/RFQ management, reverse auctions, supplier discovery
- **Ariba Contracts:** Contract lifecycle management (CLM), automated compliance monitoring
- **Ariba Buying & Invoicing:** Purchase requisition-to-pay, catalog management, three-way matching
- **Ariba Network:** Supplier-buyer transaction network for PO exchange and electronic invoicing
- **Ariba Supplier Risk:** Third-party risk monitoring, financial health scoring, sustainability data

**Integration:** SAP Ariba integrates natively with SAP S/4HANA (ERP), and via APIs/adapters with Oracle, Microsoft Dynamics, and legacy ERP systems.

**SAP Business Network (formerly Ariba Network) stats:**
- $4.3 trillion in commerce transacted annually
- 92 of Fortune 100 companies use the network

!!! info "The Ariba Network Advantage"
    When a buyer adopts SAP Ariba, their suppliers receive automated invitations to join the Ariba Network. This **network effect** means that suppliers already on the network (with existing profiles, certifications, and banking details) can onboard new buyers in hours rather than weeks. This creates a significant moat.

### 5.2 Coupa

**Coupa** (acquired by Thoma Bravo in 2022 for $8 billion) is a cloud-native Business Spend Management (BSM) platform positioning itself as the more modern, user-friendly alternative to SAP Ariba.

**Key differentiators:**
- **Community Intelligence ("Coupa AI"):** Benchmarks your pricing against anonymized community data — shows if you're paying above-market for a category
- **Open Buy:** Integrates Amazon Business, Uber for Business, and other consumer-style purchasing
- **Coupa Pay:** Integrated virtual card, ACH, and cross-border payment
- **Sustainability Dashboard:** Carbon footprint tracking per supplier and category
- **User Experience:** Praised for consumer-grade UI compared to Ariba's complexity

**Coupa vs. SAP Ariba comparison:**

| Dimension | SAP Ariba | Coupa |
|-----------|-----------|-------|
| Market Position | Market leader; global | Fast-growing challenger |
| Best Fit | SAP ERP customers; large enterprise | Mid-market to enterprise; any ERP |
| Supplier Network | 6.2M+ suppliers | 10M+ suppliers (via Business Network) |
| UX | Complex; powerful | Simpler; consumer-grade |
| AI/ML Features | Developing | Strong (Community Intelligence) |
| Implementation Time | 12–24 months | 6–12 months |
| Total Cost | High | Moderate |

---

## 6. EDI — Electronic Data Interchange

### 6.1 EDI History and Standards

**Electronic Data Interchange (EDI)** is the computer-to-computer exchange of business documents in a standard electronic format between trading partners. EDI dates to the 1960s and predates the internet.

**Why EDI persists:** Large enterprises (Walmart, Ford, Boeing, Home Depot) have mandated EDI compliance for decades. Over $5 trillion in transactions are processed via EDI annually. Switching to API-based systems would require simultaneous upgrades across thousands of supplier relationships — a coordination problem that perpetuates EDI.

**Two dominant standards:**

=== "ANSI X12 (North America)"
    Developed by the Accredited Standards Committee X12. Used predominantly in North America.
    
    **Common transaction sets:**
    | Set # | Name | Description |
    |-------|------|-------------|
    | 810 | Invoice | Supplier invoice to buyer |
    | 820 | Payment Order | Payment remittance advice |
    | 830 | Planning Schedule | Forecast and schedule |
    | 832 | Price/Sales Catalog | Catalog data from supplier |
    | 850 | Purchase Order | Buyer PO to supplier |
    | 855 | PO Acknowledgment | Supplier confirms receipt |
    | 856 | Ship Notice/Manifest | Advance Shipping Notice (ASN) |
    | 997 | Functional Acknowledgment | Confirms document receipt |
    
    **X12 850 Purchase Order — raw segment example:**
    ```
    ISA*00*          *00*          *02*BUYERCO        *01*SUPPLIERCO     *240315*1200*^*00501*000000001*0*P*>~
    GS*PO*BUYERCO*SUPPLIERCO*20240315*1200*1*X*005010~
    ST*850*0001~
    BEG*00*SA*PO-2024-018847**20240315~
    REF*DP*CHICAGO-DIV~
    DTM*002*20240330~
    N1*BT*Acme Corp*92*ACME001~
    N1*ST*Chicago Warehouse*92*CHI-WH01~
    PO1*1*100*EA*108.00*PE*IN*IBA-2234~
    PID*F****Industrial Bearing Assembly 2.234in OD~
    CTT*1~
    AMT*TT*10800.00~
    SE*11*0001~
    GE*1*1~
    IEA*1*000000001~
    ```

=== "EDIFACT (International)"
    UN/EDIFACT (United Nations/Electronic Data Interchange for Administration, Commerce and Transport). Used internationally, especially in Europe.
    
    **Common message types:**
    | Message | Name |
    |---------|------|
    | ORDERS | Purchase Order |
    | ORDRSP | Order Response |
    | DESADV | Despatch Advice (ASN) |
    | INVOIC | Invoice |
    | REMADV | Remittance Advice |
    | PRICAT | Price/Sales Catalogue |
    
    **EDIFACT uses:** Colon (`:`) as component separator, `+` as element separator, `'` as segment terminator.

### 6.2 Modern API Alternatives to EDI

REST APIs (and increasingly GraphQL and event-driven messaging) are displacing EDI for newer trading relationships:

| Dimension | Traditional EDI | REST API / Webhooks |
|-----------|----------------|---------------------|
| Format | Fixed-width, proprietary | JSON / XML (flexible) |
| Real-time | Batch (hourly/daily) | Real-time / event-driven |
| Setup Time | Weeks to months | Days to weeks |
| Cost | VAN charges, per-transaction | API hosting + developer time |
| Visibility | Limited acknowledgment | Full HTTP response + webhooks |
| Adoption | Mandated by large buyers | Required by modern platforms |
| Error Handling | 997 Acknowledgment | HTTP status codes + payload |

**Hybrid reality:** Most large enterprises now run **EDI alongside APIs** — EDI for established large-supplier relationships, APIs for new/startup suppliers and internal microservices.

---

## 7. Supplier Relationship Management (SRM)

### 7.1 The Supplier Relationship Spectrum

Not all suppliers deserve (or require) equal management attention. The **Kraljic Matrix** (Peter Kraljic, 1983) classifies suppliers by two dimensions:

```
                    HIGH SUPPLY RISK
                          │
          Strategic        │    Bottleneck
          Partners         │    Suppliers
         (Collaborate)     │  (Secure supply)
                          │
LOW PROFIT ───────────────┼─────────────────── HIGH PROFIT
IMPACT                    │                      IMPACT
                          │
          Leverage         │    Non-Critical
          Suppliers        │    Suppliers
         (Exploit)         │  (Streamline)
                          │
                    LOW SUPPLY RISK
```

**Strategic Partners** (high profit impact, high supply risk): Long-term contracts, joint development, deep integration, executive relationships.

**Leverage Suppliers** (high profit impact, low supply risk): Multiple sources, competitive bidding, price-focused negotiation.

**Bottleneck Suppliers** (low profit impact, high supply risk): Qualify alternatives, hold safety stock, monitor closely.

**Non-Critical Suppliers** (low on both): Automate procurement, reduce transaction costs, consolidate where possible.

### 7.2 Vendor Portal Features

A modern **vendor portal** provides suppliers with self-service access to their relationship with the buying organization:

- **Order Management:** View open POs, confirm receipt, update ship dates, enter tracking numbers
- **Invoice Submission:** Create and submit invoices electronically; view payment status
- **Performance Dashboard:** On-time delivery %, quality defect rate, fill rate, invoice accuracy
- **Document Exchange:** Certificates of insurance, quality certifications, financial statements
- **Onboarding / Profile:** Company info, banking details, tax forms (W-9, W-8BEN), diversity certifications
- **Communication Center:** RFP invitations, announcements, policy updates

### 7.3 Supplier Performance Metrics

| KPI | Definition | Target |
|-----|-----------|--------|
| On-Time Delivery (OTD) | % of orders delivered on or before promised date | ≥ 98% |
| Fill Rate | % of ordered quantity delivered in first shipment | ≥ 99% |
| Quality Defect Rate | PPM (parts per million) defective | < 500 PPM |
| Invoice Accuracy | % of invoices with no discrepancies | ≥ 99% |
| Lead Time Compliance | Actual lead time vs. contracted lead time | ± 1 day |

---

## 8. B2B Marketplaces and Account-Based Marketing

### 8.1 Major B2B Marketplaces

=== "Alibaba.com"
    The world's largest B2B e-commerce marketplace with over **40 million active buyers** in 190+ countries.
    
    - Founded 1999 by Jack Ma in Hangzhou, China
    - Primary use case: Global sourcing from Chinese and Asian manufacturers
    - **Trade Assurance:** Buyer protection program guaranteeing on-time delivery and product quality
    - **RFQ Marketplace:** Post sourcing needs; receive quotes from verified suppliers
    - **Verified Supplier Badges:** Factory visits and third-party audits by SGS/Bureau Veritas
    - Average order: $1,500–$5,000 (minimum order quantities vary widely)
    - Membership tiers: Gold Supplier certification for enhanced credibility

=== "ThomasNet"
    North America's leading industrial sourcing platform with 500,000+ suppliers and 6 million+ products.
    
    - Focus: US and Canadian industrial manufacturing and MRO
    - Launched in 1898 as Thomas Register (print); digitized as ThomasNet
    - **CAD models available:** Engineers can download component specs directly
    - **RFQ workflow:** Built-in quoting tools for custom manufacturing
    - Segments: Machining, electronics, chemicals, aerospace, defense, medical devices
    - Supplier verification: Certifications (ISO 9001, AS9100, ITAR) prominently displayed

=== "Amazon Business"
    Amazon's B2B marketplace with **$35 billion in annual sales** (2022) — the fastest-growing B2B platform.
    
    - Launched 2015; serves 5 million businesses in US alone
    - **Business-only pricing:** Quantity discounts visible only to logged-in business accounts
    - **Approval workflows:** PO-based purchasing, spending limits per requester
    - **Tax exemption management:** Automated tax exemption certificates by state
    - **Guided buying:** Restrict purchases to approved categories or sellers
    - **Business Prime:** Expedited shipping with 2-day delivery for business accounts
    - **Integration:** Connects to Coupa, SAP Ariba, and other P2P systems via punchout

### 8.2 Account-Based Marketing (ABM) for B2B

**Account-Based Marketing** flips the traditional B2B marketing funnel. Instead of generating volume leads and filtering, ABM identifies specific target accounts and creates personalized campaigns for each account.

**ABM Tiers:**

| Tier | Scale | Personalization | Budget per Account |
|------|-------|-----------------|-------------------|
| **Strategic ABM (1:1)** | 5–50 accounts | Fully bespoke campaigns | $10K–$100K+ |
| **ABM Lite (1:Few)** | 50–500 accounts | Industry/segment-level | $1K–$10K |
| **Programmatic ABM (1:Many)** | 500–5,000+ accounts | Automated personalization | $100–$1K |

**ABM campaign components:**
- **Intent data:** Third-party signals showing account is researching your category (Bombora, G2 Buyer Intent)
- **Account scoring:** Firmographic + technographic + intent scoring model
- **Personalized landing pages:** Custom pages referencing account name, industry, and specific pain points
- **LinkedIn ABM:** Sponsored Content targeted at specific company + job title combos
- **Sales + Marketing alignment:** Shared account plan; marketing supplies sales with account insights

---

## 9. Real-World Cases

### 9.1 Boeing Supplier Portal

Boeing operates one of the world's most sophisticated B2B procurement platforms — the **Boeing Supplier Portal (BSP)** — managing relationships with approximately **12,500 active suppliers** across 70+ countries.

**Platform capabilities:**
- **Exostar Integration:** Boeing co-founded Exostar, an aerospace B2B network for secure document exchange and supplier qualification
- **Schedule management:** Suppliers receive production schedules (similar to EDI 830) and must confirm capacity
- **Quality management:** Non-conformance reports (NCRs), corrective action requests (CARs), and First Article Inspection (FAI) status tracked digitally
- **ITAR/EAR compliance:** Export control classification integrated into supplier authorization matrix
- **D1-9000 Quality Requirements:** Boeing's supplier quality system requirements digitally enforced
- **Finance portal:** Invoice submission, payment status, early payment discount offers

**Business rules engine:** Boeing's portal enforces complex business rules:
- Supplier cannot receive new POs if quality score < 85%
- Tooling orders require Engineering approval signature
- International shipments trigger automated ITAR screening
- Any delivery > 5 days late triggers automatic escalation to commodity manager

!!! info "Scale of Boeing's Supply Chain"
    A single Boeing 787 Dreamliner has approximately **2.3 million parts** from 900+ suppliers. The supply chain spans 47 countries and includes Tier 1, 2, and 3 suppliers. Effective digital procurement infrastructure is not optional — it is existential.

### 9.2 Walmart Supplier Connect

**Walmart Supplier Connect** is Walmart's mandatory supplier engagement platform used by all 100,000+ Walmart suppliers globally.

**Key platform features:**

- **Item Management:** Suppliers manage all product data (descriptions, images, nutritional info, regulatory) in a structured PIM system that feeds Walmart.com, in-store systems, and EDI
- **EDI Compliance:** Walmart mandates EDI 850/856/810 for all transactions above a transaction threshold. Non-compliance results in financial chargebacks
- **Retail Link (analytics):** Suppliers access their own sales velocity, inventory levels, and on-shelf availability data in near-real-time — enabling them to manage their own supply more proactively
- **SQEP (Supplier Quality Excellence Program):** Performance scoring on quality, delivery, and data accuracy; scores affect shelf space allocation
- **Sustainability Index (Project Gigaton):** Suppliers report environmental metrics (GHG, water, waste) via HowGood integration

**EDI chargebacks (Walmart):**
- Late ASN (856): $250 or 1.5% of PO value
- Missing UCC-128 label: $100 per pallet
- Non-compliance with modular slot requirements: $500 per occurrence

!!! warning "Walmart's Chargeback Program"
    Walmart's chargeback system is a significant revenue source for the retailer and a significant cost for non-compliant suppliers. Some suppliers estimate chargeback costs at 1–3% of Walmart revenue annually. This drives investment in supply chain automation and EDI compliance.

---

## Key Vocabulary

| Term | Definition |
|------|-----------|
| **B2B E-Commerce** | Electronic commerce transactions between businesses |
| **DMU** | Decision-Making Unit — all individuals involved in a B2B purchase decision |
| **Sell-Side Model** | B2B platform operated by a seller to serve multiple business buyers |
| **Buy-Side Model** | B2B platform operated by a buyer to manage multiple suppliers |
| **E-Procurement** | Digital automation of the purchase-to-pay process |
| **Punch-Out Catalog** | Supplier website integrated into buyer's procurement system via cXML |
| **EDI** | Electronic Data Interchange — standardized B2B document exchange format |
| **ANSI X12** | North American EDI standard with 200+ transaction sets |
| **EDIFACT** | UN international EDI standard used in Europe and globally |
| **Reverse Auction** | Suppliers compete by bidding prices down; buyer selects lowest qualified bid |
| **SRM** | Supplier Relationship Management — strategic supplier performance management |
| **Kraljic Matrix** | Tool for classifying suppliers by profit impact and supply risk |
| **VAN** | Value-Added Network — private network for EDI transmission |
| **cXML** | Commerce XML — standard for catalog and order data in procurement systems |
| **ABM** | Account-Based Marketing — personalized B2B marketing targeting specific companies |
| **P2P** | Purchase-to-Pay — end-to-end procurement process from requisition to payment |
| **Chargeback** | Financial penalty imposed on supplier for non-compliance with trading partner requirements |

---

## Review Questions

!!! question "Week 7 Review Questions"

    1. **A manufacturing company is deciding between a sell-side portal (built by a key supplier) and a buy-side procurement platform (built internally). What are the strategic advantages and risks of each approach? How does the concept of switching costs factor into each model? Consider the impact on supplier relationships, pricing leverage, and system integration.**

    2. **Compare ANSI X12 and EDIFACT EDI standards. Why have REST APIs not fully replaced EDI in enterprise B2B commerce despite being technically superior in many respects? Describe a scenario where a company would use both simultaneously, and explain how data mapping between EDI and modern systems works.**

    3. **Apply the Kraljic Matrix to a hypothetical aerospace manufacturer's supply base. Give a specific example of a supplier in each quadrant and describe the appropriate procurement strategy and relationship model for each. How would the company's e-procurement platform treat each quadrant differently?**

    4. **Walmart's Supplier Connect platform uses financial chargebacks to enforce compliance. Analyze this approach from the perspectives of: (a) Walmart's strategic goals, (b) a large, sophisticated supplier, and (c) a small domestic supplier. Is this model ethical and effective? What technology investments would a supplier need to make to avoid chargebacks?**

    5. **Design an Account-Based Marketing (ABM) campaign for a B2B SaaS company targeting 20 mid-market manufacturing companies (500–2,000 employees) that currently use manual procurement spreadsheets. Define your ABM tier, content strategy, channel mix, and how you would measure success. How does ABM differ fundamentally from traditional B2B lead generation?**

---

## Further Reading

- Ariba. (2024). *SAP Business Network Documentation*. [help.sap.com/docs/ariba](https://help.sap.com/docs/ariba)
- Coupa Software. (2024). *Business Spend Management Platform*. [coupa.com](https://www.coupa.com)
- Alibaba Group. (2024). *Alibaba.com B2B Marketplace*. [alibaba.com](https://www.alibaba.com)
- Moazed, A., & Johnson, N. L. (2016). *Modern Monopolies: What It Takes to Dominate the 21st Century Economy*. St. Martin's Press. — Chapters on platform business models apply directly to B2B exchanges.
- Kraljic, P. (1983). Purchasing must become supply management. *Harvard Business Review*, 61(5), 109–117.
- McKinsey & Company. (2022). *The new B2B growth equation*. [mckinsey.com](https://www.mckinsey.com/capabilities/growth-marketing-and-sales/our-insights/the-new-b2b-growth-equation)
- GS1 US. (2024). *EDI Standards & Implementation Guides*. [gs1us.org](https://www.gs1us.org)
- Walmart. (2024). *Supplier Requirements and Walmart Supplier Connect*. [corporate.walmart.com](https://corporate.walmart.com)

---

[← Week 6](week06.md) | [Course Index](index.md) | [Week 8 →](week08.md)
