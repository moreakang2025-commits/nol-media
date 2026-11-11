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
