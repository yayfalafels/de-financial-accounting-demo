# Assessment 2 - Business-Facing Summary

status: draft

**Business-Facing Summary**

See [overview](assessment-2-overview.md) for the scenario and scale this summary answers. See [root-cause analysis](assessment-2-root-cause-analysis.md) and [reconciliation framework design](assessment-2-framework-design.md) for the full technical detail behind the findings and recommendations below.

## Sources

- notebook: [assessment2_gl_reconciliation.ipynb](https://github.com/yayfalafels/de-financial-accounting-demo/blob/main/notebooks/assessment2_gl_reconciliation.ipynb)
- batch: `reconciliation.rc_batch_control.batch_id = 29`

## What we found

Overall, the platform's total balance agrees with the General Ledger to the cent - no money is missing. The disagreement Finance is seeing is transactions landing in the wrong bucket. About SGD 297,137 - roughly 30 of the 589 lines on the Ledger - was posted against the wrong legal entity, the wrong GL account, or the wrong cost center. Tracing 16 transactions back to where they should have posted closes that gap exactly to zero.

Three smaller, unrelated issues turned up alongside this:

- **Duplicate entries** - 21 transactions appear to have been recorded twice (SGD 255,845 combined). Each needs to be checked against the originating system before anything is reversed, since a genuine repeat transaction would look the same as a duplicate.
- **Wrong debit/credit side** - 9 transactions (SGD 78,480 combined) were posted as a valid entry, just on the opposite side of where they belonged.
- **Currency conversion errors** - 3 transactions (SGD 4,468 combined) converted at the wrong exchange rate.
- **No accounting rule on file** - 385 transactions (SGD 4.39 million combined) have no rule to check them against. This is the largest figure by value, a coverage gap: nobody can say today whether these are posted correctly.

## What we recommend

- fix the 16 transactions behind the SGD 297,137 variance and re-run the check to confirm it closes to zero
- close the accounting-rule coverage gap - load or confirm a rule for every product and transaction type actually being posted, starting with the 385 transactions above
- investigate the 21 duplicate entries against the source system before reversing any of them
- confirm the exchange rate that should have applied, on the transaction date, for the 3 currency-conversion errors
- put standing controls in place:
    - flag a posting whose entity, account, or cost center breaks from that account's normal pattern, before it posts
    - block a posting from using a rule that has expired once a current one exists
    - flag a posting that only matches a valid rule on the opposite debit/credit side
    - alert whenever a new product or transaction type appears with no rule yet on file
    - check for duplicate entries within a batch before it is accepted
    - check the exchange rate in force at the point of posting
- move from a one-time check to a daily one, with clear pass/warning/fail thresholds, catching this kind of drift within a day, before it builds up across a reporting period
