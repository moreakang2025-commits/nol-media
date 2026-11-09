# Front Porch Stories — how to write a daily episode

Audience: Americans 55-80 who listen like radio. Channel promise: family betrayal → quiet strength → public justice → dignity.

## Format (checked by `python3 tools/fps/lint.py`)
- Copy the header layout of `fps/episodes/ep02.txt` (TITLE, THUMB_TOP, THUMB_BOTTOM, THUMB_PROMPT, VOICE_STYLE, TAGS, CAST, DESCRIPTION with {chapters}, fiction + AI disclaimer).
- 1,700-2,100 spoken words (12-15 min). 7-9 chapters.
- Pictures: ONLY `[LIB] id id` from `fps/library/catalog.md` (2 ids per block usually, a new block every 2-4 lines → a picture every ~15 s). At most 2 `[SHOT]` (each costs money). Never use an id twice in a row.
- Cast faces: `look=lib:<role>` only (grandma, grandpa, son, dil, daughter, sil, grandson, granddaughter, lawyer, realtor, nurse, friend, banker). Names change every episode; faces stay.
- Narrator voice is always Gacrux (the channel's voice). Other voices: men Orus, Charon, Algenib, Sadaltager, Iapetus; women Pulcherrima, Sulafat, Leda, Autonoe, Kore; boys/young men Puck.
- Exactly 4 `[SHORT] Hook Title` markers, each right before the line where a 45-57 s Short should start: (1) the opening insult, (2) the overheard plan / discovery, (3) the hidden card, (4) the public payoff.

## Spice (매운맛) rules
- First line = the insult itself, spoken by the villain, in under 25 words. Then the narrator reveals the secret card within 30 seconds ("What she didn't know…").
- A new twist or discovery every 2-3 minutes. Concrete numbers and objects (amounts, dates, a deed, a recording, a key).
- The payoff is public (holiday table, wedding, reading of a will, church, bank, courthouse), the villain is exposed by evidence, not violence.
- End with dignity and a one-line lesson, then the comment question + subscribe line.
- Rotate every episode: narrator (grandma / grandpa / both), villain (DIL, son, daughter, son-in-law, sibling, new spouse of a child, greedy grandchild), hidden card (trust, will codicil, recording, prior signed loan, secret property, lottery, business she secretly owns, pension, life insurance, video doorbell, old friend who is a judge…), payoff place. Check `fps/episodes/LOG.md` and don't repeat a combination from the last 10.
- Title: first person, concrete, 70-100 chars, ends on a tease, never reveals the outcome, must match what really happens.
- Never: graphic violence, sexual content, suicide, slurs, mocking looks or disabilities, real people or brands, medical/legal advice framed as real. Legal details are drama devices (the description says so).

## After writing
1. `python3 tools/fps/lint.py fps/episodes/epNN.txt` must pass.
2. Add a row to `fps/episodes/LOG.md` and the date to `fps/schedule.json`.
3. `fps/run.txt` = `epNN true YYYY-MM-DD full` → push → workflow fps-video builds, uploads and schedules everything.
