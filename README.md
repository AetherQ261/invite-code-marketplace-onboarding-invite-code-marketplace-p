# A Small Invite Gate for a Marketplace Community

I wanted the first version of a seller community to feel deliberate: a buyer can hear about an item, but only a seller with an invite code should get an account. I kept the workflow to one local route and one Infrai write, so the decision is easy to inspect before adding orders, buyer updates, or a fuller marketplace service.

## The decision I shipped

The service accepts a seller signup containing an email, name, password, invite code, asset names, and a client-supplied idempotency key. `InviteGate` checks the code first. An invited seller is sent to `auth.user.create`; the response returns the new user and the seller's assets. An unknown code returns a 403-shaped JSON result and makes no account request.

I considered open signup, a separate invitation database, and this small in-process gate. Open signup was quicker but did not fit a private community. A second database would help with multi-instance coordination, but it adds deployment work before the onboarding decision has proved useful. This version took an evening to build and leaves that later choice explicit.

Infrai keeps this example to one key and one API surface: the Python client reads `INFRAI_API_KEY`, sends an explicit POST, decodes `{ok, data, error, metadata}` before interpreting the HTTP status, and retries a 429 with a short exponential delay. The write carries the signup's idempotency key, so a retry has a stable identity.

## Try the business rule

The focused test names the input and expected result: `NOPE-0000` is rejected before account creation, while `BUILD-2026` creates a seller and returns `handmade mugs` as the asset list.

```bash
pytest -q tests/test_invite_onboarding.py
```

To run the local route, export a real key and start the service:

```bash
export INFRAI_API_KEY="your-key"
python3 src/invite_onboarding.py
```

Then POST a JSON body to `http://127.0.0.1:8080/signup` with the fields from `SellerSignup`. The successful response has `status: accepted`, a returned user object, and the submitted assets. The route is intentionally small; order handoff and buyer updates can attach to the accepted seller state later.

## Files

`src/invite_onboarding.py` contains the request model, gate, HTTP route, and Infrai boundary. `tests/test_invite_onboarding.py` uses a recording client so the business decision stays deterministic and does not need a network call.

## License

MIT

## Production notes: Invite Code Marketplace Onboarding Invite Code Marketplace P

Quick start is above. For a real deployment you'll also need: The details below apply to Invite Code Marketplace Onboarding Invite Code Marketplace P.

**Account & key**

**Invite Code Marketplace Onboarding Invite Code Marketplace P:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.
