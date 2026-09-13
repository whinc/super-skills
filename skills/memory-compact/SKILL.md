---
name: memory-compact
description: "Review and compact the agent's persistent memory: drop obsolete, duplicated, task-specific, or repository-recoverable entries, merge similar ones, keep only high-value long-term memories, and hold the primary entry file under 200 lines and 25 KB. Use when the user asks to clean up, review, prune, or compact memory, or when the memory has grown stale or noisy. Proposes one batch of keep/merge/delete/promote actions for a single confirmation, snapshots before rewriting, and reports before/after size."
---

# Memory compact

Compact the persistent memory this agent has. Use whatever memory store the harness provides — a single file, a directory with an index, or a memory API. Never assume a path or a product name. If the harness has no persistent memory, say so and stop.

The primary entry file — the whole file for a single-file store, the index for a directory store — is capped at 200 lines and 25 KB; reaching either means compaction is due.

## Procedure

1. **Locate.** Use the memory store the harness gives you. For a directory store, read the index and every topic file; the index is a pointer list, never content.

2. **Inventory.** List every entry with its size.

3. **Classify.** Give every entry exactly one action — delete, merge, promote, or keep — with a one-line reason traced to the rubric below. An entry on the never-drop list stays a keep unless the user explicitly says otherwise.

4. **Propose.** Present one batch table (entry → action → reason) and wait for a single confirmation; the user may accept all or adjust. Skip this step only if the invocation explicitly says to proceed without confirmation.

5. **Snapshot.** For a file-based store, copy the entry file(s) to a system temp path before writing and keep the path for the report. For a non-file store, the confirmation above is the only safety net — say so in the report.

6. **Rewrite.** Apply the confirmed plan in place. Never write outside the memory store.

7. **Verify the cap.** The primary entry file must end under 200 lines and under 25 KB. Topic files answer to the rubric, not to the size cap. If the memory is honestly compacted and still over, report the overage; never keep deleting just to hit the number. An explicit cap in the invocation overrides these defaults.

8. **Report.** Before/after size, counts per action, notable merges and removals, snapshot path, and any suggestion to promote something outside the memory — suggestions only, never writes to other documents.

## Rubric

| Action | Applies to |
| --- | --- |
| delete | obsolete · duplicated · task-specific · recoverable from the repository |
| merge | similar memories → one entry |
| promote | stable recurring patterns → consolidate inside the memory |
| keep | only high-value long-term memories |

**Never drop** (unless the user explicitly says so): user preferences, identity, and collaboration style · corrections that prevent repeated mistakes · active commitments with dates · validated stable patterns.

**Default drop**: implementation details recoverable from the repo or git · one-off task state and temporary TODOs · debugging recipes for already-solved problems · duplicate or near-duplicate entries.

## Never

- Never add entries just to fill space, and never delete just to hit the cap.
- Never write outside the memory store.
- Never hardcode a memory path or product name in this procedure.
