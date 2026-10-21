# Waste Collection Demo

Minimal Interoperable AI Service (MIAIS) for **waste collection**: it reads the `WasteContainer` entities of a city (NGSI-LD,
[Smart Data Models](https://github.com/smart-data-models/dataModel.WasteManagement)), lets the user pick the containers above a
filling level and computes the collection routes of the trucks with the [Openroute](https://openrouteservice.org/) optimization
service. For a detailed guide, check out our [documentation](https://citcomai-hub.github.io/services/waste_collection/).

It is a demonstrator of the integration levels of an AI service:

| Level | Where the data comes from | How |
|---|---|---|
| 1 | An NGSI-LD broker (local Orion-LD, Scorpio or a TEF platform) | `NGSI_LD_URL` |
| 2 | A **data space**: the broker of a provider, through its connector | `NGSI_LD_URL` + `DS_*` |

At level 2 the service is a **consumer** of the data space. In the CitCom data space it runs as a service of **VRAIN** (consumer
participant) and reads the waste containers of the **València City Council** (`townhall-vlc`, provider), which come from VLCi.

## Architecture

```text
 static/ (UI: Leaflet map, filters)  ──▶  server.py (Flask)  ──▶  services/DataSource.py ──▶ NGSI-LD broker / data space
                                                              ──▶  services/Optimization.py ──▶ Openroute optimization
```

-   [`services/DataSource.py`](./services/DataSource.py): reads the entities with [FiLiP](https://github.com/RWTH-EBC/FiLiP), an
    NGSI-LD client. At level 2 its HTTP session comes from
    [ds-consumer-auth](https://github.com/CitComAI-Hub/ds-consumer-auth), which adds an access token of the data space to every
    request (OID4VCI credential of the consumer + `vp_token` at the provider's verifier).
-   [`services/Optimization.py`](./services/Optimization.py): builds the Openroute (Vroom) optimization request.
-   `server.py` endpoints: `/wastecontainers`, `/trucks` (simulated trucks), `/optimization`, `/healthz`.

## Configuration

Environment variables (see [`.env.example`](./.env.example)):

| Variable | Default | Description |
|---|---|---|
| `OPENROUTESERVICE_API_KEY` | | Openroute API key (required for the optimization) |
| `NGSI_LD_URL` | `http://localhost:1026` | NGSI-LD endpoint: a broker, or the provider's data space connector |
| `NGSILD_TENANT` | | NGSI-LD tenant, if the broker uses one |
| `WASTE_CONTAINER_TYPE` | `WasteContainer` | Entity type of the containers |
| `WASTE_CONTAINER_LIMIT` | `100` | Maximum containers read. The Openroute optimization accepts up to 70 locations, and the UI waits 7 s for the data |
| `DS_ISSUER_URL`, `DS_USERNAME`, `DS_PASSWORD`, `DS_VERIFIER_URL`, `DS_SCOPE`… | | Level 2: credential of the consumer and verifier of the provider. Without `DS_ISSUER_URL`, no token is used. See [ds-consumer-auth](https://github.com/CitComAI-Hub/ds-consumer-auth#configuration) |

## Run it locally

Tested with Python 3.12.

```console
git clone https://github.com/CitComAI-Hub/waste-collection-demo.git && cd waste-collection-demo
python3 -m venv ./venv && source ./venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # set OPENROUTESERVICE_API_KEY and NGSI_LD_URL
set -a && source .env && set +a
flask --app server run
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000).

**Level 1 with a local broker**: `docker compose up` starts Orion-LD (`http://localhost:1026`, the default `NGSI_LD_URL`). It
starts empty: create `WasteContainer` entities with a `fillingLevel` and a `location` first (the branch `mvs-orionld` has a script
with fake data).

**Level 2 (CitCom data space)**: set in `.env`

```bash
NGSI_LD_URL="https://apisix-townhall-vlc.citcom-vrain-dataspace.eu"
DS_ISSUER_URL="https://keycloak-vrain.citcom-vrain-dataspace.eu/realms/provider"
DS_USERNAME="machine1"
DS_PASSWORD="..."
DS_VERIFIER_URL="https://verifier-townhall-vlc.citcom-vrain-dataspace.eu/services/machine-id"
DS_SCOPE="operator1"
```

The consumer (VRAIN) must have acquired the provider's product in the marketplace first; otherwise the verifier rejects its
credential and `/wastecontainers` answers `502` with `vp_token: the verifier rejected the credential`. See
[ds-consumer-auth's troubleshooting](https://github.com/CitComAI-Hub/ds-consumer-auth#troubleshooting).

## Docker

```console
docker build -t waste-collection-demo .
docker run --rm -p 5000:5000 --env-file .env waste-collection-demo
```

The image runs [gunicorn](https://gunicorn.org/) with one process and threads (the data space token is cached per process),
as a non-root user, and has a healthcheck on `/healthz`.

### Publishing a new version

The image `ghcr.io/citcomai-hub/waste-collection-demo` is built and pushed by
[`.github/workflows/publish.yml`](./.github/workflows/publish.yml) when a `v*` tag is pushed:

```console
git tag -a v1.1 -m "Waste collection demo v1.1"
git push origin v1.1
```

Use a new tag every time (a pod does not pull again a tag it already has) and update it in the deployment.

## Deploy in Kubernetes (CitCom data space)

[`deploy/kubernetes/waste-collection.yaml`](./deploy/kubernetes/waste-collection.yaml) deploys the service in the namespace of the
consumer (`vrain`), with its UI at `https://waste-collection-vrain.citcom-vrain-dataspace.eu`. Create the secrets first, then
apply it:

```console
read -r -s -p "DS_PASSWORD: " DS_PASSWORD; echo
read -r -s -p "OPENROUTESERVICE_API_KEY: " ORS_KEY; echo
kubectl -n vrain create secret generic waste-collection-secrets \
  --from-literal=DS_PASSWORD="$DS_PASSWORD" --from-literal=OPENROUTESERVICE_API_KEY="$ORS_KEY"
unset DS_PASSWORD ORS_KEY

kubectl apply -f deploy/kubernetes/waste-collection.yaml
kubectl -n vrain rollout status deployment/waste-collection
```

Review the host, the ingress class and the cert-manager issuer of the `Ingress` for the target cluster.

## Limitations and TODO

-   The trucks are simulated (`/trucks`); read `Vehicle` entities from the data space instead.
-   The Openroute optimization accepts up to 70 locations: deploy your own Openroute instance for more.
-   The output should follow the Smart Data Models (`FleetVehicleOperation`, `Road`, `RoadSegment`…), as recommended by MIM1/MIM2.
-   The `WasteContainer` entities are read on every page load; cache them for a while if the provider is slow.
-   Openroute API keys must never be committed: an older version of this README contained one, so rotate it.
