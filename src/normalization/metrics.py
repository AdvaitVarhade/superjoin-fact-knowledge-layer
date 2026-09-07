from typing import Dict, List

CANONICAL_METRICS: Dict[str, List[str]] = {
    "revenue": [
        "revenue from operations",
        "total income",
        "total revenue",
        "revenue",
        "net sales",
        "sales",
        "topline",
        "revenues",
        "operating revenue",
        "turnover",
        "service revenue",
    ],
    "ebitda": [
        "adjusted ebitda",
        "ebitda",
        "operating profit",
        "operating ebitda",
        "ebit",
        "operating earnings",
    ],
    "express_shipments": [
        "express parcel shipments",
        "express parcel volume",
        "express shipments",
        "express parcel shipment volume",
        "shipment volume",
        "express parcels",
        "parcel volume",
        "parcel count",
        "packages delivered",
    ],
    "pin_codes_covered": [
        "pin codes covered",
        "pincodes",
        "pincode reach",
        "pin code reach",
        "pincodes covered",
        "active pin codes",
        "network reach pin codes",
    ],
    "gdp_growth": [
        "real gdp growth",
        "gdp growth rate",
        "gdp growth",
        "economic growth",
        "projected gdp growth",
        "gdp forecast",
    ],
    "cpi_inflation": [
        "headline inflation",
        "cpi inflation",
        "consumer price index inflation",
        "retail inflation",
        "headline cpi",
        "inflation forecast",
    ],
    "vehicle_deliveries": [
        "total vehicle deliveries",
        "deliveries",
        "model 3/y deliveries",
        "other models deliveries",
    ]
}

def canonicalize_metric(text: str) -> str:
    text_lower = text.lower().strip()
    for canonical, variations in CANONICAL_METRICS.items():
        for var in variations:
            if var in text_lower:
                return canonical
    return text_lower.replace(" ", "_")
