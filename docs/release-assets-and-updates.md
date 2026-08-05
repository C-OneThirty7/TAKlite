# TAKlite Release Assets And Updates

TAKlite uses one version number across every deployment mode. If Linux, Windows Docker Desktop, and offline bundles all say the same version, they should contain the same TAKlite backend, API, admin UI, and access-control behavior.

Different release files exist only because the platform packaging is different.

## Release Asset Matrix

| Asset | Purpose | Best For |
| --- | --- | --- |
| `TAKlite-vX.Y.Z.zip` | Canonical source/update bundle | Linux/VPS install, Linux GUI update, online Docker update |
| `TAKlite-vX.Y.Z.zip.sha256` | Hash file for source/update bundle | Manual verification |
| `TAKlite-windows-docker-offline-vX.Y.Z.zip` | Windows bundle with click launchers and prebuilt Docker image | Windows Docker Desktop offline install/update |
| `TAKlite-windows-docker-offline-vX.Y.Z.zip.sha256` | Hash file for Windows offline bundle | Manual verification |

## Online Updates

Use online updates when the host running TAKlite can reach GitHub and Docker package/build sources.

### Linux/VPS GUI Update

1. Open TAKlite Admin.
2. Go to `Settings`.
3. Click `Check for Update` or `Update TAKlite`.
4. Confirm the update.
5. Wait for TAKlite to restart.

The GUI update button only runs when TAKlite can find a release zip with a SHA-256 digest. The host runner verifies the digest before applying the update.

### Linux/VPS Shell Update

Run this on the VPS:

```bash
set -Eeuo pipefail

if ! command -v git >/dev/null 2>&1; then
  apt-get update
  apt-get install -y git
fi

if [ -f /root/taklite/docker-compose.yml ]; then
  APP_DIR=/root/taklite
elif [ -f /root/TAKlite/docker-compose.yml ]; then
  APP_DIR=/root/TAKlite
elif [ -f /root/taklite-vps-bundle/docker-compose.yml ]; then
  APP_DIR=/root/taklite-vps-bundle
else
  echo "Could not find TAKlite app directory" >&2
  exit 1
fi

STAGE=/root/TAKlite-update
rm -rf "$STAGE"
git clone --depth 1 https://github.com/C-OneThirty7/TAKlite.git "$STAGE"

bash "$STAGE/update.sh" --from-dir "$STAGE" --app-dir "$APP_DIR"
```

### Windows Docker Desktop GUI Update

1. Make sure Docker Desktop is running.
2. Open TAKlite Admin.
3. Go to `Settings`.
4. Click `Check for Update` or `Update TAKlite`.

The Windows GUI update runner downloads the standard `TAKlite-vX.Y.Z.zip`, verifies its SHA-256 digest, applies it, and rebuilds the local Docker image. This requires internet access.

## Offline Updates

Use offline updates when the TAKlite host does not have internet or should not pull/build anything from the internet.

### Linux/VPS Offline Update

From an admin computer that has the release zip:

```bash
scp TAKlite-vX.Y.Z.zip root@YOUR_SERVER_IP:/root/
```

Then on the TAKlite server:

```bash
set -Eeuo pipefail

if [ -f /root/taklite/docker-compose.yml ]; then
  APP_DIR=/root/taklite
elif [ -f /root/TAKlite/docker-compose.yml ]; then
  APP_DIR=/root/TAKlite
elif [ -f /root/taklite-vps-bundle/docker-compose.yml ]; then
  APP_DIR=/root/taklite-vps-bundle
else
  echo "Could not find TAKlite app directory" >&2
  exit 1
fi

bash "$APP_DIR/update.sh" /root/TAKlite-vX.Y.Z.zip
```

### Windows Docker Desktop Offline Update

1. Download `TAKlite-windows-docker-offline-vX.Y.Z.zip` on a machine with internet.
2. Move the zip to the existing Windows TAKlite folder.
3. Put the zip inside the `update` folder.
4. Double-click `Update TAKlite.cmd`.

Use the Windows offline asset for Windows offline updates. It contains the prebuilt Docker image. The standard source zip is for online updates because Docker may need to rebuild the image.

## What Updates Preserve

Normal updates preserve:

- `.env`
- custom ports and host/IP settings
- admin account
- users
- access teams, levels, links, and overrides
- certs
- datapackages
- generated connection packages
- SQLite database
- WireGuard config on Linux/VPS installs
- WGDashboard config on Linux/VPS installs

## Release Checklist

Before publishing a release:

1. Build and test the source app.
2. Create `TAKlite-vX.Y.Z.zip`.
3. Create `TAKlite-vX.Y.Z.zip.sha256`.
4. Create `TAKlite-windows-docker-offline-vX.Y.Z.zip`.
5. Create `TAKlite-windows-docker-offline-vX.Y.Z.zip.sha256`.
6. Upload all assets to the same GitHub release tag.

Do not reuse an older offline asset under a newer release. If the offline asset is not rebuilt, offline users do not have that version yet.
