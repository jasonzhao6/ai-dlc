Here's a summary of how Claude Code would behave differently with these AI-DLC         
(AI-Driven Development Life Cycle) rules added to your project:                        

Without Rules (Default Claude Code)                                                    
                                                                                     
You say "build me X" and Claude Code jumps into coding. It reads files, writes code,   
runs tests, and iterates. It's conversational, freeform, and fast.                     
                                                                                     
With These Rules — Major Behavioral Shifts

1. Rigid Multi-Phase Waterfall Process

Instead of jumping to code, Claude would be forced through a structured lifecycle:
- Inception (planning/requirements/architecture) → Construction (design/code/test) →
Operations (placeholder)
- Each phase has multiple stages, many requiring explicit user approval before
advancing. You'd be clicking "approve" a lot.

2. No More Inline Questions — Everything Goes to Files

Claude would never ask you questions in chat. Instead, it creates .md files like
requirements-questions.md with multiple-choice options and [Answer]: tags. You edit the
file, say "done," and Claude reads your answers. This is a fundamentally different
interaction model.

3. Massive Documentation Generation

Every workflow produces a pile of markdown artifacts in aidlc-docs/:
- requirements.md, stories.md, personas.md, execution-plan.md, business-logic-model.md,
domain-entities.md, nfr-requirements.md, infrastructure-design.md,
build-instructions.md, test instructions, and more
- An aidlc-state.md state file tracking progress
- An audit.md logging every user input verbatim with ISO 8601 timestamps

4. Ask Everything, Assume Nothing

The rules include explicit overconfidence prevention — Claude would default to asking
questions even when it could reasonably infer the answer. The rules say: "When in
doubt, ask the question." This is the opposite of Claude Code's default behavior of
being action-oriented.

5. Brownfield vs. Greenfield Detection

Before anything else, Claude scans your workspace. If it finds existing code, it runs a
full reverse engineering phase producing 9 artifact files (architecture docs, API
docs, component inventory, dependency graphs, code quality assessment, etc.) before
even discussing your request.

6. Security as a Blocking Constraint

15 mandatory security rules (encryption, IAM least privilege, input validation, no
hardcoded credentials, OWASP-aligned, etc.) are enforced as hard gates — Claude cannot
advance past a stage if any rule is violated. This would slow down prototyping
considerably.

7. Checkbox-Driven Execution

Code generation follows an explicit numbered plan with checkboxes. Claude creates a
plan file, gets approval, then executes one checkbox at a time, updating the file after
each step. No ad-hoc coding.

8. Standardized Completion Messages

At the end of every Construction stage, you get exactly 2 options: "Request Changes" or
"Continue to Next Stage." No freeform discussion.

Bottom Line

These rules transform Claude Code from an agile coding assistant into a formal SDLC
process engine. It would be thorough and well-documented, but dramatically slower for
simple tasks. A quick bug fix would still go through workspace detection, requirements
analysis, workflow planning, and approval gates before any code is written.

Good for: Large greenfield projects, compliance-heavy environments, teams that need
audit trails and formal design docs.

Overkill for: Quick fixes, prototyping, exploratory coding, or anything where you just
want Claude to write code fast.
