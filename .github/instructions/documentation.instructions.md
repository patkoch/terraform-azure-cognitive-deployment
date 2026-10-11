---
description: "Use when: changing Terraform inputs, workflows, agents, skills, or README documentation."
applyTo: "README.md,*.tf,*.tfvars,.github/**"
---

# Documentation Rules

- Assess README impact for every change and update affected sections in the same
  change set. Do not make cosmetic changes when no documentation update is needed.
- Examples must match current inputs, model settings, module usage, the canonical
  `terraform.auto.tfvars`, and the documented validation sequence.
- Describe agents separately from skills: roles/tools versus procedures. Link to
  authoritative definitions rather than copying their full contents.
- Document authentication without requesting or embedding secrets.
- Report checks as passed, failed, blocked, or not applicable. Never claim a
  plan ran when only static checks completed. Include blockers and next actions.