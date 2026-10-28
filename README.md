# Leadership Handbook

Leadership Handbook is a 104-page guide in the Before You Commit series about what to know before leading people, teams, and yourself.

Read the PDF here:

[leadership_handbook.pdf](leadership_handbook.pdf)

## What This Is

This handbook is written for leaders who want a clear briefing before the consequences of leadership decisions become hard to reverse. It focuses on the actual decisions that determine whether leaders succeed or fail: hiring, onboarding, performance problems, firing, team design, one-on-ones, delegation, communication, accountability, conflict, crisis, and self-management.

The premise is direct: most people step into leadership and learn by making preventable mistakes. This handbook is meant to reduce that cost.

## Contents

The handbook is organized into five parts and four appendices:

```text
Part I - What Leadership Actually Is
01 - The Job Nobody Describes Honestly
02 - Authority, Influence, and the Gap Between Them

Part II - People Decisions
03 - Hiring: What You're Actually Deciding
04 - The First 90 Days of Someone New
05 - When Performance Starts to Slip
06 - Letting People Go

Part III - Team Decisions
07 - Building a Team That Works
08 - The One-on-One
09 - Meetings, Communication, and Information Flow
10 - Delegation and Accountability
11 - When the Team Is Broken

Part IV - Leading Yourself
12 - Your Operating System
13 - Managing Your Time and Energy
14 - Staying Calibrated

Part V - Hard Moments
15 - Delivering Hard News
16 - Conflict, Politics, and Difficult People
17 - Leading Through Uncertainty and Crisis

Appendices
A - Leadership Biases
B - Conversation Templates
C - Question Banks
D - Source Library & Online Resources
```

## Who It Is For

- New managers preparing for the real job, not the promotion announcement.
- Founders and executives building leadership judgment under pressure.
- Team leads moving from individual contribution into accountability for others.
- Operators handling hiring, feedback, delegation, team health, and hard conversations.
- Anyone deciding whether they actually want the work of leadership.

## Repository Contents

```text
README.md
leadership_handbook.pdf
content/appendix-c.md
scripts/build_handbook.py
scripts/verify_handbook.py
requirements.txt
docs/2026-10-29-notion-integration.md
```

## Format

The PDF is the primary artifact. [Appendix C](content/appendix-c.md) is also available as editable Markdown. It contains 12 question banks with guidance on when to use them, what to do with the answer, and relevant limits. The rest of the book remains in its original PDF layout; this repository does not yet contain a complete editable edition.

## October 2026 Revision

The Notion collection was compared with the existing handbook, including its embedded book-note images. This revision adds 36 question items, merges five overlapping items, and moves existing questions into the most relevant banks. Appendix C now has 178 items, including the existing cadence prompts and survey statements. No new research results are claimed. See the [integration and verification record](docs/2026-10-29-notion-integration.md) for coverage, attribution, and exclusions.

## Rebuild

Use Python 3 with the versions in `requirements.txt`:

```sh
python -m pip install -r requirements.txt
python scripts/build_handbook.py
```

The script reads the original 94-page edition from commit `2df876d44ef26f1071ab398c2fa3e73dbf41b017`, replaces its Appendix C, and renumbers the source-library pages. It verifies the baseline blob before editing. It needs that commit in local Git history; alternatively pass `--base-pdf /path/to/the-original-edition.pdf`. It makes no network requests and does not reconstruct the unchanged chapters from extracted text.

For verification, additionally install `pdfplumber` and `pypdfium2`, then run `python scripts/verify_handbook.py`. This checks preservation, all source lines, page bounds and footer numbering. Inspect rendered changed pages as well; text checks alone do not establish visual quality.
