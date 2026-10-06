---
name: data-integrity-verification
description: Use when processing data files to ensure accuracy and compliance with output requirements.
---
<body>
1. Before processing, inspect the input data (e.g., row counts, column headers, sample values) to identify duplicates or missing values.
2. If the task requires a specific output format (e.g., `clean.csv`), write a script to validate the output against the requirements before finalizing.
3. Ensure all monetary values are converted to the required unit (e.g., integer cents) as specified by the rules.
4. Use a separate verification script to confirm that the final output matches the expected counts and values.
5. Include all required metadata (e.g., `meta` block in JSON) as specified by the rules.

Self-check:
- [ ] Are all monetary values in the correct unit?
- [ ] Is the metadata block present and accurate?
- [ ] Did I handle duplicates and missing data as instructed?
- [ ] Does the output file match the required schema?
</body>
