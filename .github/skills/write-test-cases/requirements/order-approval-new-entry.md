# Order Approval - new entry

> **Short description of Approval of Order**
>
> By using the available action button 'To Review' in the Portal, a user can approve an Order.

---

## Table of Contents

- [How to Start](#how-to-start)
- [Approval functionality](#approval-functionality)

---

## How to Start

- The Order Approval is started from the [Portal](https://your-confluence.example.com/spaces/DOCS/pages/123456/Order+Portal) by clicking the Row Action button **"To Review"**

The screen is presented as a popup in front of the Order Portal and not as a separate tab.

---

## Approval functionality

1. An Order is given the status **'PendingReview'** in the event:
   1. 'ShippingFee' of a new order > 0.00

2. An Order with status **'PendingReview'** can be displayed by selecting UI button **'Pending Versions'** in the Portal.

3. The user is allowed to approve the Order if this is **another user** than the one who entered or cancelled the Order. If the user is not allowed, the **'Approve'** button is disabled. See also [Order Portal — Row Action buttons](https://your-confluence.example.com/spaces/DOCS/pages/123456/Order+Portal) where the 'Approve' button is enabled or disabled.

4. When selecting the **'To Review'** button in the portal, a screen is opened with the full details of the Order. Layout is similar to that of the view with the exception of the UI buttons. Details are displayed as read only.

5. When the **'Approve'** button is selected, the following confirmation is asked: _"**Are you sure you want to approve the Order?**"_
   1. If confirmed:
      - A service call to INV is generated to create an AccountNumber in INV and return it to the Order module. See [Create and Return Invoice Account to Order](https://your-confluence.example.com/spaces/DOCS/pages/123458/Create+and+Return+Invoice+Account).
      - The AccountNumber received from INV is stored in the Order database.
      - After receiving and storing the AccountNumber, the status changes to **'Placed'** (OrderDate is always equal to CurrentDate for a new order).
      - A ledger posting to LEDGER is created. See [Order Confirmation Posting](https://your-confluence.example.com/spaces/DOCS/pages/123459/Order+Confirmation+Posting).

6. **Rejection:**
   - **New Order:** When the **'Reject'** button is selected, the following confirmation is asked: _"**Are you sure you want to reject the Order?**"_. If confirmed:
     - Status of the Order changes to **'Rejected'**.
     - A rejected order can be accessed under the UI button **'All versions'**.
     - No AccountNumber is requested from INV and no ledger posting is created.

---

> **Note:** UI mockups for this feature are not included in this export.
