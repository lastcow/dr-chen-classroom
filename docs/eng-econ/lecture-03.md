---
title: "Lecture 3 — Time Value of Money"
lecture: 3
date: 2026-06-05
room: SY109
length_min: 110
course: Engineering Economics
tags: [lecture, tvm, present-value, future-value, ear, compounding]
---

# Lecture 3 — Time Value of Money

> **Fri 2026-06-05 · SY109 · 110 min · Engineering Economics, Spring 2026**

<a class="md-button md-button--primary" href="decks/lecture-03/index.html" target="_blank">Launch deck (new tab)</a>
<a class="md-button" href="decks/lecture-03/index.html?print-pdf" target="_blank">Print-PDF view</a>

<iframe
  src="decks/lecture-03/index.html"
  style="width:100%; height:680px; border:1px solid #c9b994; border-radius:14px; background:#faf6ef; margin-top:1rem;"
  title="Lecture 3 — Time Value of Money (Reveal.js deck)"
  loading="lazy">
</iframe>

!!! tip "How to drive the embedded deck"
    Click into the iframe, then press **F** for full-screen, **S** for speaker view, **Esc** for the slide grid. Math is rendered with MathJax, so the formulas re-typeset when you change zoom.

---

## At a glance

| | |
|---|---|
| **Slides** | 29 (cover + 27 content + references) |
| **Discussion segment** | Slide 25 — *Credit-card APR vs. EAR*, 15 min, solo → pair → plenary |
| **Worked examples** | 7 (simple, compound, F/P, P/F, sinking-fund, EAR derivation, three-bank mortgage) |
| **Self-check problems in deck** | Slide 24 ("Five common pitfalls") |
| **Problem set** | Problem Set 3 — due **Wed 2026-06-10 23:59** on Canvas |
| **Prerequisite reading** | Park §2.1–2.4 (or equivalent), Lecture 2 slides 12–18 |
| **Calculator** | Any scientific calculator. TI-30 / Casio FX-991 strongly recommended; Excel `FV`, `PV`, `NOMINAL`, `EFFECT`, `RATE` will be used in the optional Excel addendum. |

---

## Learning objectives

By the end of this 110-minute session, students will be able to:

1. **Explain** in plain language why a rational engineer prefers $1,000 today to $1,000 in twelve months, and decompose the required premium into its three economic components.
2. **Read and draw** a cash-flow diagram using the standard *P, F, A, i, n* notation, including correct sign convention for inflows and outflows.
3. **Compute** future and present values of a single cash flow under both simple and compound interest, by hand and with a calculator, and explain when each model applies.
4. **Convert** between nominal (APR), periodic, and effective annual rates (EAR) for any compounding frequency *m*, and recognise when each rate is the one a contract actually charges.
5. **Derive** the continuous-compounding limit $F = Pe^{rn}$ from the discrete compound formula by taking $m \to \infty$, and quantify how much extra return continuous compounding actually delivers over annual compounding.
6. **Diagnose** the five most common student errors on TVM problems (mismatched units, wrong rate, sign-flip, off-by-one period, treating APR as EAR) and apply a four-step sanity check to avoid them.

These outcomes correspond to deck slide 2 and map directly onto Park §2.1–2.4. Items 4 and 5 are the ones most likely to appear on the midterm.

---

## Pre-class checklist

Before walking into SY109 at 15:40, please:

- [ ] Read Park §2.1–2.4 (or the equivalent chapter in your reference text). 25–35 minutes.
- [ ] Watch the 4-minute "Rule of 72" video on Canvas.
- [ ] Bring a scientific calculator. Phones are fine for the discussion segment but not for the in-class problems.
- [ ] Be ready to answer the opening poll: *"You're offered $1,000 today or $1,100 in twelve months. Which do you take, and why?"*

---

## Detailed lecture notes

The notes below mirror the structure of the deck (Parts I–VI, slides 4–24) and are intended as your study companion: more verbose than the slides, with the worked examples spelled out and with extra commentary on the *why* behind each formula. If your goal is exam preparation, read this page once after class, then attempt Problem Set 3 without referring back.

### Part I — Why a dollar moves through time (slides 4–6)

Why is a dollar today not the same as a dollar a year from now? Three independent forces drive the premium an engineer demands for postponing consumption:

1. **Opportunity cost — the *risk-free* component.** Money received today can be deposited in an essentially risk-free instrument (a 1-year Treasury bill, an FDIC-insured savings account) and earn the prevailing risk-free rate. Postponing receipt forfeits that yield. As of early 2026 in the US, that rate sits around 4.0–4.5 %.
2. **Expected inflation.** Even if no return were available, a future dollar buys less. The Bureau of Labor Statistics CPI projection for 2026 hovers near 2.4 %. A risk-free *real* return must therefore be padded by expected inflation to keep purchasing power flat.
3. **Risk premium.** If the future payment is not guaranteed — your friend may forget, the start-up may fold, the customer may default — a rational lender requires extra compensation for bearing that uncertainty. The premium scales with the perceived probability and severity of non-payment.

Adding the three components yields the **required interest rate** *i* that an engineer should attach to a delayed cash flow. The decomposition is the conceptual foundation of the entire course: every discount rate you choose in NPV (Lecture 5), every MARR you compare against, and every cost-of-capital number on a corporate balance sheet is a sum of these three things.

The *opening question* slide is intentionally framed without numbers: $1,000 today vs. $1,100 next year. Students are asked to **reveal their reasoning before computing**, because the qualitative explanation — "I want to be paid for waiting, for losing purchasing power, and for the chance you won't pay me" — is precisely the three-part decomposition above. Quantitative agreement comes next: at i = 4 % risk-free + 2.5 % inflation + 3 % risk premium ≈ 9.5 %, the breakeven future payment is $1,095, which the $1,100 offer slightly clears. Most students will pick "today" anyway, which becomes the lecture's running motif: *intuition leans heavily toward the present; engineering economics quantifies how much it should.*

### Part II — Notation engineers can compute with (slides 7–8)

The whole course relies on six symbols:

| Symbol | Meaning | Sign convention |
|--------|---------|-----------------|
| **P** | Present value (cash flow at *t = 0*) | + if inflow, − if outflow |
| **F** | Future value (cash flow at *t = n*) | + if inflow, − if outflow |
| **A** | Uniform annuity (equal cash flows each period) | + if inflow, − if outflow |
| **G** | Arithmetic gradient (linear period-over-period change) | — |
| **i** | Interest rate **per period** | always positive |
| **n** | Number of **periods** (not necessarily years) | always positive |

The **cash-flow diagram** is the language we use to communicate problems unambiguously. The horizontal axis is the time line, marked off in equal periods. Upward arrows are inflows (money coming *to* you), downward arrows are outflows (money going *from* you). Always draw the diagram **from one party's perspective** — the borrower or the lender, never both — and keep that perspective for the whole problem. The single most common source of sign errors is silently flipping perspective halfway through.

A subtle point that catches students every term: **"i per period" and "n in periods"** must always be unit-consistent. If interest compounds monthly and the loan runs 30 years, then *i* is the monthly rate and *n = 360*. Mixing an annual *i* with monthly *n* (or vice versa) is the source of nearly half of all problem-set errors. We will repeat this rule until it is irritating.

### Part III — Simple vs. compound interest (slides 9–12)

Two competing rules govern how interest accumulates.

**Simple interest** treats interest as a flat fee on the original principal — no interest on the interest. The future-value formula is

$$F = P(1 + in)$$

This is the model used for short-term commercial paper, Treasury bills with maturities under a year, and many automobile-loan computations in the US. It is **linear** in *n*: doubling the loan term exactly doubles the interest charge.

*Example (deck slide 10).* You lend a contractor $10,000 at 8 % simple interest for 3 years. Total interest accrued is *Pin* = $10,000 × 0.08 × 3 = $2,400. Total repayment is $12,400. Notice: it does not matter whether the contractor pays interest annually, quarterly, or all at the end — simple interest is computed on the original principal regardless.

**Compound interest** treats accrued interest as itself earning interest in subsequent periods. The future-value formula is

$$F = P(1 + i)^n$$

This is the model that governs essentially every financial product you will encounter outside the short-end of the bond market: mortgages, savings accounts, credit cards, retirement accounts, corporate bonds, and discounted cash-flow analysis. It is **exponential** in *n*: doubling the term *more* than doubles the interest charge.

*Example (deck slide 11).* Same loan — $10,000 at 8 %, 3 years, but now compounded annually. The amortisation table is:

| Year start | Principal | Interest @ 8 % | Year end |
|---|---|---|---|
| 1 | 10,000.00 | 800.00 | 10,800.00 |
| 2 | 10,800.00 | 864.00 | 11,664.00 |
| 3 | 11,664.00 | 933.12 | 12,597.12 |

Total repayment $12,597.12 — $197.12 more than simple interest. The gap is the "interest on the interest." Compute directly: $F = 10{,}000 \times 1.08^3 = 12{,}597.12$. ✓

**The growth divergence (slide 12).** Over 50 years at 8 %, simple interest turns $10,000 into $50,000 (a 5× return). Compound interest turns it into $469,016 (a 47× return). The deck shows both growth curves as inline SVG; the visual is the lecture's single most important takeaway — **compounding is exponential, intuition is linear, and reality is not kind to the difference**. Quoting Einstein (apocryphally but irresistibly): "Compound interest is the eighth wonder of the world. He who understands it, earns it; he who doesn't, pays it."

The **Rule of 72** is the back-of-envelope companion: at interest rate *i* %, money roughly doubles every *72/i* years. At 8 %, doubling time is 9 years; at 6 %, 12 years; at 4 %, 18 years. Use this on any TVM problem to sanity-check your answer in five seconds.

### Part IV — Moving one dollar through time (slides 13–16)

Compound interest gives us two complementary operations:

**Future Value of a single present sum: the F/P factor.**

$$F = P(F/P, i, n) = P(1+i)^n$$

This *moves money forward*: it answers "if I have *P* today and earn *i* per period for *n* periods, how much will I have at the end?" The factor *(F/P, i, n) = (1 + i)^n* is tabulated in the back of every engineering-economics textbook for common combinations of *i* and *n* — useful when calculators are not allowed but irrelevant in 2026 practice.

*Sinking-fund example (slide 14).* An engineer deposits $5,000 today into a retirement account that earns 6 % compounded annually. How much will it grow to in 40 years? $F = 5{,}000 \times (1.06)^{40} = 5{,}000 \times 10.286 = 51{,}429.41$. The deposit grows more than tenfold without a single additional contribution — the deck's lead-in to the *power of starting early*, a topic we return to in Lecture 5.

**Present Value of a single future sum: the P/F factor.**

$$P = F(P/F, i, n) = \frac{F}{(1+i)^n}$$

This *moves money backward* — known as **discounting** — and answers the question that drives virtually all of corporate finance: "what is a future payment worth to me today, given my required rate of return?" The factor *(P/F, i, n) = 1 / (1+i)^n* is always less than 1 for positive *i* and *n*, reflecting the fact that future money is worth less than present money.

*Settlement example (slide 15).* A lawsuit will be settled in 5 years for $80,000. The plaintiff is offered $55,000 cash today to walk away. If the plaintiff's MARR (minimum acceptable rate of return) is 7 %, should they take the offer? Compute the present value of the future settlement: $P = 80{,}000 / 1.07^5 = 80{,}000 / 1.4026 = 57{,}033$. Because the present value of waiting ($57,033) exceeds the cash offer ($55,000), the plaintiff should **reject** the offer. The lecture emphasises that the answer depends critically on the MARR — at a 9 % MARR, present value falls to $51,989 and the cash offer becomes attractive. Discount rate is destiny.

### Part V — Nominal vs. periodic vs. effective annual rate (slides 17–20)

This is the part of the lecture students most often get wrong on the midterm. A single loan can have three different "interest rates" associated with it, and they are *not* interchangeable.

- **Nominal annual rate (APR, *r*).** The headline rate quoted by the bank and printed on your credit-card statement. By law (Truth in Lending Act, 1968), this is the rate × number of periods per year — it ignores compounding within the year. It is a *quotation convention*, not a true return.
- **Periodic rate (*r/m*).** The rate actually applied each compounding period. For an 18 % APR credit card compounded monthly, the periodic rate is 18 % / 12 = 1.5 % per month.
- **Effective annual rate (EAR, *i*).** The single annual rate that would produce the same end-of-year balance as the periodic compounding. This is the *real* economic rate of the loan or investment.

The conversion is:

$$\text{EAR} = \left(1 + \frac{r}{m}\right)^m - 1$$

*Derivation (slide 19).* Start a $1 deposit at nominal rate *r* compounded *m* times per year. After one period the balance is $1(1 + r/m)$. After *m* periods (one full year) the balance is $1(1 + r/m)^m$. The growth over the year is therefore $(1 + r/m)^m - 1$, which by definition is the effective annual rate. Subtract 1 because the EAR is a *rate*, not a growth factor.

*Three-mortgage example (slide 20).* Three banks all quote 6.00 % APR on a 30-year mortgage but with different compounding conventions:

| Bank | APR | Compounding (m) | Periodic | EAR | Monthly payment on $300k |
|------|-----|-----------------|----------|-----|--------------------------|
| First Federal | 6.00 % | Annual (m=1) | 6.000 % | **6.000 %** | $1,762.41 |
| Bank of the Allegheny | 6.00 % | Monthly (m=12) | 0.500 % | **6.168 %** | $1,798.65 |
| Continental Direct | 6.00 % | Daily (m=365) | 0.01644 % | **6.183 %** | $1,801.97 |

Bank of the Allegheny does **not** charge "6 %"; it charges 6.168 %. Continental Direct charges 6.183 %. Over a 30-year amortisation, the difference between the cheapest and most expensive lender — all "6 % APR" — is more than $14,000 in total interest. The slide closes with the lecture's bumper-sticker rule: **always compare EARs, never APRs.**

### Part VI — The continuous-compounding limit (slides 21–23)

What happens as compounding frequency goes to infinity?

$$F = P \lim_{m \to \infty} \left(1 + \frac{r}{m}\right)^{mn} = P \cdot e^{rn}$$

The limit is reached using the classical definition of *e*: $\lim_{m \to \infty} (1 + r/m)^{m} = e^{r}$. Continuous compounding corresponds to interest being credited *every instant*, which is mathematically clean and computationally trivial: just raise *e* to the *rn* power.

The corresponding EAR is $e^{r} - 1$. At *r* = 6 %, this is 6.184 % — only a tiny step beyond daily compounding's 6.183 %. The lesson, captured by the compounding-frequency table on slide 23:

| Compounding | m | EAR (r = 6 %) |
|-------------|---|---------------|
| Annual | 1 | 6.000 % |
| Semi-annual | 2 | 6.090 % |
| Quarterly | 4 | 6.136 % |
| Monthly | 12 | 6.168 % |
| Daily | 365 | 6.183 % |
| **Continuous** | **∞** | **6.184 %** |

**Almost all of the gain from increasing compounding frequency comes between annual and monthly.** Going from monthly to continuous gains only 16 basis points. This is why retail banking standardised on monthly compounding decades ago — past that point, the operational complexity is not worth the customer-perceived gain. Continuous compounding lives on in two places that matter for engineers: (a) options pricing (Black–Scholes, Lecture 7 cameo) and (b) academic discounting where the smoothness of $e^{rn}$ makes calculus tractable.

### Five mistakes that account for most lost points (slide 24)

1. **Period/rate mismatch.** Using an annual rate with a number of months, or a monthly rate with a number of years. Solution: pick a unit (months, quarters, years) on the cash-flow diagram and stay there for the entire problem.
2. **APR ≠ EAR.** Treating the quoted nominal rate as if it were the true annual return. Always convert before comparing loans or investments.
3. **Sign-flip mid-problem.** Halfway through a multi-step computation, accidentally treating an outflow as an inflow. Solution: choose a perspective (yours, the bank's) at the start and never switch.
4. **Off-by-one period.** Confusing "end of year 3" with "beginning of year 4", or with "after 3 years from now". The cash-flow diagram is the cure: every cash flow has a *position* on the timeline, and you can point to it.
5. **Simple where compound is needed (or vice versa).** Default to compound interest unless the problem explicitly says *simple* — virtually every modern financial product compounds.

The deck closes with a recommended **four-step sanity check** for every TVM problem: (i) draw the diagram, (ii) confirm rate and period units match, (iii) compute the answer, (iv) apply the Rule of 72 to verify the order of magnitude. If steps (iii) and (iv) disagree by more than a factor of 2, you have made an error.

---

## In-class discussion segment (slide 25, ~15 min)

**Prompt.** *"Your credit-card statement says 19.99 % APR. The fine print says 'compounded daily'. Your friend, who has not taken this course, says 'so I pay 19.99 % per year on whatever I owe'. Are they right? If not, what do they actually pay, and by how much are they off?"*

**Protocol.**

- **Solo (3 min).** Each student computes the EAR on a piece of paper and writes their answer.
- **Pair (5 min).** Pairs compare numbers, debug discrepancies, and produce a single agreed-upon answer.
- **Plenary (7 min).** Two pairs present at the board; instructor reconciles, then introduces the deeper question — *why does the law allow banks to quote APR instead of EAR, given that EAR is the true rate?*

**Expected answer.**

$\text{EAR} = (1 + 0.1999/365)^{365} - 1 = 22.13 \%$

The friend is **off by 214 basis points** — i.e. on a $5,000 balance carried for a year, they will pay $1,107, not the $1,000 they expected. The plenary discussion typically turns toward consumer-protection policy: APR is quoted because it is comparable across products of *different* compounding conventions (with care), but it understates the rate consumers actually pay, and the EAR/APR gap widens with compounding frequency. The CARD Act of 2009 partially addressed this by mandating clearer disclosure but did not force EAR onto the front of statements.

**Hard-stop reminder.** If the plenary runs long, cut it at 7 min and move on — the synthesis slide (26) is what students will write down in their notes, not the discussion. We can extend the discussion in office hours.

---

## Synthesis — the one habit (slide 26)

Every TVM problem reduces to **moving one cash flow through time using the appropriate factor**, with the right rate and period units. The four-formula matrix is:

| Direction | Single cash flow | Uniform series |
|-----------|------------------|----------------|
| Forward (find F) | $F = P(1+i)^n$ | $F = A \dfrac{(1+i)^n - 1}{i}$ *(Lecture 4)* |
| Backward (find P) | $P = F / (1+i)^n$ | $P = A \dfrac{(1+i)^n - 1}{i(1+i)^n}$ *(Lecture 4)* |

This week we own the first column. Next week (Lecture 4) we will earn the second column. The **habit** to develop now, and to keep for the rest of the course: every time you see a money decision, your first move is to *draw the cash-flow diagram*. Every other step becomes mechanical once the diagram is on paper.

---

## Problem Set 3 — assigned in class, due Wed 2026-06-10

Six problems, point values in brackets. Submit hand-written PDF or LaTeX to Canvas. Show all work; an unjustified numerical answer earns half credit at most.

1. **[10]** Decompose a 9.5 % required interest rate into the three economic components, given current US risk-free rate (4.25 %) and inflation forecast (2.4 %). Comment on whether the residual is a reasonable risk premium for a small-business loan.
2. **[15]** Draw the cash-flow diagram for a $40,000 car loan at 5.99 % APR, compounded monthly, 60-month term, with $5,000 down and a $500 dealer fee paid at closing. Label every cash flow with its sign and timing from the *borrower's* perspective.
3. **[15]** A friend asks you whether to take $7,000 today or $9,500 in three years. Their MARR is 8 %. Show your work both ways: (a) move $7,000 forward to year 3, (b) move $9,500 backward to year 0. Confirm the two methods produce the same recommendation.
4. **[20]** Three credit cards offer "20 % APR". Card A compounds annually, Card B monthly, Card C daily. Compute the EAR of each, the actual interest paid on a $6,000 balance held for one year, and rank them. Identify which card the Truth in Lending Act considers to have the lowest APR (trick question — discuss).
5. **[20]** Derive the continuous-compounding formula $F = Pe^{rn}$ starting from the discrete formula $F = P(1 + r/m)^{mn}$. Show every step. Then compute: on a $250,000 investment at 5 %, what is the difference in 25-year future value between annual, monthly, daily, and continuous compounding?
6. **[20]** *Capstone — 2026 student-loan scenario.* You graduate in May 2027 with $58,000 in federal Stafford loans at 6.53 % APR compounded monthly. The 10-year standard repayment plan begins November 2027. Compute (a) the EAR, (b) the monthly payment using the formula in the deck appendix, (c) total interest paid over the 10 years, (d) total interest paid if you instead choose a 20-year extended plan at the same APR. Recommend a plan and justify in two paragraphs.

---

## Going further — optional readings

- **Park, C.S.** *Contemporary Engineering Economics* (6e). Ch. 2, "Time Value of Money". The canonical undergraduate treatment.
- **Brealey, Myers & Allen.** *Principles of Corporate Finance* (13e). Ch. 2, "How to Calculate Present Values". A finance perspective with worked examples from corporate practice.
- **Federal Reserve Board.** *Regulation Z — Truth in Lending Act* §1026.14. The legal definition of APR and how it differs from EAR in US consumer disclosures.
- **Consumer Financial Protection Bureau (2024).** *APR vs APY: What's the difference?* A two-page consumer-facing explainer that mirrors slide 18 in plain English.
- **Hull, J.** *Options, Futures, and Other Derivatives* (11e). §4.4 explains continuous compounding from a derivatives-pricing standpoint — relevant if you continue to Lecture 7.

---

## Speaker notes & pacing (instructor only)

The deck embeds `aside.notes` on every slide; press **S** while the deck is open to see them. Headline pacing:

| Block | Slides | Wall-clock target |
|-------|--------|-------------------|
| Cover + objectives + agenda | 1–3 | 4 min |
| Part I — Motivation | 4–6 | 12 min |
| Part II — Notation | 7–8 | 8 min |
| Part III — Simple vs compound | 9–12 | 18 min |
| Part IV — F/P and P/F | 13–15 | 14 min |
| **Stretch break** | 16 | **5 min** |
| Part V — Nominal vs EAR | 17–20 | 18 min |
| Part VI — Continuous | 21–23 | 10 min |
| Five pitfalls | 24 | 5 min |
| **Discussion** | 25 | **15 min — hard stop** |
| Synthesis + PS3 + Lec 4 preview + refs | 26–29 | 6 min |
| **Total** | 29 slides | **110 min** |

If you fall behind, the place to cut is Part VI — the continuous-compounding limit can be reduced to "here's the formula, here's the table, see slide 23" without losing assessment alignment. Do not cut the discussion; it is the only segment that produces a *durable* memory of the APR/EAR distinction.

---

## Changelog

- **2026-05-17** — First publish (deck v1, lecture page v1).
