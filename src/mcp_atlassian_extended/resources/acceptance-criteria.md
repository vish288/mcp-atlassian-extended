# Acceptance Criteria Standards

## Formats

### Given/When/Then (Behavioral)

```
Given the user is on the checkout page with items in the cart,
when they select a province,
then the shipping estimate updates within 500ms without page reload.
```

### Checklist (Rule-Oriented)

```
[ ] Shipping estimate updates on province change
[ ] No full page reload
[ ] Response time under 500ms at p95
[ ] Province selector has aria-label
```

### Hybrid

Combine both when a feature has a primary workflow plus independent requirements.

## Writing Rules

### Must Be Testable

Every criterion maps to a verifiable condition.

Good: "Response time under 500ms at p95 under 100 concurrent users"
Bad: "The page should be fast"

### Must Be Specific

Include numbers, thresholds, exact behaviors.

Good: "File upload accepts PNG, JPG, GIF up to 10MB"
Bad: "File upload should work for common formats"

### Must Be Independent

Each criterion verifiable on its own.

### Must Reflect User Value

Describe outcomes, not implementation.

Good: "User sees order history sorted by date, newest first"
Bad: "Query uses ORDER BY created_at DESC"

## Anti-Patterns

- **Vague**: "Should work properly" -- define what "properly" means
- **Implementation-prescriptive**: "Use Redis with 5-min TTL" -- describe behavior instead
- **Untestable**: "UI should be intuitive" -- add measurable threshold
- **Too many**: 25 criteria on one Story -- split the Story

## Performance Criteria Quantification

Vague performance criteria ("should be fast") are untestable. Specify:

1. **Percentile**: which latency percentile matters (p50, p95, p99)
2. **Load conditions**: concurrent users, request rate, data volume
3. **Measurement method**: where and how the metric is captured
4. **Baseline**: current value if this is an improvement target

| Bad | Good |
|-----|------|
| "Page should load fast" | "LCP under 2.5s at p95 on 4G throttled Chrome, measured by Lighthouse CI" |
| "API should handle load" | "POST /orders returns 200 within 300ms at p99 under 500 req/s, measured at the load balancer" |
| "Search should be responsive" | "Search results render within 400ms at p95 for queries up to 100 chars with 1M indexed documents" |

**Template:**

```
Given [load condition],
when [user action or API call],
then [metric] is under [threshold] at [percentile],
measured by [tool/method].
```

## Dependent Criteria Handling

When criterion A cannot be verified until criterion B is complete:

**Option 1: Chain with Given/When/Then**

```
Given the user has verified their email (criterion B outcome),
when they navigate to account settings,
then they see the "Change password" option enabled.
```

**Option 2: Split into separate Stories**

Split when:
- Criterion B is a different user workflow than criterion A
- Different developers will implement A and B
- B could ship independently and still deliver value

After splitting, link Stories with `blocks` / `is blocked by` and schedule the blocking Story in the same or earlier sprint.

**Anti-pattern:** Circular criterion dependencies (A needs B, B needs A). This signals a single atomic behavior -- merge into one criterion.
