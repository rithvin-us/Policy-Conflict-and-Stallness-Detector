---
id: POL-ENC-008
title: Encryption Standard
owner: Security Architecture
author: d.chen
version: "2.0"
status: active
last_reviewed: 2025-06-15
created_at: 2023-02-10
tags: [encryption, cryptography, data_protection]
source: seed:local
---

--- Encryption Standard (v2.0, Last Reviewed: 2025-06-15) ---

Section 1: Scope
This standard defines the minimum cryptographic controls for corporate data.

Section 2.1: All data at rest must be encrypted using AES-256.

Section 2.2: All data in transit must be encrypted using TLS 1.2 or higher.

Section 3.1: Cryptographic keys must be stored in a managed key vault and must be
rotated every 180 days.
