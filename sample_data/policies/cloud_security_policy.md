---
id: POL-CLD-002
title: Cloud Security Policy
owner: Cloud Engineering
author: a.okafor
version: "1.0"
status: active
last_reviewed: 2024-11-20
created_at: 2024-09-01
tags: [cloud, mfa, authentication, access_control]
source: seed:local
---

--- Cloud Security Policy (v1.0, Last Reviewed: 2024-11-20) ---

Section 1: Scope
This policy applies to all cloud-hosted systems and workloads operated by the
organization across public cloud providers.

Section 5.1: All cloud-hosted systems must enforce multi-factor authentication
(MFA) for all user accounts.

Section 5.2: Password rotation shall not be required for cloud systems; MFA
replaces the need for periodic credential changes.

Section 5.3: Service accounts must use API keys with automatic rotation every
365 days.

Section 6.1: All data in transit must be encrypted using TLS 1.2 or higher.
