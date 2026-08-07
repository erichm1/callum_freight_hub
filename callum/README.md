# Callum — Freight Gateway Hub

Callum is a multi-modal freight gateway: the hub that sits between many
**transporters** (air, sea, land carriers) and many **partner gateways**,
exposing a REST API for integrations and a Bootstrap 5.3 console for
staff operations.

## Stack

- **Backend:** Python, Django 5, Django REST Framework
- **API docs:** drf-spectacular (OpenAPI schema + Swagger UI)
- **Frontend:** Django templates + Bootstrap 5.3 (server-rendered console, no build step)
- **DB:** SQLite by default (swap to Postgres for production — see `.env.example`)

## Design decisions (per your answers)

- **One `Shipment` model for all modes.** A `mode` field (`AIR` / `SEA` / `LAND`)
  plus a `metadata` JSONField hold mode-specific data (AWB number & flight for
  air; BL number, vessel, container for sea; waybill & plate for land). This
  keeps routing/status/tracking logic mode-agnostic while staying flexible for
  partner-specific fields — see `apps/shipments/mode_schemas.py` for the
  documented (and validated) shape of metadata per mode.
- **Integration API + console together, both minimal-but-real.** The DRF API
  under `/api/v1/` is what transporters and partner gateways call; the
  Bootstrap console under `/` is what your ops team uses to watch the network.

## Project layout

```
callum/
├── config/                  # settings, root urls, wsgi/asgi
├── apps/
│   ├── core/                 # Partner (API key) model, auth, audit log
│   ├── gateways/              # Gateway model — Callum + partner gateways
│   ├── transporters/          # Transporter model (carriers per mode)
│   ├── shipments/              # Shipment + ShipmentEvent + DRF API
│   │   └── api/                 # serializers, views, urls, filters, permissions
│   └── dashboard/              # Bootstrap console views/urls
├── templates/callum/         # base.html, home, shipment list/detail, login
└── static/css/custom.css     # design tokens & components
```

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo_data     # optional: one shipment per mode + sample partners
python manage.py runserver
```

Then visit:
- `http://localhost:8000/` — console (log in with your superuser)
- `http://localhost:8000/admin/` — Django admin (manage Gateways, Transporters, Partner API keys)
- `http://localhost:8000/api/docs/` — Swagger UI for the integration API

## Integration API

All partner-facing endpoints live under `/api/v1/`. Transporters and partner
gateways authenticate with a static key issued from **Admin → Core → Partners**,
sent as a header:

```
X-Callum-Api-Key: callum_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Key endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/shipments/` | List shipments (filter by `mode`, `status`, `origin_gateway`, `destination_gateway`, `transporter`, `eta_after`, `eta_before`) |
| `POST` | `/api/v1/shipments/` | Create a shipment (any mode) |
| `GET` | `/api/v1/shipments/{reference}/` | Retrieve one shipment |
| `PATCH` | `/api/v1/shipments/{reference}/` | Update a shipment |
| `GET` | `/api/v1/shipments/{reference}/events/` | Full tracking timeline |
| `POST` | `/api/v1/shipments/{reference}/events/` | Append a tracking event (updates shipment status) |
| `GET` | `/api/v1/shipments/modes/` | Describes the required metadata fields per mode |
| `GET` | `/api/v1/gateways/` | List gateways in the network |
| `GET` | `/api/v1/transporters/` | List registered transporters |

### Example: create an air shipment

```bash
curl -X POST http://localhost:8000/api/v1/shipments/ \
  -H "X-Callum-Api-Key: $CALLUM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
        "mode": "AIR",
        "origin_gateway": 1,
        "destination_gateway": 3,
        "transporter": 1,
        "shipper_name": "Acme Exports",
        "consignee_name": "Nordic Retail GmbH",
        "weight_kg": "420.00",
        "pieces": 12,
        "metadata": {
          "awb_number": "020-12345670",
          "flight_number": "SL204",
          "origin_airport": "MIA",
          "destination_airport": "HAM"
        },
        "eta": "2026-08-10T14:00:00Z"
      }'
```

### Example: push a tracking update

```bash
curl -X POST http://localhost:8000/api/v1/shipments/CLM-ABCDEF1234/events/ \
  -H "X-Callum-Api-Key: $CALLUM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"status": "AT_GATEWAY", "location": "HAM Gateway", "description": "Cleared inbound customs"}'
```

`metadata` is validated per mode against `apps/shipments/mode_schemas.py`
(e.g. `SEA` requires `bl_number`, `AIR` requires `awb_number`, `LAND`
requires `waybill_number`) — extra partner-specific keys are always allowed.

## Notes for production

- Swap SQLite for Postgres (commented block in `config/settings.py`).
- Put `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False` and a real `DJANGO_ALLOWED_HOSTS` in `.env`.
- Terminate TLS in front of Gunicorn/Uvicorn; the `Partner.allowed_ips` field
  gives you a lightweight per-partner IP allowlist on top of the API key.
- `WebhookDeliveryLog` (Admin → Core) gives a basic audit trail for partner
  calls — swap for structured logging/APM as the integration surface grows.
