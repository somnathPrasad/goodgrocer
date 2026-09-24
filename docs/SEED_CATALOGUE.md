# Development catalogue seed

The development seed is a representative national baseline for a small-to-medium
urban Indian kirana. A real store's assortment varies by state, neighbourhood,
season, distributor relationships and available refrigeration, so this is not a
claim that every kirana stocks every row.

## Research basis

The seed was reviewed on 24 September 2026 against:

- [McKinsey, *The state of grocery retail in India*](https://www.mckinsey.com/industries/retail/our-insights/the-state-of-grocery-retail-in-india),
  especially its finding that staples and fresh products dominate grocery and
  that potatoes, seasonal fruit and loose flour/rice are important basket items.
- [USDA Foreign Agricultural Service, *India Retail Foods*](https://apps.fas.usda.gov/newgainapi/api/report/downloadreportbyfilename?filename=Retail+Foods_New+Delhi_India_7-17-2019.pdf),
  for the role, size and distributor-led assortment of traditional kirana stores.
- [NielsenIQ's Q1 2025 India FMCG snapshot](https://nielseniq.com/global/en/insights/analysis/2025/fmcg-growth-momentum-shifts-rural-india-and-small-players-take-charge/),
  which notes continued demand for smaller affordable packs and strong home and
  personal-care volume growth.
- Current BigBasket catalogue pages for commonly available product names, pack
  sizes and price-shaped demo values, including
  [atta, salt, oil, rice, tea and biscuits](https://www.bigbasket.com/ss/grocery-shop/),
  [Aashirvaad staples](https://www.bigbasket.com/pb/aashirvaad/foodgrains-oil-masala/),
  [Amul butter](https://www.bigbasket.com/pd/104864/amul-butter-pasteurised-500-g-carton/),
  and [Surf Excel laundry products](https://bbsaathi.bigbasket.com/pb/surf-excel/).

The resulting mix gives greatest depth to fresh produce, grains, pulses, cooking
essentials and small everyday FMCG packs, while still including dairy, breakfast,
snacks, drinks, instant food, personal care, home care, feminine/baby care and
puja/household needs.

## Data policy

- Product names and pack sizes are realistic development fixtures. Brand names
  remain the property of their owners and do not imply endorsement.
- MRP and selling prices are plausible rupee values for UI, quote and checkout
  testing. They are not current prices and must not be promoted to production.
- The seed is idempotent. It updates records identified by its stable slugs,
  deactivates obsolete variants instead of deleting possibly referenced rows,
  and preserves unrelated products created by an owner.
- The seed remains explicitly disabled in production.
