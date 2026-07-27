# TAKlite Proxmox / ISP Router Deployment Profile

This profile is for admins who already have Proxmox running and already control their upstream router or firewall. It does not explain how to install Proxmox, configure a specific router brand, design VLANs, or create port-forward rules in a particular network OS.

The goal is simple: run TAKlite inside a Proxmox guest, expose only WireGuard from the internet, and keep TAKlite services reachable through the VPN.

## Topology

```text
Internet
  -> ISP public IP or DNS name
  -> Admin-managed router/firewall
  -> Proxmox guest LAN IP
  -> WireGuard VPN IP 10.66.66.1
  -> TAKlite services
```

Recommended service layout:

```text
WireGuard UDP:        Proxmox guest LAN IP:51820 or chosen UDP port
WGDashboard:          Proxmox guest LAN IP:10086
TAKlite admin LAN:    Proxmox guest LAN IP:8080, optional
TAKlite admin VPN:    10.66.66.1:8080
TAK HTTPS/Marti:      10.66.66.1:8443
TLS CoT:              10.66.66.1:8089
Plain CoT:            10.66.66.1:58087
```

The public router/firewall should forward only the WireGuard UDP port to the Proxmox guest. Do not forward TAKlite admin, WGDashboard, CoT, or Marti/datapackage ports unless you intentionally want those surfaces exposed.

## Requirements

The admin must provide:

- Proxmox already installed and working
- Ubuntu or Debian guest, either VM or LXC
- Root shell access to the guest
- Internet access from the guest
- Docker support in the guest
- WireGuard support in the guest
- `/dev/net/tun` available in the guest
- A stable LAN IP for the Proxmox guest
- Admin control of the upstream router/firewall
- One UDP port forwarded from the internet to the guest for WireGuard

For LXC, the guest must have TUN/TAP access. Verify inside the guest:

```bash
ls -l /dev/net/tun
```

Expected result:

```text
crw-rw-rw- ... /dev/net/tun
```

If `/dev/net/tun` is missing, fix the Proxmox guest configuration before running TAKlite. TAKlite cannot make WireGuard work without TUN.

## Installer Profile

During `./install.sh`, choose:

```text
Deployment profile: nat
```

The installer will display detected IPv4 interfaces before asking for values. Confirm that the detected LAN interface and LAN IP match the Proxmox guest.

The NAT profile uses these defaults:

- WireGuard endpoint defaults to the detected public IP. Replace it with a DNS name if you use one.
- WGDashboard bind IP defaults to the detected Proxmox guest LAN IP.
- TAKlite bind IP defaults to `10.66.66.1`.
- TAKlite package/API host defaults to `10.66.66.1`.
- TAKlite admin LAN access defaults to enabled.

TAKlite does not configure the upstream router/firewall. The admin must forward the selected WireGuard UDP port to the Proxmox guest.

Before any configuration is written, the installer prints an exposure plan. For this profile, that plan should show:

- WireGuard endpoint as your public DNS/IP for remote clients, or the guest LAN IP for local-only testing.
- WGDashboard on the Proxmox guest LAN IP.
- TAKlite services on `10.66.66.1`.
- Optional TAKlite admin LAN access only from the LAN CIDR.
- A reminder that the upstream router should forward only the WireGuard UDP port.

## Install Values

Use values like these when prompted.

Use the public DNS name or public IP that remote clients will use for WireGuard:

```text
Public IP or DNS name clients use for WireGuard: YOUR_PUBLIC_IP_OR_DNS
```

For local-only testing before public DNS or port forwarding is ready, use the guest LAN IP instead:

```text
Public IP or DNS name clients use for WireGuard: PROXMOX_GUEST_LAN_IP
```

Use the physical/LAN interface inside the guest:

```text
Public network interface: eth0
```

Use the normal TAKlite VPN defaults unless you have a reason to change them:

```text
WireGuard interface name: wg0
WireGuard server IPv4: 10.66.66.1
WireGuard IPv4 CIDR: 24
WireGuard UDP port: 51820
Initial admin WireGuard IPv4: 10.66.66.2
AllowedIPs for admin client: 0.0.0.0/0
```

Bind WGDashboard to the guest LAN IP if admins should reach it from the local network before joining the VPN. This is the NAT profile default:

```text
WGDashboard bind IP: PROXMOX_GUEST_LAN_IP
WGDashboard port: 10086
```

Keep TAKlite itself on the VPN IP:

```text
TAKlite bind IP: 10.66.66.1
TAKlite API host used in package URLs: 10.66.66.1
TAKlite plain CoT TCP host port: 58087
TAKlite TLS CoT TCP host port: 8089
TAKlite HTTP/admin host port: 8080
TAKlite HTTPS/Marti host port: 8443
```

This makes generated ATAK/WinTAK packages point at the VPN address instead of the LAN address.

## Optional LAN Access To TAKlite Admin

By default, TAKlite admin is normally reached over WireGuard at:

```text
http://10.66.66.1:8080/
```

For a Proxmox lab or local admin workstation, you can also expose only the TAKlite admin UI on the guest LAN IP while leaving TAK services on the VPN IP.

The installer can do this for you:

```text
Expose TAKlite admin UI on LAN IP as well: yes
TAKlite admin LAN bind IP: PROXMOX_GUEST_LAN_IP
LAN CIDR allowed to reach local dashboard/admin bindings: LAN_CIDR
```

If you need to add it after install, create a Compose override:

```bash
cd /root/TAKlite 2>/dev/null || cd /root/taklite

cat > docker-compose.override.yml <<'EOF'
services:
  taklite:
    ports:
      - "PROXMOX_GUEST_LAN_IP:${TAKLITE_HTTP_HOST_PORT:-8080}:8080/tcp"
EOF

docker compose up -d
```

Allow LAN admin access with iptables:

```bash
iptables -C INPUT -s LAN_CIDR -p tcp --dport 8080 -j ACCEPT 2>/dev/null || \
iptables -I INPUT -s LAN_CIDR -p tcp --dport 8080 -j ACCEPT
```

Example values:

```text
PROXMOX_GUEST_LAN_IP = 192.168.0.225
LAN_CIDR = 192.168.0.0/24
```

Do not forward `8080/tcp` from the internet.

## Required Router/Firewall Exposure

TAKlite expects the admin to handle the upstream router/firewall. The only required public exposure is WireGuard UDP:

```text
WAN UDP WIREGUARD_PORT -> PROXMOX_GUEST_LAN_IP UDP WIREGUARD_PORT
```

Do not publicly forward:

```text
8080/tcp    TAKlite admin / user portal
8443/tcp    TAK HTTPS/Marti/datapackage API
8089/tcp    TLS CoT
58087/tcp   Plain CoT
10086/tcp   WGDashboard
22/tcp      SSH, unless intentionally managed elsewhere
```

## Post-Install Verification

Run these inside the Proxmox guest:

```bash
ls -l /dev/net/tun
systemctl is-active wg-quick@wg0
systemctl is-active wg-dashboard
docker compose ps
wg show
ss -tulpen | grep -E '(:51820|:10086|:8080|:8443|:8089|:58087)'
curl -sS http://10.66.66.1:8080/api/health
```

Expected results:

- `/dev/net/tun` exists
- `wg-quick@wg0` is active
- `wg-dashboard` is active
- TAKlite container is running
- WireGuard is listening on the chosen UDP port
- TAKlite services are bound to `10.66.66.1`
- WGDashboard is bound to the guest LAN IP if configured that way
- Optional LAN admin UI is bound to the guest LAN IP only if you created the Compose override

## Known Good Binding Pattern

A working Proxmox guest should look broadly like this:

```text
eth0:  PROXMOX_GUEST_LAN_IP/24
wg0:   10.66.66.1/24
```

Listeners:

```text
0.0.0.0:WIREGUARD_PORT        WireGuard UDP
PROXMOX_GUEST_LAN_IP:10086    WGDashboard
PROXMOX_GUEST_LAN_IP:8080     Optional TAKlite admin LAN access
10.66.66.1:8080               TAKlite admin / portal over VPN
10.66.66.1:8443               TAK HTTPS/Marti/datapackages
10.66.66.1:8089               TLS CoT
10.66.66.1:58087              Plain CoT
```

NAT should allow VPN clients to reach the LAN/internet if `AllowedIPs = 0.0.0.0/0` is used:

```bash
iptables -t nat -S | grep -E '10.66.66|MASQUERADE'
```

The preferred MASQUERADE rule is:

```text
-A POSTROUTING -s 10.66.66.0/24 -o eth0 -j MASQUERADE
```

## Notes For Admins

- The WireGuard endpoint in generated peer configs must match what clients can reach.
- Local LAN clients can use `PROXMOX_GUEST_LAN_IP:WIREGUARD_PORT`.
- Remote clients should use `YOUR_PUBLIC_IP_OR_DNS:WIREGUARD_PORT`.
- Keep TAKlite package URLs pointed at `10.66.66.1`.
- Keep TAKlite TAK services VPN-only.
- Use WGDashboard for peer management.
- Use TAKlite admin for ATAK/WinTAK connection users and datapackages.
- Re-run `docker compose up -d` after changing Compose port bindings.
- Restart `wg-quick@wg0` after changing `/etc/wireguard/wg0.conf`.
- Restart `wg-dashboard` after changing `/opt/WGDashboard/src/wg-dashboard.ini`.
