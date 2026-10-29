# Drainer Network relay — private friend test starter

This project is a deployment-ready wrapper for the V158 Drainer Network test relay. It is **not** production-ready.

## Deploy on Render
1. Go to https://github.com/new and create a new repository named `drainer-network-relay` (private is fine). Do not put your whole Minecraft source here.
2. In your new GitHub repo, upload the **contents** of this folder (`server.py`, `render.yaml`, `test_server.py`, `README.md`), not the ZIP. Commit the files.
3. Open https://dashboard.render.com/ and choose **New > Blueprint**. Connect GitHub, choose your new repository, and deploy. The `render.yaml` file configures a Python web service.
4. In Render, open the newly created service and find its HTTPS `*.onrender.com` URL. Visit `https://YOUR-URL.onrender.com/health` in a browser. It should return a JSON object with `"ok":true`.
5. Test with V158 or newer clients by setting their `config/drainer-network.properties` line to `relay_url=https://YOUR-URL.onrender.com`, restarting/re-toggling DrainerNetwork and opting into sharing. Both players must be on the same multiplayer server and present in the server's tab list.
6. For a future release, embed the HTTPS URL as a default in the Drainer client so each user does not have to edit a properties file. This change is **not** in this relay ZIP.

## Limits and privacy
- This relay has **no verified Minecraft account authentication** and should never be used for trust, purchases, cosmetics entitlements or rank. Treat all remote names/badges as unverified.
- Public internet deployment means others may access the endpoint. Don't use it for a public Drainer release until identity verification, anti-abuse rate limiting, authentication, hosting/security review and appropriate privacy disclosures are implemented.
- Presence and cosmetics sharing are off by default and must be explicitly enabled on each client.
- Relay stores active username, UUID, cosmetics and server hash in memory for about 45 seconds; the host can see connecting IP addresses.
- Render Free spins down after 15 minutes without inbound requests and can take about a minute to start again. For reliable always-on hosting use a paid always-on instance.
- The relay has no database; it keeps short-lived data in memory and loses it when the service restarts.

## Manual alternative to Blueprint
Create a Render Web Service with Python runtime, Build Command `python -m compileall -q server.py`, Start Command `python server.py`, and environment variables `DRAINER_BIND=0.0.0.0` and `DRAINER_PORT=10000`.

## Local smoke check
Run `python test_server.py` if testing its default localhost mode. For Render use the `/health` endpoint.
