"""Constants for the Mantova Ambiente integration."""

DOMAIN = "mantova_ambiente"

# Configuration keys
CONF_ZONE = "zone"
CONF_CACHE_HOURS = "cache_hours"
CONF_WASTE_CODES = "waste_codes"

# Default values
DEFAULT_CACHE_HOURS = 24
DEFAULT_SCAN_INTERVAL = 3600  # 1 hour in seconds

# API settings
API_BASE_URL = "https://www.mantovaambiente.it/api/recyclings"
API_ZONES_URL = "https://www.mantovaambiente.it/api/zones"
API_TIMEOUT = 10

# Attributes
ATTR_NEXT_DATES = "next_dates"
ATTR_WASTE_TYPE = "waste_type"
ATTR_ZONE = "zone"

# Waste types with their IDs and titles
WASTE_TYPES = {
    "6256": "Abiti",
    "3705": "Pannolini e pannoloni",
    "3581": "Carta",
    "3701": "Indifferenziato",
    "3704": "Organico",
    "3707": "Plastica",
    "3708": "Sfalci",
    "3710": "Vetro",
    "3702": "Ingombranti",
}