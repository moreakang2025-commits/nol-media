# Front Porch Stories — how to write a daily episode

Audience: Americans 55-80 who listen like radio. Channel promise: an older person is underestimated → quiet strength → a twist nobody saw coming → public justice or a public moment of grace → dignity. Every story carries friendship or love, not only revenge.

## The ending is ALWAYS all four (owner's rule, 2026-11-11)
1. **반전 Twist** — a final reveal the listener did not see coming (planted earlier, fair, not random).
2. **참교육 Lesson taught** — the antagonist faces the consequence of exactly what they did, in front of people (loses the house/job/position/respect, has to apologize, the HOA/board votes them out…). By evidence and smarts, never violence.
3. **감동 Heart** — a moment that brings a tear: friendship or love revealed, a thank-you, a reunion, a dog's loyalty, kids hugging the grumpy neighbor.
4. **사이다 Release** — a short, sharp, satisfying last line from the hero that the audience will quote in the comments.
Order in the last chapter: twist → lesson taught → heart → one cider line → one-line lesson → comment question + subscribe.

## Theme rotation (owner's request, 2026-11-11)
Pick the theme first. Rotate between these lanes; never use the same lane two days in a row and use each lane at least once every 6 episodes (check the `theme` column of LOG.md):
- **A. Family betrayal** (the original lane): greedy child / in-law, hidden card, public exposure.
- **B. Old dog + senior**: a widower/widow and an old dog. E.g. the family wants to put the dog down or give it away "to make Grandpa move", the dog turns out to be the key (it saves someone, it was trained by the late spouse, its tag/collar hides something, a stranger claims it). Friendship, loyalty, grief healed.
- **C. Homeless young man + senior**: a senior helps (or is helped by) a young man living on the street; family or neighbors assume the worst (theft, scam). Twist: who he really is / what he did / who he is connected to. Friendship across generations, a second chance.
- **D. The strange neighbor**: the grumpy, suspicious old man (or woman) next door (night digging, packages, closed shutters). Neighbors gossip or call the HOA/city. Twist: the secret is kind or heartbreaking (a promise to a lost child, a hidden gift for the town, a past hero). Ends in friendship or late love.
- **E. The noisy kids next door**: kids who drive a grumpy senior crazy (balls, bikes, shouting). Twist: the kids are going through something hard (single mom working nights, eviction, a sick parent) or they quietly save the senior. Ends with an adopted-grandparent friendship.
- **F. Second-chance love**: a widow/widower falls in love late; the grown children object ("she's after the money"). Twist proves the love is real (prenup she asked for herself, she is the one with money, an old letter from decades ago).
Pictures are made only when needed: you MAY use ids marked (MISSING) in catalog.md — the build makes them the first time (Gemini, ~$0.04 each, then kept forever). Keep new ones to what the story needs (≤ 25 per episode, lint warns with the cost). If Gemini is down, the build automatically uses backup pictures (free) and backup voices, and writes `fps/results/epNN_engine.json`.
Lanes B-F still need: spicy first line (an insult, accusation or shocking line from the antagonist — a relative, neighbor, HOA president, landlord, store manager), a twist every 2-3 minutes, concrete evidence, a public payoff (town meeting, church, school event, HOA meeting, diner full of people, court, family dinner), and a warm, earned ending. The antagonist is exposed, the friendship/love is revealed in front of everyone.

## Format (checked by `python3 tools/fps/lint.py`)
- Copy the header layout of `fps/episodes/ep02.txt` (TITLE, THUMB_TOP, THUMB_BOTTOM, THUMB_PROMPT, VOICE_STYLE, TAGS, CAST, DESCRIPTION with {chapters}, fiction + AI disclaimer).
- 1,700-2,100 spoken words (12-15 min). 7-9 chapters.
- Pictures: ONLY `[LIB] id id` from `fps/library/catalog.md` (2 ids per block usually, a new block every 2-4 lines → a picture every ~15 s). At most 2 `[SHOT]` (each costs money). Never use an id twice in a row.
- Cast faces: `look=lib:<role>` only (grandma, grandpa, son, dil, daughter, sil, grandson, granddaughter, lawyer, realtor, nurse, friend, banker, dog, youngman, neighbor, kidboy, kidgirl, mom, widow). Names change every episode; faces stay. Use the scene groups for each lane (dog_*, ym_*, nb_*, kids_*, love_*, place_*).
- The dog never speaks (it can be a cast member only for pictures; give it no lines).
- Narrator voice is always Gacrux (the channel's voice). Other voices: men Orus, Charon, Algenib, Sadaltager, Iapetus; women Pulcherrima, Sulafat, Leda, Autonoe, Kore; boys/young men Puck.
- Exactly 4 `[SHORT] Hook Title` markers, each right before the line where a 45-57 s Short should start: (1) the opening insult / accusation, (2) the overheard plan / discovery, (3) the hidden card / twist, (4) the public payoff.

## Spice (매운맛) rules
- First line = the insult itself, spoken by the villain, in under 25 words. Then the narrator reveals the secret card within 30 seconds ("What she didn't know…").
- A new twist or discovery every 2-3 minutes. Concrete numbers and objects (amounts, dates, a deed, a recording, a key).
- The payoff is public (holiday table, wedding, reading of a will, church, bank, courthouse), the villain is exposed by evidence, not violence.
- End with dignity and a one-line lesson, then the comment question + subscribe line.
- Rotate every episode: theme lane (above), narrator (grandma / grandpa / both / the neighbor / the young man looking back years later), antagonist (DIL, son, daughter, son-in-law, sibling, new spouse of a child, greedy grandchild), hidden card (trust, will codicil, recording, prior signed loan, secret property, lottery, business she secretly owns, pension, life insurance, video doorbell, old friend who is a judge…), payoff place. Check `fps/episodes/LOG.md` (now with a `theme` column; add yours) and don't repeat a combination from the last 10.
- Title: first person, concrete, 70-100 chars, ends on a tease, never reveals the outcome, must match what really happens.
- Never: graphic violence, sexual content, suicide, slurs, mocking looks or disabilities, real people or brands, medical/legal advice framed as real. Legal details are drama devices (the description says so).

## After writing
1. `python3 tools/fps/lint.py fps/episodes/epNN.txt` must pass.
2. Add a row to `fps/episodes/LOG.md` and the date to `fps/schedule.json`.
3. `fps/run.txt` = `epNN true YYYY-MM-DD full` → push → workflow fps-video builds, uploads and schedules everything.

## Cadence (owner decision, 2026-11-23)
Views collapsed after the first week (ep01-04: 60-160 views each; ep05-ep14: 0-17 each, one outlier). Five near-identical uploads a day were competing with each other and YouTube stopped testing them. From US date 2026-11-24: ONE episode every TWO days (11-24, 11-26, 11-28 ...). Day 1: long-form 10:00 ET + s1 20:30. Day 2: s4 12:30 + s2 20:30. s3 is still written and built but not uploaded. Use the freed time for quality: a sharper first 3 seconds, the strongest possible s1/s4 lines, and only publish on days where the Gemini engine works if possible (the backup engine changes faces and voice).
Judge the change after 4 episodes on the new cadence (around 2026-12-02): views@48h per video vs ep05-ep14.

## What the data says (update every Monday from fps/results/insights.md)
Data loop: workflow fps-stats runs daily 06:17 UTC (15:17 KST) → `fps/results/stats.json` (+ history in `fps/results/stats/`) → `tools/fps/analyze.py` → `fps/results/insights.md`. Read-only; changes nothing on YouTube.
Weekly read, 2026-11-23 (Mon; ep01-ep12 public = 60 videos, 7 subscribers (+1 in a week), 544 total views (+72)). Groups with n>=6 are called patterns; the rest are hints:
- Pattern (n=12 each): s1 (the insult) and s4 (the payoff) carry the Shorts: views@48h s4 18.2, s1 13.6, s2 3.4, s3 2.3. The ep06 confrontation rule did NOT revive s2/s3. One Short per episode still takes almost everything (ep11 s1 "My Niece Said Fire The Homeless Kid Or Else" 182 views = a third of all channel views).
- Pattern (n=12 each): 15:30 ET is the dead slot (2.5 views@48h, 0.2/day). 20:30 (20.3@48h) and 12:30 (13.2) are best; 18:30 views/day is high only because of the ep11 outlier (2.0@48h). Hint only for 20:30 vs 12:30: the 20:30 group still holds five pre-rotation s4 payoffs (content and slot mixed). Next step (not yet applied, needs one more week): stop giving 15:30 to s1/s4.
- Pattern (n=8 each): lane D (strange neighbor) Shorts are dead (1 view in 8 Shorts) while C (15.5/day) and A (1.7/day, 18.2@48h) carry; B in between. A neighbor's insult means nothing to a stranger; a family member's insult does. Hint (n<6): E and F Shorts also weak (n=4 each).
- Hint (long-form, n<=4 per lane): A still the best long-form lane (3.0/day, 7.1% like rate, n=4); others n<=2.
- Hint: weekend dip continues (Sat 0.2/day n=10, Sun 0.3 n=5, Mon 0.6 n=5) vs Tue-Fri 0.9-13.2. Cannot change the daily schedule; nothing to do yet.
-> Used in ep15 (lane A, next in rotation and the best long-form lane): all four Short titles start with "My Daughter" + a confrontation, s2/s3 put on lines where the villain says something cruel out loud to or about the hero (not the hero's discovery). For future D/E/F episodes: give the antagonist a family role whenever the story allows (a son, daughter, in-law pushing the neighbor complaint), and open s1 with that family role.
Weekly read, 2026-11-16 (Mon; ep01-ep06 public = 30 videos, 6 subscribers, 472 total views; every group still has n<=6 → hints only):
- Shorts are hit-or-miss: per episode usually ONE Short takes almost all the views (ep03 s4 96, ep01 s4 70, ep04 s1 67, ep01 s1 58); the other three get 0-13. The winners all say a family role + a taboo or a public act in plain words ("My Daughter Said Put My Old Dog Down", "I Took The Microphone At Our 50th Anniversary"). Keep that title style.
- s2/s3 are still near zero (1.1 and 0.8 views/day, n=6 each). The ep06 rule (confrontation lines for s2/s3) has no public result yet (ep06 Shorts were 0-15 h old). Judge it on ep07-ep10.
- Hint: everything published from Sat 2026-11-14 on (ep05, ep06: 8 Shorts) is at ~0-8 views, while Tue-Fri uploads got 60-160. Could be the weekend, the C/D lanes, or the feed simply not testing us. Watch whether ep07 (Mon) recovers before changing anything.
- Slot rotation: started 2026-11-15; ep06 s4 (payoff) ran at 12:30 ET and got 0 in 15 h, but one day says nothing. Re-read after ~8 rotated days (around 2026-11-23).
- Theme lanes (long-form): A 7.5 views/day (n=3), D 9.7 (n=1, too young), B 2.6, C 1.7 (n=1 each). Not enough to drop or favour a lane. F (second-chance love) first used in ep08.
→ Used in ep08: every Short title first person, confrontation, under 50 characters, and each Short's first line names the relationship ("my father-in-law", "my fiancé", "my father").
First read, 2026-11-13 (ep01-ep03 only, 15 public videos, 3 subscribers; hints, not rules):
- Shorts bring ~80% of views (245 vs 52). Long-form viewers like more (3.8% vs 0.4% like rate). Shorts are the front door; the long-form is where fans are made.
- The payoff Short (s4, 20:30 ET) wins every episode: ~75 views/day vs 5-9 for s2/s3. s1 (the insult) is second. s2 (overheard plan) and s3 (hidden card) are nearly dead: a stranger in the Shorts feed doesn't know who these people are.
  → Rule from ep06: every Short must work for a stranger. Its first line names the relationship and the conflict in under 12 words ("My son-in-law took my husband's truck keys."). Put the s2/s3 markers on lines that are a confrontation said out loud, not on narration or a quiet discovery.
  → Short titles: confrontation or contrast, first person, under 50 characters. Winners: "I Took The Microphone At Our 50th Anniversary", "They Brought A Pen. I Brought A Lawyer." Avoid vague ones like "The Bank Manager Went Quiet".
- Content vs time is mixed up (s4 always went out at 20:30). From 2026-11-15 `tools/fps/when.py` rotates the four Shorts through 12:30/15:30/18:30/20:30 ET day by day. After ~8 rotated days, insights.md shows whether the payoff content or the 20:30 slot is what wins; then fix the order.
- Theme lanes: only lane A has public data so far. Compare A vs B-F once each lane has 2+ public episodes. Do not drop a lane on less than that.
- Not yet available: watch time, retention, audience age, traffic sources, best hour. They need the owner to re-authorize YouTube with the yt-analytics.readonly scope (see claude/FPS_STATUS.md). YouTube's API never gives "when viewers are online" by hour; the slot rotation is how we learn it.
