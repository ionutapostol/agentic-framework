# SHP: Allocation — Store Unit Cost

## Feature Summary

Extend the `Shp.Allocation` entity with a new `UnitCost` field. When the shipment
allocation process allocates stock using parcels sourced from **LEDGER**
(normal path), store the unit cost from the LEDGER allocation response in
`UnitCost`. When parcels are sourced from **ERP** (legacy path),
`UnitCost` must be stored as `NULL`.

## Background

The allocation process is triggered through the SHP portal workflow:

1. A Shipment is created in the SHP portal (e.g. a multi-parcel shipment).
2. The "allocate stock" process is triggered for that shipment.
3. Allocation parcels can come from two sources:
   - **LEDGER** — the standard ledger system (normal path)
   - **ERP** — the legacy system (legacy path)

## Database Change

| Property | Value |
|---|---|
| Table | `Shp.Allocation` |
| New column | `UnitCost` (nullable decimal) |
| Source: LEDGER | Populate `UnitCost` from the LEDGER allocation response |
| Source: ERP | Store `UnitCost = NULL` |

## Acceptance Criteria

1. When allocation is determined with parcels from LEDGER, `UnitCost` in
   `Shp.Allocation` is populated with the value from the LEDGER allocation response.
2. When allocation is determined with parcels from ERP, `UnitCost`
   in `Shp.Allocation` is stored as `NULL`.

## Notes

- Although this is a backend/DB change, testing it requires creating a Shipment through
  the SHP portal and triggering the allocation process — use `template-shipment-portal.csv`.
