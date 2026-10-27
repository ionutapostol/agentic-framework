# ShopApp test-authoring domain reference

ShopApp is a fictional retail/e-commerce platform used as the example domain for this framework.
Replace the values below with your own product's modules, screens, and rules.

Read the applicable section before choosing navigation, Component, an EVENTBUS trigger, or
SHP-specific expected values. Current requirement/reference sources govern feature changes;
record conflicts using SKILL.md Step 1 rather than silently overriding those sources.

## Navigation

| Module | Menu path | Notes |
|---|---|---|
| Orders | `ORD00, Orders → ORD01, Order Portal` | New opens the Order Entry screen in a new tab |
| Payments | `PAY00, Payments → [screen name]` | Use the requirement's screen |
| Shipments | `SHP00, Shipments → SHP01, Shipment Portal` | Locate a shipment, then open Details as a separate step |
| Shipments — carrier messages | `SHP00, Shipments → SHP08, Search Carrier Messages → SHPM02, Search Carrier Message` | Search stored carrier messages |

Use these paths rather than legacy identifiers such as `ORDER02` / `OrderOrder02`.
Clicking New opens an entry screen; name that screen in the expected result.

## Component

The CSV Component identifies the module whose behavior is the primary subject, not its caller.
For cross-module scenarios, choose that primary module. If ownership is unclear, clarify it;
the ADO import requires a nonempty Component.

| Value | Module | Use for |
|---|---|---|
| `ORD` | Orders | Order portal entry/modify/view flows |
| `PAY` | Payments | Payment capture, fees, settlement |
| `SHP` | Shipments | Shipment screens and services |
| `LEDGER` | Ledger | Description translation, ledger postings |
| `RFD` | Refunds | Refund flows and the Refund Voucher service |
| `INV` | Invoices | Invoice flows and services |
| `EVENTBUS` | Event Bus | Integration message submission |

Example: verifying payment-fee calculation uses PAY even if an order flow triggers it.
Verifying that ORD stores the result uses ORD.

## EVENTBUS integration

Carrier and other integration messages are submitted through:

```text
POST https://<eventbus-host>:<port>/events
```

Use this trigger for service-level tests where required. Resolve the host from environment
configuration at execution time; keep placeholders in test documentation.

## Carrier message storage

- Messages: `[CarrierExt].[ShipmentMessageXml]`.
- Parcel event XML: `[CarrierExt].[ParcelEventXml]`;
  this distinct table is the target of data-retention jobs.
- Parcel event codes: `PKD`, `DLV`, `RTN`, `LST`, `DMG`.
- Search stored messages using SHPM02 (Navigation above).

### Return-to-stock quantity signs

Stock-ledger quantity for a returned parcel (`RTN`) posting:

| Code | Location | Quantity |
|---|---|---|
| `RTN` (customer return accepted) | Customer-held | Minus quantity |
| `RTN` | Warehouse | Positive quantity |
| `LST` (parcel lost in transit) | Customer-held | No posting |
| `LST` | Write-off | Positive quantity |

## SHP allocation

For backend/DB changes to `Shp.Allocation` or `Shp.Parcel` triggered through the portal,
use `template-shipment-portal.csv`. Execute Login (Shared Steps 1000), create a shipment (for example
a split shipment across two warehouses), trigger determine allocation with the specified stock source,
query the affected DB field using a correlation key, and assert its requirement-backed value.

When behavior differs by source, author separate LEDGER and ERP cases. The legacy
system's name is ERP, not ShopAppClassic. See
[the reviewed allocation example](golden-example-shipment-allocation.csv).

## SHP individual reversal: warehouse selection

Recorded source: Confluence "Shipment Reversals", DOCS, page 123456 (fictional).

- Default `ReturnWarehouseCode`: the warehouse whose `WarehouseTag` is `Primary`
  (the configured primary warehouse).
- Exception: `ShipmentClass = DROPSHIP` and
  `ShipmentCategory.DefaultReturnSiteId <> NULL` use `DefaultReturnSiteId`
  (category-based ID, for example 7/9).
- For `PhaseCode = 'Closing'` and `IsFinalParcel = 1`, use category
  `BulkFreight` rather than `Standard` for this lookup. A final-parcel reversal
  therefore falls back to the configured primary warehouse.

For a PBI changing the default, cover the changed non-Closing path and the
Closing final-parcel exception according to the current requirement.
Trigger via SHP01: locate a processed shipment, open Details, reverse the individual
parcel. Use `template-shipment-portal.csv`.
