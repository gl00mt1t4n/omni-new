# Phase 1:

- make database: DONE
- database access/lookup functions: DONE
- Scrape trending tokens: DONE
- Get all token holders: DONE
- Profitable wallets (All stats (UPnL, RPnL, totalRev, totalSpent) should be > 1000): DONE

### Next:
- combine scraping modules into final pipeline of part 1 of phase 1
- filter through DB with some criteria, idk what it should be. Maybe top 500 wallets? Ordered according to number of tokens they appeared in?
- Put filtered wallets through gmgn, bullx api to get PnL, winrate, etc.
- Separate functions to MODIFY existing woi.db and better streamlining for NEW inserts in woi.db




General todol list:
- API for wallet aggregation through token holders: 
- add holders to omni.db using db.py: 
- Filter for wallets with multiple appearances:
- Manually make a list of some smart wallets:
- Then programatically make a list of all smart wallets and check if the manual ones appear:
- If manual list appears, continue, else go back and tweak criterion:
- Function using external API for PnL:
- Confluence check

### Known problems / Plan

- No support yet for tracking historic holders
- Limited by availability/consistency of public APIs
- No deduplication of wallets that may be the same entity
- No token-level performance tracking yet
