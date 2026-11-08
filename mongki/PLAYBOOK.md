# Mongki Money — Content Playbook

Every episode is written and checked against this file. The daily ideation task reads it before writing a script.

## 0. Daily ideation run (every episode, at run time — never from memory, never reused lists)
Goal: the most clickable, "I have to see this" money video of the day. Do all of this fresh each run.
1. **Scan wide (live search, last 24–48 h).** At least 12 searches across: US top headlines, world top headlines,
   markets' biggest movers, crypto, celebrity/music/tours, sports (NFL, NBA, football transfers, UFC/boxing),
   tech/AI launches, space/science, weather/disasters, viral memes/TikTok trends, Reddit (r/all, r/wallstreetbets,
   r/news, r/personalfinance), plus viewer comments. Note upcoming dated events in the next 7 days too (launches, earnings, games, releases).
2. **Generate ≥ 20 candidates.** For each hot item, force a money twist with these lenses:
   - **What-if collision**: two unrelated worlds smashed together ("What if Taylor Swift bought a NFL team?").
   - **Shock number**: one absurd figure ("This tweet cost $50 billion").
   - **You-math**: what it means for the viewer's wallet ("Your Thanksgiving dinner costs $X more because of …").
   - **Backtest regret**: "$10 a day in X since Y" / "If you bought at the panic".
   - **Hidden winner/loser**: who quietly made or lost money from today's news.
   - **Scale-up absurdity**: "If every American did X…", "In Bitcoin terms…".
3. **Score each 1–5** on: Shock (jaw-drop), Curiosity gap (must click to know), Freshness (today), Data (real public
   numbers exist), Wildness (nobody else is making this), Breadth (non-finance people care). Max 30.
   Kill anything < 20, anything that needs fake facts, mocks someone's looks, or is one-sided politics.
4. **Pick the top 1** (respect the rotation and 14-day ticker rule). Keep #2–#4 as fallbacks.
5. **Titles**: write 8 variants (≤ 60 chars, number or name in the first 3 words, open loop, no clickbait lie),
   pick the best 1. **Thumbnail**: ≤ 3 words of huge text that are NOT the title, one emotion, one object.
   **Thumbnail concepts (write 3, the pipeline renders all and an AI judge picks the best):** each =
   `{"big": 1–2 huge words, "sub": ≤ 2 words, "badge": tiny tag, "emotion": mascot face, "bg_prompt": one focal image}`.
   Rules: the words are the *hook*, not the title (title says "Oil crashed", thumb says "$4.76 BACK?");
   prefer a number, a symbol (▲▼ $ ?) or a power word (GONE, BROKE, 10X, WHY?, BANNED, SECRET);
   one focal object that tells the story at phone size (cracked oil barrel, giant receipt, burning chart, trophy made of cash);
   strong contrast (yellow/white on dark, red for loss, green for gain); the mascot shows an extreme emotion that matches the hook;
   no real faces, no logos, no tiny text. Computed numbers go in as {placeholders} (filled from live data), never typed from a test run. The three concepts must differ: shock number vs. question vs. before/after contrast.
6. **Shorts**: 3 different angles of the same story (the shock number, the you-math, the twist), each with its own
   hook in the first 1 second.
7. **Save the run** to `mongki/ideas/YYYY-MM-DD.json`: all candidates with scores, chosen title, rejected titles, sources.
8. **Learn**: before scoring, read `mongki/ideas/performance.json` (views/likes/comments of past uploads, filled by
   the comments workflow) and boost the lenses/categories that performed best; de-boost the weakest.

## 1. Topic selection
1. Read `mongki/ideas/comments.json` (viewer comments, sorted by likes + replies). Skip comments marked `"used": true`.
2. Screen out: spam, links, insults, hate, sexual content, anything about a private person, medical/legal advice requests, and anything that cannot be answered with public data.
3. Score the rest 1–5 on: **fun** (would a stranger click?), **data** (public numbers exist, e.g. prices, CPI, sports results, Google Trends), **surprise** (answer is not obvious), **freshness** (ties to this week's news).
4. Best comment scoring ≥ 14/20 becomes the episode. Credit the commenter in the video by display name ("Today's question comes from @name"). Mark it `"used": true`.
5. Then scan **what is hottest right now** (search at run time, never from memory), in this order:
   - **US top stories** of the last 24 h (major outlets' most-read / top headlines; markets, politics, tech, celebrities, sports, consumer prices).
   - **Global top stories** of the last 24 h (wars and trade, central banks, elections, disasters, big company news in Asia/Europe).
   - **Reddit**: what is most upvoted and discussed in the last 24 h (r/all, r/news, r/worldnews, r/wallstreetbets, r/stocks, r/personalfinance, r/technology, r/economy) and viral memes or trends.
   - Cross-check: a story that shows up in two or more of these lists is the strongest candidate.
   - **Pop & wild topics count too**: space launches and asteroids, weather and hurricanes, celebrities and tours, rumors, UFC and boxing, football transfers, NBA/NFL, K-pop, movies, games, viral memes.
6. The money angle does **not** have to be a stock. Any money is fair: ticket prices, shirt sales, a city's tourism revenue, insurance losses, salaries, prize money, betting odds, resale prices, ad rates, a country's GDP. The best ideas link two things nobody expects to be connected. Examples:
   - "If Ronaldo goes back to Man United, this stock moves" → check what Manchester United (MANU) shares did on his past transfer news.
   - "If Messi returns to Barcelona" → Barcelona isn't listed, so use shirt sales, ticket prices, Inter Miami attendance, MLS TV deals.
   - "What a Taylor Swift tour stop does to a city" / "What a hurricane does to orange juice prices" / "What a UFC title fight earns".
   - **Go wild.** The best episodes are what-ifs nobody has imagined: "What if Bruno Mars signed with the UFC? What would TKO stock do, and why Dana White could pay him hundreds of millions and still profit." Build the answer from real numbers (past celebrity crossovers, pay-per-view buys, ticket and sponsorship revenue, the company's market value per extra viewer).
   - Label every what-if as a what-if on screen and in the title ("What If…", "If … Happened"). Never present it as news, never invent quotes, never imply the person said or agreed to anything.
   - No swearing, no slurs, nothing sexual, no mocking how someone looks. Playful is fine, cruel is not.
   - Rumors: say clearly it is a rumor, never present it as fact, and answer "if it's true, here's what happened the last time something like it did."
7. Turn the hot issue into a **money angle** with public data: "X happened → what did it do to Y's price / your wallet / the market last time?" Use the hook formulas in the channel plan.
8. Final pick = highest of (best comment, best hot issue) on fun + data + surprise + freshness. Respect the category rotation and "same ticker not within 14 days" rules from the channel plan (claude/VIEWS_CHANNEL_PLAN.md).
9. Verify every fact in at least one primary or major source before it goes in the script. Any sentence that describes what the computed data will show (dates, eras, "most of them", "the last time") must be checked against real prices first: write the check in `mongki/query/q.py`, push it (the mongki-query workflow writes `mongki/query/out.txt`), and only then write the line. Never describe data you have not seen. Also confirm every ticker is still listed and trading (taken-private or delisted companies, e.g. EA in 2026, have no prices and break the build). Reddit is for **finding** topics, never as the source of a fact.
10. Correlation videos must say clearly: **correlation is not causation**. Show the number (correlation coefficient or simple "moved together X% of the time") and one honest reason it might be a coincidence.

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
