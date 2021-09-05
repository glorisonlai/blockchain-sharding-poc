# POC of Sharding interaction

Written by Glorison Lai and Jordan Morrow

Blockchain implementation created for FIT3143 Assignment 1.

All code was written within the timeframe of Assignment 1.

Code is hosted privately in GitHub, and includes timestamps from initialisation. Please contact Glorison for access.

## Files

`src/models.py` File defines all classes.

- Modify allocated shards (Line 255)
- (Optional) Modify mining difficulty (Line 525)

`src/services.py` Methods to instantiate data and call class methods.

- Modify number allocated processes (Line 28)
- (Optional) Add/Remove Blockchain users for faster bootstrapping (Line 11)

`test.py` Driver file. Make sure to modify other files first before running!

- (Optional) Modify number of transactions generated (Line 4)

`src/decorators.py` Defines custom decorators, used for timing functions, and defining private class attributes.

## Set Up

1. Create Virtual Environment

   `python -m venv ./`

2. Install required packages

   `pip -r requirements.txt`

3. Modify allocated processes and variables as necessary

   - Modify allocated shards (src/models.py - Line 226).
   - Allocate processes. Maximum number of processes calculated by (NUM_LOGICAL_PROCESSES - NUM_SHARDS - 1) (src/services.py - Line 28).

   - (Optional) Modify instantiated users (src/services.py - Line 11).
   - (Optional) Modify mining difficulty (src/models.py - Line 524). NOTE: Anything above 2 will take a VERY long time.
   - (Optional) Modify number of transactions (test.py - Line 4).

## Running

`python test.py`
