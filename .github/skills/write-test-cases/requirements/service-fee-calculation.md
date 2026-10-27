# Service Fee Calculation

> **Short description**
>
> This service calculates handling fees for a single Order or a set of Orders. The logic for single and bulk requests is equal. This page describes the process to calculate the fee amount(s) of an Order.

# Bulk service to calculate fees of Orders

## Trigger

- `<SystemDayClosedEvent>` triggers a check in the FeeSchedule table whether fee charges are due.
- A fee charge is due when:
  - FeeSchedule.DueDate <= CurrentDate and
  - FeeSchedule.Status = 'Planned'
- When a fee charge is due, a service call to PAY is created to calculate the fee for the period.

## Input

The bulk service `GetBulkFeeCalculationRequest` calculates fees for one or many Orders.

| Parameter | Format | Description |
| --- | --- | --- |
| Requests | List of FeeCalculationRequest | The set of order requests for which fees must be calculated |

FeeCalculationRequest contains:

| **Parameter** | **Format** | **Description** |
| --- | --- | --- |
| OrderId | Guid | Unique identifier of the Order |
| RoundingMode | Text | Standard rounding mode configured in the Order module |
| RepeatingGroup | | The periods with a basis amount for which the fee must be calculated |
| Period Start | DD-MM-YYYY | Start of the fee period |
| Period End | DD-MM-YYYY | End of the fee period |
| Basis Amount | amount | Amount subject to fee = Order.OrderTotal |
| Fee Rate | percentage | Rate related to the OrderId |

Input data for the calculation engine:

| **Input** | **Description** | **Source** |
| --- | --- | --- |
| Period start | Start of the fee period | FeeSchedule.PeriodStart where FeeSchedule.DueDate <= CurrentDate and FeeSchedule.Status = 'Planned' |
| Period end | End of the fee period | FeeSchedule.DueDate |
| Basis amount | Unsigned amount | Order.OrderTotal |
| Fee kind | Flat, tiered-exclusive or tiered-cascading — always **Flat** | Default = Flat |
| Rounding mode | Method to round the fee, must match a value from code table RoundingMode | Configured per installation, default **HalfUp2** |
| Repeating group | Always 1 | Default = 1 |
| Tier no. | Always 1 | Default = 1 |
| Threshold amount | Zero for the first tier; higher for each next tier | Default = zero |
| Fee rate | Fixed rate related to the Order | Order.FeeRate + Order.Surcharge |

> **Warning:**
>
> Fee rates are fixed for the life of the Order and cannot be changed after approval. An Order can be cancelled before its DeliveryDate (see Order Cancellation).

Example: Order with OrderDate 10-09-2025 and a 12-month fee period.

- AccountNumber: 50012345-F12
- OrderId: 88888888801
- Currency: EUR
- OrderTotal: 1,000.00
- FeeRate: 1.50%

Dataset delivered for calculation as per 10/9/2026:

| OrderId | Currency | PeriodStart | PeriodEnd | BasisAmount | Fee kind | RoundingMode | Repeating Group | Tier no. | Threshold Amount | Fee Rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 88888888801 | EUR | 10/9/2025 | 10/9/2026 | 1000 | Flat | HalfUp2 | 1 | 1 | 0 | 1.50% |

## Output

For each line in the bulk request the fee is calculated and returned:

| **Output** | **Description** |
| --- | --- |
| Total amount positive fee | Sum of fees over all tiers with a positive amount |
| Total amount negative fee | Sum of fees over all tiers with a negative amount |
| Factor numerator | Number of days in the fee period |
| Factor denominator | Number of days in the year |
| **Repeating Group** | **The tiers. Minimum 1. For fee kind 'Flat' always 1.** |
| Tier no. | Sequence number, starting with 1 |
| Basis in this tier | Portion of the basis amount in this tier. For 'Flat' the whole amount is in tier 1 |
| Rate | Total rate applicable on this tier |
| Fee amount | Same sign as the rate because the basis is unsigned |

# Storage and ledger posting

1. Integration uses files written to a shared volume outside of the containers.
2. The PAY module consumes the calculated fee amount.
3. A bulk ledger posting is created: [3. Bulk Ledger Postings - Fees](./3-bulk-ledger-postings-fees.md)
4. The account that the fee is posted to is determined as follows:
   1. If Order.IsFeePrepaid = FALSE, then PaymentAccount = Order.BillingAccountNumber
   2. If Order.IsFeePrepaid = TRUE:
      - If DueDate does not equal Order.DeliveryDate, then PaymentAccount = Order.AccountNumber
      - If DueDate equals Order.DeliveryDate, then PaymentAccount = Order.BillingAccountNumber
5. After the ledger posting is created, FeeSchedule.Status changes to 'Processed'.

# Integration contracts (to be defined by development team)

- GetBulkFeeCalculationRequest
- FeeCalculationRequest
- GetBulkFeeCalculationResponse
- FeeCalculationResponse

# Non functional requirements

- At most 300 lines per request
- On average a request contains 40 OrderIds
- Execution takes place outside business hours
- Performance requirements: TBD
