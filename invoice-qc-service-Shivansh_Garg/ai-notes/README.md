# AI Usage Documentation

This folder contains documentation of AI tool usage during the development of the Invoice QC Service.

## Files

1. **extraction-patterns.md** - Regex patterns for PDF text extraction
2. **api-design.md** - FastAPI endpoint structure and design decisions
3. **validation-logic.md** - Validation rule engine architecture

## Summary

### Tools Used
- **ChatGPT-4**: Architecture design, regex patterns, initial code structure
- **GitHub Copilot**: Code completion, boilerplate generation

### Overall Approach
1. Used AI for initial scaffolding and suggestions
2. Critically evaluated all AI suggestions
3. Modified/improved based on real-world requirements
4. Documented where AI fell short and why

### Key Insight
AI is excellent for:
- Boilerplate code
- Common patterns
- Initial structure
- Documentation templates

AI needs human oversight for:
- Edge case handling
- Production considerations (security, error handling)
- Performance optimization
- Domain-specific logic
- Real-world data messiness

### Percentage Breakdown
- ~40% AI-generated (initial structure, boilerplate)
- ~60% Human-modified (refinements, edge cases, production readiness)

## Lessons Learned

1. **Always validate AI suggestions** against real requirements
2. **Test with real data** - AI assumes clean inputs
3. **Add error handling** - AI often skips this
4. **Consider performance** - AI may suggest inefficient approaches
5. **Document deviations** - Helps future developers understand decisions
