# Data Processing Agreement (template) — DocuMDR

This template is intended to satisfy GDPR Article 28 and the Irish Data Protection Act 2018, section 80. It is **not** legal advice. Execute a reviewed version before processing real customer data.

**Processor:** DocuMDR (Galway, Ireland)  
**Controller:** the customer organisation using the service  
**Subject matter:** processing of software-development metadata to compile draft regulatory documentation  
**Duration:** for the term of the service plus the retention periods in the Privacy Policy  
**Nature:** collection, storage, organisation, redaction, compilation, export, erasure  
**Purpose:** providing the DocuMDR service  
**Types of personal data:** account emails; git author handles; redacted commit/PR text; IP addresses in security logs; electronic signature metadata  
**Categories of data subjects:** the controller’s employees and contractors (software engineers, quality managers). **Not** patients.

## Processor obligations

1. Process personal data only on documented instructions from the controller, including with regard to transfers, unless required by EU or Irish law.
2. Ensure persons authorised to process the data are bound by confidentiality.
3. Implement appropriate technical and organisational measures (Art. 32): encryption in transit; file-mode restrictions on local stores; redaction before persist; forbidden-content rejection; no source-code ingest; secrets excluded from git.
4. Not engage a sub-processor without prior written authorisation. This version uses **no** sub-processors.
5. Assist the controller with data-subject rights, DPIAs, and breach notification (without undue delay, and in any event in time for the controller to meet the 72-hour Art. 33 clock).
6. Delete or return personal data at the end of services, except minimised signature records retained where EU or Irish law requires.
7. Make available all information necessary to demonstrate compliance and allow audits on reasonable notice.

## Controller obligations

1. Do not instruct the processor to ingest special-category or patient data.
2. Ensure a lawful basis for any personal data in git metadata.
3. Configure quality-role access for HITL signatures.

## International transfers

Default storage and processing: EU/EEA (Ireland). No third-country transfers in this version.

## Governing law

Ireland.
