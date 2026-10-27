# 3. Bulk Ledger Postings - Fees

> **Short description**
>
> Based on the orders entered and approved, the fee charge(s) are stored in a separate table, Order.FeeSchedule. If FeeSchedule.DueDate <= SystemDayClosedEvent.BusinessDate+1, a [service is called to calculate the fee amount.](https://your-confluence.example.com/spaces/DOCS/pages/123460/Service+Fee+Calculation) After calculation and storage of the fee amount, a process is started to create bulk postings to LEDGER.

# General mapping client side

This is the complete description of fee postings related to multiple Orders.

# Start Bulk Command

Messagetype: **StartBulkCommand**

| Input parameter | Description | Input validations |
| --- | --- | --- |
| Bulk reference | `ORD` + `<DateTime>` + `'FEE'` | Mandatory |
| Bulk type | 'Order Fee' | Mandatory |
| Bulk name | 'Order Fee' + 'DDMMYY' | Optional |
| Source | ORD | Mandatory |

# Create Bulk Posting Command

Messagetype: **CreateBulkPostingCommand**

Except for the message type, the definition of this message equals `CreateSinglePostingCommand`; both are a ledger posting for one posting.

Based on the group details in this posting, the bulk posting is related to the bulk group that was started with the start bulk command.

# Mapping

| Entity / Input parameter | LEDGER description | Mapping from Order |
| --- | --- | --- |
| **Posting** | the root of a posting | One instance only |
| Posting identifier | Uniquely identifies this posting | `'ORD' + <DateTime> + AccountNumber + 'Fee'` |
| Business type code | Code to characterize the posting | 'Sale' |
| Description | Description of the posting | `'Fee Order <AccountNumber>'` |
| Is final | If 'No', the posting is not final yet and will be reversed and replaced later | "Yes" |
| Source | Token to identify the source | "ORD" |
| **Posting Group** | grouping identification for multiple postings | One instance only |
| Group type code | Code to specify the type of group | 'Order Fee' |
| Group reference | Identifies the group within the scope of the group type | + 'FEE' |
| Group name | Name of the posting group | 'Order Fee' + 'DDMMYY' |
| **Order Posting** | Posting details for one specific store | One instance: the store of the order |
| Order posting type code | Code to characterize the order posting | 'FeeCharge' |
| Case type code | Details the order posting for reporting purposes | "Scheduled Fee" |
| External reference | | n/a |
| Value date | Value date of the postings | `ValueDate` = BusinessDate |
| Posting date | | `PostingDate` = BusinessDate |
| Description store language | | Fee Order `<AccountNumber>` |
| Store unique identifier | | `<StoreNumber>` |
| Store class | | 'Retail' or 'Wholesale' |
| **Account Line** | individual postings | **1 instance per posting** |
| Quantity | Total money amount of the posting | Sum of the **Book currency amount** of the child attributions |
| Book currency ISO code | | Order.CurrencyISOCode |
| Unit price | For money by definition 1 | 1 |
| Account unique identifier | Account to post to | Order.BillingAccountNumber if Order.IsFeePrepaid=False; Order.AccountNumber if Order.IsFeePrepaid=True |
| Account type code | | "**R**eceivable" or '**P**repaid' (see account unique identifier) |
| **Attribution type code** | | **'FeeChargeAmount'** |
| Source currency ISO code | | Order.CurrencyISOCode |
| Source currency amount | Fee amount in source currency | FeeSchedule.Amount \* sign -1, rounded to the decimals of the source currency |
| Book currency amount | | = Source currency amount |

# End Bulk Command

Messagetype: **EndBulkCommand**

| Input parameter | Description | Input validations |
| --- | --- | --- |
| Bulk reference | `ORD` + `<DateTime>` + `'FEE'` | Mandatory |
| NrOfPostings | Total number of postings in this bulk; validated against the number of received `CreateBulkPostingCommand` for this bulk | Mandatory |
| Source | ORD | Mandatory |
