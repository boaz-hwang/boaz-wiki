# Return window after the 2026-02-01 policy change

Add the policy change meeting as a source and split the return window by order date: 14 days up to 2026-01-31, 30 days from 2026-02-01. The made-to-order exclusion stays.

검토 버전: `c2ffb4733f4a4e5339eaf846c29bb41b35246eaac3bc92658e03a6d211cde28e`

승인 / 수정 요청 / 보류 / 제외 중 선택. 승인 범위는 아래 변경 전후와 판단 내용입니다.

## 1. fact

- 이전: A return can be requested within 14 days of delivery.
- 제안: Orders placed from 2026-02-01 can be returned within 30 days of delivery.
- 이유: The meeting note states the new window and its start date.
- 근거: ^[/documents/policy-change.md:2]

## 2. scope

- 이전: The 14-day rule is stated without a date limit.
- 제안: The 14-day rule applies only to orders placed up to 2026-01-31. The 30-day rule is not applied to all orders.
- 이유: The meeting note keeps the existing policy for earlier orders. Applying 30 days to every order would overstate the change.
- 근거: ^[/documents/policy-change.md:3]

## 3. fact

- 이전: Made-to-order items are excluded from change-of-mind returns.
- 제안: Unchanged for both periods.
- 이유: The meeting note says the exclusion stays in place.
- 근거: ^[/documents/returns.md:3] · ^[/documents/policy-change.md:4]

## 4. relationship

- 이전: One returns source, no later change recorded.
- 제안: Link the two sources both ways. Do not mark them as contested and do not deprecate the older source.
- 이유: The two policies cover different order dates, so they are not incompatible claims about the same orders. The older source still governs January orders.
- 근거: ^[/documents/returns.md:2] · ^[/documents/policy-change.md:2-3]

## sources/returns-policy-change.md

```diff
--- before/sources/returns-policy-change.md
+++ after/sources/returns-policy-change.md
@@ -0,0 +1,36 @@
+---
+type: source
+title: Returns policy change meeting (from 2026-02-01)
+description: Meeting note that extends the return window to 30 days for orders placed from 2026-02-01 and keeps 14 days for earlier orders.
+tags: [returns, policy, meeting]
+sources:
+  - resource: /documents/policy-change.md
+    id: src-policy-change
+generated: { by: agent/claude-opus-5-5, at: 2026-10-08T00:00:00Z }
+verified: []
+status: draft
+contested: false
+contradictions: []
+supersedes: []
+related: [questions/return-window, sources/returns-policy]
+---
+# Returns policy change meeting (from 2026-02-01)
+
+The original is a short meeting note for a fictional store. It is practice material, not a real policy.^[/documents/policy-change.md:1-5]
+
+## Key facts
+
+- From 2026-02-01, new orders can request a return within 30 days of delivery.^[/documents/policy-change.md:2]
+- Orders placed up to 2026-01-31 keep the existing 14-day policy.^[/documents/policy-change.md:3]
+- The exclusion of made-to-order items from change-of-mind returns stays in place.^[/documents/policy-change.md:4]
+
+## What this source changes
+
+It narrows the 14-day rule in [[sources/returns-policy]] to orders placed up to 2026-01-31 and adds a 30-day rule for orders placed from 2026-02-01. The two policies apply to different order dates, so they are not marked as a contradiction, and the older source is not deprecated because it still governs January orders.
+
+The 30-day window does not apply to every order. The deciding condition is the date the order was placed.
+
+## Links
+
+- [[questions/return-window]]
+- [[sources/returns-policy]]
```

## questions/return-window.md

```diff
--- before/questions/return-window.md
+++ after/questions/return-window.md
@@ -1,7 +1,7 @@
 ---
 type: question
 title: How long does a customer have to request a return?
-description: Current answer on the return window and its exceptions, with what is still unknown.
+description: Current answer on the return window by order date and its exceptions, with what is still unknown.
 tags: [returns, policy, faq]
 generated: { by: agent/claude-opus-5-5, at: 2026-10-08T00:00:00Z }
 verified: []
@@ -9,15 +9,22 @@
 contested: false
 contradictions: []
 supersedes: []
-related: [sources/returns-policy]
+related: [sources/returns-policy, sources/returns-policy-change]
 ---
 # How long does a customer have to request a return?
 
 ## Current answer
 
-A return can be requested within 14 days of delivery.^[/documents/returns.md:2] Made-to-order items cannot be returned for a change of mind.^[/documents/returns.md:3] Basis: [[sources/returns-policy]].
+It depends on when the order was placed.
+
+| Order placed | Return window | Basis |
+|---|---|---|
+| Up to 2026-01-31 | 14 days from delivery | ^[/documents/returns.md:2] ^[/documents/policy-change.md:3] |
+| From 2026-02-01 | 30 days from delivery | ^[/documents/policy-change.md:2] |
+
+For both periods, made-to-order items cannot be returned for a change of mind.^[/documents/returns.md:3]^[/documents/policy-change.md:4] Basis pages: [[sources/returns-policy]], [[sources/returns-policy-change]].
 
 ## Open points
 
-- The source does not say whether the window counts calendar days or business days.
-- The source does not cover returns of made-to-order items for reasons other than a change of mind.
+- Neither source says whether the window counts calendar days or business days.
+- Neither source covers returns of made-to-order items for reasons other than a change of mind.
```

## sources/returns-policy.md

```diff
--- before/sources/returns-policy.md
+++ after/sources/returns-policy.md
@@ -12,7 +12,7 @@
 contested: false
 contradictions: []
 supersedes: []
-related: [questions/return-window]
+related: [questions/return-window, sources/returns-policy-change]
 ---
 # Returns policy (2026-01-01)
 
@@ -27,6 +27,8 @@
 
 This is the first returns source in the wiki. It sets the baseline answer for [[questions/return-window]]: 14 days from delivery, with the made-to-order exclusion.
 
+Later change: [[sources/returns-policy-change]] keeps this 14-day rule only for orders placed up to 2026-01-31.
+
 ## Not stated in the source
 
 - Whether the 14 days count calendar days or business days.
@@ -35,3 +37,4 @@
 ## Links
 
 - [[questions/return-window]]
+- [[sources/returns-policy-change]]
```
