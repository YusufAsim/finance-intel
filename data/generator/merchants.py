"""Merchant descriptors rendered in a point of sale style.

Descriptions imitate what a bank prints on a statement: an upper case
merchant name, a location and, for card transactions, a terminal number.
"""

from random import Random

GROCERY_MERCHANTS = (
    "MIGROS MMM ANKARA",
    "SOK MARKET ANKARA",
    "BIM BIRLESIK MAGAZALAR ANKARA",
    "CARREFOURSA CANKAYA",
    "A101 YENIMAHALLE",
)

DINING_MERCHANTS = (
    "STARBUCKS KIZILAY",
    "KAHVE DUNYASI TUNALI",
    "BURGER KING ANKAMALL",
    "SIMIT SARAYI BAHCELIEVLER",
    "DOMINOS PIZZA CAYYOLU",
)

ELECTRONICS_MERCHANTS = (
    "MEDIAMARKT ANKAMALL",
    "TEKNOSA CEPA",
    "VATAN BILGISAYAR ANKARA",
)

TRAVEL_MERCHANTS = (
    "THY BILET ISTANBUL",
    "PEGASUS HAVA TASIMACILIGI ISTANBUL",
    "BOOKING.COM AMSTERDAM",
)

HEALTH_MERCHANTS = (
    "ACIBADEM HASTANESI ANKARA",
    "ECZANE SIFA CANKAYA",
    "MEDICANA LABORATUVAR ANKARA",
)

# Merchants that never show up in the regular spending pattern. They are
# only used when an unusual merchant anomaly is planted.
FOREIGN_MERCHANTS = (
    "ALIEXPRESS HONG KONG",
    "STEAM GAMES LUXEMBOURG",
    "CASINO ROYAL VALLETTA",
)


def with_terminal(rng: Random, merchant: str) -> str:
    """Append a four digit terminal number to a card merchant."""
    return f"{merchant} {rng.randint(1000, 9999)}"


def pick(rng: Random, merchants: tuple[str, ...]) -> str:
    """Pick a merchant and render it with a terminal number."""
    return with_terminal(rng, rng.choice(merchants))
