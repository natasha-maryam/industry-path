# CrossLayerX

## OpenPLC Runtime (Deploy PLC)

Deploy PLC runtime validation now targets OpenPLC as the primary runtime.

### Environment Variables

Backend runtime deployer supports:

- `OPENPLC_HOST` (default: `127.0.0.1` local, `openplc` in containerized backend)
- `OPENPLC_PORT` (default: `8080`)
- `OPENPLC_PROTOCOL` (default: `OpenPLC`)

### Runtime URL Resolution

Deploy requests resolve runtime endpoint in this order:

1. Request `runtime_config`
2. Environment defaults (`OPENPLC_*`)
3. Container-aware fallback (`openplc` service hostname when backend runs in Docker)

If backend is containerized and request host is `localhost` or `127.0.0.1`, deployer rewrites host to the OpenPLC service host to avoid loopback-to-container issues.

### Health Check Integration

`GET /api/health` now includes `services.openplc` with socket + HTTP probe status.

### Local vs Containerized Dev

- Local backend + Docker OpenPLC:
	- Use `OPENPLC_HOST=127.0.0.1`, `OPENPLC_PORT=8080`
- Containerized backend + Docker OpenPLC:
	- Use `OPENPLC_HOST=openplc`, `OPENPLC_PORT=8080`
	- Ensure backend container joins `crosslayerx-net`