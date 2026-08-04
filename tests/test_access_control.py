import importlib.util
import json
import os
import pathlib
import tempfile
import threading
import urllib.request
import unittest
import xml.etree.ElementTree as ET
import zipfile
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
SERVICE_PATH = ROOT / "docker" / "taklite" / "taklite_service.py"


class AccessControlTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        tmp = pathlib.Path(self.tmpdir.name)
        os.environ["TAKLITE_DB"] = str(tmp / "taklite.sqlite3")
        os.environ["TAKLITE_PACKAGE_DIR"] = str(tmp / "packages")
        os.environ["TAKLITE_HTTPS_CERT"] = str(tmp / "certs" / "taklite.crt")
        os.environ["TAKLITE_HTTPS_KEY"] = str(tmp / "certs" / "taklite.key")
        os.environ["TAKLITE_CLIENT_CA"] = str(tmp / "certs" / "taklite-ca.crt")
        os.environ["TAKLITE_CERT_PASSWORD"] = "atakatak"
        os.environ["TAKLITE_ACCESS_CONTROL_ENFORCE"] = "true"
        os.environ["TAKLITE_HTTPS_HOST_PORT"] = "8443"
        spec = importlib.util.spec_from_file_location("taklite_service_policy", SERVICE_PATH)
        self.service = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.service)
        self.service.init_db()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_roles_groups_and_links_are_name_agnostic(self):
        observer = self.service.create_access_role("Observer", can_see_all=True, can_send_all=True)
        participant = self.service.create_access_role("Participant", can_see_own_groups=True, can_send_own_groups=True)
        hidden = self.service.create_access_role("Beacon", can_see_own_groups=False, can_send_own_groups=False)
        alpha = self.service.create_access_group("Alpha")
        bravo = self.service.create_access_group("Bravo")
        beacon = self.service.create_access_group("Beacon")

        lead = self.service.create_policy_subject("lead", role_id=observer["id"], group_ids=[alpha["id"]])
        alpha_one = self.service.create_policy_subject("alpha-one", role_id=participant["id"], group_ids=[alpha["id"]])
        alpha_two = self.service.create_policy_subject("alpha-two", role_id=participant["id"], group_ids=[alpha["id"]])
        bravo_one = self.service.create_policy_subject("bravo-one", role_id=participant["id"], group_ids=[bravo["id"]])
        beacon_one = self.service.create_policy_subject("beacon-one", role_id=hidden["id"], group_ids=[beacon["id"]])

        self.assertTrue(self.service.can_subject_see(lead["id"], alpha_one["id"]))
        self.assertTrue(self.service.can_subject_see(lead["id"], bravo_one["id"]))
        self.assertTrue(self.service.can_subject_see(lead["id"], beacon_one["id"]))

        self.assertTrue(self.service.can_subject_see(alpha_one["id"], alpha_two["id"]))
        self.assertFalse(self.service.can_subject_see(alpha_one["id"], bravo_one["id"]))
        self.assertFalse(self.service.can_subject_see(alpha_one["id"], beacon_one["id"]))
        self.assertFalse(self.service.can_subject_see(beacon_one["id"], alpha_one["id"]))

        self.service.set_policy_link(alpha["id"], beacon["id"], can_see=True, can_send=False)
        self.assertTrue(self.service.can_subject_see(alpha_one["id"], beacon_one["id"]))
        self.assertFalse(self.service.can_subject_send(alpha_one["id"], beacon_one["id"]))

    def test_unassigned_users_are_open_when_no_policy_is_assigned(self):
        alpha_one = self.service.create_policy_subject("alpha-one")
        bravo_one = self.service.create_policy_subject("bravo-one")

        self.assertFalse(self.service.access_policy_active())
        self.assertTrue(self.service.can_subject_see(alpha_one["id"], bravo_one["id"]))
        self.assertTrue(self.service.can_subject_send(alpha_one["id"], bravo_one["id"]))
        self.assertTrue(self.service.can_subject_see(bravo_one["id"], alpha_one["id"]))
        self.assertTrue(self.service.cot_delivery_allowed(alpha_one["id"], bravo_one["id"], enforce=True))

        package = {"CreatorUserId": alpha_one["id"], "Tool": "private"}
        self.assertTrue(self.service.package_visible_to_user(package, bravo_one["id"], enforce=True))

        preview = self.service.access_preview(alpha_one["id"])
        self.assertFalse(preview["policy_active"])
        self.assertTrue(preview["open_default"])
        self.assertEqual({item["username"] for item in preview["can_see"]}, {"alpha-one", "bravo-one"})

    def test_access_policy_becomes_active_after_membership_assignment(self):
        participant = self.service.create_access_role("Participant", can_see_own_groups=True, can_send_own_groups=True)
        alpha = self.service.create_access_group("Alpha")
        alpha_one = self.service.create_policy_subject("alpha-one", role_id=participant["id"], group_ids=[alpha["id"]])
        bravo_one = self.service.create_policy_subject("bravo-one")

        self.assertTrue(self.service.access_policy_active())
        self.assertFalse(self.service.can_subject_see(alpha_one["id"], bravo_one["id"]))
        self.assertFalse(self.service.can_subject_send(alpha_one["id"], bravo_one["id"]))

        package = {"CreatorUserId": alpha_one["id"], "Tool": "private"}
        self.assertFalse(self.service.package_visible_to_user(package, bravo_one["id"], enforce=True))

    def test_admin_api_creates_roles_and_groups(self):
        self.service.create_admin("admin", "password1234")
        session = self.service.create_session("admin")
        server = self.service.ThreadingHTTPServer(("127.0.0.1", 0), self.service.HttpHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"

        def request_json(path, payload=None):
            body = None if payload is None else json.dumps(payload).encode("utf-8")
            request = urllib.request.Request(
                f"{base_url}{path}",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Session-Token": session,
                },
                method="GET" if payload is None else "POST",
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                return json.loads(response.read().decode("utf-8"))

        try:
            role = request_json("/api/access-roles/create", {"name": "Range Lead", "can_see_all": True})
            group = request_json("/api/access-groups/create", {"name": "Blue Team", "color": "#64c18c"})
            summary = request_json("/api/access-control")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        self.assertEqual(role["name"], "Range Lead")
        self.assertTrue(role["can_see_all"])
        self.assertEqual(group["name"], "Blue Team")
        self.assertEqual([item["name"] for item in summary["roles"]], ["Range Lead"])
        self.assertEqual([item["name"] for item in summary["groups"]], ["Blue Team"])

    def test_plugin_bootstrap_profile_returns_ip_bound_user(self):
        user = self.service.create_policy_subject("device-one")
        with self.service.db_connect() as conn:
            conn.execute("update portal_users set assigned_ip = ? where id = ?", ("127.0.0.1", user["id"]))
            conn.commit()
        server = self.service.ThreadingHTTPServer(("127.0.0.1", 0), self.service.HttpHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        try:
            request = urllib.request.Request(f"http://127.0.0.1:{server.server_port}/api/plugin/bootstrap/profile")
            with urllib.request.urlopen(request, timeout=5) as response:
                profile = json.loads(response.read().decode("utf-8"))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        self.assertEqual(profile["schema"], "taklite-plugin-profile-v1")
        self.assertEqual(profile["name"], "device-one")
        self.assertTrue(profile["plugin_token"].startswith("tlp_"))
        events = self.service.list_audit_events(event_type="plugin_profile_bootstrap")
        self.assertEqual(events[0]["outcome"], "ok")
        self.assertEqual(events[0]["reason_code"], "profile_returned")
        self.assertEqual(events[0]["actor_name"], "device-one")

    def test_tls_identity_maps_to_portal_user_and_filters_cot_delivery(self):
        participant = self.service.create_access_role("Participant", can_see_own_groups=True, can_send_own_groups=True)
        observer = self.service.create_access_role("Observer", can_see_all=True, can_send_all=True)
        alpha = self.service.create_access_group("Alpha")
        bravo = self.service.create_access_group("Bravo")

        lead = self.service.create_policy_subject("lead", role_id=observer["id"], group_ids=[alpha["id"]])
        alpha_one = self.service.create_policy_subject("alpha-one", role_id=participant["id"], group_ids=[alpha["id"]])
        alpha_two = self.service.create_policy_subject("alpha-two", role_id=participant["id"], group_ids=[alpha["id"]])
        bravo_one = self.service.create_policy_subject("bravo-one", role_id=participant["id"], group_ids=[bravo["id"]])

        self.assertEqual(self.service.client_identity_for_cert("alpha-one")["user_id"], alpha_one["id"])
        self.assertTrue(self.service.cot_delivery_allowed(alpha_one["id"], alpha_two["id"], enforce=True))
        self.assertFalse(self.service.cot_delivery_allowed(alpha_one["id"], bravo_one["id"], enforce=True))
        self.assertTrue(self.service.cot_delivery_allowed(lead["id"], bravo_one["id"], enforce=True))
        self.assertFalse(self.service.cot_delivery_allowed(None, alpha_one["id"], enforce=True))
        self.assertTrue(self.service.cot_delivery_allowed(None, alpha_one["id"], enforce=False))

    def test_individual_user_access_can_replace_and_clear_assignments(self):
        participant = self.service.create_access_role("Participant", can_see_own_groups=True, can_send_own_groups=True)
        alpha = self.service.create_access_group("Alpha")
        bravo = self.service.create_access_group("Bravo")
        user = self.service.create_policy_subject("alpha-one", role_id=participant["id"], group_ids=[alpha["id"]])

        updated = self.service.set_user_access(user["id"], role_id=participant["id"], group_ids=[bravo["id"]])
        self.assertEqual(updated["role_id"], participant["id"])
        self.assertEqual(updated["group_ids"], [bravo["id"]])

        cleared = self.service.set_user_access(user["id"], role_id=None, group_ids=[])
        self.assertIsNone(cleared["role_id"])
        self.assertEqual(cleared["group_ids"], [])

    def test_datapackage_visibility_follows_creator_groups(self):
        participant = self.service.create_access_role("Participant", can_see_own_groups=True, can_send_own_groups=True)
        observer = self.service.create_access_role("Observer", can_see_all=True, can_send_all=True)
        alpha = self.service.create_access_group("Alpha")
        bravo = self.service.create_access_group("Bravo")

        lead = self.service.create_policy_subject("lead", role_id=observer["id"], group_ids=[alpha["id"]])
        alpha_one = self.service.create_policy_subject("alpha-one", role_id=participant["id"], group_ids=[alpha["id"]])
        alpha_two = self.service.create_policy_subject("alpha-two", role_id=participant["id"], group_ids=[alpha["id"]])
        bravo_one = self.service.create_policy_subject("bravo-one", role_id=participant["id"], group_ids=[bravo["id"]])

        package = {"CreatorUserId": alpha_one["id"], "Tool": "private"}
        self.assertTrue(self.service.package_visible_to_user(package, alpha_one["id"], enforce=True))
        self.assertTrue(self.service.package_visible_to_user(package, alpha_two["id"], enforce=True))
        self.assertTrue(self.service.package_visible_to_user(package, lead["id"], enforce=True))
        self.assertFalse(self.service.package_visible_to_user(package, bravo_one["id"], enforce=True))
        self.assertTrue(self.service.package_visible_to_user(package, None, enforce=False))

    def test_access_levels_limit_visibility_inside_allowed_groups(self):
        participant = self.service.create_access_role("Participant", can_see_own_groups=True, can_send_own_groups=True)
        alpha = self.service.create_access_group("Alpha")

        level_one = self.service.create_policy_subject("alpha-one", role_id=participant["id"], group_ids=[alpha["id"]], access_level=1)
        level_two = self.service.create_policy_subject("alpha-two", role_id=participant["id"], group_ids=[alpha["id"]], access_level=2)
        level_four = self.service.create_policy_subject("alpha-four", role_id=participant["id"], group_ids=[alpha["id"]], access_level=4)

        self.assertTrue(self.service.can_subject_see(level_one["id"], level_one["id"]))
        self.assertFalse(self.service.can_subject_see(level_one["id"], level_two["id"]))
        self.assertTrue(self.service.can_subject_see(level_two["id"], level_one["id"]))
        self.assertFalse(self.service.can_subject_send(level_two["id"], level_four["id"]))
        self.assertTrue(self.service.can_subject_send(level_four["id"], level_one["id"]))

    def test_level_tagged_datapackage_filters_after_sender_policy(self):
        participant = self.service.create_access_role("Participant", can_see_own_groups=True, can_send_own_groups=True)
        observer = self.service.create_access_role("Observer", can_see_all=True, can_send_all=True)
        alpha = self.service.create_access_group("Alpha")
        bravo = self.service.create_access_group("Bravo")

        lead = self.service.create_policy_subject("lead", role_id=observer["id"], access_level=4)
        alpha_four = self.service.create_policy_subject("alpha-four", role_id=participant["id"], group_ids=[alpha["id"]], access_level=4)
        alpha_two = self.service.create_policy_subject("alpha-two", role_id=participant["id"], group_ids=[alpha["id"]], access_level=2)
        bravo_four = self.service.create_policy_subject("bravo-four", role_id=participant["id"], group_ids=[bravo["id"]], access_level=4)

        package = {
            "CreatorUserId": alpha_four["id"],
            "Tool": "private",
            "PolicyMode": "level_only",
            "AllowedLevels": [4],
        }

        self.assertTrue(self.service.package_visible_to_user(package, alpha_four["id"], enforce=True))
        self.assertTrue(self.service.package_visible_to_user(package, lead["id"], enforce=True))
        self.assertFalse(self.service.package_visible_to_user(package, alpha_two["id"], enforce=True))
        self.assertFalse(self.service.package_visible_to_user(package, bravo_four["id"], enforce=True))

        blocked = self.service.package_access_for_user(package, alpha_two["id"], enforce=True)
        self.assertFalse(blocked["allowed"])
        self.assertEqual(blocked["reason_code"], "blocked_level_policy")

    def test_datapackage_policy_update_and_preview_explain_access(self):
        participant = self.service.create_access_role("Participant", can_see_own_groups=True, can_send_own_groups=True)
        alpha = self.service.create_access_group("Alpha")
        creator = self.service.create_policy_subject("alpha-four", role_id=participant["id"], group_ids=[alpha["id"]], access_level=4)
        level_four = self.service.create_policy_subject("alpha-four-b", role_id=participant["id"], group_ids=[alpha["id"]], access_level=4)
        level_two = self.service.create_policy_subject("alpha-two", role_id=participant["id"], group_ids=[alpha["id"]], access_level=2)

        payload = b"PK\x05\x06" + (b"\0" * 18)
        self.service.upsert_package("policyhash", "maps.dp.zip", "ANDROID-1", payload, "http://127.0.0.1", creator_user_id=creator["id"])

        updated = self.service.update_datapackage_policy("policyhash", "level_only", [4])
        self.assertEqual(updated["package"]["PolicyLabel"], "Level 4 only")

        preview = self.service.datapackage_access_preview("policyhash")
        by_user = {item["username"]: item for item in preview["items"]}
        self.assertTrue(by_user["alpha-four-b"]["allowed"])
        self.assertFalse(by_user["alpha-two"]["allowed"])
        self.assertEqual(by_user["alpha-two"]["reason_code"], "blocked_level_policy")
        self.assertEqual(preview["allowed_count"], 2)

    def test_datapackage_preview_explains_receive_policy_block(self):
        sender_role = self.service.create_access_role("Sender", can_see_own_groups=True, can_send_own_groups=True, can_receive_own_groups=True)
        receive_blocked_role = self.service.create_access_role("No Receive", can_see_own_groups=True, can_send_own_groups=True, can_receive_own_groups=False)
        alpha = self.service.create_access_group("Alpha")
        sender = self.service.create_policy_subject("sender", role_id=sender_role["id"], group_ids=[alpha["id"]])
        blocked = self.service.create_policy_subject("blocked", role_id=receive_blocked_role["id"], group_ids=[alpha["id"]])

        package = {"CreatorUserId": sender["id"], "Tool": "private", "PolicyMode": "sender", "AllowedLevels": []}
        access = self.service.package_access_for_user(package, blocked["id"], enforce=True)

        self.assertFalse(access["allowed"])
        self.assertEqual(access["reason_code"], "blocked_receive_policy")
        self.assertTrue(self.service.can_subject_send(sender["id"], blocked["id"]))
        self.assertFalse(self.service.can_subject_receive(blocked["id"], sender["id"]))

    def test_plugin_audience_allows_receive_without_pli_visibility(self):
        trusted_role = self.service.create_access_role("Trusted", can_see_own_groups=True, can_send_own_groups=True, can_receive_own_groups=True)
        external_role = self.service.create_access_role("External", can_see_own_groups=True, can_send_own_groups=True, can_receive_own_groups=True)
        trusted_group = self.service.create_access_group("Trusted")
        external_group = self.service.create_access_group("External")
        sender = self.service.create_policy_subject("trusted-one", role_id=trusted_role["id"], group_ids=[trusted_group["id"]])
        receiver = self.service.create_policy_subject("external-one", role_id=external_role["id"], group_ids=[external_group["id"]])

        self.service.set_policy_link(trusted_group["id"], external_group["id"], can_see=False, can_send=True, can_receive=True)
        self.assertFalse(self.service.can_subject_see(receiver["id"], sender["id"]))
        self.assertTrue(self.service.can_send_datapackage(sender["id"], receiver["id"]))

        audience = self.service.plugin_datapackage_audience(sender["id"], {
            "audience_mode": "specific_users",
            "user_ids": [receiver["id"]],
        })

        self.assertIn(receiver["id"], audience["allowed_user_ids"])
        by_user = {item["username"]: item for item in audience["items"]}
        self.assertEqual(by_user["external-one"]["reason_code"], "allowed_plugin_policy")

    def test_plugin_send_records_explicit_recipients_and_blocks_others(self):
        role = self.service.create_access_role("Operator", can_see_own_groups=True, can_send_own_groups=True, can_receive_own_groups=True)
        alpha = self.service.create_access_group("Alpha")
        sender = self.service.create_policy_subject("sender", role_id=role["id"], group_ids=[alpha["id"]])
        target = self.service.create_policy_subject("target", role_id=role["id"], group_ids=[alpha["id"]])
        other = self.service.create_policy_subject("other", role_id=role["id"], group_ids=[alpha["id"]])
        payload = b"PK\x05\x06" + (b"\0" * 18)
        self.service.upsert_package("pluginhash", "plugin-maps.dp.zip", "ANDROID-sender", payload, "http://127.0.0.1", creator_user_id=sender["id"])

        with mock.patch.object(self.service.RELAY, "send_to_user_ids", return_value={"sent": 0, "results": [], "missed_user_ids": [target["id"]]}):
            result = self.service.plugin_send_datapackage(sender["id"], {
                "hash": "pluginhash",
                "audience_mode": "specific_users",
                "user_ids": [target["id"]],
            })

        self.assertTrue(result["ok"])
        self.assertEqual(result["pending"], 1)
        self.assertEqual(self.service.package_explicit_recipient_ids("pluginhash"), {target["id"]})
        package = self.service.row_to_package(self.service.find_package("pluginhash"))
        self.assertTrue(self.service.package_visible_to_user(package, target["id"], enforce=True))
        self.assertTrue(self.service.package_visible_to_user(package, sender["id"], enforce=True))
        blocked = self.service.package_access_for_user(package, other["id"], enforce=True)
        self.assertFalse(blocked["allowed"])
        self.assertEqual(blocked["reason_code"], "blocked_explicit_audience")

    def test_plugin_token_auth_context_and_preview_helpers(self):
        role = self.service.create_access_role("Operator", can_see_own_groups=True, can_send_own_groups=True, can_receive_own_groups=True)
        alpha = self.service.create_access_group("Alpha")
        sender = self.service.create_policy_subject("sender", role_id=role["id"], group_ids=[alpha["id"]])
        target = self.service.create_policy_subject("target", role_id=role["id"], group_ids=[alpha["id"]])
        sender_row = self.service.portal_user_row(self.service.find_portal_user(sender["id"]), include_plugin_token=True)
        token_row = self.service.find_portal_user_by_plugin_token(sender_row["plugin_api_token"])
        user = self.service.portal_user_row(token_row)
        context = self.service.plugin_context_for_user(user)
        preview = self.service.plugin_datapackage_audience(sender["id"], {
            "audience_mode": "specific_users",
            "user_ids": [target["id"]],
        })

        self.assertEqual(context["user"]["username"], "sender")
        self.assertNotIn("plugin_api_token", context["user"])
        self.assertFalse(context["capabilities"]["broad_access"])
        self.assertFalse(context["capabilities"]["can_see_all"])
        self.assertTrue(context["capabilities"]["can_send_own_groups"])
        self.assertTrue(context["capabilities"]["can_receive_own_groups"])
        self.assertIn("specific_users", {item["id"] for item in context["audience_modes"]})
        self.assertEqual(preview["allowed_user_ids"], [target["id"]])

        broad_role = self.service.create_access_role("Broad", can_see_all=True, can_send_all=True, can_receive_all=True)
        broad = self.service.create_policy_subject("broad", role_id=broad_role["id"])
        broad_user = self.service.portal_user_row(self.service.find_portal_user(broad["id"]))
        broad_context = self.service.plugin_context_for_user(broad_user)
        self.assertTrue(broad_context["capabilities"]["broad_access"])
        self.assertTrue(broad_context["capabilities"]["can_see_all"])
        self.assertTrue(broad_context["capabilities"]["can_send_all"])
        self.assertTrue(broad_context["capabilities"]["can_receive_all"])

    def test_device_binding_finds_exact_ip_and_optional_mac(self):
        first = self.service.create_policy_subject("device-one")
        second = self.service.create_policy_subject("device-two")
        with self.service.db_connect() as conn:
            conn.execute("update portal_users set assigned_ip = ?, device_mac = ? where id = ?", ("10.66.66.23", "aa:bb:cc:dd:ee:ff", first["id"]))
            conn.execute("update portal_users set assigned_ip = ? where id = ?", ("10.66.66.24", second["id"]))
            conn.commit()

        self.assertEqual(self.service.validate_device_mac("AABB.CCDD.EEFF"), "aa:bb:cc:dd:ee:ff")
        self.assertEqual(self.service.find_portal_user_by_device_binding("10.66.66.23", "aa-bb-cc-dd-ee-ff")["username"], "device-one")
        self.assertIsNone(self.service.find_portal_user_by_device_binding("10.66.66.23"))
        self.assertEqual(self.service.find_portal_user_by_device_binding("10.66.66.24")["username"], "device-two")

        with self.service.db_connect() as conn:
            conn.execute("update portal_users set assigned_ip = ? where id = ?", ("10.66.66.24", first["id"]))
            conn.commit()
        self.assertIsNone(self.service.find_portal_user_by_device_binding("10.66.66.24"))

    def test_field_enrollment_creates_bound_user_and_profile_once(self):
        cert_dir = pathlib.Path(self.tmpdir.name) / "certs"
        cert_dir.mkdir(exist_ok=True)
        (cert_dir / "taklite-ca.crt").write_text("ca", encoding="utf-8")
        (cert_dir / "taklite-ca.key").write_text("key", encoding="utf-8")
        truststore = cert_dir / "taklite-truststore.p12"
        truststore.write_bytes(b"truststore")

        def fake_openssl(args):
            if "-out" in args:
                pathlib.Path(args[args.index("-out") + 1]).write_bytes(b"generated")

        role = self.service.create_access_role("Field Lead", can_see_own_groups=True, can_send_own_groups=True)
        group = self.service.create_access_group("Alpha")
        enrollment = self.service.create_field_enrollment(
            "Alpha Join",
            "alpha",
            "field add",
            expires_in_hours=2,
            max_uses=1,
            role_id=role["id"],
            group_ids=[group["id"]],
            access_level=2,
            base_url="http://10.66.66.1:8080",
        )

        self.assertTrue(enrollment["active"])
        self.assertEqual(enrollment["remaining_uses"], 1)
        self.assertIn("/connect/enroll?code=", enrollment["join_url"])

        with mock.patch.object(self.service, "ensure_truststore_file", return_value=truststore), \
             mock.patch.object(self.service, "run_openssl", side_effect=fake_openssl):
            result = self.service.redeem_field_enrollment(
                enrollment["join_code"],
                source_ip="10.66.66.44",
                device_id="AABBCCDDEEFF",
                display_name="Alpha One",
                base_url="http://10.66.66.1:8080",
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["user"]["assigned_ip"], "10.66.66.44")
        self.assertEqual(result["user"]["device_mac"], "aa:bb:cc:dd:ee:ff")
        self.assertEqual(result["user"]["role_id"], role["id"])
        self.assertEqual(result["user"]["group_ids"], [group["id"]])
        self.assertEqual(result["user"]["access_level"], 2)
        self.assertTrue(result["profile"]["plugin_token"].startswith("tlp_"))
        self.assertIn("/connect/", result["connection_package_url"])

        updated = self.service.list_field_enrollments("http://10.66.66.1:8080")[0]
        self.assertEqual(updated["used_count"], 1)
        self.assertEqual(updated["remaining_uses"], 0)
        self.assertFalse(updated["active"])
        with self.assertRaisesRegex(ValueError, "no remaining uses"):
            self.service.redeem_field_enrollment(enrollment["join_code"], "10.66.66.45", "", "Alpha Two")

    def test_admin_datapackage_send_records_offline_pending_delivery(self):
        creator = self.service.create_policy_subject("creator")
        target = self.service.create_policy_subject("target")
        payload = b"PK\x05\x06" + (b"\0" * 18)
        self.service.upsert_package("sendhash", "maps.dp.zip", "ANDROID-1", payload, "http://127.0.0.1", creator_user_id=creator["id"])

        with mock.patch.object(self.service.RELAY, "send_to_user_ids", return_value={"sent": 0, "results": [], "missed_user_ids": [target["id"]]}):
            result = self.service.send_datapackage_to_clients({"hash": "sendhash", "user_ids": [target["id"]]})

        self.assertTrue(result["ok"])
        self.assertEqual(result["sent"], 0)
        self.assertEqual(result["pending"], 1)
        self.assertEqual(result["results"][0]["reason_code"], "pending_offline")

        deliveries = self.service.list_datapackage_deliveries("sendhash")
        self.assertEqual(len(deliveries), 1)
        self.assertEqual(deliveries[0]["status"], "pending")
        self.assertEqual(deliveries[0]["target_user_id"], target["id"])

    def test_admin_datapackage_send_records_successful_user_delivery(self):
        creator = self.service.create_policy_subject("creator")
        target = self.service.create_policy_subject("target")
        payload = b"PK\x05\x06" + (b"\0" * 18)
        self.service.upsert_package("senthash", "maps.dp.zip", "ANDROID-1", payload, "http://127.0.0.1", creator_user_id=creator["id"])

        relay_result = {
            "sent": 1,
            "results": [{
                "user_id": target["id"],
                "username": "target",
                "uid": "ANDROID-target",
                "callsign": "TARGET",
                "ip": "10.66.66.8",
                "sent": True,
                "reason_code": "sent",
                "reason": "File-share event sent to connected client.",
            }],
            "missed_user_ids": [],
        }
        with mock.patch.object(self.service.RELAY, "send_to_user_ids", return_value=relay_result):
            result = self.service.send_datapackage_to_clients({"hash": "senthash", "user_ids": [target["id"]]})

        self.assertTrue(result["ok"])
        self.assertEqual(result["sent"], 1)
        self.assertEqual(result["pending"], 0)
        self.assertEqual(result["results"][0]["status"], "sent")

        deliveries = self.service.list_datapackage_deliveries("senthash")
        self.assertEqual(len(deliveries), 1)
        self.assertEqual(deliveries[0]["status"], "sent")
        self.assertEqual(deliveries[0]["target_uid"], "ANDROID-target")

    def test_datapackage_filename_policy_parser_accepts_field_names(self):
        self.assertEqual(
            self.service.parse_datapackage_filename_policy("maps__lvl4ONLY.dp.zip"),
            {"mode": "level_only", "allowed_levels": [4], "label": "Level 4 only"},
        )
        self.assertEqual(
            self.service.parse_datapackage_filename_policy("maps__tl-lvl4-all.dp.zip")["allowed_levels"],
            [1, 2, 3, 4],
        )
        self.assertEqual(
            self.service.parse_datapackage_filename_policy("maps__lvl4and2ONLY.dp.zip")["allowed_levels"],
            [2, 4],
        )
        self.assertEqual(
            self.service.parse_datapackage_filename_policy("maps.dp.zip")["mode"],
            "sender",
        )

    def test_public_tool_datapackage_is_visible_without_identity(self):
        package = {"CreatorUserId": None, "Visibility": "private", "Tool": "public"}

        self.assertTrue(self.service.package_visible_to_user(package, None, enforce=True))

    def test_user_created_public_tool_datapackage_still_follows_access_policy(self):
        participant = self.service.create_access_role("Participant", can_see_own_groups=True, can_send_own_groups=True)
        alpha = self.service.create_access_group("Alpha")
        bravo = self.service.create_access_group("Bravo")
        alpha_one = self.service.create_policy_subject("alpha-one", role_id=participant["id"], group_ids=[alpha["id"]])
        alpha_two = self.service.create_policy_subject("alpha-two", role_id=participant["id"], group_ids=[alpha["id"]])
        bravo_one = self.service.create_policy_subject("bravo-one", role_id=participant["id"], group_ids=[bravo["id"]])

        package = {
            "CreatorUserId": alpha_one["id"],
            "Visibility": "public",
            "Tool": "public",
            "PolicyMode": "sender",
            "AllowedLevels": [],
        }

        self.assertFalse(self.service.package_visible_to_user(package, None, enforce=True))
        self.assertTrue(self.service.package_visible_to_user(package, alpha_two["id"], enforce=True))
        blocked = self.service.package_access_for_user(package, bravo_one["id"], enforce=True)
        self.assertFalse(blocked["allowed"])
        self.assertEqual(blocked["reason_code"], "blocked_sender_policy")

    def test_access_preview_reports_visible_and_seen_by_users(self):
        admin = self.service.create_access_role("Admin", can_see_all=True, can_send_all=True)
        student = self.service.create_access_role("Student", can_see_own_groups=True, can_send_own_groups=True)
        hidden = self.service.create_access_role("Hidden", can_see_own_groups=False, can_send_own_groups=False)
        alpha = self.service.create_access_group("Alpha")
        beacon = self.service.create_access_group("Beacon")

        lead = self.service.create_policy_subject("lead", role_id=admin["id"], group_ids=[])
        alpha_one = self.service.create_policy_subject("alpha-one", role_id=student["id"], group_ids=[alpha["id"]])
        alpha_two = self.service.create_policy_subject("alpha-two", role_id=student["id"], group_ids=[alpha["id"]])
        beacon_one = self.service.create_policy_subject("beacon-one", role_id=hidden["id"], group_ids=[beacon["id"]])

        alpha_preview = self.service.access_preview(alpha_one["id"])
        beacon_preview = self.service.access_preview(beacon_one["id"])

        self.assertEqual({item["username"] for item in alpha_preview["can_see"]}, {"alpha-one", "alpha-two"})
        self.assertNotIn("lead", {item["username"] for item in alpha_preview["can_see"]})
        self.assertNotIn("beacon-one", {item["username"] for item in alpha_preview["can_see"]})
        self.assertEqual({item["username"] for item in beacon_preview["can_see"]}, {"beacon-one"})
        self.assertIn("lead", {item["username"] for item in beacon_preview["seen_by"]})

    def test_runtime_health_reports_database_and_storage(self):
        health = self.service.runtime_health()

        self.assertTrue(health["database"]["ok"])
        self.assertGreaterEqual(health["storage"]["package_bytes"], 0)
        self.assertIn("access_enforcement", health["security"])

    def test_cot_send_timeout_is_scoped_to_outbound_writes(self):
        class FakeRequest:
            def __init__(self):
                self.timeout = None
                self.timeouts = []
                self.sent = []

            def gettimeout(self):
                return self.timeout

            def settimeout(self, value):
                self.timeouts.append(value)
                self.timeout = value

            def sendall(self, data):
                self.sent.append(data)

        class FakeHandler:
            def __init__(self):
                self.request = FakeRequest()
                self.send_lock = threading.Lock()

        relay = self.service.CotRelay()
        handler = FakeHandler()

        self.assertTrue(relay.send_to(handler, b"<event></event>"))
        self.assertEqual(handler.request.sent, [b"<event></event>"])
        self.assertEqual(handler.request.timeouts, [self.service.SOCKET_SEND_TIMEOUT_SECONDS, None])
        self.assertIsNone(handler.request.gettimeout())

    def test_connection_datapackage_uses_connection_scoped_cert_preferences(self):
        cert_dir = pathlib.Path(self.tmpdir.name) / "certs"
        cert_dir.mkdir(exist_ok=True)
        (cert_dir / "taklite-ca.crt").write_text("ca", encoding="utf-8")
        (cert_dir / "taklite-ca.key").write_text("key", encoding="utf-8")
        truststore = cert_dir / "taklite-truststore.p12"
        truststore.write_bytes(b"truststore")
        openssl_calls = []

        def fake_openssl(args):
            openssl_calls.append(args)
            if "-out" in args:
                out_path = pathlib.Path(args[args.index("-out") + 1])
                out_path.write_bytes(b"generated")

        with mock.patch.object(self.service, "ensure_truststore_file", return_value=truststore), \
             mock.patch.object(self.service, "run_openssl", side_effect=fake_openssl):
            profile = self.service.create_cert_profile("alpha-phone", "test", plugin_token="tlp_testprofiletoken1234567890")

        package = cert_dir / profile["datapackage_file"]
        with zipfile.ZipFile(package) as zf:
            names = zf.namelist()

        self.assertEqual(names.count("MANIFEST/manifest.xml"), 1)
        self.assertEqual(names.count("certs/server.pref"), 1)
        self.assertEqual(names.count("certs/taklite-server.pref"), 0)
        self.assertEqual(names.count("certs/10.66.66.1.p12"), 1)
        self.assertEqual(names.count("certs/alpha-phone.p12"), 1)
        self.assertNotIn("manifest.xml", names)
        self.assertNotIn("server.pref", names)
        self.assertNotIn("taklite-server.pref", names)
        self.assertEqual(len(names), len(set(names)))
        self.assertLess(names.index("certs/10.66.66.1.p12"), names.index("certs/server.pref"))
        self.assertLess(names.index("certs/alpha-phone.p12"), names.index("certs/server.pref"))
        with zipfile.ZipFile(package) as zf:
            server_pref = zf.read("certs/server.pref").decode("utf-8")
            manifest = zf.read("MANIFEST/manifest.xml").decode("utf-8")
            plugin_config = json.loads(zf.read("certs/taklite-plugin.json").decode("utf-8"))
        self.assertIn('<entry key="description0" class="class java.lang.String">TAKlite alpha-phone</entry>', server_pref)
        self.assertEqual(ET.fromstring(server_pref).tag, "preferences")
        self.assertIn('<entry key="caLocation0" class="class java.lang.String">cert/10.66.66.1.p12</entry>', server_pref)
        self.assertIn('<entry key="certificateLocation0" class="class java.lang.String">cert/alpha-phone.p12</entry>', server_pref)
        self.assertNotIn('<entry key="caLocation" class="class java.lang.String">', server_pref)
        self.assertNotIn('<entry key="certificateLocation" class="class java.lang.String">', server_pref)
        self.assertNotIn('<entry key="caPassword" class="class java.lang.String">', server_pref)
        self.assertNotIn('<entry key="clientPassword" class="class java.lang.String">', server_pref)
        self.assertIn('<entry key="apiSecureServerPort" class="class java.lang.String">8443</entry>', server_pref)
        self.assertIn('<entry key="apiUnsecureServerPort" class="class java.lang.String">8080</entry>', server_pref)
        self.assertIn('<Parameter name="onReceiveImport" value="true"/>', manifest)
        self.assertIn('<Parameter name="onReceiveDelete" value="false"/>', manifest)
        self.assertLess(manifest.index('zipEntry="certs/10.66.66.1.p12"'), manifest.index('zipEntry="certs/server.pref"'))
        self.assertLess(manifest.index('zipEntry="certs/alpha-phone.p12"'), manifest.index('zipEntry="certs/server.pref"'))
        self.assertIn('<Content ignore="false" zipEntry="certs/server.pref"/>', manifest)
        self.assertIn('<Content ignore="false" zipEntry="certs/taklite-plugin.json"/>', manifest)
        self.assertIn('<Content ignore="false" zipEntry="certs/10.66.66.1.p12"/>', manifest)
        self.assertIn('<Content ignore="false" zipEntry="certs/alpha-phone.p12"/>', manifest)
        self.assertIn("certs/taklite-plugin.json", names)
        self.assertEqual(plugin_config["schema"], "taklite-plugin-profile-v1")
        self.assertEqual(plugin_config["name"], "alpha-phone")
        self.assertEqual(plugin_config["server_url"], "http://10.66.66.1:8080")
        self.assertEqual(plugin_config["server_urls"], ["http://10.66.66.1:8080", "https://10.66.66.1:8443"])
        self.assertEqual(plugin_config["connect_string"], "10.66.66.1:8089:ssl")
        self.assertEqual(plugin_config["ports"]["http"], 8080)
        self.assertEqual(plugin_config["ports"]["https"], 8443)
        self.assertEqual(plugin_config["ports"]["cot_tls"], 8089)
        self.assertEqual(plugin_config["plugin_token"], "tlp_testprofiletoken1234567890")
        self.assertEqual(plugin_config["default_audience_mode"], "all_allowed")
        self.assertEqual(plugin_config["api"]["me"], "/api/plugin/me")
        self.assertEqual(plugin_config["api"]["preview"], "/api/plugin/datapackages/preview")
        self.assertEqual(plugin_config["api"]["upload"], "/api/plugin/datapackages/upload")
        self.assertEqual(plugin_config["api"]["send"], "/api/plugin/datapackages/send")
        pkcs12_calls = [call for call in openssl_calls if call[:2] == ["pkcs12", "-export"]]
        self.assertEqual(len(pkcs12_calls), 1)
        self.assertIn("-certpbe", pkcs12_calls[0])
        self.assertIn("PBE-SHA1-3DES", pkcs12_calls[0])
        self.assertIn("-keypbe", pkcs12_calls[0])
        self.assertIn("-macalg", pkcs12_calls[0])
        self.assertIn("sha1", pkcs12_calls[0])

    def test_truststore_file_uses_stable_non_server_cert_name(self):
        cert_dir = pathlib.Path(self.tmpdir.name) / "certs"
        cert_dir.mkdir(exist_ok=True)
        (cert_dir / "taklite-ca.crt").write_text("ca", encoding="utf-8")
        (cert_dir / "taklite-ca.key").write_text("key", encoding="utf-8")
        openssl_calls = []

        def fake_openssl(args):
            openssl_calls.append(args)
            out_path = pathlib.Path(args[args.index("-out") + 1])
            out_path.write_bytes(b"truststore")

        with mock.patch.object(self.service.shutil, "which", return_value=None), \
             mock.patch.object(self.service, "run_openssl", side_effect=fake_openssl):
            truststore = self.service.ensure_truststore_file()

        self.assertEqual(truststore.name, "taklite-truststore.p12")
        self.assertTrue(truststore.exists())
        pkcs12_calls = [call for call in openssl_calls if call[:2] == ["pkcs12", "-export"]]
        self.assertEqual(len(pkcs12_calls), 1)
        self.assertIn("-nokeys", pkcs12_calls[0])
        self.assertNotIn("-certfile", pkcs12_calls[0])
        self.assertNotIn("-inkey", pkcs12_calls[0])
        self.assertIn(str(cert_dir / "taklite-ca.crt"), pkcs12_calls[0])
        self.assertIn("-certpbe", pkcs12_calls[0])
        self.assertIn("PBE-SHA1-3DES", pkcs12_calls[0])
        self.assertNotIn("-keypbe", pkcs12_calls[0])
        self.assertIn("-macalg", pkcs12_calls[0])
        self.assertIn("sha1", pkcs12_calls[0])

    def test_server_cert_identity_parses_ip_dns_and_cn(self):
        text = """
subject=CN=10.0.2.2
X509v3 Subject Alternative Name:
    IP Address:10.0.2.2, IP Address:192.168.0.115, DNS:taklite.local, DNS:Example.local
"""
        identities = self.service.cert_identity_set_from_text(text)

        self.assertIn(("IP", "10.0.2.2"), identities)
        self.assertIn(("IP", "192.168.0.115"), identities)
        self.assertIn(("DNS", "taklite.local"), identities)
        self.assertIn(("DNS", "example.local"), identities)

    def test_server_cert_sans_include_server_public_and_local_names(self):
        original_server = self.service.SERVER_HOST
        original_public = self.service.PUBLIC_HOST
        try:
            self.service.SERVER_HOST = "192.168.0.115"
            self.service.PUBLIC_HOST = "axon.local"

            hosts = self.service.tls_server_hosts()
            sans = self.service.subject_alt_name_for_hosts(hosts)
        finally:
            self.service.SERVER_HOST = original_server
            self.service.PUBLIC_HOST = original_public

        self.assertIn("IP:192.168.0.115", sans)
        self.assertIn("DNS:axon.local", sans)
        self.assertIn("DNS:localhost", sans)
        self.assertIn("IP:127.0.0.1", sans)
        self.assertIn("DNS:taklite.local", sans)


if __name__ == "__main__":
    unittest.main()
