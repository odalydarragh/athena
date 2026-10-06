# Data Protection Impact Assessment note — DocuMDR (pre-incorporation)

**Date:** 6 October 2026  
**Status:** Screening / lightweight DPIA. Not a full Art. 35 DPIA because residual risk is assessed as not high **if** the product rules below remain in force.

## Processing

Compile SaMD technical-file drafts from git metadata for professional B2B users.

## Screening (DPC DPIA guidance)

| Criterion | Applies? | Mitigation |
|-----------|----------|------------|
| Systematic evaluation / scoring of people | No | We score software items, not individuals |
| Automated decision with legal effect | No | HITL required; humans sign |
| Systematic monitoring | No | |
| Special-category / health data | **Forbidden** | Redaction + reject `PATIENT` / `MRN:` / `DOB:` |
| Large-scale processing of vulnerable people | No | B2B, 18+ |
| New technology used in a novel way on people | Limited | Git metadata only |
| Prevents exercising a right | No | DSAR/erase in-product |

## Residual risks

- Accidental ingest of personal data in commit messages → redaction + reject.
- Customer uploads source or patient data despite contract → product refuses file bodies; CLI is local.
- Signature records contain names → minimise on erasure; 10-year retention for accountability.

## Conclusion

If DocuMDR later stores source code, model training sets, or any patient/clinical data, stop and complete a full DPIA and consult the Data Protection Commission **before** that processing starts.
