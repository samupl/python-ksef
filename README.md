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
