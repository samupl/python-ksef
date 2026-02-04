# Integration tests

**These tests are NOT safe to run blindly.** They connect to a live KSEF test
environment and perform real authentication. Do not run them in CI without
understanding what they do.

## Running

```bash
uv run pytest -m integration
```

## Providing credentials

All credentials are read from environment variables. Set the ones that match
the authentication method you want to test.

### KSeF Token authentication

| Variable     | Description                              |
|------------- |------------------------------------------|
| `KSEF_TOKEN` | KSeF authorization token (from the portal or API) |
| `KSEF_NIP`   | NIP (tax identification number) to authenticate with |

```bash
export KSEF_TOKEN="your-token-here"
export KSEF_NIP="1234567890"
uv run pytest -m integration -k token
```

### XAdES certificate authentication

| Variable             | Description                                         |
|--------------------- |-----------------------------------------------------|
| `KSEF_CERT_PATH`     | Path to the PEM-encoded signing certificate          |
| `KSEF_KEY_PATH`      | Path to the PEM-encoded private key                  |
| `KSEF_KEY_PASSWORD`  | Password for the private key (omit if not encrypted) |
| `KSEF_NIP`           | NIP (tax identification number)                      |

```bash
export KSEF_CERT_PATH="/path/to/cert.pem"
export KSEF_KEY_PATH="/path/to/key.pem"
export KSEF_KEY_PASSWORD="optional-password"
export KSEF_NIP="1234567890"
uv run pytest -m integration -k xades
```

### Running all integration tests

```bash
export KSEF_TOKEN="..."
export KSEF_CERT_PATH="/path/to/cert.pem"
export KSEF_KEY_PATH="/path/to/key.pem"
export KSEF_KEY_PASSWORD="optional-password"
export KSEF_NIP="1234567890"
uv run pytest -m integration
```

Tests that are missing the required environment variables will be skipped
automatically.
