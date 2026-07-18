# VRCCustomDesktop Status Data

This repository publishes normalized VRChat service status data for
VRCCustomDesktop.

The data is retrieved from the official VRChat Status service, validated,
normalized, and deployed to GitHub Pages by GitHub Actions.

## Published URLs

Landing page:

```text
https://jumpworks3d.github.io/vrc-status/
```

Status data:

```text
https://jumpworks3d.github.io/vrc-status/vrc-status.txt
```

## Data source

The source data is retrieved from the official VRChat Status API:

```text
https://status.vrchat.com/api/v2/summary.json
```

The following service groups are currently used:

- Overall status
- API / Website
- Realtime Networking

Component IDs and names are both validated before publishing.

## File format

The published file uses UTF-8 without a BOM, LF line endings, and a final
newline.

Example:

```text
version=1
generated_at=2026-07-18T12:00:00Z
source_updated_at=2026-07-18T11:59:30Z
overall=operational
api_website=operational
realtime_networking=operational
```

### Keys

| Key | Description |
| --- | --- |
| `version` | Version of the published file format |
| `generated_at` | UTC time when this repository generated the file |
| `source_updated_at` | UTC update time reported by the official source |
| `overall` | Normalized overall VRChat service status |
| `api_website` | Normalized API / Website status |
| `realtime_networking` | Normalized Realtime Networking status |

## Normalized status values

| Value | Meaning |
| --- | --- |
| `operational` | Operating normally |
| `degraded` | Degraded performance |
| `partial_outage` | Partial outage |
| `major_outage` | Major outage |
| `maintenance` | Under maintenance |
| `unknown` | Status cannot be determined safely |

Unknown source values are not treated as operational.

## Status update workflow

The `Update VRChat status` workflow performs the following operations:

1. Retrieves the official VRChat Status summary.
2. Validates the response structure, page identity, component IDs, and names.
3. Rejects unknown source status values.
4. Generates `public/vrc-status.txt`.
5. Validates the generated file.
6. Uploads the `public` directory as a GitHub Pages artifact.
7. Deploys the artifact to GitHub Pages.

A new deployment is performed only when all required validation succeeds.

The workflow is configured with multiple explicit cron schedules intended to
run approximately every 10 minutes.

Scheduled workflow start times are not guaranteed. GitHub Actions may delay or
skip scheduled runs during periods of high load. The cron configuration may be
adjusted based on observed scheduling behavior.

The workflow can also be started manually from:

```text
Actions → Update VRChat status → Run workflow
```

## Failure behavior

If retrieval or validation fails:

- The generation job fails.
- The deployment job is skipped.
- No new Pages deployment is performed.
- The last successfully published file remains available.
- Clients should use `generated_at` to detect stale data.

This behavior has been tested using a temporary branch with an intentionally
invalid source URL.

## Scheduled workflow keepalive

GitHub may disable scheduled workflows in inactive public repositories.

The `Keep scheduled workflows active` workflow periodically updates:

```text
.github/keepalive
```

The keepalive workflow:

- Runs on the 1st and 21st of each month.
- Can also be started manually.
- Writes the current UTC date to `.github/keepalive`.
- Creates a commit only when the file content changes.
- Uses the `github-actions[bot]` commit identity.
- Does not require a Personal Access Token or repository secret.

The keepalive workflow is a maintenance safeguard, but scheduled workflow
activity should still be reviewed periodically.

## GitHub Pages protection

The `github-pages` environment permits deployments from the `main` branch
only.

Test branches cannot deploy to the production GitHub Pages environment.

## Repository structure

```text
.github/
  workflows/
    keepalive.yml
    update-vrc-status.yml
  keepalive

public/
  index.html

scripts/
  update-vrc-status.py

README.md
```

`public/vrc-status.txt` is generated during the status workflow and is not
committed to the repository.

## Client behavior

Clients should:

- Require `version=1`.
- Require all documented keys.
- Reject duplicate or malformed keys.
- Accept only the documented normalized status values.
- Treat unsupported versions and invalid data as unknown.
- Use `generated_at` to detect stale data.
- Avoid assuming that scheduled updates occur at exact times.

## VRChat compatibility

The published status URL has been tested successfully with
`VRCStringDownloader` in:

- Unity Play Mode
- VRChat Build & Test

The same URL can be downloaded again in an existing VRChat instance after a
new GitHub Pages deployment.

## Manual checks

Periodically confirm that:

1. Scheduled status workflows are still running.
2. The generated file contains all required keys.
3. `generated_at` continues to advance.
4. GitHub Pages deployments succeed.
5. The direct status URL remains accessible.
6. VRChat can still download and parse the file.
7. The official component IDs and names have not changed.
8. No personal account is exposed through repository activity.

## Disclaimer

This is an unofficial service operated by jumpWorks3D.

It is not affiliated with or endorsed by VRChat Inc. The published data may be
delayed or temporarily unavailable. Refer to the official VRChat Status page
for authoritative information.

VRChat and related names are trademarks of their respective owners.
