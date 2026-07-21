# Templates

Templates let users create `dstack` runs from the UI via a launch wizard — select a template,
pick GPU resources, adjust settings, and review the final configuration.

While `dstack` is typically used via the CLI, templates make it easy to launch runs
directly from the UI through a guided experience.

## Using templates

> [!NOTE]
> Templates require `dstack` server version 0.20.12 or newer.

To enable the launch wizard for every project, point the server to a Git repository
containing templates via the `DSTACK_SERVER_TEMPLATES_REPO` environment variable:

```shell
$ DSTACK_SERVER_TEMPLATES_REPO=https://github.com/dstackai/dstack-templates dstack server
```

Once configured, the **Launch** button on the **Runs** page will show the available templates.
Select a template, configure the parameters, and click **Apply** to create the run.

On current dstack releases, an administrator can instead configure a templates repository
for one project in **Project settings**. A project-specific repository takes precedence over
the server-wide default.

<img width="850" src="https://dstack.ai/static-assets/static-assets/images/dstack-templates-in-browser-ide-o.gif" />

> [!NOTE]
> The launch wizard is an experimental feature.

## Zinnia templates

This fork also carries a curated self-service catalog for the Zinnia `main` project:

- `Zinnia GPU Lab` for interactive development
- `Qwen Image Lab` for Zed-based Qwen image editing and LoRA experimentation
- `Zinnia Python Batch` for one-off GPU jobs

Stable inference services intentionally remain in the infra repository and are
applied through the dstack CLI. dstack 0.20.28's Launch UI does not accept all of
the fields they need, including `volumes`, `shell`, and `backend_options`. Fleet,
volume, and stable-service definitions therefore remain outside this UI catalog.

### GPU Lab workflow

`Zinnia GPU Lab` defaults to Zed, dstack's managed Python environment,
`/dstack/run`, and one GPU with at least 24GB of VRAM. The final resource picker
may select a larger GPU while preserving the template's CPU, memory, disk,
shared-memory, provider, and price constraints.

In the launch wizard:

1. Choose a run name and desktop IDE. Zed is the default.
2. Choose an offer within the `$2.50/hour` template limit.
3. Choose a Python version (such as `3.12`) or provide a custom Docker image.
4. Enable **Repo** and provide a public Git URL when the workspace should start
   with source code. Leave **Path** empty to clone it directly into
   `/dstack/run`, or set an absolute destination.
5. Review the generated YAML and launch the run.

Keep the `dstack apply` or `dstack attach` command running while using a desktop
IDE. To reconnect to a run launched from the UI:

```shell
dstack attach <run-name>
```

While attached, the printed IDE link and `ssh <run-name>` work through the local
dstack-managed SSH configuration. For Zed, the equivalent macOS command is:

```shell
open 'zed://ssh/<run-name>/dstack/run'
```

The template stops after one hour without an IDE, SSH, `apply`, or `attach`
connection, and has a six-hour hard maximum. `inactivity_duration` stops the
run; the `pooled-gpu` fleet's separate five-minute `idle_duration` controls how
long reusable VM capacity may remain after a run has stopped. The fleet setting
does not apply to container-based Vast.ai and RunPod instances.

The UI's Repo field clones the remote repository state. To include unpushed
commits or other local working-tree changes, use a checked-out `.dstack.yml`
through the CLI and configure `repos` with a local path; dstack clones the Git
repository and applies its local changes when submitting the run.

### Qwen Image Lab workflow

`Qwen Image Lab` is a focused Zed interactive environment for
`Qwen/Qwen-Image-Edit-2511`. It currently uses Hugging Face's CUDA Diffusers
development image pinned by digest. The validated editor dependencies and
starter are also captured by `images/qwen-image-lab/Dockerfile`; the matching
GitHub Actions workflow publishes `ghcr.io/gurdasnijor/zinnia-image-lab` so the
template can migrate to an immutable derivative without installing tools on a
billable GPU. Model weights, tokens, inputs, and outputs are deliberately not
baked into that image.

GitHub Container Registry creates the package as private on its first build.
Make it public once, then update this template to the immutable digest recorded
in the workflow summary. RunPod and Vast cannot use dstack `registry_auth`, so
do not switch this template to the derivative while the package is private.
The `HF_TOKEN` dstack project secret is made available to the Hub client
without exposing it in this repository.

When no repository is selected in the launch wizard, the template seeds a
small project with a runnable Zed `# %%` workflow, `inputs/` and `outputs/`
directories, and an optional Diffusers LoRA hook. When a repository is
selected, its files take precedence and the starter does not overwrite it.
The template also exposes the image's `/opt/venv` Python tools to remote Zed
terminals and stores the Hugging Face login in the standard local Hub cache.

The template requests one GPU with at least 80GB of VRAM, 128GB of system
memory, and 200GB of disk. Its $5/hour ceiling still lets the launch wizard
rank qualifying offers across Vast.ai, RunPod, and Lambda. The model repository
contains roughly 58GB of assets, so the first model load can remain lengthy on
an uncached marketplace instance.

After launch, attach from the workstation and open the printed Zed link:

```shell
dstack attach <run-name>
```

Open a Python file in Zed, separate interactive cells with `# %%`, and select
the registered `Qwen Image Lab` kernel. Run a cell with `Ctrl-Shift-Enter`.
Zed's REPL displays images and plots inline using the remote Jupyter kernel.
The run stops after two hours without any Zed, SSH, `apply`, or `attach`
connection and has a six-hour hard maximum.

dstack 0.20.28's Launch UI does not preserve the `volumes` field when it turns
a template into a run. This UI-launched lab is therefore intentionally
ephemeral and remains eligible for the pooled providers. The durable variant
is `workloads/zinnia/inference/qwen-image-lab.dev.dstack.yml` in the infra
repository; it is applied with the CLI and mounts the regional RunPod cache for
Hugging Face models, LoRAs, inputs, and outputs.

## Creating custom templates

To define your own templates, fork this repository or create a new one following the same layout.

Templates are YAML files placed under the `.dstack/templates/` directory in the repository.
Each file defines a single template.

## Template format

Each template file has the following top-level fields:

- `type` — always `template`
- `name` — unique identifier within the repository
- `title` — human-readable label shown in the UI
- `description` — short description shown in the UI
- `parameters` — list of configurable [parameters](#parameters)
- `configuration` — a standard `dstack` run configuration ([`dev-environment`](https://dstack.ai/docs/concepts/dev-environments), [`service`](https://dstack.ai/docs/concepts/services), or [`task`](https://dstack.ai/docs/concepts/tasks))


### Examples

#### Desktop IDE

A simple template that launches a dev environment accessible from a desktop IDE:

```yaml
type: template
name: desktop-ide

title: Desktop IDE
description: Access the instance from your desktop VS Code, Cursor, or Windsurf.

parameters:
  - type: name
  - type: ide
  - type: resources
  - type: python_or_docker
  - type: repo
  - type: working_dir

configuration:
  type: dev-environment
```

#### In-browser IDE

A template that deploys in-browser VS Code as a service:

```yaml
type: template
name: in-browser-ide

title: In-browser IDE
description: Access the instance using VS Code in the browser.

parameters:
  - type: name
  - type: resources
  - type: python_or_docker
  - type: repo
  - type: working_dir

  - type: env
    title: Password
    name: PASSWORD
    value: $random-password

configuration:
  type: service

  env:
    - BIND_ADDR=0.0.0.0:8080
  commands:
    - |
      echo "Your password is $PASSWORD. Share it carefully as it grants full access to the IDE."
    - |
      curl -fsSL https://code-server.dev/install.sh | sh -s -- --method standalone --prefix /tmp/code-server
    - |
      /tmp/code-server/bin/code-server --bind-addr $BIND_ADDR --auth password --disable-telemetry --disable-update-check .
  port: 8080

  probes:
    - type: http
      url: /healthz

  gateway: true
  https: auto
  auth: false
```

The `env` parameter with `value: $random-password` tells the UI to auto-generate a random
password and pass it to the run configuration.

## Parameters

Parameters are special constructs supported by the `dstack` UI. Each parameter type maps to
a dedicated UI widget that provides context-aware configuration (e.g. showing available GPU offers,
listing Git repos, etc.).

| Type               | Description                                                                                                     |
|--------------------|-----------------------------------------------------------------------------------------------------------------|
| `name`             | Configure an optional run name.                                                                                 |
| `ide`              | Pick a desktop IDE (VS Code, Cursor, Windsurf, or Zed).                                                         |
| `resources`        | Configure GPU/CPU resources based on available offers in the project.                                            |
| `python_or_docker` | Select a Python version (to use the `dstack` base image) or specify a Docker image.                              |
| `repo`             | Configure a Git repo to clone into the run.                                                                      |
| `working_dir`      | Configure a working directory.                                                                                   |
| `env`              | Define a custom environment variable. Supports `title`, `name`, and `value` properties. The special value `$random-password` tells the UI to auto-generate a random password. |

## What's next?

1. Check the [dstack docs](https://dstack.ai/docs)
2. Learn about [dev environments](https://dstack.ai/docs/concepts/dev-environments), [tasks](https://dstack.ai/docs/concepts/tasks), and [services](https://dstack.ai/docs/concepts/services)
3. Browse [examples](https://dstack.ai/docs/examples)
