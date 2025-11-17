# Bugs Found During Testing

## Bug #1: Abstention Threshold Too Permissive

**Date**: November 17, 2025  
**Severity**: High  
**Status**: Identified

### Problem

The system is answering questions it should abstain from:
- Q9: "Which specific hybrid corn cultivar had the top yield in the 2023 Doktar internal field trials?" 
  - Answer: Gibberish about corn hybrids (not the specific 2023 Doktar trial)
  - Score: 0.780
  - **Should abstain**: This is Doktar-internal data not in public corpus

- Q15: "What was the precise volume of registered neonicotinoid seed treatment used on canola in Türkiye in Q2 2021?"
  - Answer: Generic canola sentences (not specific to Turkey Q2 2021)
  - Score: 0.680
  - **Should abstain**: Very specific regional/temporal data not in corpus

- Q19: "What was the average farm-gate price for fresh tomatoes in Eskisehir on 15 July 2024?"
  - Answer: Random tomato sentences (not price data)
  - Score: 0.680
  - **Should abstain**: Specific price data for 2024 not in corpus

- Q20-22: Judgment/advice questions
  - These require agronomic judgment, not factual retrieval
  - **Should abstain**: System should not give management advice

### Root Cause

Current abstention threshold is `0.35` which is too low. Questions with scores of `0.68-0.78` are being answered even though:
1. Retrieved sentences don't actually answer the specific question
2. The system is just finding topically related text
3. No evidence exists in the corpus for these specific queries

### Proposed Solution

**Option 1**: Increase abstention threshold
```yaml
# config.yaml
selection:
  abstain_score_thresh: 0.65  # Increase from 0.35
```

**Option 2**: Add answer quality check
- Check if retrieved sentences actually contain key entities from question
- For questions with numbers/dates/names: verify those appear in retrieved text

**Option 3**: Combine both
- Higher base threshold (0.50)
- Additional quality checks for specific question types

### Testing Plan

1. Adjust threshold to 0.65
2. Re-run batch processing
3. Verify Q9, Q15, Q19-22 now abstain
4. Check that answerable questions (Q1-8, Q10-14, Q16-18) still get answered

---

## Summary

- **Total bugs found**: 1
- **Critical**: 0
- **High**: 1  
- **Medium**: 0
- **Low**: 0

