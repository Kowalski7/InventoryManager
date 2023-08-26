<h3>Thresholds</h3>
<b>Restock (in days)</b>: if a lot's remaining days before expiry are less or equal to this value, a <i>Restock</i> suggestion will be generated for that lot.<br>
<b>Price increase/decrease</b>: these values are used internally by the suggestion algorithm to determine when a suggestion should be made. A lower value for the price increase (and a higher value for the price decrease) will determine a higher sensitivity for suggestions.
<h3>Multipliers</h3>
These values are used within the suggestion algorithm to determine the new price in case of price increase and price decrease suggestion types. A higher value represents a more drastic change in pricing.
<h3>Automation</h3>
Some features of the platform can take extended periods of time to complete. In order to avoid interruption during the day, these tasks can be scheduled to run automatically outside of the working hours.<br>
<b>Generate recommandations</b>: This task will generate the recommendations visible on the main page of this app. They can take some time to generate depending of the amount of transactions of the store and the number of inventory items.<br>
<b>Inventory cleanup</b>: After an inventory item remains without any items in stock, it can be moved in the "Archive" in order to avoid generating further suggestions for it. It is recommended to schedule this task after the <b>Generate recommendations</b> task in order to still receive <i>Restock</i> notifications the next day for items that have 0 items left in the lot.