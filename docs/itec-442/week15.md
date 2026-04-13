---
title: "Week 15 — E-Commerce System Design & Implementation Capstone"
description: "Complete e-commerce system architecture, Node.js/Express/MySQL implementation walkthrough with real code, database schema design, authentication, deployment, performance, SEO, security hardening, analytics, and final project rubric for ITEC 442."
---

# Week 15 — E-Commerce System Design & Implementation Capstone

> **Course Objective:** CO9 — Design, implement, and evaluate a complete e-commerce system, integrating frontend, backend, database, payment, and deployment components with professional engineering practices.

---

## Learning Objectives

By the end of this week, you should be able to:

- [x] Design a complete e-commerce system architecture diagram with all major components
- [x] Select an appropriate technology stack using a structured decision framework
- [x] Implement a Node.js/Express REST API for product catalog, cart, and order management
- [x] Design a normalized e-commerce database schema with appropriate indexes
- [x] Implement JWT-based authentication with bcrypt password hashing and refresh tokens
- [x] Integrate Stripe payment processing for one-time purchases and subscriptions
- [x] Containerize an application with Docker for consistent development and deployment
- [x] Apply a security hardening checklist to a production e-commerce deployment
- [x] Configure GA4 e-commerce events for comprehensive purchase funnel analytics

---

## 1. Complete E-Commerce System Architecture

### 1.1 The Big Picture

A production-grade e-commerce system is not a single application — it is a **distributed system** of cooperating services, each responsible for a bounded domain. Before writing a single line of code, architects must understand all the components and how they interact.

```
                        ┌─────────────────────────────┐
                        │     CUSTOMER DEVICES         │
                        │  Browser │ Mobile App │ PWA  │
                        └──────────────┬──────────────┘
                                       │ HTTPS
                        ┌──────────────▼──────────────┐
                        │   CDN / Edge Network         │
                        │  (Cloudflare / CloudFront)   │
                        │  Static assets, DDoS protect │
                        └──────────────┬──────────────┘
                                       │
               ┌───────────────────────┼───────────────────────┐
               │                       │                       │
   ┌───────────▼──────┐   ┌────────────▼───────┐   ┌──────────▼──────┐
   │   FRONTEND SPA   │   │   API GATEWAY /     │   │  ADMIN PANEL    │
   │  (Next.js/React) │   │   LOAD BALANCER     │   │  (React + Auth) │
   │  Hosted on Vercel│   │  (Nginx / AWS ALB)  │   │                 │
   └──────────────────┘   └────────────┬────────┘   └─────────────────┘
                                       │
              ┌────────────────────────┼──────────────────────┐
              │                        │                      │
   ┌──────────▼───────┐    ┌───────────▼──────┐   ┌──────────▼──────┐
   │  PRODUCT SERVICE │    │  ORDER SERVICE   │   │  AUTH SERVICE   │
   │  Node.js/Express │    │  Node.js/Express │   │  Node.js/Express│
   │  GET catalog     │    │  POST orders     │   │  JWT / OAuth    │
   └──────────┬───────┘    └───────────┬──────┘   └──────────┬──────┘
              │                        │                      │
   ┌──────────▼───────┐    ┌───────────▼──────┐   ┌──────────▼──────┐
   │   MySQL (RDS)    │    │  MySQL (RDS)     │   │  Redis           │
   │   Product tables │    │  Order tables    │   │  Session/Token  │
   └──────────────────┘    └───────────┬──────┘   └─────────────────┘
                                       │
              ┌────────────────────────┼──────────────────────┐
              │                        │                      │
   ┌──────────▼───────┐    ┌───────────▼──────┐   ┌──────────▼──────┐
   │  STRIPE API      │    │  EMAIL SERVICE   │   │  SEARCH SERVICE  │
   │  Payment intent  │    │  (SendGrid)      │   │  (Elasticsearch  │
   │  Webhooks        │    │  Order confirm.  │   │   or Typesense)  │
   └──────────────────┘    └──────────────────┘   └─────────────────┘
```

### 1.2 Technology Stack Selection Framework

Choosing your stack is one of the most consequential architectural decisions. Use a structured framework rather than defaulting to "whatever I know best."

=== "Frontend Options"
    | Technology | Strengths | When to Choose |
    |-----------|-----------|----------------|
    | **Next.js (React)** | SSR/SSG for SEO, excellent DX, huge ecosystem, Vercel deployment | Most new e-commerce builds; when SEO matters |
    | **Nuxt.js (Vue)** | Similar to Next.js; Vue ecosystem | Vue.js teams; slightly gentler learning curve |
    | **Remix** | Full-stack React; excellent loading patterns | Complex data requirements; real-time features |
    | **Astro** | Zero-JS by default; islands architecture | Content-heavy catalogs; maximum performance |
    | **SvelteKit** | Minimal boilerplate; excellent performance | Smaller teams wanting less complexity |

=== "Backend Options"
    | Technology | Strengths | When to Choose |
    |-----------|-----------|----------------|
    | **Node.js + Express** | Fast I/O; JS everywhere; massive npm ecosystem | API-heavy services; full-stack JS teams |
    | **Node.js + Fastify** | 2-3x faster than Express; schema-based validation | Performance-critical APIs |
    | **Python + FastAPI** | Automatic OpenAPI docs; type hints; data science integration | ML-powered features; Python teams |
    | **Go** | Excellent performance; low memory; compiled | High-throughput microservices; DevOps-friendly teams |
    | **Java + Spring Boot** | Enterprise-grade; mature ecosystem | Large enterprise; existing Java teams |

=== "Database Options"
    | Technology | Type | When to Choose |
    |-----------|------|----------------|
    | **MySQL / PostgreSQL** | Relational SQL | Default for e-commerce; ACID transactions required |
    | **MongoDB** | Document NoSQL | Product catalogs with highly variable attributes; flexible schema |
    | **Redis** | In-memory key-value | Session storage; cart caching; rate limiting; real-time inventory |
    | **Elasticsearch** | Search engine | Product search with faceting, typo tolerance, relevance tuning |
    | **DynamoDB** | Managed NoSQL | Extreme scale; serverless; AWS-native |

=== "E-Commerce Platform Options"
    | Approach | Stack | When to Choose |
    |---------|-------|----------------|
    | **SaaS Platform** | Shopify, BigCommerce, WooCommerce | < $1M GMV; speed to market priority; limited dev resources |
    | **Headless + SaaS Backend** | Next.js + Shopify Storefront API | $1M-$50M GMV; custom UX needed; standard commerce logic |
    | **Custom Build** | Node.js + MySQL + Stripe | Learning project OR very unique business logic requirements |
    | **Open Source** | Medusa.js, Vendure, Saleor | Developer-first; full control; no licensing cost |

!!! warning "The Custom Build Trap"
    Building a full e-commerce platform from scratch is appropriate for this course as a **learning exercise** but rarely the right choice for a real business. Shopify has 10,000+ engineers and 16+ years of e-commerce development refinement. Your custom build will have security vulnerabilities, scaling limitations, and missing edge cases that Shopify solved years ago. **Build to learn; use platforms to earn.**

---

## 2. Database Schema Design

### 2.1 E-Commerce Entity Relationship Overview

A well-designed e-commerce database schema is the foundation everything else builds on. Let's design a normalized, production-ready schema.

```sql
-- =====================================================
-- E-COMMERCE DATABASE SCHEMA
-- MySQL 8.0 | InnoDB | UTF8MB4
-- =====================================================

-- -----------------------------------------------------
-- CATEGORIES (hierarchical, supports subcategories)
-- -----------------------------------------------------
CREATE TABLE categories (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    parent_id   INT UNSIGNED NULL,           -- NULL = top-level category
    name        VARCHAR(100) NOT NULL,
    slug        VARCHAR(100) NOT NULL,       -- URL-safe identifier
    description TEXT NULL,
    image_url   VARCHAR(500) NULL,
    sort_order  TINYINT UNSIGNED DEFAULT 0,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    UNIQUE KEY uq_categories_slug (slug),
    KEY idx_categories_parent (parent_id),
    CONSTRAINT fk_cat_parent FOREIGN KEY (parent_id) 
        REFERENCES categories(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- PRODUCTS
-- -----------------------------------------------------
CREATE TABLE products (
    id              INT UNSIGNED NOT NULL AUTO_INCREMENT,
    category_id     INT UNSIGNED NOT NULL,
    name            VARCHAR(255) NOT NULL,
    slug            VARCHAR(255) NOT NULL,
    description     TEXT NULL,
    short_description VARCHAR(500) NULL,
    sku             VARCHAR(100) NOT NULL,
    price           DECIMAL(10,2) NOT NULL,
    compare_price   DECIMAL(10,2) NULL,      -- "was" price for sale display
    cost_price      DECIMAL(10,2) NULL,      -- for margin reporting
    stock_quantity  INT NOT NULL DEFAULT 0,
    low_stock_threshold INT DEFAULT 10,
    weight_grams    INT UNSIGNED NULL,        -- for shipping calculation
    is_active       BOOLEAN DEFAULT TRUE,
    is_featured     BOOLEAN DEFAULT FALSE,
    meta_title      VARCHAR(255) NULL,        -- SEO
    meta_description VARCHAR(500) NULL,       -- SEO
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    UNIQUE KEY uq_products_slug (slug),
    UNIQUE KEY uq_products_sku (sku),
    KEY idx_products_category (category_id),
    KEY idx_products_price (price),
    KEY idx_products_active_featured (is_active, is_featured),
    CONSTRAINT fk_products_category FOREIGN KEY (category_id) 
        REFERENCES categories(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- PRODUCT IMAGES
-- -----------------------------------------------------
CREATE TABLE product_images (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    product_id  INT UNSIGNED NOT NULL,
    url         VARCHAR(500) NOT NULL,
    alt_text    VARCHAR(255) NULL,
    sort_order  TINYINT UNSIGNED DEFAULT 0,
    is_primary  BOOLEAN DEFAULT FALSE,
    
    PRIMARY KEY (id),
    KEY idx_pimages_product (product_id),
    CONSTRAINT fk_pimages_product FOREIGN KEY (product_id) 
        REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- USERS (customers)
-- -----------------------------------------------------
CREATE TABLE users (
    id              INT UNSIGNED NOT NULL AUTO_INCREMENT,
    email           VARCHAR(255) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,   -- bcrypt hash; NEVER plaintext
    first_name      VARCHAR(100) NULL,
    last_name       VARCHAR(100) NULL,
    phone           VARCHAR(30) NULL,
    is_verified     BOOLEAN DEFAULT FALSE,   -- email verification
    is_admin        BOOLEAN DEFAULT FALSE,
    stripe_customer_id VARCHAR(100) NULL,    -- Stripe customer reference
    last_login_at   DATETIME NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email (email),
    KEY idx_users_stripe (stripe_customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- ADDRESSES
-- -----------------------------------------------------
CREATE TABLE addresses (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id     INT UNSIGNED NOT NULL,
    type        ENUM('shipping','billing') DEFAULT 'shipping',
    is_default  BOOLEAN DEFAULT FALSE,
    first_name  VARCHAR(100) NOT NULL,
    last_name   VARCHAR(100) NOT NULL,
    company     VARCHAR(200) NULL,
    address1    VARCHAR(255) NOT NULL,
    address2    VARCHAR(255) NULL,
    city        VARCHAR(100) NOT NULL,
    state       VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    country     CHAR(2) NOT NULL DEFAULT 'US',  -- ISO 3166-1 alpha-2
    phone       VARCHAR(30) NULL,
    
    PRIMARY KEY (id),
    KEY idx_addresses_user (user_id),
    CONSTRAINT fk_addresses_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- ORDERS
-- -----------------------------------------------------
CREATE TABLE orders (
    id                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id             INT UNSIGNED NULL,       -- NULL = guest checkout
    order_number        VARCHAR(50) NOT NULL,    -- human-readable: ORD-2024-00042
    status              ENUM(
                            'pending',           -- awaiting payment
                            'payment_processing', -- Stripe processing
                            'paid',              -- payment confirmed
                            'processing',        -- fulfillment started
                            'shipped',           -- carrier received
                            'delivered',         -- confirmed delivery
                            'cancelled',
                            'refunded',
                            'partially_refunded'
                        ) DEFAULT 'pending',
    
    -- Financial summary (denormalized for reporting performance)
    subtotal            DECIMAL(10,2) NOT NULL,
    discount_amount     DECIMAL(10,2) DEFAULT 0.00,
    shipping_amount     DECIMAL(10,2) DEFAULT 0.00,
    tax_amount          DECIMAL(10,2) DEFAULT 0.00,
    total_amount        DECIMAL(10,2) NOT NULL,
    
    -- Shipping information (snapshot at order time; address may change later)
    shipping_name       VARCHAR(200) NOT NULL,
    shipping_address1   VARCHAR(255) NOT NULL,
    shipping_address2   VARCHAR(255) NULL,
    shipping_city       VARCHAR(100) NOT NULL,
    shipping_state      VARCHAR(100) NOT NULL,
    shipping_postal     VARCHAR(20) NOT NULL,
    shipping_country    CHAR(2) NOT NULL DEFAULT 'US',
    
    -- Fulfillment
    tracking_number     VARCHAR(200) NULL,
    carrier             VARCHAR(100) NULL,       -- UPS, FedEx, USPS
    notes               TEXT NULL,
    guest_email         VARCHAR(255) NULL,       -- for guest orders
    
    -- Timestamps
    paid_at             DATETIME NULL,
    shipped_at          DATETIME NULL,
    delivered_at        DATETIME NULL,
    cancelled_at        DATETIME NULL,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    UNIQUE KEY uq_orders_number (order_number),
    KEY idx_orders_user (user_id),
    KEY idx_orders_status (status),
    KEY idx_orders_created (created_at),
    CONSTRAINT fk_orders_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- ORDER ITEMS
-- -----------------------------------------------------
CREATE TABLE order_items (
    id              INT UNSIGNED NOT NULL AUTO_INCREMENT,
    order_id        INT UNSIGNED NOT NULL,
    product_id      INT UNSIGNED NULL,       -- NULL if product later deleted
    
    -- Snapshot fields: product details at time of purchase (immutable)
    product_name    VARCHAR(255) NOT NULL,
    product_sku     VARCHAR(100) NOT NULL,
    product_image   VARCHAR(500) NULL,
    unit_price      DECIMAL(10,2) NOT NULL,  -- price paid (after any discount)
    quantity        INT UNSIGNED NOT NULL,
    subtotal        DECIMAL(10,2) NOT NULL,  -- unit_price × quantity
    
    PRIMARY KEY (id),
    KEY idx_oitems_order (order_id),
    KEY idx_oitems_product (product_id),
    CONSTRAINT fk_oitems_order FOREIGN KEY (order_id) 
        REFERENCES orders(id) ON DELETE CASCADE,
    CONSTRAINT fk_oitems_product FOREIGN KEY (product_id) 
        REFERENCES products(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- PAYMENTS
-- -----------------------------------------------------
CREATE TABLE payments (
    id                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    order_id            INT UNSIGNED NOT NULL,
    stripe_payment_intent_id VARCHAR(200) NOT NULL,
    stripe_charge_id    VARCHAR(200) NULL,
    amount              DECIMAL(10,2) NOT NULL,
    currency            CHAR(3) NOT NULL DEFAULT 'usd',
    status              ENUM('pending','succeeded','failed','refunded','partially_refunded') 
                            DEFAULT 'pending',
    payment_method_type VARCHAR(50) NULL,       -- card, paypal, link, etc.
    card_last4          CHAR(4) NULL,
    card_brand          VARCHAR(20) NULL,        -- visa, mastercard, amex
    refund_amount       DECIMAL(10,2) DEFAULT 0.00,
    stripe_refund_id    VARCHAR(200) NULL,
    metadata            JSON NULL,              -- additional Stripe metadata
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    UNIQUE KEY uq_payments_intent (stripe_payment_intent_id),
    KEY idx_payments_order (order_id),
    KEY idx_payments_status (status),
    CONSTRAINT fk_payments_order FOREIGN KEY (order_id) 
        REFERENCES orders(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- REFRESH TOKENS (for JWT rotation)
-- -----------------------------------------------------
CREATE TABLE refresh_tokens (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id     INT UNSIGNED NOT NULL,
    token_hash  VARCHAR(255) NOT NULL,        -- bcrypt hash of token
    expires_at  DATETIME NOT NULL,
    revoked_at  DATETIME NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    KEY idx_rtokens_user (user_id),
    KEY idx_rtokens_expires (expires_at),
    CONSTRAINT fk_rtokens_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 3. Node.js + Express API Implementation

### 3.1 Project Setup and Structure

```
ecommerce-api/
├── src/
│   ├── app.js                 # Express application setup
│   ├── server.js              # HTTP server entry point
│   ├── config/
│   │   ├── database.js        # MySQL connection pool
│   │   └── env.js             # Environment variable validation
│   ├── middleware/
│   │   ├── auth.js            # JWT authentication middleware
│   │   ├── rateLimiter.js     # Rate limiting middleware
│   │   ├── errorHandler.js    # Global error handling
│   │   └── validate.js        # Request validation middleware
│   ├── routes/
│   │   ├── auth.routes.js
│   │   ├── products.routes.js
│   │   ├── cart.routes.js
│   │   ├── orders.routes.js
│   │   └── webhooks.routes.js
│   ├── controllers/
│   │   ├── auth.controller.js
│   │   ├── products.controller.js
│   │   ├── cart.controller.js
│   │   └── orders.controller.js
│   └── utils/
│       ├── asyncHandler.js    # Wraps async route handlers
│       └── generateOrderNumber.js
├── package.json
├── .env.example
└── Dockerfile
```

### 3.2 Application Bootstrap

```javascript
// src/app.js
const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const rateLimit = require('express-rate-limit');

const authRoutes = require('./routes/auth.routes');
const productRoutes = require('./routes/products.routes');
const cartRoutes = require('./routes/cart.routes');
const orderRoutes = require('./routes/orders.routes');
const webhookRoutes = require('./routes/webhooks.routes');
const errorHandler = require('./middleware/errorHandler');

const app = express();

// ── Security middleware ──────────────────────────────────────────────────────
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "https://js.stripe.com"],
      frameSrc: ["https://js.stripe.com"],
      connectSrc: ["'self'", "https://api.stripe.com"]
    }
  },
  hsts: { maxAge: 31536000, includeSubDomains: true, preload: true }
}));

app.use(cors({
  origin: process.env.ALLOWED_ORIGINS.split(','),
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true
}));

// ── Stripe webhooks MUST receive raw body before JSON parsing ────────────────
app.use('/api/webhooks/stripe', express.raw({ type: 'application/json' }));

// ── Body parsing ─────────────────────────────────────────────────────────────
app.use(express.json({ limit: '10kb' }));  // Limit body size

// ── Global rate limiting ─────────────────────────────────────────────────────
const globalLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,   // 15 minutes
  max: 100,                    // 100 requests per window per IP
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many requests, please try again later.' }
});
app.use('/api/', globalLimiter);

// ── Routes ───────────────────────────────────────────────────────────────────
app.use('/api/auth', authRoutes);
app.use('/api/products', productRoutes);
app.use('/api/cart', cartRoutes);
app.use('/api/orders', orderRoutes);
app.use('/api/webhooks', webhookRoutes);

// Health check (for load balancer / container orchestration)
app.get('/health', (req, res) => res.json({ status: 'ok', timestamp: new Date() }));

// ── Global error handler (must be last) ─────────────────────────────────────
app.use(errorHandler);

module.exports = app;
```

### 3.3 Authentication Implementation (JWT + bcrypt)

```javascript
// src/controllers/auth.controller.js
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const crypto = require('crypto');
const db = require('../config/database');

const SALT_ROUNDS = 12;
const ACCESS_TOKEN_EXPIRY = '15m';
const REFRESH_TOKEN_EXPIRY = '30d';

// ── Helper: Generate token pair ──────────────────────────────────────────────
function generateTokens(userId) {
  const accessToken = jwt.sign(
    { sub: userId, type: 'access' },
    process.env.JWT_ACCESS_SECRET,
    { expiresIn: ACCESS_TOKEN_EXPIRY, issuer: 'ecommerce-api' }
  );
  
  // Refresh token is a cryptographically random string (NOT a JWT)
  // JWTs as refresh tokens cannot be revoked server-side without a token store
  const refreshToken = crypto.randomBytes(40).toString('hex');
  
  return { accessToken, refreshToken };
}

// ── POST /api/auth/register ──────────────────────────────────────────────────
exports.register = async (req, res, next) => {
  try {
    const { email, password, firstName, lastName } = req.body;
    
    // Check for existing user
    const [existing] = await db.query(
      'SELECT id FROM users WHERE email = ?', [email]
    );
    if (existing.length > 0) {
      return res.status(409).json({ error: 'Email already registered' });
    }
    
    // Hash password — bcrypt with cost factor 12
    const passwordHash = await bcrypt.hash(password, SALT_ROUNDS);
    
    // Insert user
    const [result] = await db.query(
      `INSERT INTO users (email, password_hash, first_name, last_name) 
       VALUES (?, ?, ?, ?)`,
      [email.toLowerCase(), passwordHash, firstName, lastName]
    );
    const userId = result.insertId;
    
    // Generate tokens
    const { accessToken, refreshToken } = generateTokens(userId);
    
    // Store hashed refresh token
    const refreshTokenHash = await bcrypt.hash(refreshToken, 10);
    const expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);
    await db.query(
      'INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)',
      [userId, refreshTokenHash, expiresAt]
    );
    
    // Set refresh token as httpOnly cookie
    res.cookie('refreshToken', refreshToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 30 * 24 * 60 * 60 * 1000   // 30 days
    });
    
    res.status(201).json({
      message: 'Account created successfully',
      accessToken,
      user: { id: userId, email, firstName, lastName }
    });
    
  } catch (error) {
    next(error);
  }
};

// ── POST /api/auth/login ─────────────────────────────────────────────────────
exports.login = async (req, res, next) => {
  try {
    const { email, password } = req.body;
    
    // Fetch user — use constant-time comparison to prevent timing attacks
    const [users] = await db.query(
      'SELECT id, email, password_hash, first_name, last_name, is_admin FROM users WHERE email = ?',
      [email.toLowerCase()]
    );
    
    // Always hash even if user not found (prevent timing oracle)
    const dummyHash = '$2a$12$K.sLHHs6WMsVF9WL4bZ9b.';
    const hashToCompare = users[0]?.password_hash || dummyHash;
    const passwordMatch = await bcrypt.compare(password, hashToCompare);
    
    if (!users[0] || !passwordMatch) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }
    
    const user = users[0];
    const { accessToken, refreshToken } = generateTokens(user.id);
    
    // Store refresh token
    const refreshTokenHash = await bcrypt.hash(refreshToken, 10);
    const expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);
    await db.query(
      'INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)',
      [user.id, refreshTokenHash, expiresAt]
    );
    
    // Update last_login_at
    await db.query('UPDATE users SET last_login_at = NOW() WHERE id = ?', [user.id]);
    
    res.cookie('refreshToken', refreshToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 30 * 24 * 60 * 60 * 1000
    });
    
    res.json({
      accessToken,
      user: {
        id: user.id,
        email: user.email,
        firstName: user.first_name,
        lastName: user.last_name,
        isAdmin: user.is_admin
      }
    });
    
  } catch (error) {
    next(error);
  }
};

// ── POST /api/auth/refresh ───────────────────────────────────────────────────
exports.refreshToken = async (req, res, next) => {
  try {
    const incomingToken = req.cookies.refreshToken;
    if (!incomingToken) {
      return res.status(401).json({ error: 'No refresh token' });
    }
    
    // Find non-expired, non-revoked tokens for comparison
    const [tokens] = await db.query(
      `SELECT rt.id, rt.token_hash, rt.user_id, u.email, u.is_admin
       FROM refresh_tokens rt
       JOIN users u ON rt.user_id = u.id
       WHERE rt.expires_at > NOW() AND rt.revoked_at IS NULL
       ORDER BY rt.created_at DESC LIMIT 10`
    );
    
    // Find matching token (bcrypt comparison)
    let matchedToken = null;
    for (const token of tokens) {
      if (await bcrypt.compare(incomingToken, token.token_hash)) {
        matchedToken = token;
        break;
      }
    }
    
    if (!matchedToken) {
      return res.status(401).json({ error: 'Invalid or expired refresh token' });
    }
    
    // Rotate: revoke old token, issue new pair
    await db.query(
      'UPDATE refresh_tokens SET revoked_at = NOW() WHERE id = ?',
      [matchedToken.id]
    );
    
    const { accessToken, refreshToken: newRefreshToken } = generateTokens(matchedToken.user_id);
    const newHash = await bcrypt.hash(newRefreshToken, 10);
    const expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);
    
    await db.query(
      'INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)',
      [matchedToken.user_id, newHash, expiresAt]
    );
    
    res.cookie('refreshToken', newRefreshToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 30 * 24 * 60 * 60 * 1000
    });
    
    res.json({ accessToken });
    
  } catch (error) {
    next(error);
  }
};
```

### 3.4 Product Catalog API

```javascript
// src/controllers/products.controller.js
const db = require('../config/database');

// ── GET /api/products ────────────────────────────────────────────────────────
// Supports: ?category=electronics&sort=price_asc&page=1&limit=20&search=laptop
exports.getProducts = async (req, res, next) => {
  try {
    const {
      category,
      sort = 'created_at_desc',
      page = 1,
      limit = 20,
      search,
      minPrice,
      maxPrice,
      featured
    } = req.query;
    
    const pageNum = Math.max(1, parseInt(page));
    const limitNum = Math.min(100, Math.max(1, parseInt(limit)));
    const offset = (pageNum - 1) * limitNum;
    
    // Build dynamic WHERE clause
    let whereConditions = ['p.is_active = TRUE'];
    const params = [];
    
    if (category) {
      whereConditions.push('c.slug = ?');
      params.push(category);
    }
    if (search) {
      whereConditions.push('(p.name LIKE ? OR p.description LIKE ? OR p.sku LIKE ?)');
      const searchTerm = `%${search}%`;
      params.push(searchTerm, searchTerm, searchTerm);
    }
    if (minPrice) {
      whereConditions.push('p.price >= ?');
      params.push(parseFloat(minPrice));
    }
    if (maxPrice) {
      whereConditions.push('p.price <= ?');
      params.push(parseFloat(maxPrice));
    }
    if (featured === 'true') {
      whereConditions.push('p.is_featured = TRUE');
    }
    
    // Build ORDER BY
    const sortMap = {
      'price_asc':       'p.price ASC',
      'price_desc':      'p.price DESC',
      'name_asc':        'p.name ASC',
      'created_at_desc': 'p.created_at DESC',
      'popularity':      'order_count DESC'
    };
    const orderBy = sortMap[sort] || 'p.created_at DESC';
    
    const whereClause = whereConditions.join(' AND ');
    
    // Count query for pagination
    const [countResult] = await db.query(
      `SELECT COUNT(*) as total
       FROM products p
       JOIN categories c ON p.category_id = c.id
       WHERE ${whereClause}`,
      params
    );
    const total = countResult[0].total;
    
    // Data query
    const [products] = await db.query(
      `SELECT 
          p.id, p.name, p.slug, p.short_description,
          p.price, p.compare_price, p.stock_quantity,
          p.is_featured,
          c.name AS category_name, c.slug AS category_slug,
          pi.url AS primary_image, pi.alt_text AS primary_image_alt,
          COUNT(DISTINCT oi.id) AS order_count
       FROM products p
       JOIN categories c ON p.category_id = c.id
       LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = TRUE
       LEFT JOIN order_items oi ON oi.product_id = p.id
       WHERE ${whereClause}
       GROUP BY p.id
       ORDER BY ${orderBy}
       LIMIT ? OFFSET ?`,
      [...params, limitNum, offset]
    );
    
    res.json({
      data: products,
      pagination: {
        page: pageNum,
        limit: limitNum,
        total,
        totalPages: Math.ceil(total / limitNum)
      }
    });
    
  } catch (error) {
    next(error);
  }
};

// ── GET /api/products/:slug ──────────────────────────────────────────────────
exports.getProductBySlug = async (req, res, next) => {
  try {
    const { slug } = req.params;
    
    const [products] = await db.query(
      `SELECT 
          p.*,
          c.name AS category_name, c.slug AS category_slug
       FROM products p
       JOIN categories c ON p.category_id = c.id
       WHERE p.slug = ? AND p.is_active = TRUE`,
      [slug]
    );
    
    if (products.length === 0) {
      return res.status(404).json({ error: 'Product not found' });
    }
    
    const product = products[0];
    
    // Fetch all images
    const [images] = await db.query(
      'SELECT id, url, alt_text, sort_order, is_primary FROM product_images WHERE product_id = ? ORDER BY sort_order',
      [product.id]
    );
    
    product.images = images;
    delete product.cost_price;  // Never expose cost to frontend
    
    res.json({ data: product });
    
  } catch (error) {
    next(error);
  }
};
```

### 3.5 Cart Management

```javascript
// src/controllers/cart.controller.js
// Cart is stored in Redis for authenticated users, localStorage on frontend
// This controller manages server-side cart validation before checkout

const db = require('../config/database');
const redis = require('../config/redis');

// ── POST /api/cart/validate ──────────────────────────────────────────────────
// Validates cart items before checkout: checks stock, verifies prices
exports.validateCart = async (req, res, next) => {
  try {
    const { items } = req.body;
    // items = [{ product_id: 1, quantity: 2 }, ...]
    
    if (!items || items.length === 0) {
      return res.status(400).json({ error: 'Cart is empty' });
    }
    
    const productIds = items.map(item => item.product_id);
    
    const [products] = await db.query(
      `SELECT id, name, slug, price, stock_quantity, is_active
       FROM products WHERE id IN (?)`,
      [productIds]
    );
    
    const productMap = {};
    products.forEach(p => { productMap[p.id] = p; });
    
    const validationErrors = [];
    const validatedItems = [];
    let subtotal = 0;
    
    for (const item of items) {
      const product = productMap[item.product_id];
      
      if (!product) {
        validationErrors.push({
          product_id: item.product_id,
          error: 'Product not found'
        });
        continue;
      }
      
      if (!product.is_active) {
        validationErrors.push({
          product_id: item.product_id,
          name: product.name,
          error: 'Product is no longer available'
        });
        continue;
      }
      
      if (product.stock_quantity < item.quantity) {
        validationErrors.push({
          product_id: item.product_id,
          name: product.name,
          error: `Only ${product.stock_quantity} units available`,
          available_quantity: product.stock_quantity
        });
        continue;
      }
      
      const itemSubtotal = product.price * item.quantity;
      subtotal += itemSubtotal;
      
      validatedItems.push({
        product_id: product.id,
        name: product.name,
        slug: product.slug,
        unit_price: product.price,
        quantity: item.quantity,
        subtotal: itemSubtotal
      });
    }
    
    if (validationErrors.length > 0) {
      return res.status(422).json({
        error: 'Cart validation failed',
        validation_errors: validationErrors
      });
    }
    
    res.json({
      items: validatedItems,
      subtotal: subtotal.toFixed(2)
    });
    
  } catch (error) {
    next(error);
  }
};
```

### 3.6 Stripe Payment Integration

```javascript
// src/controllers/orders.controller.js
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);
const db = require('../config/database');

// ── POST /api/orders/create-payment-intent ────────────────────────────────── 
// Step 1: Create Stripe PaymentIntent, return client_secret to frontend
exports.createPaymentIntent = async (req, res, next) => {
  try {
    const { items, shipping_address } = req.body;
    const userId = req.user?.id || null;
    
    // Validate cart server-side (never trust client-provided totals)
    const productIds = items.map(i => i.product_id);
    const [products] = await db.query(
      'SELECT id, name, sku, price, stock_quantity FROM products WHERE id IN (?) AND is_active = TRUE',
      [productIds]
    );
    
    const productMap = {};
    products.forEach(p => { productMap[p.id] = p; });
    
    let subtotal = 0;
    const lineItems = [];
    
    for (const item of items) {
      const product = productMap[item.product_id];
      if (!product || product.stock_quantity < item.quantity) {
        return res.status(422).json({ 
          error: 'Cart validation failed', 
          product_id: item.product_id 
        });
      }
      const lineTotal = product.price * item.quantity;
      subtotal += lineTotal;
      lineItems.push({ ...product, quantity: item.quantity, subtotal: lineTotal });
    }
    
    // Calculate tax (simplified; real implementation uses Stripe Tax or TaxJar)
    const taxRate = 0.06;  // 6% flat tax
    const taxAmount = subtotal * taxRate;
    const shippingAmount = subtotal >= 50 ? 0 : 7.99;  // free shipping over $50
    const totalAmount = subtotal + taxAmount + shippingAmount;
    
    // Convert to cents (Stripe uses integer cents)
    const amountCents = Math.round(totalAmount * 100);
    
    // Get or create Stripe customer for authenticated users
    let stripeCustomerId;
    if (userId) {
      const [userRows] = await db.query(
        'SELECT stripe_customer_id, email, first_name, last_name FROM users WHERE id = ?',
        [userId]
      );
      const user = userRows[0];
      
      if (!user.stripe_customer_id) {
        const customer = await stripe.customers.create({
          email: user.email,
          name: `${user.first_name} ${user.last_name}`,
          metadata: { user_id: String(userId) }
        });
        stripeCustomerId = customer.id;
        await db.query(
          'UPDATE users SET stripe_customer_id = ? WHERE id = ?',
          [customer.id, userId]
        );
      } else {
        stripeCustomerId = user.stripe_customer_id;
      }
    }
    
    // Create PaymentIntent
    const paymentIntent = await stripe.paymentIntents.create({
      amount: amountCents,
      currency: 'usd',
      customer: stripeCustomerId,
      automatic_payment_methods: { enabled: true },
      metadata: {
        user_id: userId ? String(userId) : 'guest',
        subtotal: subtotal.toFixed(2),
        tax: taxAmount.toFixed(2),
        shipping: shippingAmount.toFixed(2)
      }
    });
    
    // Create pending order in DB (updated to 'paid' after webhook confirmation)
    const orderNumber = `ORD-${new Date().getFullYear()}-${String(Date.now()).slice(-6)}`;
    
    const [orderResult] = await db.query(
      `INSERT INTO orders 
       (user_id, order_number, status, subtotal, tax_amount, shipping_amount, 
        total_amount, shipping_name, shipping_address1, shipping_address2,
        shipping_city, shipping_state, shipping_postal, shipping_country,
        guest_email)
       VALUES (?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        userId, orderNumber, subtotal, taxAmount, shippingAmount, totalAmount,
        shipping_address.name, shipping_address.address1, shipping_address.address2 || null,
        shipping_address.city, shipping_address.state, shipping_address.postal_code,
        shipping_address.country || 'US', shipping_address.email || null
      ]
    );
    const orderId = orderResult.insertId;
    
    // Insert order items
    for (const item of lineItems) {
      await db.query(
        `INSERT INTO order_items 
         (order_id, product_id, product_name, product_sku, unit_price, quantity, subtotal)
         VALUES (?, ?, ?, ?, ?, ?, ?)`,
        [orderId, item.id, item.name, item.sku, item.price, item.quantity, item.subtotal]
      );
    }
    
    // Create payment record
    await db.query(
      `INSERT INTO payments 
       (order_id, stripe_payment_intent_id, amount, currency, status)
       VALUES (?, ?, ?, 'usd', 'pending')`,
      [orderId, paymentIntent.id, totalAmount]
    );
    
    res.json({
      client_secret: paymentIntent.client_secret,
      order_id: orderId,
      order_number: orderNumber,
      summary: {
        subtotal: subtotal.toFixed(2),
        tax: taxAmount.toFixed(2),
        shipping: shippingAmount.toFixed(2),
        total: totalAmount.toFixed(2)
      }
    });
    
  } catch (error) {
    next(error);
  }
};

// ── POST /api/webhooks/stripe ─────────────────────────────────────────────── 
// Stripe sends server-to-server webhook when payment succeeds/fails
// This is the AUTHORITATIVE payment confirmation source
exports.handleStripeWebhook = async (req, res) => {
  const sig = req.headers['stripe-signature'];
  let event;
  
  try {
    // Verify webhook signature (prevents forged webhooks)
    event = stripe.webhooks.constructEvent(
      req.body,  // raw body — must NOT be parsed by express.json()
      sig,
      process.env.STRIPE_WEBHOOK_SECRET
    );
  } catch (err) {
    console.error('Webhook signature verification failed:', err.message);
    return res.status(400).send(`Webhook Error: ${err.message}`);
  }
  
  // Handle event types
  switch (event.type) {
    case 'payment_intent.succeeded': {
      const paymentIntent = event.data.object;
      
      // Update payment record
      await db.query(
        `UPDATE payments 
         SET status = 'succeeded', 
             stripe_charge_id = ?,
             card_last4 = ?,
             card_brand = ?,
             updated_at = NOW()
         WHERE stripe_payment_intent_id = ?`,
        [
          paymentIntent.latest_charge,
          paymentIntent.payment_method_details?.card?.last4 || null,
          paymentIntent.payment_method_details?.card?.brand || null,
          paymentIntent.id
        ]
      );
      
      // Update order status and decrement stock
      const [paymentRows] = await db.query(
        'SELECT order_id FROM payments WHERE stripe_payment_intent_id = ?',
        [paymentIntent.id]
      );
      
      if (paymentRows.length > 0) {
        const orderId = paymentRows[0].order_id;
        
        await db.query(
          "UPDATE orders SET status = 'paid', paid_at = NOW() WHERE id = ?",
          [orderId]
        );
        
        // Decrement stock quantities
        const [items] = await db.query(
          'SELECT product_id, quantity FROM order_items WHERE order_id = ?',
          [orderId]
        );
        
        for (const item of items) {
          await db.query(
            'UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?',
            [item.quantity, item.product_id]
          );
        }
        
        // TODO: Send order confirmation email via SendGrid
      }
      break;
    }
    
    case 'payment_intent.payment_failed': {
      const paymentIntent = event.data.object;
      await db.query(
        "UPDATE payments SET status = 'failed' WHERE stripe_payment_intent_id = ?",
        [paymentIntent.id]
      );
      break;
    }
  }
  
  res.json({ received: true });
};
```

---

## 4. Deployment Architecture

### 4.1 Dockerfile for the API

```dockerfile
# Dockerfile — Node.js API service
# Multi-stage build: reduces final image size significantly

# ── Stage 1: Dependencies ─────────────────────────────────────────────────────
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
# Install only production dependencies
RUN npm ci --omit=dev

# ── Stage 2: Build (if TypeScript or build step needed) ───────────────────────
FROM node:20-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# If using TypeScript: RUN npm run build

# ── Stage 3: Production image ─────────────────────────────────────────────────
FROM node:20-alpine AS runner
WORKDIR /app

# Security: run as non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nodeuser

COPY --from=build --chown=nodeuser:nodejs /app/node_modules ./node_modules
COPY --from=build --chown=nodeuser:nodejs /app/src ./src
COPY --from=build --chown=nodeuser:nodejs /app/package.json ./

USER nodeuser

EXPOSE 3000

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

CMD ["node", "src/server.js"]
```

### 4.2 Cloud Deployment Options

=== "AWS (Most Common)"
    **Recommended AWS architecture for a growing e-commerce startup:**
    
    ```
    Route 53 (DNS)
        │
    CloudFront (CDN + WAF)
        │
    ┌───┴────────────────────────────────┐
    │         Application Load Balancer  │
    │         (across 2 AZs)             │
    └───┬────────────────────────────────┘
        │
    ECS Fargate (Node.js API containers)
        │   Auto-scaling: 2-20 tasks based on CPU/request count
        │
    ┌───┼──────────────────────────────────┐
    │   │                                  │
    RDS MySQL           ElastiCache Redis
    (Multi-AZ)          (session storage,
                         rate limiting)
    ```
    
    **Services used:**
    - **ECS Fargate:** Serverless containers; no EC2 management
    - **RDS MySQL Multi-AZ:** Managed MySQL with automatic failover
    - **ElastiCache Redis:** Managed Redis for sessions, caching, rate limiting
    - **S3 + CloudFront:** Static assets (product images) served globally
    - **SES:** Transactional email (order confirmations)
    - **Secrets Manager:** Store .env secrets securely, injected at container runtime

=== "Google Cloud"
    **GCP equivalent architecture:**
    
    - **Cloud Run:** Serverless container hosting (equivalent to ECS Fargate)
    - **Cloud SQL (MySQL):** Managed MySQL
    - **Memorystore (Redis):** Managed Redis
    - **Cloud CDN + Cloud Armor:** CDN and WAF
    - **Cloud Storage:** Object storage for product images
    - **Secret Manager:** Secrets management
    
    Cloud Run advantage: Auto-scales to zero during low-traffic periods, ideal for cost-sensitive startups

=== "Azure"
    **Azure equivalent architecture:**
    
    - **Azure Container Apps:** Serverless container hosting
    - **Azure Database for MySQL:** Managed MySQL
    - **Azure Cache for Redis:** Managed Redis
    - **Azure Front Door:** CDN + WAF + load balancing
    - **Azure Blob Storage:** Object storage
    - **Azure Key Vault:** Secrets management

---

## 5. Performance Optimization

### 5.1 Database Query Optimization

```sql
-- EXPLAIN ANALYZE your slow queries before optimizing

EXPLAIN SELECT p.*, pi.url AS primary_image
FROM products p
LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = TRUE
WHERE p.category_id = 3 AND p.is_active = TRUE
ORDER BY p.price ASC
LIMIT 20;

-- If you see "type: ALL" (full table scan), add an index:
CREATE INDEX idx_products_cat_active_price 
ON products (category_id, is_active, price);

-- After index: should see "type: ref" using the composite index
```

### 5.2 API Response Caching

```javascript
// Redis cache middleware for product listings
const redis = require('../config/redis');

async function cacheMiddleware(keyPrefix, ttlSeconds = 300) {
  return async (req, res, next) => {
    const cacheKey = `${keyPrefix}:${req.originalUrl}`;
    
    try {
      const cached = await redis.get(cacheKey);
      if (cached) {
        res.setHeader('X-Cache', 'HIT');
        return res.json(JSON.parse(cached));
      }
    } catch (err) {
      console.warn('Redis cache miss:', err.message);
    }
    
    // Override res.json to capture and cache the response
    const originalJson = res.json.bind(res);
    res.json = async (data) => {
      try {
        await redis.setEx(cacheKey, ttlSeconds, JSON.stringify(data));
      } catch (err) {
        console.warn('Failed to cache response:', err.message);
      }
      res.setHeader('X-Cache', 'MISS');
      return originalJson(data);
    };
    
    next();
  };
}

// Use in product routes:
router.get('/', cacheMiddleware('products', 120), productController.getProducts);
```

### 5.3 Image Optimization

```javascript
// Next.js Image component handles optimization automatically
import Image from 'next/image';

export function ProductCard({ product }) {
  return (
    <div className="product-card">
      <Image
        src={product.primary_image}
        alt={product.primary_image_alt || product.name}
        width={400}
        height={400}
        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 25vw"
        loading="lazy"       // lazy load below the fold
        placeholder="blur"   // blur-up placeholder while loading
        blurDataURL={product.blur_data_url}  // tiny base64 preview
      />
    </div>
  );
}
```

**Image optimization checklist:**
- [ ] All images served as WebP (or AVIF for cutting-edge browsers) — 25-35% smaller than JPEG
- [ ] Responsive images with `srcset` and `sizes` attributes
- [ ] Lazy loading for below-the-fold images
- [ ] Product images stored in S3; served via CloudFront CDN
- [ ] Thumbnail generation: create 3-4 size variants per image at upload time
- [ ] No images larger than their display size (no 2000px image displayed at 400px)

---

## 6. Security Hardening Checklist

!!! danger "Security is Not Optional"
    E-commerce systems handle payment data, personal information, and order history. A breach can violate PCI DSS compliance, trigger GDPR/CCPA penalties, destroy customer trust, and result in civil liability. Security hardening is a **mandatory engineering practice**, not an optional enhancement.

### 6.1 Transport Security

```nginx
# Nginx configuration — HTTPS and security headers
server {
    listen 443 ssl http2;
    server_name shop.example.com;
    
    # TLS configuration
    ssl_certificate /etc/ssl/shop.example.com/fullchain.pem;
    ssl_certificate_key /etc/ssl/shop.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
    
    # Redirect HTTP to HTTPS
    error_page 497 https://$host$request_uri;
}

server {
    listen 80;
    server_name shop.example.com;
    return 301 https://$host$request_uri;
}
```

### 6.2 Complete Security Checklist

**Authentication & Authorization**
- [ ] Passwords hashed with bcrypt (cost factor ≥12) or Argon2id — never SHA/MD5
- [ ] JWT access tokens expire in ≤15 minutes
- [ ] Refresh tokens stored as bcrypt hashes; rotated on each use
- [ ] Refresh tokens transmitted via httpOnly, Secure, SameSite=Strict cookies
- [ ] Failed login attempts rate-limited (max 5/IP/15min; max 10/email/hour)
- [ ] Account lockout with exponential backoff after repeated failures
- [ ] Admin routes require separate admin role check on every request
- [ ] Password reset tokens are time-limited (15 min) and single-use

**Input Validation & SQL Injection Prevention**
- [ ] All SQL uses parameterized queries / prepared statements — no string concatenation
- [ ] Request body validation on every endpoint (express-validator or Joi)
- [ ] File upload type validation (MIME type + extension; process server-side, never trust client)
- [ ] URL parameter sanitization (no directory traversal: `../../etc/passwd`)
- [ ] HTML output sanitized for any user-generated content (DOMPurify on frontend)

**Payment Security (PCI DSS relevant)**
- [ ] Card numbers NEVER touch your server — use Stripe Elements or Stripe.js (client-side tokenization)
- [ ] Stripe Radar fraud detection enabled with appropriate rules
- [ ] Stripe webhook signature verified on every webhook
- [ ] No raw payment data logged anywhere in application logs
- [ ] PCI DSS SAQ-A completed (for Stripe-only integrations)

**Infrastructure**
- [ ] TLS 1.2+ only; TLS 1.0/1.1 disabled
- [ ] HSTS header with ≥1 year max-age and preload
- [ ] Content Security Policy header preventing XSS
- [ ] Dependencies audited weekly (`npm audit`); critical vulnerabilities patched within 24h
- [ ] Docker images scanned for vulnerabilities (Trivy, Snyk)
- [ ] Database not publicly accessible; only accessible from application server security group
- [ ] Secrets in environment variables or secrets manager — never in source code or container images
- [ ] Principle of least privilege: database user has only SELECT/INSERT/UPDATE on required tables

---

## 7. SEO Technical Checklist for E-Commerce

```html
<!-- Product Page: Essential SEO meta tags -->
<head>
  <!-- Title: 50-60 characters; include product name and brand -->
  <title>Oslo 3-Seater Sofa | Grey | FurnCo</title>
  
  <!-- Meta description: 120-158 characters; include price/CTA if space allows -->
  <meta name="description" 
        content="The Oslo 3-Seater Sofa in Heather Grey. Premium fabric, solid wood legs. Free shipping on orders over $999. Shop the full Oslo collection.">
  
  <!-- Canonical URL: prevents duplicate content from filters/sorting -->
  <link rel="canonical" href="https://furnco.com/products/oslo-3-seater-sofa-grey">
  
  <!-- Open Graph: controls how page appears when shared on social media -->
  <meta property="og:type" content="product">
  <meta property="og:title" content="Oslo 3-Seater Sofa | Heather Grey | FurnCo">
  <meta property="og:description" content="Premium fabric sofa with solid wood legs. Free shipping over $999.">
  <meta property="og:image" content="https://cdn.furnco.com/products/oslo-sofa-grey-hero.jpg">
  <meta property="og:url" content="https://furnco.com/products/oslo-3-seater-sofa-grey">
  <meta property="product:price:amount" content="1299.00">
  <meta property="product:price:currency" content="USD">
  
  <!-- Structured Data: enables rich snippets in search results -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": "Oslo 3-Seater Sofa",
    "description": "Premium fabric sofa with solid wood legs in Heather Grey",
    "sku": "OSLO-SOFA-3S-GRY",
    "image": ["https://cdn.furnco.com/products/oslo-sofa-grey-hero.jpg"],
    "brand": { "@type": "Brand", "name": "FurnCo" },
    "offers": {
      "@type": "Offer",
      "url": "https://furnco.com/products/oslo-3-seater-sofa-grey",
      "priceCurrency": "USD",
      "price": "1299.00",
      "priceValidUntil": "2025-12-31",
      "availability": "https://schema.org/InStock",
      "seller": { "@type": "Organization", "name": "FurnCo" }
    },
    "aggregateRating": {
      "@type": "AggregateRating",
      "ratingValue": "4.6",
      "reviewCount": "142"
    }
  }
  </script>
</head>
```

**E-Commerce SEO Checklist:**
- [ ] Every product has unique title tag and meta description
- [ ] Product URLs are descriptive slugs, not `/product?id=12345`
- [ ] Canonical tags on faceted navigation pages (color/size filters create duplicate content)
- [ ] Product structured data (Schema.org Product) with price, availability, ratings
- [ ] Breadcrumb structured data for category hierarchy
- [ ] XML sitemap includes all product and category URLs; submitted to Google Search Console
- [ ] Robots.txt blocks `/cart`, `/checkout`, `/admin`, `/api` from crawling
- [ ] Image alt text on all product images (descriptive, includes product name)
- [ ] Core Web Vitals: LCP < 2.5s, CLS < 0.1, FID < 100ms (measure with PageSpeed Insights)
- [ ] Mobile-friendly: verified in Google Search Console

---

## 8. GA4 E-Commerce Analytics Setup

### 8.1 GA4 E-Commerce Events

Google Analytics 4 uses an event-based model with standardized e-commerce events. Implement these on the frontend:

```javascript
// GA4 E-Commerce Event Implementation (Google Tag Manager or gtag.js)

// 1. View Product List (category page)
gtag('event', 'view_item_list', {
  item_list_id: 'category_sofas',
  item_list_name: 'Sofas',
  items: products.map((p, index) => ({
    item_id: p.sku,
    item_name: p.name,
    item_category: p.category_name,
    price: parseFloat(p.price),
    index: index,       // position in list
    quantity: 1
  }))
});

// 2. View Product Detail (product page)
gtag('event', 'view_item', {
  currency: 'USD',
  value: parseFloat(product.price),
  items: [{
    item_id: product.sku,
    item_name: product.name,
    item_category: product.category_name,
    item_brand: product.brand,
    price: parseFloat(product.price),
    quantity: 1
  }]
});

// 3. Add to Cart
gtag('event', 'add_to_cart', {
  currency: 'USD',
  value: parseFloat(product.price) * quantity,
  items: [{
    item_id: product.sku,
    item_name: product.name,
    item_category: product.category_name,
    price: parseFloat(product.price),
    quantity: quantity
  }]
});

// 4. Begin Checkout
gtag('event', 'begin_checkout', {
  currency: 'USD',
  value: cartTotal,
  coupon: appliedCoupon || undefined,
  items: cartItems.map(item => ({
    item_id: item.sku,
    item_name: item.name,
    price: item.unit_price,
    quantity: item.quantity
  }))
});

// 5. Purchase (fire after order confirmation — MOST IMPORTANT)
gtag('event', 'purchase', {
  transaction_id: orderNumber,     // e.g., 'ORD-2024-004215'
  value: orderTotal,               // total including tax and shipping
  tax: taxAmount,
  shipping: shippingAmount,
  currency: 'USD',
  coupon: appliedCoupon || undefined,
  items: orderItems.map(item => ({
    item_id: item.product_sku,
    item_name: item.product_name,
    item_category: item.category_name,
    price: item.unit_price,
    quantity: item.quantity
  }))
});
```

!!! tip "Purchase Event Critical Note"
    Fire the `purchase` event on the **order confirmation page**, not the checkout completion page. Ensure it fires exactly **once per order** — use the order number to deduplicate (check if event already fired for this order ID using sessionStorage before firing).

---

## 9. Final Project Rubric and Grading Criteria

### 9.1 Final Project Overview

The final project for ITEC 442 requires you to design and document (and optionally implement) a complete e-commerce solution for a business scenario of your choosing. Your deliverable is a **comprehensive technical and business document** demonstrating mastery of the course objectives.

**Project deliverable format:** Professional technical report (Word/PDF), 3,000-5,000 words, supplemented by architecture diagrams and, for bonus implementation credit, a working codebase.

### 9.2 Grading Rubric

| Category | Points | Criteria |
|----------|--------|---------|
| **Business Analysis (CO1)** | 15 | Clear business model, target market, revenue model, competitive analysis, value proposition statement |
| **System Architecture (CO9)** | 20 | Complete architecture diagram with all components; justified technology stack selection; data flow documentation |
| **Database Design (CO9)** | 15 | Normalized schema (at minimum 3NF); appropriate indexes; ER diagram; explanation of design decisions |
| **Security Design (CO4)** | 15 | Authentication design, payment security (PCI DSS), input validation, HTTPS/headers, threat model |
| **User Experience (CO2)** | 10 | Mobile-first design documentation; wireframes or mockups; accessibility considerations; checkout flow design |
| **Payment & Checkout (CO3)** | 10 | Payment processor selection and justification; checkout flow design; fraud prevention measures |
| **Analytics & Measurement (CO5)** | 10 | KPI framework; GA4 event plan; conversion funnel definition; A/B testing plan |
| **Writing Quality** | 5 | Professional writing; proper citations; clear structure; appropriate use of technical terminology |
| **BONUS: Working Implementation** | +15 | Deployed or locally runnable code implementing at least 3 core features (product listing, cart, checkout) |

**Total: 100 points base (+ 15 bonus)**

### 9.3 Grading Scale

| Grade | Points | Descriptor |
|-------|--------|-----------|
| **A** | 90–100 | Exceptional work demonstrating mastery; could serve as a real business specification |
| **B** | 80–89 | Solid work with minor gaps; demonstrates strong understanding of course concepts |
| **C** | 70–79 | Adequate work; meets minimum requirements but lacks depth or contains notable omissions |
| **D** | 60–69 | Below expectations; significant gaps in understanding or missing major components |
| **F** | < 60 | Does not meet minimum requirements; incomplete or demonstrates fundamental misunderstandings |

### 9.4 Common Deductions

!!! warning "Avoid These Common Mistakes"
    - **-5 points:** No security section or security section limited to "use HTTPS" without deeper analysis
    - **-5 points:** Architecture diagram missing critical components (payment processor, CDN, email service)
    - **-5 points:** Database schema missing primary keys, foreign keys, or critical indexes
    - **-3 points:** Technology stack selected without justification ("We chose React because it's popular")
    - **-3 points:** No mobile-first design consideration
    - **-5 points:** Plagiarism or AI-generated content submitted without disclosure (see Academic Integrity Policy)
    - **-10 points:** Missing more than 2 major categories from the rubric

### 9.5 Academic Integrity Note

!!! danger "Academic Integrity"
    All submitted work must represent your own analysis and design. You may use AI tools (ChatGPT, Claude, etc.) as research assistants to explain concepts or review your work, but the analysis, design decisions, architecture choices, and written explanations must be your own intellectual work. Submitting AI-generated content as your own analysis is a violation of Frostburg State University's Academic Integrity Policy and will result in a zero for the assignment and potential course failure.

---

## Key Vocabulary

| Term | Definition |
|------|-----------|
| **REST API** | Representational State Transfer — architectural style for HTTP APIs using resources, HTTP verbs, and status codes |
| **JWT (JSON Web Token)** | Compact, self-contained token encoding claims; signed with HMAC or RSA; used for stateless authentication |
| **bcrypt** | Password hashing function designed to be slow; cost factor makes brute-force impractical |
| **Refresh Token Rotation** | Security pattern where using a refresh token immediately invalidates it and issues a new one |
| **Payment Intent (Stripe)** | Stripe object representing the lifecycle of a payment; client_secret returned to frontend for card element |
| **Stripe Webhook** | HTTP POST from Stripe to your server when an event occurs (payment_intent.succeeded, etc.) |
| **PCI DSS** | Payment Card Industry Data Security Standard — compliance requirements for handling cardholder data |
| **Docker Multi-stage Build** | Dockerfile pattern using multiple FROM stages to produce a minimal production image |
| **Idempotency** | Property of an operation that can be safely retried without changing the result beyond the first application |
| **N+1 Query Problem** | Performance anti-pattern where a query is executed once per item in a list (solved with JOIN or eager loading) |
| **Content Security Policy (CSP)** | HTTP header specifying approved content sources, preventing XSS attacks |
| **HSTS** | HTTP Strict Transport Security — header instructing browsers to always use HTTPS for a domain |
| **Core Web Vitals** | Google's user experience metrics: LCP (load), FID/INP (interactivity), CLS (visual stability) |
| **GA4 Purchase Event** | Standardized Google Analytics 4 event recording completed transaction with items, revenue, and metadata |
| **Structured Data** | Schema.org JSON-LD markup enabling rich search results (price, availability, ratings in Google SERP) |

---

## Review Questions

!!! question "Week 15 Review Questions"

    **1.** A startup is building an artisan marketplace platform (Etsy-like model) connecting 500 independent sellers with buyers. They are debating between: (a) Shopify Plus + Shopify's multi-vendor marketplace apps, (b) a fully custom Node.js + MySQL + Stripe build, or (c) a headless approach using Medusa.js (open source) as the commerce backend. Compare these three approaches for this specific use case on cost, time-to-market, flexibility, and scalability.

    **2.** Walk through the complete security vulnerability surface of the `POST /api/orders/create-payment-intent` endpoint in the code examples above. Identify at least five specific security considerations that the implementation addresses, and two additional security enhancements that would make it even more robust for a production environment.

    **3.** The e-commerce database schema uses a "snapshot" pattern for order items — storing `product_name`, `product_sku`, and `unit_price` as columns in `order_items` rather than only a foreign key to the `products` table. Explain why this design decision is correct from both a data integrity and business logic perspective. What would go wrong if you only stored `product_id` in `order_items`?

    **4.** You've just deployed your e-commerce store and Google Search Console shows 847 URLs with "Duplicate content" issues. Investigation reveals the issues come from: (a) `/products?sort=price_asc`, `/products?sort=price_desc`, `/products?sort=name` generating separate indexed pages for the same product listing, and (b) `/products/blue-running-shoes`, `/products/blue-running-shoes?color=blue`, `/products/blue-running-shoes?size=10` each being indexed. Explain the canonical tag strategy and robots.txt configuration you would implement to resolve these issues.

    **5.** You fire the GA4 `purchase` event on your order confirmation page. Three months later, your analytics show a 23% conversion rate (purchases / sessions), which you know is impossibly high (industry average is 2-3%). Diagnose what is likely happening and describe how to fix the measurement issue. What GA4 reports would you use to investigate?

---

## Further Reading

- Fowler, M. (2018). *Patterns of Enterprise Application Architecture.* Addison-Wesley.
- Newman, S. (2021). *Building Microservices* (2nd ed.). O'Reilly Media.
- Stripe Documentation. (2024). *Accept a Payment — Integration Guide.* [https://stripe.com/docs/payments/accept-a-payment](https://stripe.com/docs/payments/accept-a-payment)
- OWASP. (2023). *OWASP Top Ten Web Application Security Risks.* [https://owasp.org/www-project-top-ten/](https://owasp.org/www-project-top-ten/)
- Google. (2024). *Core Web Vitals.* [https://web.dev/vitals/](https://web.dev/vitals/)
- Google. (2024). *GA4 Ecommerce Events Reference.* [https://developers.google.com/analytics/devguides/collection/ga4/ecommerce](https://developers.google.com/analytics/devguides/collection/ga4/ecommerce)
- PCI Security Standards Council. (2022). *PCI DSS v4.0.* [https://www.pcisecuritystandards.org/](https://www.pcisecuritystandards.org/)
- Kleppmann, M. (2017). *Designing Data-Intensive Applications.* O'Reilly Media. *(Chapters 1-3 on data storage)*
- Schema.org. (2024). *Product Structured Data.* [https://schema.org/Product](https://schema.org/Product)
- MySQL. (2024). *MySQL 8.0 Reference Manual: Optimization.* [https://dev.mysql.com/doc/refman/8.0/en/optimization.html](https://dev.mysql.com/doc/refman/8.0/en/optimization.html)

---

## A Final Word to ITEC 442 Students

!!! success "Congratulations — You've Completed ITEC 442 Electronic Commerce"

    You began this course learning the fundamental principles of e-commerce — how digital markets operate, what makes online buyers tick, and why the shift from physical to digital commerce is one of the defining economic transformations of our era.

    Over fifteen weeks, you've traced the arc from basic e-commerce models through mobile-first experiences, government digital services, enterprise knowledge systems, learning technologies, and — in this final week — the full technical architecture of systems that power modern digital commerce.

    **What you now understand that most people don't:**
    
    - Why the "buy" button in a TikTok video represents a decade of infrastructure investment
    - Why e-government transformation is simultaneously obvious and impossibly hard
    - Why knowledge management failure costs organizations billions annually
    - Why headless commerce isn't just a buzzword but a fundamental architectural shift
    - Why a SQL injection vulnerability in a `product_id` parameter can expose every customer's credit card
    
    **Three things that will serve you well:**
    
    1. **Stay curious about the mechanism.** When you use an e-commerce experience, ask: how does this work? What's the database schema behind this recommendation? How is this payment being processed? The habit of looking beneath the surface is what separates engineers from users.
    
    2. **Technology changes; principles don't.** The specific platforms and languages covered in this course will look dated in five years. But user-centered design, security-first thinking, data-driven iteration, and the economics of attention and conversion — these principles will be relevant for your entire career.
    
    3. **Build things.** The review questions, labs, and projects in this course are designed to give you the vocabulary and frameworks to think clearly about e-commerce systems. But there is no substitute for building a real project, hitting real problems, and solving them. Fork the code examples from Week 15. Build something you can show in an interview.

    Good luck with your final projects, your remaining courses, and your careers. Dr. Chen and the ITEC faculty are proud of the work you've done this semester.
    
    *Go build something worth buying.*

---

[← Week 14](week14.md) | [Course Index](index.md)
