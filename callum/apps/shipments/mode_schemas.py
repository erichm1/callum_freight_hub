"""
Callum stores one Shipment model for every transport mode, with a `mode`
field plus a free-form `metadata` JSONField. This module documents and
validates the *expected* shape of that JSON per mode, so the flexibility
of a single table doesn't turn into an anything-goes payload.

Fields listed here are advisory (not database-enforced) — unknown extra
keys are always allowed, since partner gateways/transporters vary in what
they can supply. Only the fields marked required are validated on write.
"""

MODE_SCHEMAS = {
    "AIR": {
        "required": ["awb_number"],
        "fields": {
            "awb_number": "Air Waybill number",
            "flight_number": "Operating flight number",
            "carrier_iata": "IATA code of the operating airline",
            "origin_airport": "IATA airport code, e.g. JFK",
            "destination_airport": "IATA airport code, e.g. NRT",
            "pieces": "Number of pieces in the shipment",
            "chargeable_weight_kg": "Chargeable (dimensional) weight in kg",
        },
    },
    "SEA": {
        "required": ["bl_number"],
        "fields": {
            "bl_number": "Bill of Lading number",
            "vessel_name": "Name of the vessel",
            "voyage_number": "Voyage number",
            "container_number": "Container number (ISO 6346)",
            "container_type": "e.g. 20GP, 40HC, 40RF",
            "origin_port": "UN/LOCODE of the port of loading",
            "destination_port": "UN/LOCODE of the port of discharge",
            "is_fcl": "Boolean — full container load vs LCL",
        },
    },
    "LAND": {
        "required": ["waybill_number"],
        "fields": {
            "waybill_number": "Domestic/road waybill or CMR number",
            "plate_number": "Vehicle / trailer plate number",
            "driver_name": "Driver of record",
            "route": "Free-text route description",
            "border_crossing": "Border crossing point, if cross-border",
        },
    },
}


def validate_metadata(mode: str, metadata: dict) -> list:
    """Returns a list of human-readable errors (empty list = valid)."""
    schema = MODE_SCHEMAS.get(mode)
    if not schema:
        return [f"Unknown transport mode '{mode}'."]

    errors = []
    for required_field in schema["required"]:
        if not metadata.get(required_field):
            errors.append(f"'{required_field}' is required in metadata for {mode} shipments.")
    return errors
