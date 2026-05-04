---
description: End-to-end pipeline — find profitable niche → generate product idea → size market → produce launch plan
argument-hint: "[broad domain or 'auto' for fully open discovery]"
---

# /find-and-plan — Niche → Idea → Money → Launch Plan

Run a sequential pipeline that takes a broad domain (or nothing) and returns a concrete product concept, a defensible market size, and a launch plan.

**Input:** `$ARGUMENTS` — broad domain hint (e.g. `productivity for SMB`, `b2c mental health`, `dev tools`). If empty or `auto`, the pipeline runs domain-agnostic discovery.

---

## Pipeline (strict order — each step's output is the next step's input)

### Phase 1 — Discovery (find the niche)

1. **Invoke subagent `trend-analyst`** with this brief:
   > Identify 8–12 emerging niches inside the domain `$ARGUMENTS` (or domain-agnostic if empty). For each: weak signal sources (search trends, patents, academic, social), trajectory (12–24 months), addressable audience hypothesis, and a 1–10 opportunity score. Return a ranked table.

2. **Invoke skill `content-trend-researcher`** on the top 5 niches from step 1:
   > For each niche, classify intent (informational/commercial/transactional/navigational/problem-solving), surface content gaps with difficulty rating, and platform-specific demand signals (Google Trends, Reddit, X, YouTube, Substack). Output an `opportunity_score` per niche.

3. **Cross-rank** results from steps 1 and 2. Pick **top 3 niches** by combined score. Print the shortlist with rationale.

### Phase 2 — Idea formulation

4. **For each of the top 3 niches**, draft 2 candidate product concepts (one SaaS / web-app, one Chrome-extension or thin wrapper). Each concept = `{name, one-liner, target persona, primary job-to-be-done, monetization hypothesis}`.

5. **Invoke subagent `competitive-analyst`** on each candidate:
   > Map direct + indirect competitors, substitutes, adjacent markets. Apply Porter's 5 forces. Identify 2–3 concrete differentiation angles.

6. **Invoke subagent `project-idea-validator`** on each candidate:
   > Run the 8-dimension scorecard (demand, competition, uniqueness, difficulty, audience, weaknesses, strengths, viability). Return `GO`, `PIVOT (with specific suggestion)`, or `KILL`.

7. **Pick the single winning concept** with the highest validator score. Print the concept brief and the rejection reasons for the rest.

### Phase 3 — Money in the niche

8. **Invoke skill `validating-ideas`** on the winning concept:
   > Build Lean Canvas, Riskiest Assumption Test list, Mom Test interview script, Pretotype design. Output GO/PIVOT/KILL scorecard with evidence requirements.

9. **Invoke subagent `market-researcher`** (rohitg00 variant — statistically disciplined):
   > Compute TAM/SAM/SOM using both top-down and bottom-up methods. Require convergence ≤30%. Provide cons/base/opt ranges. SOM year-1 capped at 1–2% SAM. Source every number with a date.

10. **Invoke skill `modeling-finances`**:
    > Build revenue model, 13-week cash flow, burn rate calculator, scenario planning. Pull market size from step 9.

### Phase 4 — Launch plan

11. **Invoke skill `planning-market-entry`**:
    > Produce a beachhead segment recommendation and market attractiveness scorecard for entry sequence.

12. **Invoke skill `launching-go-to-market`**:
    > Produce: Beachhead analysis, Racecar growth map, channel scorecards, PLG readiness assessment, 90-day launch milestones with budget.

13. **Invoke skill `gathering-competitive-intelligence`** in parallel with step 12:
    > Battle cards for top 3 competitors against the winning concept.

### Phase 5 — Final deliverable

14. **Compile a single markdown report** in the working directory: `output/launch-plan-<date>.md`. Sections:
    - Executive summary (one paragraph)
    - The niche and why it wins
    - The product concept brief
    - Competitive landscape and differentiation
    - Validation scorecard (GO/PIVOT/KILL with reasoning)
    - Market size (TAM/SAM/SOM with sources)
    - Financial model (revenue + cash flow + scenarios)
    - Launch plan (beachhead, channels, 90-day milestones, budget)
    - Battle cards
    - Open risks and the next 5 actions

---

## Rules

- Run phases in order. Do not parallelize across phases.
- Inside a phase, parallel sub-tasks are encouraged when independent (steps 12 and 13).
- Every quantitative claim cites a source with date.
- If the validator returns `KILL` on all 6 candidates in step 6, restart Phase 2 with 6 new candidates from the same shortlist before returning failure.
- If the financial model in step 10 shows SOM year-1 revenue under $100k base case, flag it and recommend a pivot to a richer adjacent niche.
