# omni-new

Omni is a web3, solana based wallet tracking system that:
1. Identifies and tags smart wallets.
2. Identifies wallet clusters.
3. Classifies walllet behaviour historically as well as over time.

The aim of this project is to utilize the multitude of free web3 tools, and combine all of them into a hypercompressed data aggregation platform which analyses confluences, information snippets, and wallet appearances to enable me (and any potential users) to identify and classify onchain wallet behaviour.

## Roadmap

This will be a multi-phased project. For now, I am only describing Phase 1.
### Phase 1:
- The goal is to make a raw database of all active wallets, filter them down to wallets of interest, and then further filter down to smart money, and then track these wallets.
- This phase assumes every single wallet as an equal, and does not bestow and characteristic/behavioural properties to each wallet, neither does it identiy wallet clusters as a single individual. It simply identifies wallets who bought low, sold high, made good multiples on high volume coins.

To achieve this, we will be using sqlite as our main database.
This project will almost entirely be in Python, with maybe some usage of C and/or JS for web development.

Frameworks I will be using, subject to change. May or may not actually use all of these depending on specifics of what I need.

SQLite3 for database management. May have to switch over to postgreSQL later when I wish to run it on a server, but to get things up and running sqlite is best.
Bullx, gmgn, photon, solscan, dexscreener, defined.fi APIs will be reverse engineered.
Helius, solscan.fm, moralis might be some other proper API frameworks that will be used.

High level process overview:
1. Scan through holders of top x tokens daily
2. Add them to db.py
3. Wallets which appear more times will be marked as wallets of interest (WoI)
4. WoI will be further filtered by using currently existing PnL APIs (gmgn, dexcheck.ai, etc)
5. Wallets with good stats will be tracked.
6. OPTIONAL: I will attempt to somehow write code to see what would be the optimal strategy in following the selected wallets. Example, I will set a hard buy amount (small) and then simulate how much ROI I would be making if I bought all tokens and sold in how much (fixed) time period. I will not filter according to wallet behaviour here.

Fallbacks:
1. Wallets are all treated the same. Special mention will only be given to wallets which I manually go through, and will be added under the 'notes' column in the db.
2. No autoupdate.
3. Depends on external PnL APIs which can vary
4. Will not take into account historic holders
These issues will all be addressed in future phases of this project.

Database specifics:
db.py will be the main database file. Its schema is so:
wallet (primary key), tokens it appears in, last_active, note (special points to add after manual inspection)


