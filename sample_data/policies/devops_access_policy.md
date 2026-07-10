---
id: POL-DEV-006
title: DevOps Access Policy
owner: Platform Engineering
author: r.patel
version: "1.0"
status: active
last_reviewed: 2024-08-12
created_at: 2024-08-01
tags: [network, vpn, access_control, ci_cd]
source: seed:local
---

--- DevOps Access Policy (v1.0, Last Reviewed: 2024-08-12) ---

Section 1: Scope
This policy applies to members of the Developers and Platform Engineering
groups operating CI/CD pipelines.

Section 3.1: Developers may bypass the corporate VPN for CI/CD pipeline traffic
that terminates inside the trusted build network.

Section 3.2: All CI/CD secrets must be stored in the managed vault and must be
rotated every 90 days.

Section 4.1: Encryption must be applied to all pipeline artifacts at rest.
