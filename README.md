[![Open in Dev Containers](https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/samupl/python-ksef)

# ksef

**NOT PRODUCTION READY**

A python library for Polish KSEF (National e-invoice system, original: Krajowy System e-Faktur) system.

The official KSEF API documentation can be found at https://github.com/CIRFMF/ksef-docs/tree/main.

**IMPORTANT** Currently the project is not even in alpha stage, I barely started working on it. Initially it will 
support my personal needs only, but I plan to gradually implement new and more complex features.

## Using

To add and install this package as a dependency of your project, run `uv add ksef` (or `pip install ksef`).

## Authentication Setup

The library supports two authentication methods for KSEF API v2:

### KSeF Token Authentication

A KSeF token can be generated via the KSeF web portal or obtained through the API after XAdES authentication.

```python
from ksef.auth.token import TokenAuthorization
from ksef.client import Client
from ksef.constants import Environment

auth = TokenAuthorization(
    token="your-ksef-token",
    environment=Environment.TEST,
)
tokens = auth.authorize(nip="1234567890")

client = Client(authorization=auth, environment=Environment.TEST)
```

### XAdES Certificate Authentication

Requires a qualified certificate from a trusted CA, or a KSeF-issued certificate. Provide PEM-encoded certificate and private key bytes.

```python
from pathlib import Path

from ksef.auth.xades import XadesAuthorization
from ksef.client import Client
from ksef.constants import Environment

auth = XadesAuthorization(
    signing_cert=Path("cert.pem").read_bytes(),
    private_key=Path("key.pem").read_bytes(),
    environment=Environment.TEST,
)
tokens = auth.authorize(nip="1234567890")

client = Client(authorization=auth, environment=Environment.TEST)
```

### Environments

- `Environment.PRODUCTION` — `https://api.ksef.mf.gov.pl/api/v2/`
- `Environment.DEMO` — `https://api-demo.ksef.mf.gov.pl/api/v2/`
- `Environment.TEST` — `https://api-test.ksef.mf.gov.pl/api/v2/`

## Building Invoices

### Basic invoice structure

```python
from datetime import date
from decimal import Decimal

from ksef.models.invoice import (
    Address,
    Invoice,
    InvoiceData,
    InvoiceType,
    Issuer,
    IssuerIdentificationData,
    NipIdentification,
    Subject,
)
from ksef.models.invoice_rows import InvoiceRow, InvoiceRows
from ksef.models.invoice_annotations import InvoiceAnnotations

invoice = Invoice(
    issuer=Issuer(
        identification_data=IssuerIdentificationData(
            nip="1234567890",
            full_name="My Company Sp. z o.o.",
        ),
        address=Address(
            country_code="PL",
            city="Warszawa",
            street="Marszałkowska",
            house_number="10",
            apartment_number="5",
            postal_code="00-001",
        ),
    ),
    recipient=Subject(
        identification_data=NipIdentification(nip="0987654321"),
        address=Address(
            country_code="PL",
            city="Kraków",
            street="Floriańska",
            house_number="1",
            postal_code="30-001",
        ),
        name="Customer Sp. z o.o.",
    ),
    invoice_data=InvoiceData(
        currency_code="PLN",
        issue_date=date(2026, 3, 25),
        issue_number="2026/03/001",
        sell_date=date(2026, 3, 25),
        total_amount=Decimal("123.00"),
        invoice_type=InvoiceType.REGULAR_VAT,
        invoice_annotations=InvoiceAnnotations(),
        invoice_rows=InvoiceRows(rows=[
            InvoiceRow(
                name="Hosting service",
                unit_of_measure="szt.",
                quantity=Decimal("1"),
                unit_net_price=Decimal("100.00"),
                net_value=Decimal("100.00"),
                tax=23,
                delivery_date=date(2026, 3, 25),
            ),
        ]),
    ),
)
```

### Recipient identification types

The library supports all KSeF recipient identification methods:

```python
from ksef.models.invoice import (
    NipIdentification,        # Polish NIP
    EuVatIdentification,      # EU VAT number
    ForeignIdentification,    # Non-EU tax ID
    NoIdentification,         # No tax ID (individuals)
)

# Polish company
id_pl = NipIdentification(nip="1234567890")

# EU company
id_eu = EuVatIdentification(eu_country_code="DE", eu_vat_number="123456789")

# Non-EU company
id_foreign = ForeignIdentification(country_code="US", tax_id="12-3456789")

# Individual (no tax ID)
id_none = NoIdentification()
```

### Tax rates

Invoice rows support all valid KSeF tax rates via the `tax` field, plus OSS/IOSS rates via `tax_oss`:

```python
from ksef.models.invoice_rows import (
    InvoiceRow,
    # Standard rates
    TAX_23, TAX_22, TAX_8, TAX_7, TAX_5, TAX_4, TAX_3,
    # Zero rates
    TAX_0_KR,   # 0% domestic
    TAX_0_WDT,  # 0% intra-Community supply
    TAX_0_EX,   # 0% export
    # Special rates
    TAX_ZW,     # exempt from tax
    TAX_OO,     # reverse charge
    TAX_NP_I,   # not subject to taxation
    TAX_NP_II,  # not subject (art. 100)
)

# Standard 23% rate
row = InvoiceRow(name="Service", tax=TAX_23)

# Intra-Community supply at 0%
row = InvoiceRow(name="Goods to EU", tax=TAX_0_WDT)

# OSS rate for EU consumer (e.g. 21% Belgian VAT)
row = InvoiceRow(name="Digital service", tax_oss=Decimal("21"))
```

### Tax summary (P_13/P_14 fields)

For KSeF to display Netto/VAT totals, provide a `TaxSummary` on `InvoiceData`:

```python
from ksef.models.invoice import TaxSummary

tax_summary = TaxSummary(
    net_standard=Decimal("100.00"),   # P_13_1 — net at 23%/22%
    vat_standard=Decimal("23.00"),    # P_14_1 — VAT at 23%/22%
)
```

Available fields:

| Fields | Rate | XML |
|--------|------|-----|
| `net_standard` / `vat_standard` | 23% or 22% | P_13_1 / P_14_1 |
| `net_reduced_1` / `vat_reduced_1` | 8% or 7% | P_13_2 / P_14_2 |
| `net_reduced_2` / `vat_reduced_2` | 5% | P_13_3 / P_14_3 |
| `net_flat_rate` / `vat_flat_rate` | 4% or 3% | P_13_4 / P_14_4 |
| `net_oss` / `vat_oss` | OSS/IOSS | P_13_5 / P_14_5 |
| `net_zero_domestic` | 0% domestic | P_13_6_1 |
| `net_zero_wdt` | 0% intra-Community | P_13_6_2 |
| `net_zero_export` | 0% export | P_13_6_3 |
| `net_exempt` | exempt (zw) | P_13_7 |
| `net_not_subject` | not subject (np I) | P_13_8 |
| `net_not_subject_art100` | not subject (np II) | P_13_9 |
| `net_reverse_charge` | reverse charge (oo) | P_13_10 |

For foreign currency invoices, use the `*_pln` fields to provide VAT converted to PLN:

```python
TaxSummary(
    net_standard=Decimal("100.00"),        # EUR
    vat_standard=Decimal("23.00"),         # EUR
    vat_standard_pln=Decimal("98.31"),     # P_14_1W — VAT in PLN
)
```

### Foreign currency invoices

For non-PLN invoices, set the exchange rate per row and add descriptions for the rate source:

```python
from ksef.models.invoice import AdditionalDescription

row = InvoiceRow(
    name="Service",
    tax=23,
    unit_net_price=Decimal("100.00"),
    net_value=Decimal("100.00"),
    quantity=Decimal("1"),
    exchange_rate=Decimal("4.2867"),  # KursWaluty per row
)

# NBP rate source as a key-value note
desc = AdditionalDescription(
    key="Kurs waluty",
    value="4.2867 PLN/EUR, tabela kursów średnich NBP nr 056/A/NBP/2026 z dnia 23.03.2026",
)

invoice_data = InvoiceData(
    currency_code="EUR",
    additional_descriptions=[desc],
    # ...
)
```

### Additional recipients (Podmiot3)

For invoices with a third party (e.g. a government receiver/school when the buyer is a city hall):

```python
from ksef.models.invoice import (
    AdditionalRecipient,
    ROLE_RECEIVER,         # 2 — internal unit/branch of the buyer
    ROLE_JST_RECEIVER,     # 8 — government unit receiver
    ROLE_FAKTOR,           # 1 — factoring entity
    ROLE_ADDITIONAL_BUYER, # 4 — additional buyer
)

receiver = AdditionalRecipient(
    identification_data=NipIdentification(nip="9876543210"),
    name="Szkoła Podstawowa nr 1",
    address=Address(
        country_code="PL",
        city="Tarnów",
        street="Słoneczna",
        house_number="15",
        postal_code="33-100",
    ),
    role=ROLE_RECEIVER,
)

invoice = Invoice(
    issuer=issuer,
    recipient=buyer,
    additional_recipients=[receiver],
    invoice_data=invoice_data,
)
```

### Sending an invoice

```python
from ksef.xml_converters import convert_invoice_to_xml

# Convert to XML and send
result = client.send_invoice(invoice)
print(result.reference_number)
print(result.session_reference_number)

# Check status later
status = client.get_invoice_status(
    session_reference_number=result.session_reference_number,
    reference_number=result.reference_number,
)
print(status.status.code)    # 200 = accepted
print(status.ksef_number)    # e.g. "1234567890-20260325-ABCDEF-01"
```

## Integration Tests

Integration tests connect to the live KSEF test environment using real credentials. They are excluded from the default test run and must be invoked explicitly:

```bash
source .env
uv run pytest -m integration
```

Credentials are provided via environment variables. Tests with missing variables are skipped automatically. See [`tests/integration/README.md`](tests/integration/README.md) for the full list of variables and per-method usage.

## Contributing

<details>
<summary>Prerequisites</summary>

<details>
<summary>1. Set up Git to use SSH</summary>

1. [Generate an SSH key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent#generating-a-new-ssh-key) and [add the SSH key to your GitHub account](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account).
1. Configure SSH to automatically load your SSH keys:
    ```sh
    cat << EOF >> ~/.ssh/config
    Host *
      AddKeysToAgent yes
      IgnoreUnknown UseKeychain
      UseKeychain yes
    EOF
    ```

</details>

<details>
<summary>2. Install Docker</summary>

1. [Install Docker Desktop](https://www.docker.com/get-started).
    - Enable _Use Docker Compose V2_ in Docker Desktop's preferences window.
    - _Linux only_:
        - [Configure Docker to use the BuildKit build system](https://docs.docker.com/build/buildkit/#getting-started). On macOS and Windows, BuildKit is enabled by default in Docker Desktop.
        - Export your user's user id and group id so that [files created in the Dev Container are owned by your user](https://github.com/moby/moby/issues/3206):
            ```sh
            cat << EOF >> ~/.bashrc
            export UID=$(id --user)
            export GID=$(id --group)
            EOF
            ```

</details>

<details>
<summary>3. Install VS Code or PyCharm</summary>

1. [Install VS Code](https://code.visualstudio.com/) and [VS Code's Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers). Alternatively, install [PyCharm](https://www.jetbrains.com/pycharm/download/).
2. _Optional:_ install a [Nerd Font](https://www.nerdfonts.com/font-downloads) such as [FiraCode Nerd Font](https://github.com/ryanoasis/nerd-fonts/tree/master/patched-fonts/FiraCode) and [configure VS Code](https://github.com/tonsky/FiraCode/wiki/VS-Code-Instructions) or [configure PyCharm](https://github.com/tonsky/FiraCode/wiki/Intellij-products-instructions) to use it.

</details>

</details>

<details open>
<summary>Development environments</summary>

The following development environments are supported:

1. ⭐️ _GitHub Codespaces_: click on _Code_ and select _Create codespace_ to start a Dev Container with [GitHub Codespaces](https://github.com/features/codespaces).
1. ⭐️ _Dev Container (with container volume)_: click on [Open in Dev Containers](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/samupl/python-ksef) to clone this repository in a container volume and create a Dev Container with VS Code.
1. _Dev Container_: clone this repository, open it with VS Code, and run <kbd>Ctrl/⌘</kbd> + <kbd>⇧</kbd> + <kbd>P</kbd> → _Dev Containers: Reopen in Container_.
1. _PyCharm_: clone this repository, open it with PyCharm, and [configure Docker Compose as a remote interpreter](https://www.jetbrains.com/help/pycharm/using-docker-compose-as-a-remote-interpreter.html#docker-compose-remote) with the `dev` service.
1. _Terminal_: clone this repository, open it with your terminal, and run `docker compose up --detach dev` to start a Dev Container in the background, and then run `docker compose exec dev zsh` to open a shell prompt in the Dev Container.

</details>

<details>
<summary>Developing</summary>

- This project follows the [Conventional Commits](https://www.conventionalcommits.org/) standard to automate [Semantic Versioning](https://semver.org/) and [Keep A Changelog](https://keepachangelog.com/) with [Commitizen](https://github.com/commitizen-tools/commitizen).
- Run `poe` from within the development environment to print a list of [Poe the Poet](https://github.com/nat-n/poethepoet) tasks available to run on this project.
- Run `poetry add {package}` from within the development environment to install a run time dependency and add it to `pyproject.toml` and `poetry.lock`. Add `--group test` or `--group dev` to install a CI or development dependency, respectively.
- Run `poetry update` from within the development environment to upgrade all dependencies to the latest versions allowed by `pyproject.toml`.
- Run `cz bump` to bump the package's version, update the `CHANGELOG.md`, and create a git tag.

</details>
