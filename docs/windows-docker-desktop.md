# TAKlite Windows Docker Desktop Guide

This guide is for running TAKlite directly on a Windows machine with Docker Desktop. It is useful when the network already exists and the Windows host has a stable LAN address that ATAK/WinTAK clients can reach.

This mode installs TAKlite only. It does not install WireGuard, WGDashboard, Linux systemd services, or Linux firewall runners.

## When To Use This

Use Windows Docker Desktop mode when:

- TAKlite should run next to another Windows-hosted service.
- The Windows machine already has the correct network access.
- ATAK/WinTAK clients can reach the Windows machine directly over LAN, routed network, or a VPN you manage separately.
- You want Docker Desktop to run the TAKlite container.

Use the full Linux installer instead when you want TAKlite to install and manage WireGuard, WGDashboard, fail2ban, Linux iptables, and the complete VPS appliance flow.

## Requirements

- Windows 11 x64 with hardware virtualization enabled.
- Docker Desktop installed and configured to use the Linux engine.
- Administrator account for first install.
- A stable IPv4 address on the Windows Ethernet or Wi-Fi adapter.
- ATAK or WinTAK clients able to reach that IPv4 address.

TAKlite uses these default TCP ports:

```text
8080/tcp     TAKlite admin and user portal
8443/tcp     TAK HTTPS/Marti/datapackage API
8089/tcp     TLS CoT
58087/tcp    Plain CoT
```

These do not conflict with Axon's default TCP 80 service or host-only control panel.

## Install

Download and extract the Windows Docker Desktop release asset.

Double-click:

```text
Install TAKlite.cmd
```

Approve the Windows administrator prompt. The command launcher runs the TAKlite PowerShell installer for you.

If Windows blocks the downloaded files, right-click the extracted folder, open Properties, and unblock it if that option is shown. If Windows does not show an unblock checkbox but still blocks scripts, open PowerShell in the extracted folder and run:

```powershell
Get-ChildItem -Recurse | Unblock-File
```

## Optional Command-Line Install

Most admins should use `Install TAKlite.cmd`. The direct PowerShell entrypoint is only for advanced options.

Open PowerShell as Administrator from the extracted TAKlite folder:

```powershell
.\scripts\Install-TAKliteWindows.ps1
```

## What The Installer Does

The Windows installer:

- verifies Docker Desktop is available;
- starts Docker Desktop if needed;
- lists connected physical adapters and IPv4 addresses;
- selects the only usable adapter/IP automatically when there is only one;
- asks you to choose the adapter or IP when there are multiple;
- preserves the Windows NIC, gateway, DNS, and IP settings;
- writes `.env` for Docker Desktop mode;
- binds TAKlite to the selected Windows IPv4 address;
- creates scoped Windows Firewall rules for the TAKlite TCP ports;
- builds and starts TAKlite with Docker Compose.

The installer does not rewrite Windows networking. If the selected IP is wrong, fix Windows networking first, then rerun the installer.

## Explicit Install Options

Use a specific Windows IP:

```powershell
.\scripts\Install-TAKliteWindows.ps1 -BindIp 192.168.1.50
```

Use a specific adapter name and IP:

```powershell
.\scripts\Install-TAKliteWindows.ps1 -InterfaceAlias "Ethernet" -BindIp 192.168.1.50
```

Allow only specific source networks through Windows Firewall:

```powershell
.\scripts\Install-TAKliteWindows.ps1 -AllowedRemoteAddress "192.168.1.0/24","10.66.66.0/24"
```

Regenerate `.env` after changing the intended IP:

```powershell
.\scripts\Install-TAKliteWindows.ps1 -BindIp 192.168.1.50 -EnvMode Recreate
```

Skip Windows Firewall rule creation:

```powershell
.\scripts\Install-TAKliteWindows.ps1 -SkipFirewall
```

## After Install

The installer prints the TAKlite URLs and bootstrap token.

Default layout:

```text
Dashboard:    http://WINDOWS_HOST_IP:8080/
Portal:       http://WINDOWS_HOST_IP:8080/connect/
HTTPS/Marti:  https://WINDOWS_HOST_IP:8443/Marti
TLS CoT:      WINDOWS_HOST_IP:8089
Plain CoT:    WINDOWS_HOST_IP:58087
```

Open the TAKlite dashboard and use the bootstrap token to create the first admin account.

Then create Connection Users or Connection Packages in TAKlite and import the generated `.dp.zip` into ATAK/WinTAK.

The certificate password defaults to:

```text
atakatak
```

## Running Next To Axon

TAKlite and Axon can run side by side on the same Windows Docker Desktop host when their ports do not overlap.

Default service split:

```text
Axon:     http://WINDOWS_HOST_IP/
TAKlite:  http://WINDOWS_HOST_IP:8080/
```

Keep each project in its own folder and use each project's own installer.

TAKlite uses Docker Compose project name `taklite`. Axon uses its own Compose project and runtime layout.

## WireGuard

WireGuard is optional in Windows Docker Desktop mode.

Use one of these patterns:

- Existing LAN or routed network: no WireGuard needed.
- Existing VPN elsewhere: point ATAK/WinTAK packages at the Windows host IP reachable through that VPN.
- WireGuard on the Windows host: install and manage WireGuard for Windows separately, then rerun TAKlite with `-BindIp` set to the IP clients should use.
- Full TAKlite VPN appliance: use the Linux VPS installer instead.

## Validate

From the Windows host:

```powershell
docker compose --project-name taklite --env-file .\.env --file .\docker-compose.yml ps
curl.exe http://WINDOWS_HOST_IP:8080/api/health
```

From another machine on the same network:

```powershell
curl.exe http://WINDOWS_HOST_IP:8080/api/health
```

If the second command fails:

- confirm the Windows host IP is correct;
- confirm Docker Desktop is running;
- confirm Windows Firewall allows TAKlite ports;
- confirm the client network can route to the Windows host;
- confirm no other process owns the TAKlite ports.

## Stop Or Restart

From the TAKlite folder:

```powershell
docker compose --project-name taklite --env-file .\.env --file .\docker-compose.yml restart
```

Stop:

```powershell
docker compose --project-name taklite --env-file .\.env --file .\docker-compose.yml down
```

This preserves TAKlite data in the project folder under:

```text
taklite\data
taklite\packages
taklite\certs
```
