"""Carrier tracking URL abstraction and resolution."""

CARRIER_TRACKING_URLS = {
    'FedEx': 'https://www.fedex.com/fedextrack/?trknbr={tracking_code}',
    'UPS': 'https://www.ups.com/track?tracknum={tracking_code}',
    'USPS': 'https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_code}',
    'DHL': 'https://www.dhl.com/en/express/tracking.html?AWB={tracking_code}',
    'Standard Delivery': None,
}

def get_tracking_url(carrier: str, tracking_code: str) -> str | None:
    """Return external tracking URL for carrier and tracking code, if applicable."""
    template = CARRIER_TRACKING_URLS.get(carrier)
    if template:
        return template.format(tracking_code=tracking_code)
    return None
