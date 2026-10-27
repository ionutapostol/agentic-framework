# 1. Order Confirmation Posting

## General mapping (client side)

This document describes the confirmation posting of an Order. The posting is processed after approval and creation of the AccountNumber for the new Order.

## Create Single Posting Command

- Message type: `CreateSinglePostingCommand`

## Mapping (clean table)

| Entity / Input parameter | LEDGER description | Mapping from Order |
|--------------------------|--------------------|--------------------|
| Posting | The root of a posting (one instance only) | One instance only |
| Posting identifier | Uniquely identifies the ledger posting | `'ORD' + <DateTime> + AccountNumber + 'Confirm'` |
| Business type code | Code to characterize the posting | `'Sale'` |
| Description | Description of the posting | `'Order Confirmed <AccountNumber>'` |
| Is final | Indicates whether the posting is final (reversed/replaced if No) | `"Yes"` |
| Source | Token to identify the source (user or system) | `"ORD"` |
| Posting Group / Group type / Group reference / Group name | Grouping identification for multiple postings | leave out / n/a |

### Order Posting (one instance: the customer store of the order)

- Order posting type code: `'OrderOpen'`
- Case type code: `'ConfirmedOrder'`
- External reference: n/a
- Value date: `<ValueDate>` = OrderDate
- Posting date: `<PostingDate>` = BusinessDate
- Description (store language): `'Order Confirmed <AccountNumber>'`
- Store unique identifier: `<StoreNumber>`
- Store class: `<Store.StoreClassCode>`
- Store type: `<Store.StoreTypeCode>`

## Account Lines (2 instances per posting; 3 when ShippingFee > 0)

Each confirmation posting produces these account line instances:

1) Receivable line on the BillingAccount of the Order
- Quantity: total money amount (sum of child book currency amounts)
- Book currency ISO code: `Order.CurrencyISOCode`
- Unit price: `1` (money)
- Account unique identifier: `Order.AccountNumber`
- AccountTypeCode: `"R"` (Receivable)
- Attribution type code = `'GoodsTotal'`
- Source currency ISO code: `Order.CurrencyISOCode`
- Source currency amount: `(Order.OrderTotal - Order.ShippingFee) * sign +1` (rounded to currency decimals)
- Book currency amount: = Source currency amount

2) Revenue line on the BillingAccount (Receivable or Prepaid)
- Quantity: total money amount
- Book currency ISO code: `Order.CurrencyISOCode`
- Account unique identifier: `Order.BillingAccountNumber`
- AccountTypeCode: `"R"` or `"P"` depending on BillingAccountNumber
- Attribution type code = `'GoodsTotal'`
- Source currency ISO code: `Order.CurrencyISOCode`
- Source currency amount: `(Order.OrderTotal - Order.ShippingFee) * sign -1` (rounded)
- Book currency amount: = Source currency amount

3) Shipping line (only when `Order.ShippingFee > 0`)
- Account unique identifier: `Order.AccountNumber`
- AccountTypeCode: `"R"`
- Attribution type code = `'ShippingCharge'`
- Source currency amount: `Order.ShippingFee * sign +1` (rounded)
- Book currency amount: = Source currency amount
- When `Order.ShippingFee = 0`, no shipping line is created.
