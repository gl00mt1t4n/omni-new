## KNOWN ISSUES
- Minor: No function to effectively remove wallets or tokens from the list
- Minor: woi_data.py has a function to filter 'active/good' wallets, which should have been in gmgn.py
- Minor: woi_data.py also has the pipeline function, which should be written in a pipeline file (not just called in the pipeline file)


### 14-15 May 2025
- Finished modular sqlite layer
- Finished updating schema + modular db.py for basic lookup functions, insertion functions, confluence lookups, etc.

### 15-16 May 2025
- Added scrapers/
- Added defined_fi.py for scraping top 20 trending tokens. Will be called every x hours.
- Added helius_utils.py to fetch all holders of a token using helius API
- added .env file for healthy, anti-hardcoding practice.
- Less work today, had issues bypassing cloudfare anti-bot measures. Had to GPT, reddit, stackexchange lot of it. 
- Ended up using cloudscraper to bypass defined.fi, couldn't bypass solscan so ditched it and switched to helius. 

### 18-21 May 2025
- Added bullx api
- Added gmgn api
- added final smart money database
- added final filtering
- finished phase 1
