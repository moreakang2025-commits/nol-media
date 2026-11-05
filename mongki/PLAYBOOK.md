# Mongki Money — Content Playbook

Every episode is written and checked against this file. The daily ideation task reads it before writing a script.

## 1. Topic selection
1. Read `mongki/ideas/comments.json` (viewer comments, sorted by likes + replies). Skip comments marked `"used": true`.
2. Screen out: spam, links, insults, hate, sexual content, anything about a private person, medical/legal advice requests, and anything that cannot be answered with public data.
3. Score the rest 1–5 on: **fun** (would a stranger click?), **data** (public numbers exist, e.g. prices, CPI, sports results, Google Trends), **surprise** (answer is not obvious), **freshness** (ties to this week's news).
4. Best comment scoring ≥ 14/20 becomes the episode. Credit the commenter in the video by display name ("Today's question comes from @name"). Mark it `"used": true`.
5. No good comment? Pick from the news rotation in the channel plan (claude/VIEWS_CHANNEL_PLAN.md): pillars, category rotation, same ticker not within 14 days.
6. Correlation videos must say clearly: **correlation is not causation**. Show the number (correlation coefficient or simple "moved together X% of the time") and one honest reason it might be a coincidence.

## 2. Retention structure (8–10 min long form)
| Time | Job |
|---|---|
| 0:00–0:02 | Logo sting |
| 0:02–0:05 | **Promise confirmation**: the exact claim from the title and thumbnail, on screen, with the shock number |
| 0:05–0:30 | Context in 2–3 punchy lines + **open loop** ("at the end I'll show you …") that is paid off later |
| 0:30–1:30 | **First payoff**: one real, useful answer early |
| every 60–120 s | **Section reset** with a re-hook line ("Here's the part most headlines skip", "But here's the twist", "Okay. Time for the data") and a new scene type |
| last 25% | The promised payoff (backtest / correlation reveal) — deliver it, then end fast |
| outro ≤ 25 s | Subscribe + **comment prompt** ("Drop two things you think are connected; I'll run the numbers and shout you out") + next video |

## 3. Rules that keep people watching
- Title, thumbnail and first 5 seconds say the same thing. A mismatch causes the biggest early drop.
- No segment longer than ~20 s on one static idea. Change scene type, add a pattern break (data, question, example, twist).
- Pattern breaks must change meaning, not just pixels.
- Captions on every spoken line; alternate punch-in zoom on caption chunks; progress bar on top.
- Don't stretch the ending. Payoff, one line of meaning, outro.
- Every number on screen has a source line.

## 4. Never
- Fake quotes, fake numbers, invented events, predictions presented as fact.
- Real people's faces or photos, other companies' logos, other creators' clips or music.
- One-sided political mockery. Both sides get the same treatment.
- Investment advice. Always "Not financial advice. For education only."
