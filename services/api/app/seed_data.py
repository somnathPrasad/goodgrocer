"""Curated development catalogue for a representative urban Indian kirana.

Prices are plausible demo values in rupees, not a live price feed. Product and
brand names are included only to make local development data recognisable.
"""

import re
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class SeedVariant:
    name: str
    mrp: Decimal
    selling_price: Decimal
    available: bool = True


@dataclass(frozen=True)
class SeedProduct:
    name: str
    slug: str
    brand: str
    categories: tuple[str, ...]
    description: str
    variants: tuple[SeedVariant, ...]
    available: bool = True


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def v(name: str, mrp: str, price: str | None = None, available: bool = True):
    return SeedVariant(name, Decimal(mrp), Decimal(price or mrp), available)


def p(
    name: str,
    brand: str,
    category: str,
    variants: tuple[SeedVariant, ...],
    *,
    slug: str | None = None,
    also: tuple[str, ...] = (),
    description: str | None = None,
    available: bool = True,
):
    category_name = next(label for label, key in CATEGORIES if key == category)
    return SeedProduct(
        name=name,
        slug=slug or _slug(name),
        brand=brand,
        categories=(category, *also),
        description=description
        or f"{name}, a commonly stocked {category_name.lower()} item for everyday households.",
        variants=variants,
        available=available,
    )


BRANDS = (
    ("Local Produce", "local-produce"),
    ("Loose Staples", "loose-staples"),
    ("Amul", "amul"),
    ("Mother Dairy", "mother-dairy"),
    ("Aashirvaad", "aashirvaad"),
    ("India Gate", "india-gate"),
    ("Daawat", "daawat"),
    ("Tata Sampann", "tata-sampann"),
    ("Tata Salt", "tata-salt"),
    ("Fortune", "fortune"),
    ("Saffola", "saffola"),
    ("Everest", "everest"),
    ("MDH", "mdh"),
    ("Catch", "catch"),
    ("Red Label", "red-label"),
    ("Tata Tea", "tata-tea"),
    ("Nescafe", "nescafe"),
    ("Bru", "bru"),
    ("Parle", "parle"),
    ("Britannia", "britannia"),
    ("Haldiram's", "haldirams"),
    ("Lay's", "lays"),
    ("Kurkure", "kurkure"),
    ("Maggi", "maggi"),
    ("Kissan", "kissan"),
    ("Real", "real"),
    ("Coca-Cola", "coca-cola"),
    ("Thums Up", "thums-up"),
    ("Surf Excel", "surf-excel"),
    ("Rin", "rin"),
    ("Vim", "vim"),
    ("Harpic", "harpic"),
    ("Lizol", "lizol"),
    ("Dettol", "dettol"),
    ("Lifebuoy", "lifebuoy"),
    ("Lux", "lux"),
    ("Dove", "dove"),
    ("Clinic Plus", "clinic-plus"),
    ("Colgate", "colgate"),
    ("Pepsodent", "pepsodent"),
    ("Parachute", "parachute"),
    ("Whisper", "whisper"),
    ("Pampers", "pampers"),
    ("Goodknight", "goodknight"),
    ("Cycle", "cycle"),
)

LEGACY_SEED_BRANDS = ("town-harvest", "daily-dairy", "pantry-co")


CATEGORIES = (
    ("Fresh fruits & vegetables", "fresh-produce"),
    ("Milk, dairy, eggs & bread", "dairy-breakfast"),
    ("Atta, rice & grains", "rice-grains"),
    ("Dals, pulses, salt & sugar", "dals-pulses"),
    ("Cooking oil & ghee", "oil-ghee"),
    ("Masalas & cooking essentials", "masala-essentials"),
    ("Tea, coffee & beverages", "tea-beverages"),
    ("Biscuits, snacks & sweets", "snacks-drinks"),
    ("Noodles, sauces & packaged food", "packaged-food"),
    ("Bath, hair & oral care", "personal-care"),
    ("Laundry & dishwashing", "laundry-dishwash"),
    ("Home cleaning & pest control", "home-care"),
    ("Baby & feminine care", "baby-feminine-care"),
    ("Puja & household needs", "puja-household"),
)

LEGACY_SEED_CATEGORIES = ("pantry-essentials",)


PRODUCTS = (
    # Fresh produce: high-frequency kirana basket builders.
    p(
        "Tomatoes",
        "local-produce",
        "fresh-produce",
        (v("500 g", "30", "25"), v("1 kg", "60", "48")),
        slug="tomatoes",
    ),
    p(
        "Bananas",
        "local-produce",
        "fresh-produce",
        (v("Pack of 6", "55", "48"), v("1 dozen", "105", "90")),
        slug="bananas",
    ),
    p(
        "Potatoes",
        "local-produce",
        "fresh-produce",
        (v("1 kg", "45", "40"), v("2 kg", "88", "75")),
        slug="potatoes",
    ),
    p(
        "Onions",
        "local-produce",
        "fresh-produce",
        (v("1 kg", "50", "44"), v("2 kg", "98", "82")),
        slug="onions",
    ),
    p(
        "Green chillies",
        "local-produce",
        "fresh-produce",
        (v("100 g", "18", "15"), v("250 g", "40", "35")),
    ),
    p("Coriander leaves", "local-produce", "fresh-produce", (v("1 bunch", "15", "12"),)),
    p("Ginger", "local-produce", "fresh-produce", (v("100 g", "28", "24"), v("250 g", "65", "55"))),
    p(
        "Garlic",
        "local-produce",
        "fresh-produce",
        (v("250 g", "60", "52"), v("500 g", "115", "98")),
    ),
    p("Lemons", "local-produce", "fresh-produce", (v("Pack of 4", "35", "30"),)),
    p(
        "Apples",
        "local-produce",
        "fresh-produce",
        (v("500 g", "140", "125"), v("1 kg", "275", "240")),
    ),
    p("Oranges", "local-produce", "fresh-produce", (v("1 kg", "140", "125"),)),
    p(
        "Coconut",
        "local-produce",
        "fresh-produce",
        (v("1 pc", "45", "40"),),
        also=("puja-household",),
    ),
    # Chilled and breakfast basics.
    p(
        "Amul Taaza toned milk",
        "amul",
        "dairy-breakfast",
        (v("500 ml pouch", "29"), v("1 L pouch", "57")),
        slug="fresh-milk",
    ),
    p(
        "Amul Masti dahi",
        "amul",
        "dairy-breakfast",
        (v("400 g pouch", "35"), v("1 kg pouch", "77")),
        slug="natural-curd",
    ),
    p(
        "Amul fresh paneer",
        "amul",
        "dairy-breakfast",
        (v("200 g", "95", "90"), v("500 g", "240", "225")),
        slug="paneer",
        available=False,
    ),
    p(
        "Amul pasteurised butter",
        "amul",
        "dairy-breakfast",
        (v("100 g carton", "63"), v("500 g carton", "310", "309")),
    ),
    p("Amul cheese slices", "amul", "dairy-breakfast", (v("200 g pack", "145", "140"),)),
    p(
        "Mother Dairy dairy whitener",
        "mother-dairy",
        "dairy-breakfast",
        (v("200 g pouch", "120", "115"), v("500 g pouch", "285", "270")),
    ),
    p(
        "Fresh white eggs",
        "local-produce",
        "dairy-breakfast",
        (v("Pack of 6", "48", "44"), v("Pack of 12", "92", "84")),
    ),
    p("Britannia milk bread", "britannia", "dairy-breakfast", (v("400 g loaf", "50", "48"),)),
    p("Britannia brown bread", "britannia", "dairy-breakfast", (v("400 g loaf", "55", "52"),)),
    # Monthly staples: both small top-up and family packs.
    p(
        "Aashirvaad whole wheat atta",
        "aashirvaad",
        "rice-grains",
        (v("1 kg", "68", "64"), v("5 kg", "306", "274"), v("10 kg", "654", "575")),
        slug="whole-wheat-atta",
        also=("dals-pulses",),
    ),
    p("Aashirvaad multigrains atta", "aashirvaad", "rice-grains", (v("5 kg", "412", "342"),)),
    p(
        "India Gate Rozzana basmati rice",
        "india-gate",
        "rice-grains",
        (v("1 kg", "155", "142"), v("5 kg", "760", "699")),
        slug="basmati-rice",
        also=("dals-pulses",),
    ),
    p(
        "Daawat Rozana gold basmati rice",
        "daawat",
        "rice-grains",
        (v("1 kg", "145", "132"), v("5 kg", "710", "655")),
    ),
    p(
        "Sona masoori rice",
        "loose-staples",
        "rice-grains",
        (v("1 kg", "70", "62"), v("5 kg", "340", "295"), v("10 kg", "670", "570")),
    ),
    p(
        "Kolam rice",
        "loose-staples",
        "rice-grains",
        (v("1 kg", "82", "74"), v("5 kg", "400", "350")),
    ),
    p(
        "Poha thick",
        "loose-staples",
        "rice-grains",
        (v("500 g", "48", "42"), v("1 kg", "92", "80")),
    ),
    p("Sooji rava", "aashirvaad", "rice-grains", (v("500 g", "42", "39"), v("1 kg", "76", "69"))),
    p("Besan", "tata-sampann", "rice-grains", (v("500 g", "82", "75"), v("1 kg", "158", "145"))),
    p("Maida", "aashirvaad", "rice-grains", (v("500 g", "38", "35"), v("1 kg", "72", "66"))),
    p(
        "Tata Sampann toor dal",
        "tata-sampann",
        "dals-pulses",
        (v("500 g", "105", "96"), v("1 kg", "205", "185")),
        slug="toor-dal",
        also=("rice-grains",),
    ),
    p(
        "Tata Sampann moong dal",
        "tata-sampann",
        "dals-pulses",
        (v("500 g", "105", "96"), v("1 kg", "205", "188")),
    ),
    p(
        "Chana dal",
        "loose-staples",
        "dals-pulses",
        (v("500 g", "62", "55"), v("1 kg", "120", "105")),
    ),
    p(
        "Masoor dal",
        "loose-staples",
        "dals-pulses",
        (v("500 g", "72", "65"), v("1 kg", "140", "125")),
    ),
    p(
        "Urad dal split",
        "loose-staples",
        "dals-pulses",
        (v("500 g", "92", "84"), v("1 kg", "180", "160")),
    ),
    p(
        "Kabuli chana",
        "loose-staples",
        "dals-pulses",
        (v("500 g", "90", "80"), v("1 kg", "175", "155")),
    ),
    p(
        "Rajma chitra",
        "loose-staples",
        "dals-pulses",
        (v("500 g", "95", "86"), v("1 kg", "185", "165")),
    ),
    p("Tata iodised salt", "tata-salt", "dals-pulses", (v("1 kg pouch", "28"),), slug="salt"),
    p("Sugar", "loose-staples", "dals-pulses", (v("1 kg", "55", "50"), v("5 kg", "270", "240"))),
    p("Jaggery", "loose-staples", "dals-pulses", (v("500 g", "55", "48"), v("1 kg", "105", "92"))),
    p(
        "Fortune Sunlite sunflower oil",
        "fortune",
        "oil-ghee",
        (v("1 L pouch", "180", "165"), v("5 L jar", "890", "810")),
        slug="sunflower-oil",
    ),
    p("Fortune kachi ghani mustard oil", "fortune", "oil-ghee", (v("1 L bottle", "155", "142"),)),
    p("Fortune filtered groundnut oil", "fortune", "oil-ghee", (v("1 L pouch", "205", "188"),)),
    p(
        "Saffola Gold blended oil",
        "saffola",
        "oil-ghee",
        (v("1 L pouch", "225", "205"), v("5 L jar", "1110", "995")),
    ),
    p(
        "Amul pure ghee",
        "amul",
        "oil-ghee",
        (v("500 ml carton", "410", "399"), v("1 L carton", "820", "799")),
    ),
    # Spices and cooking helpers.
    p(
        "Everest turmeric powder",
        "everest",
        "masala-essentials",
        (v("100 g", "42", "39"), v("200 g", "80", "74")),
    ),
    p(
        "Everest red chilli powder",
        "everest",
        "masala-essentials",
        (v("100 g", "58", "54"), v("200 g", "112", "104")),
    ),
    p(
        "Everest coriander powder",
        "everest",
        "masala-essentials",
        (v("100 g", "38", "35"), v("200 g", "72", "66")),
    ),
    p("MDH garam masala", "mdh", "masala-essentials", (v("100 g", "96", "89"),)),
    p("MDH chana masala", "mdh", "masala-essentials", (v("100 g", "90", "84"),)),
    p("Everest kitchen king masala", "everest", "masala-essentials", (v("100 g", "92", "85"),)),
    p("Catch cumin seeds", "catch", "masala-essentials", (v("100 g", "68", "62"),)),
    p(
        "Mustard seeds",
        "loose-staples",
        "masala-essentials",
        (v("100 g", "25", "22"), v("250 g", "58", "50")),
    ),
    p("Tamarind seedless", "loose-staples", "masala-essentials", (v("200 g", "70", "62"),)),
    p(
        "Kissan fresh tomato ketchup",
        "kissan",
        "masala-essentials",
        (v("500 g pouch", "85", "79"), v("850 g bottle", "160", "145")),
        also=("packaged-food",),
    ),
    # Drinks and quick foods.
    p(
        "Red Label tea",
        "red-label",
        "tea-beverages",
        (v("250 g carton", "160", "155"), v("500 g carton", "320", "298"), v("1 kg", "610", "555")),
        slug="tea",
        also=("dairy-breakfast",),
    ),
    p(
        "Tata Tea Premium",
        "tata-tea",
        "tea-beverages",
        (v("250 g", "145", "135"), v("500 g", "285", "265")),
    ),
    p(
        "Nescafe Classic instant coffee",
        "nescafe",
        "tea-beverages",
        (v("50 g jar", "185", "175"), v("100 g jar", "365", "345")),
    ),
    p(
        "Bru instant coffee",
        "bru",
        "tea-beverages",
        (v("50 g pouch", "120", "112"), v("200 g pouch", "420", "357")),
    ),
    p("Real mixed fruit juice", "real", "tea-beverages", (v("1 L carton", "130", "118"),)),
    p(
        "Real mango juice",
        "real",
        "tea-beverages",
        (v("1 L carton", "125", "112"),),
        slug="mango-juice",
    ),
    p(
        "Coca-Cola",
        "coca-cola",
        "tea-beverages",
        (v("250 ml bottle", "20"), v("750 ml bottle", "45"), v("2.25 L bottle", "105", "99")),
        also=("snacks-drinks",),
    ),
    p(
        "Thums Up",
        "thums-up",
        "tea-beverages",
        (v("250 ml bottle", "20"), v("750 ml bottle", "45"), v("2.25 L bottle", "105", "99")),
        also=("snacks-drinks",),
    ),
    p(
        "Parle-G glucose biscuits",
        "parle",
        "snacks-drinks",
        (v("79 g pack", "10"), v("250 g pack", "25"), v("800 g pack", "90", "85")),
        slug="biscuits",
        also=("dairy-breakfast",),
    ),
    p(
        "Britannia Marie Gold biscuits",
        "britannia",
        "snacks-drinks",
        (v("250 g pack", "40", "38"), v("950 g pack", "140", "124")),
    ),
    p(
        "Britannia Good Day cashew cookies",
        "britannia",
        "snacks-drinks",
        (v("100 g pack", "25", "23"), v("600 g family pack", "150", "138")),
    ),
    p("Parle Monaco biscuits", "parle", "snacks-drinks", (v("200 g pack", "40", "37"),)),
    p(
        "Haldiram's roasted peanuts",
        "haldirams",
        "snacks-drinks",
        (v("200 g pack", "55", "50"), v("400 g family pack", "105", "95")),
        slug="roasted-peanuts",
    ),
    p(
        "Haldiram's aloo bhujia",
        "haldirams",
        "snacks-drinks",
        (v("200 g pack", "55", "50"), v("400 g pack", "110", "99")),
    ),
    p("Haldiram's moong dal", "haldirams", "snacks-drinks", (v("200 g pack", "55", "50"),)),
    p(
        "Lay's India's Magic Masala",
        "lays",
        "snacks-drinks",
        (v("48 g pack", "20"), v("90 g pack", "50", "47")),
    ),
    p(
        "Kurkure Masala Munch",
        "kurkure",
        "snacks-drinks",
        (v("75 g pack", "20"), v("166 g pack", "50", "47")),
    ),
    p(
        "Maggi 2-Minute masala noodles",
        "maggi",
        "packaged-food",
        (
            v("70 g pack", "15"),
            v("280 g pack of 4", "60", "58"),
            v("560 g pack of 8", "120", "114"),
        ),
    ),
    p("Maggi masala-ae-magic", "maggi", "packaged-food", (v("72 g pack of 12", "60", "55"),)),
    p(
        "Kissan mixed fruit jam",
        "kissan",
        "packaged-food",
        (v("200 g jar", "85", "80"), v("500 g jar", "190", "175")),
        also=("dairy-breakfast",),
    ),
    p("Kissan chilli tomato sauce", "kissan", "packaged-food", (v("500 g pouch", "90", "84"),)),
    # Non-food FMCG is a core kirana shelf, especially compact packs.
    p(
        "Lifebuoy total soap",
        "lifebuoy",
        "personal-care",
        (v("100 g bar", "38", "36"), v("Pack of 4", "152", "138")),
    ),
    p(
        "Lux rose soap",
        "lux",
        "personal-care",
        (v("100 g bar", "40", "38"), v("Pack of 4", "160", "145")),
    ),
    p(
        "Dove cream beauty bathing bar",
        "dove",
        "personal-care",
        (v("100 g bar", "68", "64"), v("Pack of 3", "204", "190")),
    ),
    p(
        "Dettol original soap",
        "dettol",
        "personal-care",
        (v("100 g bar", "42", "40"), v("Pack of 4", "168", "152")),
    ),
    p(
        "Clinic Plus strong & long shampoo",
        "clinic-plus",
        "personal-care",
        (v("6 ml sachet", "2"), v("175 ml bottle", "120", "110"), v("340 ml bottle", "220", "199")),
    ),
    p("Dove daily shine shampoo", "dove", "personal-care", (v("180 ml bottle", "210", "195"),)),
    p(
        "Colgate Strong Teeth toothpaste",
        "colgate",
        "personal-care",
        (v("100 g", "72", "68"), v("200 g", "135", "125")),
    ),
    p(
        "Pepsodent Germicheck toothpaste",
        "pepsodent",
        "personal-care",
        (v("100 g", "70", "65"), v("200 g", "130", "120")),
    ),
    p(
        "Colgate zigzag toothbrush",
        "colgate",
        "personal-care",
        (v("1 pc", "35", "32"), v("Pack of 3", "105", "92")),
    ),
    p(
        "Parachute coconut oil",
        "parachute",
        "personal-care",
        (v("100 ml bottle", "50", "47"), v("300 ml bottle", "145", "135")),
    ),
    p(
        "Surf Excel Easy Wash powder",
        "surf-excel",
        "laundry-dishwash",
        (v("80 g pouch", "10"), v("500 g", "78", "73"), v("1 kg", "155", "145")),
    ),
    p("Surf Excel detergent bar", "surf-excel", "laundry-dishwash", (v("145 g bar", "20", "19"),)),
    p(
        "Rin detergent bar",
        "rin",
        "laundry-dishwash",
        (v("250 g bar", "25", "23"), v("Pack of 4", "100", "90")),
    ),
    p(
        "Vim lemon dishwash bar",
        "vim",
        "laundry-dishwash",
        (v("200 g bar", "20", "19"), v("Pack of 4", "80", "72")),
    ),
    p(
        "Vim lemon dishwash gel",
        "vim",
        "laundry-dishwash",
        (v("250 ml bottle", "58", "54"), v("500 ml bottle", "115", "105")),
    ),
    p(
        "Harpic Power Plus toilet cleaner",
        "harpic",
        "home-care",
        (v("500 ml bottle", "105", "98"), v("1 L bottle", "205", "188")),
    ),
    p(
        "Lizol citrus floor cleaner",
        "lizol",
        "home-care",
        (v("500 ml bottle", "105", "98"), v("1 L bottle", "205", "188")),
    ),
    p(
        "Dettol antiseptic liquid",
        "dettol",
        "home-care",
        (v("125 ml bottle", "75", "70"), v("550 ml bottle", "235", "220")),
    ),
    p(
        "Goodknight Gold Flash refill",
        "goodknight",
        "home-care",
        (v("45 ml refill", "85", "80"), v("Machine + refill", "110", "102")),
    ),
    p("Garbage bags medium", "loose-staples", "home-care", (v("Pack of 30", "85", "75"),)),
    p(
        "Whisper Choice Ultra pads",
        "whisper",
        "baby-feminine-care",
        (v("Pack of 6", "45", "42"), v("Pack of 20", "160", "148")),
    ),
    p(
        "Pampers baby-dry pants medium",
        "pampers",
        "baby-feminine-care",
        (v("Pack of 9", "135", "125"), v("Pack of 28", "399", "370")),
    ),
    p("Cycle three-in-one agarbatti", "cycle", "puja-household", (v("100 g pack", "65", "60"),)),
    p("Cotton wicks", "loose-staples", "puja-household", (v("Pack of 100", "35", "30"),)),
    p("Camphor tablets", "cycle", "puja-household", (v("50 g pack", "75", "68"),)),
    p("Matchbox", "loose-staples", "puja-household", (v("Pack of 10", "20", "18"),)),
    p("Aluminium foil", "loose-staples", "puja-household", (v("9 m roll", "75", "68"),)),
)
