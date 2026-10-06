---
name: strict-rule-compliance
description: Use when a task specifies explicit formatting, schema, or procedural rules (e.g., RULE: ...).
---
<body>
1. Before starting, extract all lines starting with "RULE:" into a checklist.
2. For every output file, verify the schema (keys, types, nesting) against the rules.
3. For every data processing step, verify the transformation logic (e.g., currency conversion, sorting, string normalization) against the rules.
4. Before submitting, perform a final pass: check each rule in your checklist against the generated output.
5. If a rule requires a specific header or metadata block, ensure it is the first thing written to the file.

Self-check:
- [ ] Did I implement every "RULE:" requirement?
- [ ] Is the output schema exactly as requested?
- [ ] Are all data transformations (sorting, formatting, units) verified?
</body>
