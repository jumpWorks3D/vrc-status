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

## Update behavior

GitHub Actions is scheduled to retrieve and publish the status data
approximately every 10 minutes.

Scheduled workflow start times are not guaranteed. GitHub Actions may delay or
skip scheduled runs during periods of high load.

The workflow can also be started manually from:

```text
Actions → Update VRChat status → Run workflow
```

## Failure behavior

A new deployment is performed only when all required source data passes
validation.

If retrieval or validation fails:

- The workflow fails.
- No new Pages deployment is performed.
- The last successfully published file remains available.
- Clients should use `generated_at` to detect stale data.

## Repository structure

```text
.github/
  workflows/
    update-vrc-status.yml

public/
  index.html

scripts/
  update-vrc-status.py

README.md
```

`public/vrc-status.txt` is generated during the workflow and is not committed
to the repository.

## Maintenance notes

Scheduled workflows in public repositories may be disabled by GitHub after
60 days without repository activity.

Review the Actions page periodically and confirm that scheduled runs continue
to occur.

The exact timing of scheduled runs is not guaranteed. The cron configuration
may be adjusted based on observed GitHub Actions scheduling behavior.

## Disclaimer

This is an unofficial service operated by jumpWorks3D.

It is not affiliated with or endorsed by VRChat Inc. The published data may be
delayed or temporarily unavailable. Refer to the official VRChat Status page
for authoritative information.

VRChat and related names are trademarks of their respective owners.
