import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class ReleasePackagingTests(unittest.TestCase):
    def test_dockerfile_makes_service_readable_by_non_root_user(self):
        dockerfile = (ROOT / "docker" / "taklite" / "Dockerfile").read_text()

        self.assertIn("COPY --chmod=0644 docker/taklite/taklite_service.py /app/taklite_service.py", dockerfile)

    def test_release_defaults_enable_policy_ready_secure_mode(self):
        compose = (ROOT / "docker-compose.yml").read_text()
        env_example = (ROOT / ".env.example").read_text()
        installer = (ROOT / "install.sh").read_text()

        self.assertIn("TAKLITE_COT_TLS_REQUIRE_CLIENT_CERT: \"${TAKLITE_COT_TLS_REQUIRE_CLIENT_CERT:-true}\"", compose)
        self.assertIn("TAKLITE_ALLOW_LEGACY_CLIENT_CERT: \"${TAKLITE_ALLOW_LEGACY_CLIENT_CERT:-false}\"", compose)
        self.assertIn("TAKLITE_ACCESS_CONTROL_ENFORCE: \"${TAKLITE_ACCESS_CONTROL_ENFORCE:-true}\"", compose)
        self.assertIn("TAKLITE_LEGACY_CERT_DOWNLOADS: \"${TAKLITE_LEGACY_CERT_DOWNLOADS:-false}\"", compose)
        self.assertIn("TAKLITE_GUI_UPDATE_ENABLED: \"${TAKLITE_GUI_UPDATE_ENABLED:-false}\"", compose)
        self.assertIn("TAKLITE_GUI_UPDATE_REQUEST_DIR: \"${TAKLITE_GUI_UPDATE_REQUEST_DIR:-}\"", compose)
        self.assertIn("TAKLITE_SETTINGS_REQUEST_DIR: \"${TAKLITE_SETTINGS_REQUEST_DIR:-}\"", compose)
        self.assertIn("TAKLITE_FIREWALL_REQUEST_DIR: \"${TAKLITE_FIREWALL_REQUEST_DIR:-}\"", compose)
        self.assertIn("TAKLITE_WGDASHBOARD_URL: \"${TAKLITE_WGDASHBOARD_URL-http://10.66.66.1:10086}\"", compose)
        self.assertIn("TAKLITE_AUTO_INIT_CERTS: \"${TAKLITE_AUTO_INIT_CERTS:-false}\"", compose)
        self.assertIn('user: "${TAKLITE_CONTAINER_USER:-10001:10001}"', compose)
        self.assertIn("TAKLITE_SERVER_HOST=10.66.66.1", env_example)
        self.assertIn("TAKLITE_AUTO_INIT_CERTS=false", env_example)
        self.assertIn("TAKLITE_CONTAINER_USER=10001:10001", env_example)
        self.assertIn("TAKLITE_COT_TLS_REQUIRE_CLIENT_CERT=true", env_example)
        self.assertIn("TAKLITE_ALLOW_LEGACY_CLIENT_CERT=false", env_example)
        self.assertIn("TAKLITE_ACCESS_CONTROL_ENFORCE=true", env_example)
        self.assertIn("TAKLITE_LEGACY_CERT_DOWNLOADS=false", env_example)
        self.assertIn("TAKLITE_GUI_UPDATE_ENABLED=false", env_example)
        self.assertIn("TAKLITE_GUI_UPDATE_REQUEST_DIR=", env_example)
        self.assertIn("TAKLITE_SETTINGS_REQUEST_DIR=", env_example)
        self.assertIn("TAKLITE_FIREWALL_REQUEST_DIR=", env_example)
        self.assertIn('prompt_default "Enable secure mode: require TLS cert identity and enforce groups" "yes"', installer)
        self.assertIn("TAKLITE_CONTAINER_USER=10001:10001", installer)
        self.assertIn("TAKLITE_AUTO_INIT_CERTS=false", installer)
        self.assertIn("TAKLITE_GUI_UPDATE_ENABLED=true", installer)
        self.assertIn("TAKLITE_GUI_UPDATE_REQUEST_DIR=/data/gui-update", installer)
        self.assertIn("TAKLITE_SETTINGS_REQUEST_DIR=/data/settings", installer)
        self.assertIn("TAKLITE_FIREWALL_REQUEST_DIR=/data/firewall", installer)
        self.assertIn('if command -v docker >/dev/null 2>&1; then', installer)
        self.assertIn('log "Existing Docker install detected; reusing it"', installer)
        self.assertIn("apt_package_available() {", installer)
        self.assertIn("apt_packages_available docker-ce docker-ce-cli containerd.io", installer)
        self.assertIn("docker-ce docker-ce-cli containerd.io", installer)
        self.assertIn("docker_packages=(docker.io)", installer)
        self.assertIn('if docker compose version >/dev/null 2>&1; then', installer)
        self.assertIn('log "Existing Docker Compose v2 detected; reusing it"', installer)
        self.assertIn('Deployment profiles:', installer)
        self.assertIn('profile="$(prompt_default "Deployment profile" "cloud")"', installer)
        self.assertIn('nat|router|proxmox)', installer)
        self.assertIn('local|lan|lab)', installer)
        self.assertIn('TAKLITE_ADMIN_LAN_BIND_IP=', installer)
        self.assertIn('docker-compose.override.yml', installer)
        self.assertIn('validate_settings() {', installer)
        self.assertIn('print_exposure_summary() {', installer)
        self.assertIn('Continue with this install plan', installer)
        self.assertIn('WireGuard endpoint must be a public IP, LAN IP, or DNS name clients can reach', installer)
        self.assertIn('network interface does not exist', installer)

        updater = (ROOT / "update.sh").read_text()
        append_start = updater.index("append_env_default() {")
        append_end = updater.index("set_env_value() {")
        append_body = updater[append_start:append_end]
        self.assertIn('if ! grep -q "^${key}=" "${env_file}"; then', append_body)
        self.assertNotIn("sed -i", append_body)
        self.assertIn('append_env_default "${env_file}" "TAKLITE_COT_TLS_REQUIRE_CLIENT_CERT" "true"', updater)
        self.assertIn('append_env_default "${env_file}" "TAKLITE_ALLOW_LEGACY_CLIENT_CERT" "false"', updater)
        self.assertIn('append_env_default "${env_file}" "TAKLITE_ACCESS_CONTROL_ENFORCE" "true"', updater)
        self.assertIn('append_env_default "${env_file}" "TAKLITE_LEGACY_CERT_DOWNLOADS" "false"', updater)
        self.assertIn('append_env_default "${env_file}" "TAKLITE_SERVER_HOST" "10.66.66.1"', updater)
        self.assertIn('append_env_default "${env_file}" "TAKLITE_CONTAINER_USER" "10001:10001"', updater)
        self.assertIn('append_env_default "${env_file}" "TAKLITE_AUTO_INIT_CERTS" "false"', updater)
        self.assertIn('append_env_default "${env_file}" "TAKLITE_GUI_UPDATE_ENABLED" "true"', updater)
        self.assertIn('append_env_default "${env_file}" "TAKLITE_SETTINGS_REQUEST_DIR" "/data/settings"', updater)
        self.assertIn('append_env_default "${env_file}" "TAKLITE_FIREWALL_REQUEST_DIR" "/data/firewall"', updater)
        self.assertIn("taklite-gui-update.path", updater)
        self.assertIn("taklite-settings.path", updater)
        self.assertIn("taklite-firewall.path", updater)
        self.assertIn("--exclude 'plugins/'", updater)
        self.assertIn("--exclude 'docs/plugin-controlled-delivery.md'", updater)
        self.assertIn('"${APP_DIR}/uninstall.sh"', updater)
        self.assertIn("EXPECTED_SHA256", updater)
        self.assertIn("sha256sum -c -", updater)
        self.assertIn("--release-zip", updater)

        service = (ROOT / "docker" / "taklite" / "taklite_service.py").read_text()
        self.assertIn('VERSION = "TAKlite 0.2.25"', service)
        self.assertIn('TAKLITE_COT_TLS_REQUIRE_CLIENT_CERT", "true"', service)
        self.assertIn('TAKLITE_ALLOW_LEGACY_CLIENT_CERT", "false"', service)
        self.assertIn('TAKLITE_ACCESS_CONTROL_ENFORCE", "true"', service)
        self.assertIn('TAKLITE_LEGACY_CERT_DOWNLOADS", "false"', service)
        self.assertIn('TAKLITE_AUTO_INIT_CERTS", "false"', service)
        self.assertIn("verified_release_asset", service)
        self.assertIn("validate_sha256", service)

    def test_uninstall_removes_host_side_security_and_runner_state(self):
        uninstall = (ROOT / "uninstall.sh").read_text()

        self.assertIn("/etc/fail2ban/jail.d/taklite-vps.local", uninstall)
        self.assertIn("/etc/fail2ban/jail.d/taklite-auth.local", uninstall)
        self.assertIn("/etc/fail2ban/filter.d/taklite-auth.conf", uninstall)
        self.assertIn("taklite-gui-update.path", uninstall)
        self.assertIn("taklite-settings.path", uninstall)
        self.assertIn("taklite-firewall.path", uninstall)
        self.assertIn("/usr/local/sbin/taklite-gui-update-runner", uninstall)

    def test_release_packagers_exclude_local_plugin_prototypes(self):
        packager = (ROOT / "scripts" / "package-windows-offline.sh").read_text()
        reinstall = (ROOT / "reinstall.sh").read_text()
        dockerignore = (ROOT / ".dockerignore").read_text()
        readme = (ROOT / "README.md").read_text()

        for text in (packager, reinstall, dockerignore):
            self.assertIn("plugins", text)
            self.assertIn("docs/plugin-controlled-delivery.md", text)
            self.assertIn("docs/wintak-plugin-api.md", text)
        self.assertNotIn("plugins/atak-taklite-control", readme)
        self.assertNotIn("plugin-controlled-delivery.md", readme)
        self.assertNotIn("wintak-plugin-api.md", readme)

    def test_gui_update_runner_requires_hash_verified_release_zip(self):
        installer = (ROOT / "install.sh").read_text()
        updater = (ROOT / "update.sh").read_text()

        for script in (installer, updater):
            self.assertIn("RELEASE_ZIP_URL", script)
            self.assertIn("EXPECTED_SHA256", script)
            self.assertIn("sha256sum -c -", script)
            self.assertIn("--release-zip", script)

    def test_installer_configures_taklite_auth_fail2ban_filter(self):
        installer = (ROOT / "install.sh").read_text()

        self.assertIn("/etc/fail2ban/filter.d/taklite-auth.conf", installer)
        self.assertIn("[taklite-auth]", installer)
        self.assertIn("TAKlite auth failure scope=", installer)
        self.assertIn("/var/lib/docker/containers/*/*.log", installer)

    def test_installer_uses_capability_based_linux_gate(self):
        installer = (ROOT / "install.sh").read_text()

        self.assertIn("continuing in best-effort mode", installer)
        self.assertIn("apt-get not found; assuming host dependencies were installed manually", installer)
        self.assertIn("require_commands curl fail2ban-client git ip iptables python3 qrencode rsync wg wg-quick openssl zip docker", installer)
        self.assertNotIn("22|24|26", installer)
        self.assertNotIn("unsupported Ubuntu version", installer)

    def test_portable_desktop_assets_are_packaged(self):
        env_desktop = (ROOT / ".env.desktop.example").read_text()
        portable_sh = ROOT / "portable-start.sh"
        portable_ps1 = ROOT / "portable-start.ps1"
        windows_cmd = ROOT / "Install TAKlite.cmd"
        windows_installer = ROOT / "scripts" / "Install-TAKliteWindows.ps1"
        windows_guide = ROOT / "docs" / "windows-docker-desktop.md"
        windows_guide_pdf = ROOT / "docs" / "TAKlite-Windows-Docker-Desktop-Guide.pdf"

        self.assertTrue(portable_sh.exists())
        self.assertTrue(portable_ps1.exists())
        self.assertTrue(windows_cmd.exists())
        self.assertTrue(windows_installer.exists())
        self.assertTrue(windows_guide.exists())
        self.assertTrue(windows_guide_pdf.exists())
        self.assertIn("TAKLITE_AUTO_INIT_CERTS=true", env_desktop)
        self.assertIn("WG_BIND_IP=127.0.0.1", env_desktop)
        self.assertIn("portable mode does not install wireguard", portable_sh.read_text().lower())
        self.assertIn("Portable mode does not install WireGuard", portable_ps1.read_text())
        self.assertIn("Install-TAKliteWindows.ps1", windows_cmd.read_text())
        self.assertIn("Get-NetAdapter -Physical", windows_installer.read_text())
        self.assertIn("New-NetFirewallRule", windows_installer.read_text())
        self.assertIn("TAKLITE_PUBLIC_HOST=$BindIp", windows_installer.read_text())
        self.assertIn("Rerun with -EnvMode Recreate", windows_installer.read_text())
        self.assertIn("TAKLITE_GUI_UPDATE_ENABLED=true", windows_installer.read_text())
        self.assertIn("GuiUpdateRunner-TAKliteWindows.ps1", windows_installer.read_text())
        self.assertTrue((ROOT / "scripts" / "GuiUpdateRunner-TAKliteWindows.ps1").exists())
        self.assertIn("--build", (ROOT / "scripts" / "Update-TAKliteWindows.ps1").read_text())
        self.assertIn("Running Next To Axon", windows_guide.read_text())
        self.assertIn("Update TAKlite.cmd", windows_guide.read_text())
        self.assertIn("update", windows_guide.read_text().lower())

    def test_frontend_primary_user_workflow_does_not_show_redundant_packages_nav(self):
        frontend = (ROOT / "frontend" / "src" / "main.jsx").read_text()

        self.assertIn("Connection Users", frontend)
        self.assertIn("/api/portal-users/create", frontend)
        self.assertNotIn("id: 'packages'", frontend)


if __name__ == "__main__":
    unittest.main()
