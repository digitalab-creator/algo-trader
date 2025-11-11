# Step 04 – Recommendation APIs

## Goals
- Deliver actionable suggestions (strategy + params + symbols) before trading sessions.
- Allow scenario analysis for different risk profiles.

## Tasks
- ☐ Build `/recommendations` endpoint selecting top combos via model output/grid results.
- ☐ Implement scenario analysis API (expected ROI/drawdown for user-defined blends).
- ☐ Cache results for quick retrieval; invalidate on new grid runs.

## Deliverables
- REST endpoints providing ranked strategy recommendations tailored to risk levels.
- Documentation/tutorial on consuming the API for portfolio planning.
