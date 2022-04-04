# Full node log cleaner

These are the scripts I used to clean the debug logs from the full nodes every 6 hours and save the data therein.

block-add.py, hash-add.py and tx-add.py are scripts to fetch block or transaction data from the full nodes to use with the data, such as when checking for valid block hashes when making the probability distribution graph etc.

Works only on Linux Ubuntu 16.04
All scripts use in-processor SQLite 3, and require it to run.
Python 3 is required.