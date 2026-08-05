#!/usr/bin/env python3
import base64
import hashlib
import hmac
import html
import ipaddress
import io
import json
import os
import re
import secrets
import shlex
import shutil
import socket
import sqlite3
import ssl
import subprocess
import threading
import time
import uuid
import zipfile
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from socketserver import ThreadingMixIn, TCPServer, BaseRequestHandler
from urllib.parse import parse_qs, quote, unquote, urlparse
from urllib.request import Request, urlopen

HTTP_BIND = os.environ.get("TAKLITE_HTTP_BIND", "0.0.0.0")
HTTP_PORT = int(os.environ.get("TAKLITE_HTTP_PORT", "8080"))
HTTP_PUBLIC_PORT = int(os.environ.get("TAKLITE_HTTP_PUBLIC_PORT", os.environ.get("TAKLITE_HTTP_HOST_PORT", str(HTTP_PORT))))
HTTPS_BIND = os.environ.get("TAKLITE_HTTPS_BIND", "0.0.0.0")
HTTPS_PORT = int(os.environ.get("TAKLITE_HTTPS_PORT", "8443"))
HTTPS_PUBLIC_PORT = int(os.environ.get("TAKLITE_HTTPS_PUBLIC_PORT", os.environ.get("TAKLITE_HTTPS_HOST_PORT", str(HTTPS_PORT))))
HTTPS_CERT = Path(os.environ.get("TAKLITE_HTTPS_CERT", "/certs/taklite.crt"))
HTTPS_KEY = Path(os.environ.get("TAKLITE_HTTPS_KEY", "/certs/taklite.key"))
CERT_DIR = HTTPS_CERT.parent
CLIENT_CA = Path(os.environ.get("TAKLITE_CLIENT_CA", "/certs/taklite-ca.crt"))
AUTO_INIT_CERTS = os.environ.get("TAKLITE_AUTO_INIT_CERTS", "false").lower() in ("1", "true", "yes", "on")
COT_BIND = os.environ.get("TAKLITE_COT_BIND", "0.0.0.0")
COT_PORT = int(os.environ.get("TAKLITE_COT_PORT", "58087"))
COT_PUBLIC_PORT = int(os.environ.get("TAKLITE_COT_PUBLIC_PORT", os.environ.get("TAKLITE_COT_HOST_PORT", str(COT_PORT))))
COT_TLS_BIND = os.environ.get("TAKLITE_COT_TLS_BIND", "0.0.0.0")
COT_TLS_PORT = int(os.environ.get("TAKLITE_COT_TLS_PORT", "8089"))
COT_TLS_PUBLIC_PORT = int(os.environ.get("TAKLITE_COT_TLS_PUBLIC_PORT", os.environ.get("TAKLITE_COT_TLS_HOST_PORT", str(COT_TLS_PORT))))
ADMIN_TOKEN = os.environ.get("TAKLITE_ADMIN_TOKEN", "")
PUBLIC_HOST = os.environ.get("TAKLITE_PUBLIC_HOST", "")
SERVER_HOST = os.environ.get("TAKLITE_SERVER_HOST", PUBLIC_HOST or "10.66.66.1")
CERT_PASSWORD = os.environ.get("TAKLITE_CERT_PASSWORD", "")
DB_PATH = Path(os.environ.get("TAKLITE_DB", "/data/taklite.sqlite3"))
PACKAGE_DIR = Path(os.environ.get("TAKLITE_PACKAGE_DIR", "/packages"))
STATIC_DIR = Path(os.environ.get("TAKLITE_STATIC_DIR", "/app/static"))
WG_DASHBOARD_URL = os.environ.get("TAKLITE_WGDASHBOARD_URL", "")
VERSION = "TAKlite 0.2.24"
STARTED_AT = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
PORTAL_SESSION_HOURS = 2
MAX_UPLOAD_BYTES = int(os.environ.get("TAKLITE_MAX_UPLOAD_BYTES", str(256 * 1024 * 1024)))
MAX_ZIP_ENTRIES = int(os.environ.get("TAKLITE_MAX_ZIP_ENTRIES", "1000"))
MAX_ZIP_UNCOMPRESSED_BYTES = int(os.environ.get("TAKLITE_MAX_ZIP_UNCOMPRESSED_BYTES", str(512 * 1024 * 1024)))
MAX_ZIP_COMPRESSION_RATIO = int(os.environ.get("TAKLITE_MAX_ZIP_COMPRESSION_RATIO", "100"))
MAX_JSON_BYTES = int(os.environ.get("TAKLITE_MAX_JSON_BYTES", str(256 * 1024)))
MAX_FIELD_ENROLLMENT_HOURS = int(os.environ.get("TAKLITE_MAX_FIELD_ENROLLMENT_HOURS", "720"))
COT_MAX_BUFFER_BYTES = int(os.environ.get("TAKLITE_COT_MAX_BUFFER_BYTES", str(1024 * 1024)))
EVENT_RETENTION_ROWS = int(os.environ.get("TAKLITE_EVENT_RETENTION_ROWS", "50000"))
COT_TLS_REQUIRE_CLIENT_CERT = os.environ.get("TAKLITE_COT_TLS_REQUIRE_CLIENT_CERT", "true").lower() in ("1", "true", "yes", "on")
ALLOW_LEGACY_CLIENT_CERT = os.environ.get("TAKLITE_ALLOW_LEGACY_CLIENT_CERT", "false").lower() in ("1", "true", "yes", "on")
ACCESS_CONTROL_ENFORCE = os.environ.get("TAKLITE_ACCESS_CONTROL_ENFORCE", "true").lower() in ("1", "true", "yes", "on")
LEGACY_CERT_DOWNLOADS = os.environ.get("TAKLITE_LEGACY_CERT_DOWNLOADS", "false").lower() in ("1", "true", "yes", "on")
LOGIN_LIMIT_ATTEMPTS = int(os.environ.get("TAKLITE_LOGIN_LIMIT_ATTEMPTS", "8"))
LOGIN_LIMIT_WINDOW_SECONDS = int(os.environ.get("TAKLITE_LOGIN_LIMIT_WINDOW_SECONDS", "300"))
MAX_BULK_USERS = int(os.environ.get("TAKLITE_MAX_BULK_USERS", "100"))
SOCKET_SEND_TIMEOUT_SECONDS = float(os.environ.get("TAKLITE_SOCKET_SEND_TIMEOUT_SECONDS", "2.5"))
GUI_UPDATE_ENABLED = os.environ.get("TAKLITE_GUI_UPDATE_ENABLED", "false").lower() in ("1", "true", "yes", "on")
GUI_UPDATE_COMMAND = os.environ.get("TAKLITE_GUI_UPDATE_COMMAND", "")
GUI_UPDATE_WORKDIR = os.environ.get("TAKLITE_GUI_UPDATE_WORKDIR", "")
GUI_UPDATE_TIMEOUT_SECONDS = int(os.environ.get("TAKLITE_GUI_UPDATE_TIMEOUT_SECONDS", "900"))
GUI_UPDATE_REQUEST_DIR = os.environ.get("TAKLITE_GUI_UPDATE_REQUEST_DIR", "")
SETTINGS_REQUEST_DIR = os.environ.get("TAKLITE_SETTINGS_REQUEST_DIR", "")
FIREWALL_REQUEST_DIR = os.environ.get("TAKLITE_FIREWALL_REQUEST_DIR", "")
WG_INTERFACE = os.environ.get("TAKLITE_WG_INTERFACE", "wg0")
PUBLIC_INTERFACE = os.environ.get("TAKLITE_PUBLIC_INTERFACE", "")
WIREGUARD_PORT = int(os.environ.get("TAKLITE_WIREGUARD_PORT", "51820"))
WGDASHBOARD_PORT = int(os.environ.get("TAKLITE_WGDASHBOARD_PORT", "10086"))
RELEASES_URL = "https://github.com/C-OneThirty7/TAKlite/releases"
LATEST_RELEASE_API_URL = "https://api.github.com/repos/C-OneThirty7/TAKlite/releases/latest"
UPDATE_STATUS_CACHE = {"checked_at": 0, "status": None}
UPDATE_STATUS_CACHE_SECONDS = 300
FIREWALL_SERVICES = {
    "ssh": {"label": "SSH", "protocol": "tcp", "port": 22, "lockout_sensitive": True},
    "wireguard": {"label": "WireGuard", "protocol": "udp", "port": WIREGUARD_PORT, "lockout_sensitive": True},
    "wg_dashboard": {"label": "WG Dashboard", "protocol": "tcp", "port": WGDASHBOARD_PORT},
    "taklite_admin": {"label": "TAKlite Admin", "protocol": "tcp", "port": HTTP_PUBLIC_PORT},
    "tak_https": {"label": "TAK HTTPS/Marti", "protocol": "tcp", "port": HTTPS_PUBLIC_PORT},
    "cot_tcp": {"label": "CoT TCP", "protocol": "tcp", "port": COT_PUBLIC_PORT},
    "cot_tls": {"label": "TLS CoT", "protocol": "tcp", "port": COT_TLS_PUBLIC_PORT},
}
FIREWALL_STATES = {"public", "vpn", "closed"}

EVENT_END = b"</event>"
EVENT_RE = re.compile(rb"<event\b.*?</event>", re.DOTALL)
UID_RE = re.compile(rb'\buid="([^"]+)"')
TYPE_RE = re.compile(rb'\btype="([^"]+)"')
CALLSIGN_RE = re.compile(rb'<contact\b[^>]*\bcallsign="([^"]+)"')
EVENT_SAVE_COUNT = 0
LOGIN_FAILURES = {}
LOGIN_LOCK = threading.Lock()
BULK_PASSWORD_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"
BULK_PORTAL_PASSWORD = "atakatak"
ACCESS_LEVEL_UNCHANGED = object()


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value):
    try:
        parsed = datetime.fromisoformat((value or "").replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return datetime.fromtimestamp(0, tz=timezone.utc)


def new_plugin_token():
    return f"tlp_{secrets.token_urlsafe(32)}"


def version_tuple(value):
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", value or "")
    if not match:
        return ()
    return tuple(int(part) for part in match.groups())


def version_tag(value):
    parts = version_tuple(value)
    return f"v{'.'.join(str(part) for part in parts)}" if parts else ""


def ensure_dirs():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def db_connect():
    conn = sqlite3.connect(DB_PATH, timeout=15, factory=ClosingConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("pragma foreign_keys = on")
    conn.execute("pragma journal_mode = wal")
    conn.execute("pragma synchronous = normal")
    return conn


def init_db():
    ensure_dirs()
    with db_connect() as conn:
        conn.execute("""
            create table if not exists datapackages (
                PrimaryKey integer primary key autoincrement,
                UID text not null,
                Name text not null,
                Hash text not null unique,
                SubmissionDateTime text not null,
                SubmissionUser text,
                CreatorUid text,
                Keywords text,
                MIMEType text,
                Size integer not null default 0,
                Path text not null,
                Tool text not null default 'public'
            )
        """)
        conn.execute("""
            create table if not exists events (
                id integer primary key autoincrement,
                uid text,
                callsign text,
                received_at text not null,
                remote text,
                cot text not null
            )
        """)
        conn.execute("""
            create table if not exists admins (
                username text primary key,
                password_hash text not null,
                created_at text not null,
                totp_secret text,
                totp_enabled integer not null default 0
            )
        """)
        conn.execute("""
            create table if not exists admin_sessions (
                token text primary key,
                username text not null,
                created_at text not null,
                expires_at text not null
            )
        """)
        conn.execute("""
            create table if not exists cert_profiles (
                id integer primary key autoincrement,
                name text not null unique,
                description text,
                download_token text unique,
                connect_string text not null,
                truststore_file text not null,
                client_cert_file text not null,
                datapackage_file text not null,
                created_at text not null,
                revoked_at text
            )
        """)
        conn.execute("""
            create table if not exists portal_users (
                id integer primary key autoincrement,
                username text not null unique,
                password_hash text not null,
                plugin_api_token text unique,
                display_name text,
                description text,
                assigned_ip text,
                device_mac text,
                cert_profile_id integer not null,
                pli_enabled integer not null default 1,
                allow_redownload integer not null default 0,
                first_download_at text,
                last_download_at text,
                download_count integer not null default 0,
                created_at text not null,
                revoked_at text,
                foreign key(cert_profile_id) references cert_profiles(id)
            )
        """)
        conn.execute("""
            create table if not exists access_roles (
                id integer primary key autoincrement,
                name text not null unique,
                description text,
                can_see_all integer not null default 0,
                can_send_all integer not null default 0,
                can_receive_all integer not null default 0,
                can_see_own_groups integer not null default 1,
                can_send_own_groups integer not null default 1,
                can_receive_own_groups integer not null default 1,
                created_at text not null
            )
        """)
        conn.execute("""
            create table if not exists access_groups (
                id integer primary key autoincrement,
                name text not null unique,
                description text,
                color text,
                created_at text not null
            )
        """)
        conn.execute("""
            create table if not exists access_user_groups (
                user_id integer not null,
                group_id integer not null,
                primary key(user_id, group_id),
                foreign key(user_id) references portal_users(id) on delete cascade,
                foreign key(group_id) references access_groups(id) on delete cascade
            )
        """)
        conn.execute("""
            create table if not exists access_policy_links (
                source_group_id integer not null,
                target_group_id integer not null,
                can_see integer not null default 0,
                can_send integer not null default 0,
                can_receive integer not null default 0,
                primary key(source_group_id, target_group_id),
                foreign key(source_group_id) references access_groups(id) on delete cascade,
                foreign key(target_group_id) references access_groups(id) on delete cascade
            )
        """)
        conn.execute("""
            create table if not exists portal_sessions (
                token text primary key,
                user_id integer not null,
                created_at text not null,
                expires_at text not null,
                foreign key(user_id) references portal_users(id)
            )
        """)
        conn.execute("""
            create table if not exists datapackage_deliveries (
                id integer primary key autoincrement,
                package_hash text not null,
                target_user_id integer,
                target_uid text,
                target_callsign text,
                status text not null,
                reason_code text not null,
                reason text not null,
                attempts integer not null default 0,
                created_at text not null,
                updated_at text not null,
                delivered_at text,
                foreign key(target_user_id) references portal_users(id) on delete set null
            )
        """)
        conn.execute("""
            create table if not exists datapackage_recipients (
                package_hash text not null,
                target_user_id integer not null,
                created_at text not null,
                primary key(package_hash, target_user_id),
                foreign key(target_user_id) references portal_users(id) on delete cascade
            )
        """)
        conn.execute("""
            create table if not exists audit_events (
                id integer primary key autoincrement,
                occurred_at text not null,
                event_type text not null,
                actor_type text,
                actor_id integer,
                actor_name text,
                remote text,
                outcome text not null,
                reason_code text,
                details text
            )
        """)
        conn.execute("""
            create table if not exists field_enrollments (
                id integer primary key autoincrement,
                name text not null,
                token text not null unique,
                username_prefix text not null,
                description text,
                role_id integer,
                access_level integer,
                group_ids text not null default '[]',
                max_uses integer not null default 1,
                used_count integer not null default 0,
                expires_at text not null,
                created_at text not null,
                revoked_at text,
                foreign key(role_id) references access_roles(id) on delete set null
            )
        """)
        columns = {row["name"] for row in conn.execute("pragma table_info(cert_profiles)").fetchall()}
        if "download_token" not in columns:
            conn.execute("alter table cert_profiles add column download_token text")
        for row in conn.execute("select id from cert_profiles where download_token is null or download_token = ''").fetchall():
            conn.execute("update cert_profiles set download_token = ? where id = ?", (secrets.token_urlsafe(18), row["id"]))
        portal_columns = {row["name"] for row in conn.execute("pragma table_info(portal_users)").fetchall()}
        if "role_id" not in portal_columns:
            conn.execute("alter table portal_users add column role_id integer")
        if "access_level" not in portal_columns:
            conn.execute("alter table portal_users add column access_level integer")
        if "plugin_api_token" not in portal_columns:
            conn.execute("alter table portal_users add column plugin_api_token text")
        if "assigned_ip" not in portal_columns:
            conn.execute("alter table portal_users add column assigned_ip text")
        if "device_mac" not in portal_columns:
            conn.execute("alter table portal_users add column device_mac text")
        if "pli_enabled" not in portal_columns:
            conn.execute("alter table portal_users add column pli_enabled integer not null default 1")
        for row in conn.execute("select id from portal_users where plugin_api_token is null or plugin_api_token = ''").fetchall():
            conn.execute("update portal_users set plugin_api_token = ? where id = ?", (new_plugin_token(), row["id"]))
        admin_columns = {row["name"] for row in conn.execute("pragma table_info(admins)").fetchall()}
        if "totp_secret" not in admin_columns:
            conn.execute("alter table admins add column totp_secret text")
        if "totp_enabled" not in admin_columns:
            conn.execute("alter table admins add column totp_enabled integer not null default 0")
        package_columns = {row["name"] for row in conn.execute("pragma table_info(datapackages)").fetchall()}
        if "CreatorUserId" not in package_columns:
            conn.execute("alter table datapackages add column CreatorUserId integer")
        if "Visibility" not in package_columns:
            conn.execute("alter table datapackages add column Visibility text not null default 'private'")
        if "PolicyMode" not in package_columns:
            conn.execute("alter table datapackages add column PolicyMode text not null default 'sender'")
        if "AllowedLevels" not in package_columns:
            conn.execute("alter table datapackages add column AllowedLevels text not null default ''")
        role_columns = {row["name"] for row in conn.execute("pragma table_info(access_roles)").fetchall()}
        if "can_receive_all" not in role_columns:
            conn.execute("alter table access_roles add column can_receive_all integer not null default 0")
            conn.execute("update access_roles set can_receive_all = can_send_all")
        if "can_receive_own_groups" not in role_columns:
            conn.execute("alter table access_roles add column can_receive_own_groups integer not null default 1")
            conn.execute("update access_roles set can_receive_own_groups = can_send_own_groups")
        link_columns = {row["name"] for row in conn.execute("pragma table_info(access_policy_links)").fetchall()}
        if "can_receive" not in link_columns:
            conn.execute("alter table access_policy_links add column can_receive integer not null default 0")
            conn.execute("update access_policy_links set can_receive = can_send")
        conn.execute("create index if not exists idx_events_uid on events(uid)")
        conn.execute("create index if not exists idx_events_received_at on events(received_at)")
        conn.execute("create index if not exists idx_datapackages_hash on datapackages(Hash)")
        conn.execute("create index if not exists idx_datapackage_deliveries_hash on datapackage_deliveries(package_hash)")
        conn.execute("create index if not exists idx_datapackage_deliveries_pending on datapackage_deliveries(target_user_id, status)")
        conn.execute("create index if not exists idx_datapackage_recipients_user on datapackage_recipients(target_user_id)")
        conn.execute("create index if not exists idx_portal_users_profile on portal_users(cert_profile_id)")
        conn.execute("create index if not exists idx_portal_users_assigned_ip on portal_users(assigned_ip)")
        conn.execute("create index if not exists idx_portal_users_device_mac on portal_users(device_mac)")
        conn.execute("create index if not exists idx_access_user_groups_user on access_user_groups(user_id)")
        conn.execute("create index if not exists idx_access_user_groups_group on access_user_groups(group_id)")
        conn.execute("create index if not exists idx_audit_events_time on audit_events(occurred_at)")
        conn.execute("create index if not exists idx_audit_events_type on audit_events(event_type)")
        conn.execute("create index if not exists idx_field_enrollments_token on field_enrollments(token)")
        conn.execute("create index if not exists idx_field_enrollments_expires on field_enrollments(expires_at)")
        conn.commit()


def package_path(hash_value, filename):
    safe_hash = re.sub(r"[^A-Za-z0-9_.-]", "_", hash_value or uuid.uuid4().hex)
    suffix = Path(filename or "package.dp.zip").suffix or ".zip"
    return PACKAGE_DIR / f"{safe_hash}{suffix}"


def safe_download_name(filename, fallback="download.bin"):
    name = Path(filename or fallback).name
    name = re.sub(r"[^A-Za-z0-9_.() -]+", "_", name).strip(" .")
    return name[:160] or fallback


def record_audit_event(event_type, actor_type="", actor_id=None, actor_name="", remote="", outcome="ok", reason_code="", details=None):
    details = details or {}
    try:
        details_json = json.dumps(details, sort_keys=True)[:4096]
        with db_connect() as conn:
            conn.execute("""
                insert into audit_events
                  (occurred_at, event_type, actor_type, actor_id, actor_name, remote, outcome, reason_code, details)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                utc_now(),
                (event_type or "event").strip()[:80],
                (actor_type or "").strip()[:40],
                actor_id,
                (actor_name or "").strip()[:120],
                (remote or "").strip()[:120],
                (outcome or "ok").strip()[:40],
                (reason_code or "").strip()[:80],
                details_json,
            ))
            conn.commit()
    except Exception as exc:
        print(f"TAKlite audit record failed: {exc}", flush=True)


def audit_row(row):
    details = {}
    try:
        details = json.loads(row["details"] or "{}")
    except Exception:
        details = {}
    return {
        "id": row["id"],
        "occurred_at": row["occurred_at"],
        "event_type": row["event_type"],
        "actor_type": row["actor_type"] or "",
        "actor_id": row["actor_id"],
        "actor_name": row["actor_name"] or "",
        "remote": row["remote"] or "",
        "outcome": row["outcome"],
        "reason_code": row["reason_code"] or "",
        "details": details,
    }


def list_audit_events(limit=100, event_type=""):
    try:
        limit = int(limit or 100)
    except (TypeError, ValueError):
        limit = 100
    limit = max(1, min(limit, 500))
    params = []
    where = ""
    if event_type:
        where = "where event_type = ?"
        params.append(event_type.strip())
    params.append(limit)
    with db_connect() as conn:
        rows = conn.execute(f"""
            select *
            from audit_events
            {where}
            order by id desc
            limit ?
        """, params).fetchall()
    return [audit_row(row) for row in rows]


def normalize_datapackage_name(filename, fallback="datapackage.zip"):
    name = safe_download_name(unquote(filename or ""), fallback)
    if not name.lower().endswith((".zip", ".dp.zip")):
        name = f"{name}.zip"
    return name


def validate_access_level(value, allow_empty=True):
    if value in (None, "") and allow_empty:
        return None
    try:
        level = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("access level must be 1, 2, 3, 4, or blank") from exc
    if level < 1 or level > 4:
        raise ValueError("access level must be 1, 2, 3, 4, or blank")
    return level


def parse_datapackage_filename_policy(filename):
    base = Path(filename or "").name
    lowered = base.lower()
    for suffix in (".dp.zip", ".zip"):
        if lowered.endswith(suffix):
            lowered = lowered[:-len(suffix)]
            break
    compact = re.sub(r"[^a-z0-9]", "", lowered)
    mode = ""
    if compact.endswith("only"):
        mode = "only"
        source = compact[:-4]
    elif compact.endswith("all"):
        mode = "all"
        source = compact[:-3]
    else:
        return {"mode": "sender", "allowed_levels": [], "label": "Sender policy"}
    if "lvl" not in source:
        return {"mode": "sender", "allowed_levels": [], "label": "Sender policy"}
    level_source = source[source.find("lvl"):]
    levels = sorted({int(value) for value in re.findall(r"(?:lvl)?([1-4])", level_source)})
    if not levels:
        return {"mode": "sender", "allowed_levels": [], "label": "Sender policy"}
    if mode == "all":
        levels = list(range(1, max(levels) + 1))
        label = f"Levels {', '.join(str(level) for level in levels)}"
    else:
        label = f"Level{'s' if len(levels) > 1 else ''} {', '.join(str(level) for level in levels)} only"
    return {"mode": f"level_{mode}", "allowed_levels": levels, "label": label}


def serialize_levels(levels):
    return ",".join(str(validate_access_level(level, allow_empty=False)) for level in sorted({int(level) for level in levels or []}))


def deserialize_levels(value):
    levels = []
    for part in str(value or "").split(","):
        part = part.strip()
        if not part:
            continue
        levels.append(validate_access_level(part, allow_empty=False))
    return sorted(set(levels))


def parse_datapackage_policy_label(mode, allowed_levels):
    levels = deserialize_levels(allowed_levels)
    mode = (mode or "sender").lower()
    if not mode.startswith("level_") or not levels:
        return "Sender policy"
    if mode == "level_only":
        return f"Level{'s' if len(levels) > 1 else ''} {', '.join(str(level) for level in levels)} only"
    return f"Levels {', '.join(str(level) for level in levels)}"


def marti_timestamp(value):
    try:
        parsed = parse_utc(value)
    except Exception:
        parsed = None
    if not parsed:
        return value or utc_now().replace("Z", ".000Z")
    parsed = parsed.astimezone(timezone.utc)
    return parsed.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def row_to_package(row):
    return {
        "PrimaryKey": row["PrimaryKey"],
        "UID": row["UID"],
        "Name": row["Name"],
        "Hash": row["Hash"],
        "SubmissionDateTime": marti_timestamp(row["SubmissionDateTime"]),
        "SubmissionUser": row["SubmissionUser"] or "",
        "CreatorUid": row["CreatorUid"] or "",
        "Keywords": row["Keywords"] or "missionpackage",
        "MIMEType": row["MIMEType"] or "application/x-zip-compressed",
        "Size": row["Size"],
        "Tool": row["Tool"] or "public",
        "CreatorUserId": row["CreatorUserId"] if "CreatorUserId" in row.keys() else None,
        "Visibility": row["Visibility"] if "Visibility" in row.keys() else "private",
        "PolicyMode": row["PolicyMode"] if "PolicyMode" in row.keys() else "sender",
        "AllowedLevels": deserialize_levels(row["AllowedLevels"]) if "AllowedLevels" in row.keys() else [],
        "PolicyLabel": parse_datapackage_policy_label(
            row["PolicyMode"] if "PolicyMode" in row.keys() else "sender",
            row["AllowedLevels"] if "AllowedLevels" in row.keys() else "",
        ),
    }


def list_packages(user_id=None, enforce=None):
    with db_connect() as conn:
        rows = conn.execute(
            "select * from datapackages order by PrimaryKey desc"
        ).fetchall()
    packages = [row_to_package(row) for row in rows]
    if enforce is None:
        enforce = ACCESS_CONTROL_ENFORCE
    if not enforce:
        return packages
    return [package for package in packages if package_visible_to_user(package, user_id, enforce=True)]


def find_package(hash_value):
    with db_connect() as conn:
        return conn.execute(
            "select * from datapackages where Hash = ?", (hash_value,)
        ).fetchone()


def upsert_package(hash_value, filename, creator_uid, data, host_url, creator_user_id=None, visibility="private", policy=None):
    actual_hash = hashlib.sha256(data).hexdigest()
    hash_value = hash_value or actual_hash
    filename = filename or f"{hash_value}.dp.zip"
    policy = policy or parse_datapackage_filename_policy(filename)
    policy_mode = policy.get("mode") or "sender"
    allowed_levels = serialize_levels(policy.get("allowed_levels", []))
    path = package_path(hash_value, filename)
    path.write_bytes(data)
    now = utc_now()
    uid = str(uuid.uuid4())
    with db_connect() as conn:
        existing = conn.execute(
            "select UID from datapackages where Hash = ?", (hash_value,)
        ).fetchone()
        if existing:
            uid = existing["UID"]
        conn.execute("""
            insert into datapackages
                (UID, Name, Hash, SubmissionDateTime, SubmissionUser, CreatorUid, Keywords, MIMEType, Size, Path, Tool, CreatorUserId, Visibility, PolicyMode, AllowedLevels)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, coalesce((select Tool from datapackages where Hash = ?), ?), ?, ?, ?, ?)
            on conflict(Hash) do update set
                Name=excluded.Name,
                SubmissionDateTime=excluded.SubmissionDateTime,
                CreatorUid=excluded.CreatorUid,
                Keywords=excluded.Keywords,
                MIMEType=excluded.MIMEType,
                Size=excluded.Size,
                Path=excluded.Path,
                CreatorUserId=coalesce(excluded.CreatorUserId, CreatorUserId),
                Visibility=excluded.Visibility,
                PolicyMode=excluded.PolicyMode,
                AllowedLevels=excluded.AllowedLevels
        """, (
            uid, filename, hash_value, now, creator_uid or "", creator_uid or "",
            "missionpackage", "application/x-zip-compressed", len(data), str(path), hash_value, visibility or "private", creator_user_id, visibility or "private", policy_mode, allowed_levels,
        ))
        conn.commit()
    return f"{host_url}/Marti/sync/content?hash={quote(hash_value)}"


def tak_marti_base_url():
    host = PUBLIC_HOST or SERVER_HOST
    if HTTPS_CERT.exists() and HTTPS_KEY.exists():
        return f"https://{host}:{HTTPS_PUBLIC_PORT}"
    return f"http://{host}:{HTTP_PUBLIC_PORT}"


def tak_marti_content_url(hash_value):
    return f"{tak_marti_base_url()}/Marti/sync/content?hash={quote(hash_value)}"


def tak_marti_metadata_tool_url(hash_value):
    return f"{tak_marti_base_url()}/Marti/api/sync/metadata/{quote(hash_value)}/tool"


def delete_package(hash_value, delete_file=True):
    row = find_package(hash_value)
    if not row:
        return {"deleted_rows": 0, "deleted_files": []}
    deleted_files = []
    path = Path(row["Path"])
    with db_connect() as conn:
        conn.execute("delete from datapackages where Hash = ?", (hash_value,))
        conn.commit()
    if delete_file and path.exists() and path.resolve().is_relative_to(PACKAGE_DIR.resolve()):
        path.unlink()
        deleted_files.append(str(path))
    return {"deleted_rows": 1, "deleted_files": deleted_files}


def prune_events_if_needed(conn):
    global EVENT_SAVE_COUNT
    if EVENT_RETENTION_ROWS <= 0:
        return
    EVENT_SAVE_COUNT += 1
    if EVENT_SAVE_COUNT % 100:
        return
    conn.execute("""
        delete from events
        where id not in (
            select id from events order by id desc limit ?
        )
    """, (EVENT_RETENTION_ROWS,))


def save_event(data, remote, user_id=None):
    uid = decode_match(UID_RE.search(data))
    callsign = decode_match(CALLSIGN_RE.search(data))
    try:
        cot = data.decode("utf-8", "replace")
    except Exception:
        cot = repr(data)
    with db_connect() as conn:
        conn.execute(
            "insert into events (uid, callsign, received_at, remote, cot) values (?, ?, ?, ?, ?)",
            (uid, callsign, utc_now(), remote, cot),
        )
        prune_events_if_needed(conn)
        conn.commit()
    if uid or callsign:
        RELAY.update_client(remote, uid, callsign, user_id=user_id)
    if uid:
        RELAY.remember_event(uid, data, user_id)


def is_pli_event(data):
    event_type = decode_match(TYPE_RE.search(data)).strip().lower()
    if not event_type:
        return False
    if event_type.startswith(("b-f", "t-x", "t-k", "t-s", "t-r")):
        return False
    if not event_type.startswith("a-"):
        return False
    return b"<point " in data and b"<contact" in data and (b"<track" in data or b"<precisionlocation" in data)


def user_pli_enabled(user_id):
    if not user_id:
        return True
    with db_connect() as conn:
        row = conn.execute("select pli_enabled from portal_users where id = ?", (int(user_id),)).fetchone()
    return bool(not row or row["pli_enabled"])


def decode_match(match):
    if not match:
        return ""
    return match.group(1).decode("utf-8", "replace")


def cert_common_name(peer_cert):
    for part in peer_cert.get("subject", ()):
        for key, value in part:
            if key == "commonName":
                return value
    return ""


def parse_utc(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def cot_time(delta_seconds=0):
    value = datetime.now(timezone.utc) + timedelta(seconds=delta_seconds)
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def server_status_event():
    return (
        f'<event version="2.0" uid="taklite-server" type="t-x-c-t" '
        f'time="{cot_time()}" start="{cot_time()}" stale="{cot_time(30)}" how="m-g">'
        '<point lat="0.0" lon="0.0" hae="9999999.0" ce="9999999.0" le="9999999.0"/>'
        '<detail><contact callsign="TAKlite"/><remarks>TAKlite keepalive</remarks></detail>'
        '</event>'
    ).encode("utf-8")


def fileshare_event(package):
    name = safe_download_name(package["Name"], "datapackage.zip")
    hash_value = package["Hash"]
    size = int(package["Size"] or 0)
    event_uid = f"taklite-fileshare-{uuid.uuid4()}"
    ack_uid = str(uuid.uuid4())
    sender_url = tak_marti_content_url(hash_value)
    return (
        f'<event version="2.0" uid="{html.escape(event_uid)}" type="b-f-t-r" '
        f'time="{cot_time()}" start="{cot_time()}" stale="{cot_time(600)}" how="h-e">'
        '<point lat="0.0" lon="0.0" hae="9999999.0" ce="9999999.0" le="9999999.0"/>'
        '<detail>'
        f'<fileshare filename="{html.escape(name)}" name="{html.escape(name)}" '
        f'senderUrl="{html.escape(sender_url)}" sizeInBytes="{size}" '
        f'sha256="{html.escape(hash_value)}" senderUid="taklite-server" senderCallsign="TAKlite Admin"/>'
        f'<ackrequest uid="{html.escape(ack_uid)}" ackrequested="true" tag="{html.escape(name)}"/>'
        '</detail></event>'
    ).encode("utf-8")


def password_hash(password):
    salt = secrets.token_bytes(16)
    iterations = 220000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    try:
        alg, iterations, salt_hex, digest_hex = stored.split("$", 3)
        if alg != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(digest.hex(), digest_hex)
    except Exception:
        return False


def new_totp_secret():
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def decode_totp_secret(secret):
    normalized = re.sub(r"\s+", "", secret or "").upper()
    normalized += "=" * ((8 - len(normalized) % 8) % 8)
    return base64.b32decode(normalized, casefold=True)


def totp_code(secret, for_time=None, step=30, digits=6):
    timestamp = time.time() if for_time is None else float(for_time)
    counter = int(timestamp // step)
    digest = hmac.new(decode_totp_secret(secret), counter.to_bytes(8, "big"), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = int.from_bytes(digest[offset:offset + 4], "big") & 0x7FFFFFFF
    return str(value % (10 ** digits)).zfill(digits)


def verify_totp_code(secret, code, for_time=None, window=1):
    candidate = re.sub(r"\s+", "", code or "")
    if not re.fullmatch(r"\d{6}", candidate):
        return False
    timestamp = time.time() if for_time is None else float(for_time)
    for drift in range(-window, window + 1):
        expected = totp_code(secret, timestamp + drift * 30)
        if hmac.compare_digest(expected, candidate):
            return True
    return False


def rate_limit_key(scope, remote, username):
    return f"{scope}:{remote}:{(username or '').strip().lower()}"


def login_limited(scope, remote, username):
    now = time.time()
    key = rate_limit_key(scope, remote, username)
    with LOGIN_LOCK:
        attempts = [seen for seen in LOGIN_FAILURES.get(key, []) if now - seen < LOGIN_LIMIT_WINDOW_SECONDS]
        LOGIN_FAILURES[key] = attempts
        return len(attempts) >= LOGIN_LIMIT_ATTEMPTS


def record_login_failure(scope, remote, username):
    now = time.time()
    key = rate_limit_key(scope, remote, username)
    with LOGIN_LOCK:
        attempts = [seen for seen in LOGIN_FAILURES.get(key, []) if now - seen < LOGIN_LIMIT_WINDOW_SECONDS]
        attempts.append(now)
        LOGIN_FAILURES[key] = attempts
    safe_scope = re.sub(r"[^A-Za-z0-9_.:-]", "_", scope or "unknown")
    safe_remote = re.sub(r"[^A-Za-z0-9_.:-]", "_", remote or "unknown")
    safe_user = re.sub(r"[^A-Za-z0-9_.@-]", "_", username or "unknown")
    print(f"TAKlite auth failure scope={safe_scope} remote={safe_remote} username={safe_user} attempts={len(attempts)}", flush=True)


def clear_login_failures(scope, remote, username):
    key = rate_limit_key(scope, remote, username)
    with LOGIN_LOCK:
        LOGIN_FAILURES.pop(key, None)


def admin_count():
    with db_connect() as conn:
        return int(conn.execute("select count(*) from admins").fetchone()[0])


def create_admin(username, password):
    username = (username or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.@-]{3,64}", username):
        raise ValueError("username must be 3-64 characters: letters, numbers, dot, underscore, dash, or @")
    if len(password or "") < 10:
        raise ValueError("password must be at least 10 characters")
    with db_connect() as conn:
        conn.execute(
            "insert into admins (username, password_hash, created_at) values (?, ?, ?)",
            (username, password_hash(password), utc_now()),
        )
        conn.commit()
    return username


def admin_totp_status(username):
    with db_connect() as conn:
        row = conn.execute("select totp_enabled, totp_secret from admins where username = ?", ((username or "").strip(),)).fetchone()
    if not row:
        raise ValueError("admin user not found")
    return {"username": (username or "").strip(), "totp_enabled": bool(row["totp_enabled"]), "totp_configured": bool(row["totp_secret"])}


def create_admin_totp_setup(username, current_password):
    username = (username or "").strip()
    if authenticate_admin(username, current_password, allow_missing_totp=True) != username:
        raise PermissionError("current password is incorrect")
    secret = new_totp_secret()
    issuer = quote("TAKlite")
    label = quote(f"TAKlite:{username}")
    uri = f"otpauth://totp/{label}?secret={secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"
    with db_connect() as conn:
        conn.execute("update admins set totp_secret = ?, totp_enabled = 0 where username = ?", (secret, username))
        conn.commit()
    return {"username": username, "secret": secret, "otpauth_uri": uri, "totp_enabled": False}


def enable_admin_totp(username, current_password, code, for_time=None, current_token=""):
    username = (username or "").strip()
    if authenticate_admin(username, current_password, allow_missing_totp=True) != username:
        raise PermissionError("current password is incorrect")
    with db_connect() as conn:
        row = conn.execute("select totp_secret from admins where username = ?", (username,)).fetchone()
        if not row or not row["totp_secret"]:
            raise ValueError("two-factor setup has not been started")
        if not verify_totp_code(row["totp_secret"], code, for_time=for_time):
            raise PermissionError("two-factor code is incorrect")
        conn.execute("update admins set totp_enabled = 1 where username = ?", (username,))
        if current_token:
            conn.execute("delete from admin_sessions where username = ? and token != ?", (username, current_token))
        else:
            conn.execute("delete from admin_sessions where username = ?", (username,))
        conn.commit()
    return admin_totp_status(username)


def disable_admin_totp(username, current_password, code, for_time=None, current_token=""):
    username = (username or "").strip()
    if authenticate_admin(username, current_password, code, for_time=for_time) != username:
        raise PermissionError("current password or two-factor code is incorrect")
    with db_connect() as conn:
        conn.execute("update admins set totp_secret = null, totp_enabled = 0 where username = ?", (username,))
        if current_token:
            conn.execute("delete from admin_sessions where username = ? and token != ?", (username, current_token))
        else:
            conn.execute("delete from admin_sessions where username = ?", (username,))
        conn.commit()
    return admin_totp_status(username)


def create_session(username):
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=12)
    with db_connect() as conn:
        conn.execute(
            "insert into admin_sessions (token, username, created_at, expires_at) values (?, ?, ?, ?)",
            (token, username, now.replace(microsecond=0).isoformat().replace("+00:00", "Z"), expires.replace(microsecond=0).isoformat().replace("+00:00", "Z")),
        )
        conn.commit()
    return token


def validate_session(token):
    if not token:
        return ""
    with db_connect() as conn:
        row = conn.execute("select username, expires_at from admin_sessions where token = ?", (token,)).fetchone()
        if not row:
            return ""
        expires = parse_utc(row["expires_at"])
        if not expires or expires <= datetime.now(timezone.utc):
            conn.execute("delete from admin_sessions where token = ?", (token,))
            conn.commit()
            return ""
        return row["username"]


def authenticate_admin(username, password, totp_value="", for_time=None, allow_missing_totp=False):
    with db_connect() as conn:
        row = conn.execute("select password_hash, totp_secret, totp_enabled from admins where username = ?", ((username or "").strip(),)).fetchone()
    if not row or not verify_password(password or "", row["password_hash"]):
        return ""
    if row["totp_enabled"] and not allow_missing_totp:
        if not row["totp_secret"] or not verify_totp_code(row["totp_secret"], totp_value, for_time=for_time):
            return ""
    return (username or "").strip()


def admin_requires_totp(username, password):
    with db_connect() as conn:
        row = conn.execute("select password_hash, totp_enabled from admins where username = ?", ((username or "").strip(),)).fetchone()
    return bool(row and row["totp_enabled"] and verify_password(password or "", row["password_hash"]))


def change_admin_password(username, current_password, new_password, keep_session_token=""):
    username = (username or "").strip()
    if len(new_password or "") < 10:
        raise ValueError("new password must be at least 10 characters")
    with db_connect() as conn:
        row = conn.execute("select password_hash from admins where username = ?", (username,)).fetchone()
        if not row or not verify_password(current_password or "", row["password_hash"]):
            raise PermissionError("current password is incorrect")
        conn.execute("update admins set password_hash = ? where username = ?", (password_hash(new_password), username))
        if keep_session_token:
            conn.execute("delete from admin_sessions where username = ? and token != ?", (username, keep_session_token))
        else:
            conn.execute("delete from admin_sessions where username = ?", (username,))
        conn.commit()
    clear_login_failures("admin", "", username)
    return True


def validate_portal_username(username):
    username = (username or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.@-]{3,64}", username):
        raise ValueError("portal username must be 3-64 characters: letters, numbers, dot, underscore, dash, or @")
    return username


def validate_assigned_ip(value):
    value = (value or "").strip()
    if not value:
        return ""
    try:
        return str(ipaddress.ip_address(value))
    except ValueError as exc:
        raise ValueError("assigned IP must be a valid IPv4 or IPv6 address") from exc


def validate_device_mac(value):
    value = (value or "").strip()
    if not value:
        return ""
    compact = re.sub(r"[^0-9A-Fa-f]", "", value)
    if len(compact) == 12 and re.fullmatch(r"[0-9A-Fa-f]{12}", compact):
        return ":".join(compact[idx:idx + 2] for idx in range(0, 12, 2)).lower()
    if not re.fullmatch(r"[A-Za-z0-9_.:@-]{3,128}", value):
        raise ValueError("device ID must be 3-128 characters: letters, numbers, dot, underscore, dash, colon, or @")
    return value


def validate_access_name(name, label="name"):
    name = (name or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.@() -]{0,63}", name):
        raise ValueError(f"{label} must be 1-64 characters and start with a letter or number")
    return name


def row_to_role(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"] or "",
        "can_see_all": bool(row["can_see_all"]),
        "can_send_all": bool(row["can_send_all"]),
        "can_receive_all": bool(row["can_receive_all"]),
        "can_see_own_groups": bool(row["can_see_own_groups"]),
        "can_send_own_groups": bool(row["can_send_own_groups"]),
        "can_receive_own_groups": bool(row["can_receive_own_groups"]),
        "created_at": row["created_at"],
    }


def row_to_group(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"] or "",
        "color": row["color"] or "",
        "created_at": row["created_at"],
    }


def row_to_policy_link(row):
    return {
        "source_group_id": row["source_group_id"],
        "target_group_id": row["target_group_id"],
        "can_see": bool(row["can_see"]),
        "can_send": bool(row["can_send"]),
        "can_receive": bool(row["can_receive"]),
    }


def create_access_role(name, description="", can_see_all=False, can_send_all=False, can_see_own_groups=True, can_send_own_groups=True, can_receive_all=None, can_receive_own_groups=None):
    name = validate_access_name(name, "role name")
    if can_receive_all is None:
        can_receive_all = can_send_all
    if can_receive_own_groups is None:
        can_receive_own_groups = can_send_own_groups
    with db_connect() as conn:
        conn.execute("""
            insert into access_roles
              (name, description, can_see_all, can_send_all, can_receive_all, can_see_own_groups, can_send_own_groups, can_receive_own_groups, created_at)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            (description or "").strip(),
            1 if can_see_all else 0,
            1 if can_send_all else 0,
            1 if can_receive_all else 0,
            1 if can_see_own_groups else 0,
            1 if can_send_own_groups else 0,
            1 if can_receive_own_groups else 0,
            utc_now(),
        ))
        conn.commit()
        row = conn.execute("select * from access_roles where name = ?", (name,)).fetchone()
    return row_to_role(row)


def update_access_role(role_id, name, description="", can_see_all=False, can_send_all=False, can_see_own_groups=True, can_send_own_groups=True, can_receive_all=None, can_receive_own_groups=None):
    name = validate_access_name(name, "role name")
    if can_receive_all is None:
        can_receive_all = can_send_all
    if can_receive_own_groups is None:
        can_receive_own_groups = can_send_own_groups
    with db_connect() as conn:
        conn.execute("""
            update access_roles
            set name = ?, description = ?, can_see_all = ?, can_send_all = ?, can_receive_all = ?, can_see_own_groups = ?, can_send_own_groups = ?, can_receive_own_groups = ?
            where id = ?
        """, (
            name,
            (description or "").strip(),
            1 if can_see_all else 0,
            1 if can_send_all else 0,
            1 if can_receive_all else 0,
            1 if can_see_own_groups else 0,
            1 if can_send_own_groups else 0,
            1 if can_receive_own_groups else 0,
            role_id,
        ))
        conn.commit()
        row = conn.execute("select * from access_roles where id = ?", (role_id,)).fetchone()
    if not row:
        raise ValueError("role not found")
    return row_to_role(row)


def delete_access_role(role_id):
    with db_connect() as conn:
        conn.execute("update portal_users set role_id = null where role_id = ?", (role_id,))
        deleted = conn.execute("delete from access_roles where id = ?", (role_id,)).rowcount
        conn.commit()
    return {"deleted_rows": deleted}


def create_access_group(name, description="", color=""):
    name = validate_access_name(name, "group name")
    color = (color or "").strip()
    if color and not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
        raise ValueError("group color must be a hex color like #64c18c")
    with db_connect() as conn:
        conn.execute("""
            insert into access_groups (name, description, color, created_at)
            values (?, ?, ?, ?)
        """, (name, (description or "").strip(), color, utc_now()))
        conn.commit()
        row = conn.execute("select * from access_groups where name = ?", (name,)).fetchone()
    return row_to_group(row)


def update_access_group(group_id, name, description="", color=""):
    name = validate_access_name(name, "group name")
    color = (color or "").strip()
    if color and not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
        raise ValueError("group color must be a hex color like #64c18c")
    with db_connect() as conn:
        conn.execute("update access_groups set name = ?, description = ?, color = ? where id = ?", (name, (description or "").strip(), color, group_id))
        conn.commit()
        row = conn.execute("select * from access_groups where id = ?", (group_id,)).fetchone()
    if not row:
        raise ValueError("group not found")
    return row_to_group(row)


def delete_access_group(group_id):
    with db_connect() as conn:
        conn.execute("delete from access_user_groups where group_id = ?", (group_id,))
        conn.execute("delete from access_policy_links where source_group_id = ? or target_group_id = ?", (group_id, group_id))
        deleted = conn.execute("delete from access_groups where id = ?", (group_id,)).rowcount
        conn.commit()
    return {"deleted_rows": deleted}


def list_access_roles():
    with db_connect() as conn:
        rows = conn.execute("select * from access_roles order by lower(name)").fetchall()
    return [row_to_role(row) for row in rows]


def list_access_groups():
    with db_connect() as conn:
        rows = conn.execute("select * from access_groups order by lower(name)").fetchall()
    return [row_to_group(row) for row in rows]


def list_policy_links():
    with db_connect() as conn:
        rows = conn.execute("select * from access_policy_links order by source_group_id, target_group_id").fetchall()
    return [row_to_policy_link(row) for row in rows]


def set_user_access(user_id, role_id=None, group_ids=None, access_level=ACCESS_LEVEL_UNCHANGED):
    group_ids = [int(value) for value in (group_ids or []) if str(value).strip()]
    role_id = int(role_id or 0) or None
    if access_level is not ACCESS_LEVEL_UNCHANGED:
        access_level = validate_access_level(access_level)
    with db_connect() as conn:
        if role_id and not conn.execute("select id from access_roles where id = ?", (role_id,)).fetchone():
            raise ValueError("role not found")
        if group_ids:
            placeholders = ",".join("?" for _ in group_ids)
            found = {row["id"] for row in conn.execute(f"select id from access_groups where id in ({placeholders})", group_ids).fetchall()}
            missing = sorted(set(group_ids) - found)
            if missing:
                raise ValueError(f"group not found: {missing[0]}")
        if not conn.execute("select id from portal_users where id = ?", (user_id,)).fetchone():
            raise ValueError("user not found")
        if access_level is ACCESS_LEVEL_UNCHANGED:
            conn.execute("update portal_users set role_id = ? where id = ?", (role_id, user_id))
        else:
            conn.execute("update portal_users set role_id = ?, access_level = ? where id = ?", (role_id, access_level, user_id))
        conn.execute("delete from access_user_groups where user_id = ?", (user_id,))
        conn.executemany("insert into access_user_groups (user_id, group_id) values (?, ?)", [(user_id, gid) for gid in group_ids])
        conn.commit()
    return attach_access_to_users([portal_user_row(find_portal_user(user_id))])[0]


def bulk_set_user_access(user_ids, role_id=None, group_ids=None, group_mode="replace", access_level=None, level_mode="unchanged", role_mode="unchanged"):
    user_ids = sorted({int(value) for value in (user_ids or []) if str(value).strip()})
    if not user_ids:
        raise ValueError("select at least one user")
    group_ids = [int(value) for value in (group_ids or []) if str(value).strip()]
    group_mode = (group_mode or "replace").strip().lower()
    if group_mode not in ("replace", "add", "remove"):
        raise ValueError("group mode must be replace, add, or remove")
    role_id = int(role_id or 0) or None
    role_mode = (role_mode or "unchanged").strip().lower()
    if role_mode not in ("unchanged", "set", "clear"):
        raise ValueError("access override action must be unchanged, set, or clear")
    if role_mode == "unchanged" and role_id is not None:
        role_mode = "set"
    if role_mode == "set" and role_id is None:
        raise ValueError("choose an access override")
    level_mode = (level_mode or "unchanged").strip().lower()
    if level_mode not in ("unchanged", "set", "clear"):
        raise ValueError("level mode must be unchanged, set, or clear")
    access_level = validate_access_level(access_level, allow_empty=(level_mode != "set"))
    with db_connect() as conn:
        placeholders = ",".join("?" for _ in user_ids)
        found_users = {row["id"] for row in conn.execute(f"select id from portal_users where id in ({placeholders})", user_ids).fetchall()}
        missing_users = sorted(set(user_ids) - found_users)
        if missing_users:
            raise ValueError(f"user not found: {missing_users[0]}")
        if role_mode == "set" and role_id and not conn.execute("select id from access_roles where id = ?", (role_id,)).fetchone():
            raise ValueError("role not found")
        if group_ids:
            group_placeholders = ",".join("?" for _ in group_ids)
            found_groups = {row["id"] for row in conn.execute(f"select id from access_groups where id in ({group_placeholders})", group_ids).fetchall()}
            missing_groups = sorted(set(group_ids) - found_groups)
            if missing_groups:
                raise ValueError(f"group not found: {missing_groups[0]}")
        if role_mode == "set":
            conn.executemany("update portal_users set role_id = ? where id = ?", [(role_id, user_id) for user_id in user_ids])
        elif role_mode == "clear":
            conn.executemany("update portal_users set role_id = null where id = ?", [(user_id,) for user_id in user_ids])
        if level_mode == "set":
            conn.executemany("update portal_users set access_level = ? where id = ?", [(access_level, user_id) for user_id in user_ids])
        elif level_mode == "clear":
            conn.executemany("update portal_users set access_level = null where id = ?", [(user_id,) for user_id in user_ids])
        if group_mode == "replace":
            conn.executemany("delete from access_user_groups where user_id = ?", [(user_id,) for user_id in user_ids])
            conn.executemany(
                "insert into access_user_groups (user_id, group_id) values (?, ?)",
                [(user_id, gid) for user_id in user_ids for gid in group_ids],
            )
        elif group_mode == "add" and group_ids:
            conn.executemany(
                "insert or ignore into access_user_groups (user_id, group_id) values (?, ?)",
                [(user_id, gid) for user_id in user_ids for gid in group_ids],
            )
        elif group_mode == "remove" and group_ids:
            conn.executemany(
                "delete from access_user_groups where user_id = ? and group_id = ?",
                [(user_id, gid) for user_id in user_ids for gid in group_ids],
            )
        conn.commit()
    return {"ok": True, "updated": len(user_ids)}


def set_policy_link(source_group_id, target_group_id, can_see=False, can_send=False, can_receive=None):
    source_group_id = int(source_group_id)
    target_group_id = int(target_group_id)
    if can_receive is None:
        can_receive = can_send
    with db_connect() as conn:
        for gid in (source_group_id, target_group_id):
            if not conn.execute("select id from access_groups where id = ?", (gid,)).fetchone():
                raise ValueError("group not found")
        if can_see or can_send or can_receive:
            conn.execute("""
                insert into access_policy_links (source_group_id, target_group_id, can_see, can_send, can_receive)
                values (?, ?, ?, ?, ?)
                on conflict(source_group_id, target_group_id) do update set
                    can_see = excluded.can_see,
                    can_send = excluded.can_send,
                    can_receive = excluded.can_receive
            """, (source_group_id, target_group_id, 1 if can_see else 0, 1 if can_send else 0, 1 if can_receive else 0))
        else:
            conn.execute("delete from access_policy_links where source_group_id = ? and target_group_id = ?", (source_group_id, target_group_id))
        conn.commit()
        row = conn.execute("select * from access_policy_links where source_group_id = ? and target_group_id = ?", (source_group_id, target_group_id)).fetchone()
    return row_to_policy_link(row) if row else {"source_group_id": source_group_id, "target_group_id": target_group_id, "can_see": False, "can_send": False, "can_receive": False}


def access_policy_active():
    with db_connect() as conn:
        row = conn.execute("""
            select
              (select count(*) from portal_users where role_id is not null and revoked_at is null) as assigned_roles,
              (select count(*) from access_user_groups) as group_memberships,
              (select count(*) from access_policy_links) as group_links
        """).fetchone()
    return any(int(row[key] or 0) > 0 for key in row.keys())


def subject_policy(user_id):
    with db_connect() as conn:
        row = conn.execute("""
            select u.id, u.username, u.role_id, u.access_level,
                   r.can_see_all, r.can_send_all, r.can_receive_all,
                   r.can_see_own_groups, r.can_send_own_groups, r.can_receive_own_groups
            from portal_users u
            left join access_roles r on r.id = u.role_id
            where u.id = ? and u.revoked_at is null
        """, (user_id,)).fetchone()
        if not row:
            return None
        groups = {group_row["group_id"] for group_row in conn.execute("select group_id from access_user_groups where user_id = ?", (user_id,)).fetchall()}
    has_role = row["role_id"] is not None
    return {
        "id": row["id"],
        "username": row["username"],
        "access_level": row["access_level"] if "access_level" in row.keys() else None,
        "can_see_all": bool(row["can_see_all"]) if has_role else False,
        "can_send_all": bool(row["can_send_all"]) if has_role else False,
        "can_receive_all": bool(row["can_receive_all"]) if has_role else False,
        "can_see_own_groups": bool(row["can_see_own_groups"]) if has_role else True,
        "can_send_own_groups": bool(row["can_send_own_groups"]) if has_role else True,
        "can_receive_own_groups": bool(row["can_receive_own_groups"]) if has_role else True,
        "groups": groups,
    }


def can_subject_action(viewer_id, target_id, action):
    return explain_subject_action(viewer_id, target_id, action)["allowed"]


def explain_subject_action(viewer_id, target_id, action):
    if int(viewer_id) == int(target_id):
        return {"allowed": True, "reason_code": "self", "reason": "Same user."}
    viewer = subject_policy(viewer_id)
    target = subject_policy(target_id)
    if not viewer or not target:
        return {"allowed": False, "reason_code": "missing_user", "reason": "Source or target user is missing or revoked."}
    if not access_policy_active():
        return {"allowed": True, "reason_code": "open_default", "reason": "No access policy is assigned; users can interact by default."}
    if viewer[f"can_{action}_all"]:
        return {"allowed": True, "reason_code": f"{action}_all", "reason": f"Source role can {action} all users."}
    def level_allowed():
        if action == "receive":
            return (True, "level_not_applied", "Receive permission is controlled by recipient policy.")
        viewer_level = viewer.get("access_level") or 1
        target_level = target.get("access_level") or 1
        allowed = int(viewer_level) >= int(target_level)
        return (
            allowed,
            "level_allowed" if allowed else "level_blocked",
            f"Source level {viewer_level} {'meets' if allowed else 'is below'} target level {target_level}.",
        )
    if viewer[f"can_{action}_own_groups"] and viewer["groups"] & target["groups"]:
        allowed, level_code, level_reason = level_allowed()
        if allowed:
            return {"allowed": True, "reason_code": f"own_group_{action}", "reason": f"Users share a team. {level_reason}"}
        return {"allowed": False, "reason_code": level_code, "reason": level_reason}
    if not viewer["groups"] or not target["groups"]:
        return {"allowed": False, "reason_code": "missing_group", "reason": "Source or target has no team membership for this policy path."}
    column = f"can_{action}"
    with db_connect() as conn:
        source_groups = target["groups"] if action == "receive" else viewer["groups"]
        target_groups = viewer["groups"] if action == "receive" else target["groups"]
        source_placeholders = ",".join("?" for _ in source_groups)
        target_placeholders = ",".join("?" for _ in target_groups)
        params = list(source_groups) + list(target_groups)
        row = conn.execute(f"""
            select 1
            from access_policy_links
            where source_group_id in ({source_placeholders})
              and target_group_id in ({target_placeholders})
              and {column} = 1
            limit 1
        """, params).fetchone()
    if not row:
        return {"allowed": False, "reason_code": f"no_group_link_{action}", "reason": f"No team link allows this {action} path."}
    allowed, level_code, level_reason = level_allowed()
    if allowed:
        return {"allowed": True, "reason_code": f"group_link_{action}", "reason": f"A team link allows this {action} path. {level_reason}"}
    return {"allowed": False, "reason_code": level_code, "reason": level_reason}


def can_subject_see(viewer_id, target_id):
    return can_subject_action(viewer_id, target_id, "see")


def can_subject_send(viewer_id, target_id):
    return can_subject_action(viewer_id, target_id, "send")


def can_subject_receive(recipient_id, sender_id):
    return can_subject_action(recipient_id, sender_id, "receive")


def can_send_datapackage(sender_id, recipient_id):
    return can_subject_send(sender_id, recipient_id) and can_subject_receive(recipient_id, sender_id)


def access_summary():
    return {
        "roles": list_access_roles(),
        "groups": list_access_groups(),
        "links": list_policy_links(),
        "policy_active": access_policy_active(),
        "open_default": ACCESS_CONTROL_ENFORCE and not access_policy_active(),
    }


def access_preview(user_id):
    user_id = int(user_id or 0)
    users = [user for user in list_portal_users() if not user.get("revoked")]
    subject = next((user for user in users if int(user["id"]) == user_id), None)
    if not subject:
        raise ValueError("user not found")

    def preview_user(user, can_see=False, can_send=False, can_receive=False):
        return {
            "id": user["id"],
            "username": user["username"],
            "display_name": user.get("display_name", ""),
            "role_name": user.get("role_name", ""),
            "access_level": user.get("access_level"),
            "groups": user.get("groups", []),
            "can_see": can_see,
            "can_send": can_send,
            "can_receive": can_receive,
        }

    can_see = []
    can_send = []
    seen_by = []
    senders = []
    for target in users:
        if can_subject_see(user_id, target["id"]):
            can_see.append(preview_user(target, can_see=True, can_send=can_send_datapackage(user_id, target["id"]), can_receive=can_send_datapackage(target["id"], user_id)))
        if can_send_datapackage(user_id, target["id"]):
            can_send.append(preview_user(target, can_see=can_subject_see(user_id, target["id"]), can_send=True, can_receive=can_subject_receive(target["id"], user_id)))
        if can_subject_see(target["id"], user_id):
            seen_by.append(preview_user(target, can_see=True, can_send=can_send_datapackage(target["id"], user_id), can_receive=can_send_datapackage(user_id, target["id"])))
        if can_send_datapackage(target["id"], user_id):
            senders.append(preview_user(target, can_see=can_subject_see(target["id"], user_id), can_send=True, can_receive=can_subject_receive(user_id, target["id"])))
    return {
        "subject": preview_user(subject),
        "can_see": can_see,
        "can_send": can_send,
        "seen_by": seen_by,
        "senders": senders,
        "enforced": ACCESS_CONTROL_ENFORCE,
        "policy_active": access_policy_active(),
        "open_default": ACCESS_CONTROL_ENFORCE and not access_policy_active(),
    }


def parse_int_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        raw = []
        for item in value:
            raw.extend(parse_int_list(item))
        return raw
    return [int(part) for part in re.split(r"[, ]+", str(value).strip()) if part]


def find_portal_user_by_plugin_token(token):
    token = (token or "").strip()
    if not re.fullmatch(r"tlp_[A-Za-z0-9_-]{20,100}", token):
        return None
    with db_connect() as conn:
        return conn.execute("""
            select u.*, p.name as profile_name, p.connect_string, p.datapackage_file, p.revoked_at as profile_revoked_at
            from portal_users u
            left join cert_profiles p on p.id = u.cert_profile_id
            where u.plugin_api_token = ?
        """, (token,)).fetchone()


def find_portal_user_by_device_binding(source_ip, device_mac=""):
    source_ip = validate_assigned_ip(source_ip)
    device_mac = validate_device_mac(device_mac)
    with db_connect() as conn:
        rows = conn.execute("""
            select u.*, p.name as profile_name, p.connect_string, p.datapackage_file, p.revoked_at as profile_revoked_at
            from portal_users u
            left join cert_profiles p on p.id = u.cert_profile_id
            where u.assigned_ip = ?
              and u.revoked_at is null
              and p.revoked_at is null
        """, (source_ip,)).fetchall()
    if not rows:
        return None
    if device_mac:
        rows = [row for row in rows if (row["device_mac"] or "").lower() in ("", device_mac)]
    elif any(row["device_mac"] for row in rows):
        return None
    return rows[0] if len(rows) == 1 else None


def learn_portal_user_device(user_id, source_ip="", device_id=""):
    source_ip = validate_assigned_ip(source_ip)
    device_id = validate_device_mac(device_id)
    if not user_id or (not source_ip and not device_id):
        return False
    assignments = []
    params = []
    if source_ip:
        assignments.append("assigned_ip = coalesce(nullif(assigned_ip, ''), ?)")
        params.append(source_ip)
    if device_id:
        assignments.append("device_mac = coalesce(nullif(device_mac, ''), ?)")
        params.append(device_id)
    if not assignments:
        return False
    params.append(int(user_id))
    with db_connect() as conn:
        row = conn.execute("select assigned_ip, device_mac from portal_users where id = ?", (int(user_id),)).fetchone()
        if not row:
            return False
        conn.execute(f"update portal_users set {', '.join(assignments)} where id = ?", params)
        conn.commit()
        updated = conn.execute("select assigned_ip, device_mac from portal_users where id = ?", (int(user_id),)).fetchone()
    return bool(updated and (updated["assigned_ip"] != row["assigned_ip"] or updated["device_mac"] != row["device_mac"]))


def plugin_user_for_request(handler):
    auth = handler.headers.get("Authorization", "")
    token = handler.headers.get("X-TAKlite-Plugin-Token", "")
    if not token and auth.lower().startswith("bearer "):
        token = auth.split(None, 1)[1]
    row = find_portal_user_by_plugin_token(token)
    if row and not row["revoked_at"] and not row["profile_revoked_at"]:
        return portal_user_row(row)
    identity = client_identity_for_cert(handler.client_cert_common_name())
    if identity:
        found = find_portal_user(identity["user_id"])
        if found:
            return portal_user_row(found)
    return None


def group_id_set(user):
    return {int(group_id) for group_id in user.get("group_ids", []) if str(group_id).strip()}


def plugin_context_for_user(user):
    user = attach_access_to_users([user])[0]
    policy = subject_policy(user["id"]) or {}
    users = [item for item in list_portal_users() if not item.get("revoked")]
    groups = list_access_groups()
    roles = list_access_roles()
    return {
        "ok": True,
        "user": user,
        "capabilities": {
            "broad_access": bool(policy.get("can_see_all") or policy.get("can_send_all") or policy.get("can_receive_all")),
            "can_see_all": bool(policy.get("can_see_all")),
            "can_send_all": bool(policy.get("can_send_all")),
            "can_receive_all": bool(policy.get("can_receive_all")),
            "can_see_own_groups": bool(policy.get("can_see_own_groups")),
            "can_send_own_groups": bool(policy.get("can_send_own_groups")),
            "can_receive_own_groups": bool(policy.get("can_receive_own_groups")),
            "can_manage_users": plugin_user_can_create_field_enrollment(user),
            "can_toggle_pli": bool(policy.get("can_see_all") or policy.get("can_send_all") or policy.get("can_receive_all") or user.get("access_level")),
        },
        "access": {
            "policy_active": access_policy_active(),
            "enforced": ACCESS_CONTROL_ENFORCE,
            "roles": roles,
            "groups": groups,
            "links": list_policy_links(),
        },
        "audience_modes": [
            {
                "id": "all_allowed",
                "label": "Everyone I Am Allowed To Send To",
                "description": "The server policy decides every allowed recipient.",
            },
            {
                "id": "own_groups",
                "label": "My Teams Only",
                "description": "Send only to users who share at least one team with me.",
            },
            {
                "id": "groups",
                "label": "Chosen Teams",
                "description": "Send only to members of the teams selected below.",
            },
            {
                "id": "specific_users",
                "label": "Chosen Users",
                "description": "Send only to the users selected below.",
            },
        ],
        "levels": [1, 2, 3, 4],
        "users": [
            {
                "id": item["id"],
                "username": item["username"],
                "display_name": item.get("display_name", ""),
                "role_name": item.get("role_name", ""),
                "access_level": item.get("access_level"),
                "groups": item.get("groups", []),
                "can_send_package": can_send_datapackage(user["id"], item["id"]),
                "can_receive_package": can_send_datapackage(item["id"], user["id"]),
                "can_see_pli": can_subject_see(user["id"], item["id"]),
                "seen_by": can_subject_see(item["id"], user["id"]),
            }
            for item in users
        ],
    }


def plugin_user_can_create_field_enrollment(user):
    user = attach_access_to_users([user])[0]
    policy = subject_policy(user["id"]) or {}
    level = user.get("access_level")
    try:
        level = int(level) if level is not None else 0
    except (TypeError, ValueError):
        level = 0
    return bool(
        (policy.get("can_see_all") and policy.get("can_send_all") and policy.get("can_receive_all"))
        or (level >= 4 and (policy.get("can_see_all") or policy.get("can_send_all") or policy.get("can_receive_all")))
    )


def require_plugin_manager(user):
    if not plugin_user_can_create_field_enrollment(user):
        raise ValueError("this Axon profile cannot manage users")


def plugin_admin_snapshot(user):
    require_plugin_manager(user)
    return {
        "ok": True,
        "users": list_portal_users(),
        "clients": RELAY.snapshot(),
        "access": access_summary(),
    }


def plugin_revoke_user(actor, user_id):
    require_plugin_manager(actor)
    user_id = int(user_id or 0)
    if int(actor["id"]) == user_id:
        raise ValueError("cannot revoke the current Axon profile from the plugin")
    return {"ok": True, "user": revoke_portal_user(user_id)}


def plugin_reissue_user(actor, user_id):
    require_plugin_manager(actor)
    user_id = int(user_id or 0)
    if int(actor["id"]) == user_id:
        raise ValueError("cannot reissue the current Axon profile from the plugin")
    return {"ok": True, "user": reissue_portal_user(user_id)}


def set_user_pli_enabled(actor, user_id, enabled):
    user_id = int(user_id or 0)
    if int(actor["id"]) != user_id and not plugin_user_can_create_field_enrollment(actor):
        raise ValueError("this Axon profile cannot change another user's PLI setting")
    with db_connect() as conn:
        row = conn.execute("select id from portal_users where id = ? and revoked_at is null", (user_id,)).fetchone()
        if not row:
            raise ValueError("portal user not found")
        conn.execute("update portal_users set pli_enabled = ? where id = ?", (1 if enabled else 0, user_id))
        conn.commit()
    return {"ok": True, "user": attach_access_to_users([portal_user_row(find_portal_user(user_id))])[0]}


def plugin_policy_test(actor, source_user_id, target_user_id):
    require_plugin_manager(actor)
    source_user_id = int(source_user_id or 0)
    target_user_id = int(target_user_id or 0)
    source = find_portal_user(source_user_id)
    target = find_portal_user(target_user_id)
    if not source or not target:
        raise ValueError("source or target user not found")
    source_see = explain_subject_action(source_user_id, target_user_id, "see")
    source_send = explain_subject_action(source_user_id, target_user_id, "send")
    target_receive = explain_subject_action(target_user_id, source_user_id, "receive")
    target_see = explain_subject_action(target_user_id, source_user_id, "see")
    target_send = explain_subject_action(target_user_id, source_user_id, "send")
    source_receive = explain_subject_action(source_user_id, target_user_id, "receive")
    return {
        "ok": True,
        "source": attach_access_to_users([portal_user_row(source)])[0],
        "target": attach_access_to_users([portal_user_row(target)])[0],
        "can_see_pli": source_see["allowed"],
        "can_send_package": source_send["allowed"],
        "can_receive_package": target_receive["allowed"],
        "target_can_see_source": target_see["allowed"],
        "target_can_send_source": target_send["allowed"],
        "source_can_receive_target": source_receive["allowed"],
        "reasons": {
            "source_see": source_see,
            "source_send": source_send,
            "target_receive": target_receive,
            "target_see": target_see,
            "target_send": target_send,
            "source_receive": source_receive,
        },
    }


def plugin_create_field_enrollment(user, payload, base_url):
    if not plugin_user_can_create_field_enrollment(user):
        raise ValueError("this Axon profile cannot create Field Registration passes")
    item = create_field_enrollment(
        payload.get("name", "Field Registration"),
        payload.get("username_prefix", "field-user"),
        payload.get("description", ""),
        payload.get("expires_in_hours", 24),
        payload.get("max_uses", 1),
        payload.get("role_id"),
        payload.get("group_ids", []),
        payload.get("access_level"),
        base_url,
    )
    record_audit_event(
        "plugin_field_enrollment_created",
        actor_type="portal_user",
        actor_id=user["id"],
        actor_name=user.get("username", ""),
        outcome="ok",
        reason_code="created",
        details={"id": item.get("id"), "name": item.get("name"), "max_uses": item.get("max_uses")},
    )
    return item


def plugin_audience_filter(sender, target, payload):
    mode = (payload.get("audience_mode") or payload.get("mode") or "all_allowed").strip().lower()
    include_self = bool(payload.get("include_self", False))
    if int(sender["id"]) == int(target["id"]) and not include_self:
        return False, "blocked_self", "Sender is excluded from this audience."
    levels = set(parse_int_list(payload.get("levels", payload.get("allowed_levels", []))))
    if levels:
        target_level = target.get("access_level")
        if target_level is None or int(target_level) not in levels:
            return False, "blocked_level_filter", f"Target level is {target_level or 'not assigned'}."
    if mode in ("all", "all_allowed", "linked", "linked_groups", "trusted", "trusted_groups"):
        return True, "audience_match", "Target is inside the requested broad audience."
    if mode in ("own", "own_group", "own_groups", "my_team", "my_teams"):
        if group_id_set(sender) & group_id_set(target):
            return True, "audience_match_own_group", "Target shares a team with sender."
        return False, "blocked_audience_group", "Target does not share a team with sender."
    if mode in ("group", "groups", "team", "teams"):
        requested_groups = set(parse_int_list(payload.get("group_ids", payload.get("team_ids", []))))
        if not requested_groups:
            return False, "blocked_audience_missing_groups", "No target teams were selected."
        if requested_groups & group_id_set(target):
            return True, "audience_match_group", "Target is in a selected team."
        return False, "blocked_audience_group", "Target is not in a selected team."
    if mode in ("specific", "specific_users", "users", "contacts"):
        requested_users = set(parse_int_list(payload.get("user_ids", payload.get("target_user_ids", []))))
        if not requested_users:
            return False, "blocked_audience_missing_users", "No target users were selected."
        if int(target["id"]) in requested_users:
            return True, "audience_match_user", "Target user was selected."
        return False, "blocked_audience_user", "Target user was not selected."
    return False, "blocked_audience_mode", f"Unsupported audience mode: {mode}."


def plugin_datapackage_audience(sender_user_id, payload):
    sender = portal_user_row(find_portal_user(sender_user_id))
    sender = attach_access_to_users([sender])[0]
    users = [user for user in list_portal_users() if not user.get("revoked")]
    results = []
    for target in users:
        in_audience, audience_code, audience_reason = plugin_audience_filter(sender, target, payload)
        if not in_audience:
            results.append({
                "user_id": target["id"],
                "username": target["username"],
                "display_name": target.get("display_name", ""),
                "allowed": False,
                "reason_code": audience_code,
                "reason": audience_reason,
            })
            continue
        if not can_subject_send(sender["id"], target["id"]):
            results.append({
                "user_id": target["id"],
                "username": target["username"],
                "display_name": target.get("display_name", ""),
                "allowed": False,
                "reason_code": "blocked_sender_policy",
                "reason": "Sender is not allowed to send datapackages to this target.",
            })
            continue
        if not can_subject_receive(target["id"], sender["id"]):
            results.append({
                "user_id": target["id"],
                "username": target["username"],
                "display_name": target.get("display_name", ""),
                "allowed": False,
                "reason_code": "blocked_receive_policy",
                "reason": "Target is not allowed to receive datapackages from sender.",
            })
            continue
        results.append({
            "user_id": target["id"],
            "username": target["username"],
            "display_name": target.get("display_name", ""),
            "allowed": True,
            "reason_code": "allowed_plugin_policy",
            "reason": "Target matched the requested audience and server policy allows delivery.",
        })
    return {
        "sender": sender,
        "audience": {
            "mode": (payload.get("audience_mode") or payload.get("mode") or "all_allowed").strip().lower(),
            "user_ids": parse_int_list(payload.get("user_ids", payload.get("target_user_ids", []))),
            "group_ids": parse_int_list(payload.get("group_ids", payload.get("team_ids", []))),
            "levels": parse_int_list(payload.get("levels", payload.get("allowed_levels", []))),
            "include_self": bool(payload.get("include_self", False)),
        },
        "allowed_user_ids": [item["user_id"] for item in results if item["allowed"]],
        "allowed_count": sum(1 for item in results if item["allowed"]),
        "blocked_count": sum(1 for item in results if not item["allowed"]),
        "items": results,
    }


def plugin_datapackage_history(user_id, limit=25):
    user_id = int(user_id)
    limit = max(1, min(int(limit or 25), 100))
    with db_connect() as conn:
        rows = conn.execute("""
            select distinct p.*
            from datapackages p
            left join datapackage_recipients r on r.package_hash = p.Hash
            left join datapackage_deliveries d on d.package_hash = p.Hash
            where p.CreatorUserId = ?
               or r.target_user_id = ?
               or d.target_user_id = ?
            order by p.PrimaryKey desc
            limit ?
        """, (user_id, user_id, user_id, limit)).fetchall()

        items = []
        for row in rows:
            package = row_to_package(row)
            deliveries = conn.execute("""
                select d.*, u.username, u.display_name
                from datapackage_deliveries d
                left join portal_users u on u.id = d.target_user_id
                where d.package_hash = ?
                order by d.id desc
                limit 20
            """, (package["Hash"],)).fetchall()
            delivery_items = []
            sent = pending = blocked = failed = 0
            for delivery in deliveries:
                item = delivery_row(delivery)
                item["username"] = delivery["username"] or ""
                item["display_name"] = delivery["display_name"] or ""
                delivery_items.append(item)
                status = item["status"]
                if status == "sent":
                    sent += 1
                elif status == "pending":
                    pending += 1
                elif status == "blocked":
                    blocked += 1
                elif status == "failed":
                    failed += 1
            direction = "outbox" if package.get("CreatorUserId") == user_id else "inbox"
            items.append({
                "package": package,
                "direction": direction,
                "sent": sent,
                "pending": pending,
                "blocked": blocked,
                "failed": failed,
                "deliveries": delivery_items,
            })
    return {"ok": True, "items": items}


def plugin_upload_datapackage(handler, qs):
    user = handler.require_plugin_user()
    if not user:
        return None
    payload = {
        "audience_mode": qs.get("audience_mode", qs.get("mode", ["all_allowed"]))[0],
        "user_ids": qs.get("user_ids", qs.get("target_user_ids", [""]))[0],
        "group_ids": qs.get("group_ids", qs.get("team_ids", [""]))[0],
        "levels": qs.get("levels", qs.get("allowed_levels", [""]))[0],
        "include_self": qs.get("include_self", ["false"])[0].lower() in ("1", "true", "yes", "on"),
    }
    filename, data = parse_upload(handler)
    query_name = qs.get("filename", qs.get("name", [""]))[0]
    package_name = normalize_datapackage_name(query_name or filename or "taklite-plugin.dp.zip")
    hash_value = hashlib.sha256(data).hexdigest()
    audience = plugin_datapackage_audience(user["id"], payload)
    policy = normalize_datapackage_policy("sender")
    upsert_package(
        hash_value,
        package_name,
        user.get("username", ""),
        data,
        tak_marti_base_url(),
        creator_user_id=user["id"],
        visibility="private",
        policy=policy,
    )
    allowed_user_ids = audience["allowed_user_ids"]
    set_datapackage_recipients(hash_value, allowed_user_ids)
    if not allowed_user_ids:
        package = row_to_package(find_package(hash_value))
        record_audit_event(
            "plugin_datapackage_upload",
            actor_type="portal_user",
            actor_id=user["id"],
            actor_name=user.get("username", ""),
            remote=handler.client_address[0],
            outcome="blocked",
            reason_code="no_allowed_recipients",
            details={"hash": hash_value, "name": package_name, "blocked": audience["blocked_count"], "audience": audience["audience"]},
        )
        return {
            "ok": False,
            "package": package,
            "url": tak_marti_content_url(hash_value),
            "sent": 0,
            "pending": 0,
            "blocked": audience["blocked_count"],
            "failed": 0,
            "results": audience["items"],
            "audience": audience,
            "error": "no allowed recipients for selected audience",
        }
    send_result = send_datapackage_to_clients({"hash": hash_value, "user_ids": allowed_user_ids})
    send_result["audience"] = audience
    record_audit_event(
        "plugin_datapackage_upload",
        actor_type="portal_user",
        actor_id=user["id"],
        actor_name=user.get("username", ""),
        remote=handler.client_address[0],
        outcome="ok" if send_result.get("ok") else "failed",
        reason_code="uploaded",
        details={"hash": hash_value, "name": package_name, "sent": send_result.get("sent", 0), "pending": send_result.get("pending", 0), "blocked": send_result.get("blocked", 0), "audience": audience["audience"]},
    )
    return send_result


def plugin_send_datapackage(sender_user_id, payload):
    hash_value = (payload.get("hash") or "").strip()
    if not hash_value:
        raise ValueError("hash is required")
    row = find_package(hash_value)
    if not row:
        raise ValueError("datapackage not found")
    package = row_to_package(row)
    creator = package.get("CreatorUserId")
    sender = subject_policy(sender_user_id)
    if creator and int(creator) != int(sender_user_id) and not (sender and sender.get("can_send_all")):
        raise PermissionError("only the package creator or a send-all role can resend this package")
    audience = plugin_datapackage_audience(sender_user_id, payload)
    set_datapackage_recipients(hash_value, audience["allowed_user_ids"])
    if not audience["allowed_user_ids"]:
        record_audit_event(
            "plugin_datapackage_send",
            actor_type="portal_user",
            actor_id=sender_user_id,
            actor_name=audience["sender"].get("username", ""),
            outcome="blocked",
            reason_code="no_allowed_recipients",
            details={"hash": hash_value, "blocked": audience["blocked_count"], "audience": audience["audience"]},
        )
        return {
            "ok": False,
            "package": package,
            "url": tak_marti_content_url(hash_value),
            "sent": 0,
            "pending": 0,
            "blocked": audience["blocked_count"],
            "failed": 0,
            "results": audience["items"],
            "audience": audience,
            "error": "no allowed recipients for selected audience",
        }
    result = send_datapackage_to_clients({"hash": hash_value, "user_ids": audience["allowed_user_ids"]})
    result["audience"] = audience
    record_audit_event(
        "plugin_datapackage_send",
        actor_type="portal_user",
        actor_id=sender_user_id,
        actor_name=audience["sender"].get("username", ""),
        outcome="ok" if result.get("ok") else "failed",
        reason_code="sent_or_queued",
        details={"hash": hash_value, "sent": result.get("sent", 0), "pending": result.get("pending", 0), "blocked": result.get("blocked", 0), "audience": audience["audience"]},
    )
    return result


def marti_groups_response():
    groups = []
    for idx, group in enumerate(list_access_groups(), start=1):
        groups.append({
            "name": group["name"],
            "direction": "OUT",
            "created": group.get("created_at", ""),
            "type": "USER",
            "bitpos": idx,
            "active": True,
            "description": group.get("description", ""),
            "color": group.get("color", ""),
        })
    return {"version": 3, "type": "GroupList", "data": groups}


def client_endpoints_response():
    endpoints = []
    for info in RELAY.snapshot():
        last_seen = info.get("last_seen") or info.get("connected_at") or utc_now()
        endpoints.append({
            "uid": info.get("uid", ""),
            "callsign": info.get("callsign", ""),
            "lastStatus": "Connected",
            "lastEventTime": marti_timestamp(last_seen),
        })
    return {"version": 3, "type": "com.bbn.marti.remote.ClientEndpoint", "data": endpoints}


def mission_empty_response(kind="MissionList"):
    return {"version": 3, "type": kind, "data": []}


def create_policy_subject(username, role_id=None, group_ids=None, access_level=None):
    username = validate_portal_username(username)
    with db_connect() as conn:
        conn.execute("""
            insert into cert_profiles
              (name, description, download_token, connect_string, truststore_file, client_cert_file, datapackage_file, created_at, revoked_at)
            values (?, ?, ?, ?, ?, ?, ?, ?, null)
        """, (username, "test policy subject", secrets.token_urlsafe(18), "10.66.66.1:8089:ssl", "", "", "", utc_now()))
        profile_id = conn.execute("select id from cert_profiles where name = ?", (username,)).fetchone()["id"]
        conn.execute("""
            insert into portal_users
              (username, password_hash, plugin_api_token, display_name, description, cert_profile_id, allow_redownload, created_at, revoked_at, role_id, access_level)
            values (?, ?, ?, ?, ?, ?, 0, ?, null, ?, ?)
        """, (username, password_hash("atakatak"), new_plugin_token(), username, "", profile_id, utc_now(), role_id, validate_access_level(access_level)))
        user_id = conn.execute("select id from portal_users where username = ?", (username,)).fetchone()["id"]
        conn.commit()
    return set_user_access(user_id, role_id=role_id, group_ids=group_ids, access_level=access_level)


def build_bulk_usernames(prefix, count):
    prefix = (prefix or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.@-]{1,56}", prefix):
        raise ValueError("bulk username prefix must use letters, numbers, dot, underscore, dash, or @")
    try:
        count = int(count)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"bulk user count must be between 1 and {MAX_BULK_USERS}") from exc
    if count < 1 or count > MAX_BULK_USERS:
        raise ValueError(f"bulk user count must be between 1 and {MAX_BULK_USERS}")
    usernames = [validate_portal_username(f"{prefix}{idx}") for idx in range(1, count + 1)]
    if len(set(usernames)) != len(usernames):
        raise ValueError("bulk username prefix produced duplicate users")
    return usernames


def generate_portal_password(length=12):
    return "".join(secrets.choice(BULK_PASSWORD_ALPHABET) for _ in range(length))


def new_enrollment_token():
    return f"axj_{secrets.token_urlsafe(24)}"


def validate_username_prefix(prefix):
    prefix = (prefix or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.@-]{3,48}", prefix):
        raise ValueError("username prefix must be 3-48 characters: letters, numbers, dot, underscore, dash, or @")
    return prefix


def validate_enrollment_hours(value):
    try:
        hours = int(value or 24)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"field enrollment expiration must be 1-{MAX_FIELD_ENROLLMENT_HOURS} hours") from exc
    if hours < 1 or hours > MAX_FIELD_ENROLLMENT_HOURS:
        raise ValueError(f"field enrollment expiration must be 1-{MAX_FIELD_ENROLLMENT_HOURS} hours")
    return hours


def validate_enrollment_uses(value):
    try:
        uses = int(value or 1)
    except (TypeError, ValueError) as exc:
        raise ValueError("field enrollment max uses must be 1-100") from exc
    if uses < 1 or uses > 100:
        raise ValueError("field enrollment max uses must be 1-100")
    return uses


def validate_enrollment_token(token):
    token = (token or "").strip()
    if token.startswith("axon-enroll://") or token.startswith("http://") or token.startswith("https://"):
        parsed = urlparse(token)
        params = parse_qs(parsed.query)
        token = (params.get("code") or params.get("token") or [""])[0]
    if not re.fullmatch(r"axj_[A-Za-z0-9_-]{20,100}", token):
        raise ValueError("field enrollment join code is invalid")
    return token


def parse_json_int_list(value):
    if not value:
        return []
    try:
        loaded = json.loads(value)
    except Exception:
        loaded = []
    return parse_int_list(loaded)


def unique_portal_username(prefix, preferred=""):
    candidates = []
    if preferred:
        safe_preferred = re.sub(r"[^A-Za-z0-9_.@-]+", "-", preferred.strip()).strip(".-")
        if len(safe_preferred) >= 3:
            candidates.append(safe_preferred[:64])
    candidates.append(prefix[:64])
    for base in candidates:
        try:
            base = validate_portal_username(base)
        except ValueError:
            continue
        for idx in range(0, 1000):
            suffix = "" if idx == 0 else f"-{idx + 1}"
            candidate = validate_portal_username(f"{base[:64 - len(suffix)]}{suffix}")
            with db_connect() as conn:
                user_exists = conn.execute("select 1 from portal_users where username = ?", (candidate,)).fetchone()
                profile_exists = conn.execute("select 1 from cert_profiles where name = ?", (candidate,)).fetchone()
            if not user_exists and not profile_exists:
                return candidate
    raise ValueError("could not allocate a unique username for field enrollment")


def enrollment_row(row, base_url=""):
    group_ids = parse_json_int_list(row["group_ids"])
    item = {
        "id": row["id"],
        "name": row["name"],
        "token": row["token"],
        "join_code": row["token"],
        "username_prefix": row["username_prefix"],
        "description": row["description"] or "",
        "role_id": row["role_id"],
        "role_name": row_get(row, "role_name", "") or "",
        "access_level": row["access_level"],
        "group_ids": group_ids,
        "max_uses": row["max_uses"],
        "used_count": row["used_count"],
        "remaining_uses": max(0, int(row["max_uses"] or 0) - int(row["used_count"] or 0)),
        "expires_at": row["expires_at"],
        "created_at": row["created_at"],
        "revoked_at": row["revoked_at"] or "",
        "revoked": bool(row["revoked_at"]),
        "expired": parse_time(row["expires_at"]) <= datetime.now(timezone.utc),
    }
    item["active"] = not item["revoked"] and not item["expired"] and item["remaining_uses"] > 0
    item["join_path"] = f"/connect/enroll?code={quote(item['token'])}"
    item["axon_uri"] = f"axon://field-enroll?code={quote(item['token'])}"
    if base_url:
        item["join_url"] = f"{base_url}{item['join_path']}"
        item["axon_uri"] = f"axon://field-enroll?server={quote(base_url, safe='')}&code={quote(item['token'])}"
    return item


def list_field_enrollments(base_url=""):
    with db_connect() as conn:
        rows = conn.execute("""
            select e.*, r.name as role_name
            from field_enrollments e
            left join access_roles r on r.id = e.role_id
            order by e.id desc
        """).fetchall()
    return [enrollment_row(row, base_url) for row in rows]


def find_field_enrollment(enrollment_id):
    with db_connect() as conn:
        return conn.execute("select * from field_enrollments where id = ?", (int(enrollment_id or 0),)).fetchone()


def find_field_enrollment_by_token(token):
    token = validate_enrollment_token(token)
    with db_connect() as conn:
        return conn.execute("select * from field_enrollments where token = ?", (token,)).fetchone()


def create_field_enrollment(name, username_prefix, description="", expires_in_hours=24, max_uses=1, role_id=None, group_ids=None, access_level=None, base_url=""):
    name = validate_access_name(name or "Field Enrollment", "field enrollment name")
    username_prefix = validate_username_prefix(username_prefix or "field-user")
    expires_in_hours = validate_enrollment_hours(expires_in_hours)
    max_uses = validate_enrollment_uses(max_uses)
    access_level = validate_access_level(access_level)
    group_ids = [int(value) for value in (group_ids or []) if str(value).strip()]
    role_id = int(role_id or 0) or None
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    token = new_enrollment_token()
    with db_connect() as conn:
        if role_id and not conn.execute("select id from access_roles where id = ?", (role_id,)).fetchone():
            raise ValueError("role not found")
        if group_ids:
            placeholders = ",".join("?" for _ in group_ids)
            found = {row["id"] for row in conn.execute(f"select id from access_groups where id in ({placeholders})", group_ids).fetchall()}
            missing = sorted(set(group_ids) - found)
            if missing:
                raise ValueError(f"group not found: {missing[0]}")
        conn.execute("""
            insert into field_enrollments
              (name, token, username_prefix, description, role_id, access_level, group_ids, max_uses, used_count, expires_at, created_at, revoked_at)
            values (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, null)
        """, (name, token, username_prefix, (description or "").strip(), role_id, access_level, json.dumps(group_ids), max_uses, expires_at, utc_now()))
        conn.commit()
        row = conn.execute("select * from field_enrollments where token = ?", (token,)).fetchone()
    return enrollment_row(row, base_url)


def revoke_field_enrollment(enrollment_id):
    with db_connect() as conn:
        row = conn.execute("select * from field_enrollments where id = ?", (int(enrollment_id or 0),)).fetchone()
        if not row:
            raise ValueError("field enrollment pass not found")
        conn.execute("update field_enrollments set revoked_at = coalesce(revoked_at, ?) where id = ?", (utc_now(), row["id"]))
        conn.commit()
        row = conn.execute("select * from field_enrollments where id = ?", (row["id"],)).fetchone()
    return enrollment_row(row)


def redeem_field_enrollment(token, source_ip="", device_id="", display_name="", base_url=""):
    token = validate_enrollment_token(token)
    source_ip = validate_assigned_ip(source_ip)
    device_id = validate_device_mac(device_id)
    now = datetime.now(timezone.utc)
    with db_connect() as conn:
        row = conn.execute("select * from field_enrollments where token = ?", (token,)).fetchone()
        if not row:
            raise ValueError("field enrollment pass not found")
        info = enrollment_row(row, base_url)
        if info["revoked"]:
            raise ValueError("field enrollment pass has been revoked")
        if info["expired"]:
            raise ValueError("field enrollment pass has expired")
        if info["remaining_uses"] <= 0:
            raise ValueError("field enrollment pass has no remaining uses")
        conn.execute("update field_enrollments set used_count = used_count + 1 where id = ?", (row["id"],))
        conn.commit()

    username = unique_portal_username(row["username_prefix"], display_name)
    password = generate_portal_password(16)
    user = create_portal_user(
        username,
        password,
        display_name or username,
        row["description"] or f"Field enrollment {row['name']}",
        True,
        row["role_id"],
        parse_json_int_list(row["group_ids"]),
        row["access_level"],
        source_ip,
        device_id,
    )
    user_with_token = portal_user_row(find_portal_user(user["id"]), include_plugin_token=True)
    profile = json.loads(build_portal_user_plugin_config(user_with_token))
    cert_profile = find_cert_profile(user["cert_profile_id"])
    package_path_value = cert_profile_row(cert_profile)["public_download_path"] if cert_profile else ""
    user_public = attach_access_to_users([portal_user_row(find_portal_user(user["id"]))])[0]
    result = {
        "ok": True,
        "message": "field enrollment complete",
        "user": user_public,
        "profile": profile,
        "portal_password": password,
        "connection_package_url": f"{base_url}{package_path_value}" if base_url and package_path_value else package_path_value,
        "portal_url": f"{base_url}{user['portal_path']}" if base_url else user["portal_path"],
    }
    record_audit_event(
        "field_enrollment_redeemed",
        actor_type="portal_user",
        actor_id=user["id"],
        actor_name=user["username"],
        remote=source_ip,
        outcome="ok",
        reason_code="redeemed",
        details={"enrollment": row["name"], "device_id_supplied": bool(device_id)},
    )
    return result


def ensure_bulk_users_available(usernames):
    if not usernames:
        raise ValueError("no users requested")
    placeholders = ",".join("?" for _ in usernames)
    with db_connect() as conn:
        users = conn.execute(f"select username from portal_users where username in ({placeholders})", usernames).fetchall()
        profiles = conn.execute(f"select name from cert_profiles where name in ({placeholders})", usernames).fetchall()
    conflicts = sorted({row[0] for row in users} | {row[0] for row in profiles})
    if conflicts:
        preview = ", ".join(conflicts[:8])
        suffix = "..." if len(conflicts) > 8 else ""
        raise ValueError(f"bulk user/profile already exists: {preview}{suffix}")


def create_bulk_portal_users(prefix, count, description="", allow_redownload=False, base_url="", role_id=None, group_ids=None, access_level=None):
    usernames = build_bulk_usernames(prefix, count)
    ensure_bulk_users_available(usernames)
    shared_password = BULK_PORTAL_PASSWORD
    items = []
    note = (description or "").strip()
    for username in usernames:
        create_args = [
            username,
            shared_password,
            username,
            note or f"Bulk user {username}",
            allow_redownload,
        ]
        if role_id or group_ids or access_level:
            create_args.extend([role_id, group_ids, access_level])
        user = create_portal_user(*create_args)
        portal_path = user.get("portal_path") or "/connect/"
        items.append({
            **user,
            "password": shared_password,
            "portal_url": f"{base_url}{portal_path}" if base_url else portal_path,
            "download_url": f"/api/cert-profiles/download?id={user['cert_profile_id']}",
        })
    return {"ok": True, "count": len(items), "shared_password": shared_password, "items": items}


def unique_profile_name(base):
    base = safe_profile_name(base)
    with db_connect() as conn:
        for idx in range(100):
            candidate = base if idx == 0 else f"{base}-{idx + 1}"
            row = conn.execute("select id from cert_profiles where name = ?", (candidate,)).fetchone()
            if not row:
                return candidate
    return f"{base}-{secrets.token_hex(3)}"


def row_get(row, key, default=""):
    try:
        if key in row.keys():
            return row[key]
    except AttributeError:
        if isinstance(row, dict):
            return row.get(key, default)
    return default


def portal_user_row(row, include_plugin_token=False):
    profile = row["profile_name"] or ""
    revoked = bool(row["revoked_at"] or row["profile_revoked_at"])
    username = row["username"]
    role_id = row["role_id"] if "role_id" in row.keys() else None
    access_level = row["access_level"] if "access_level" in row.keys() else None
    item = {
        "id": row["id"],
        "username": username,
        "display_name": row["display_name"] or "",
        "description": row["description"] or "",
        "assigned_ip": row["assigned_ip"] if "assigned_ip" in row.keys() and row["assigned_ip"] else "",
        "device_mac": row["device_mac"] if "device_mac" in row.keys() and row["device_mac"] else "",
        "cert_profile_id": row["cert_profile_id"],
        "profile_name": profile,
        "connect_string": row["connect_string"] or "",
        "allow_redownload": bool(row["allow_redownload"]),
        "first_download_at": row["first_download_at"] or "",
        "last_download_at": row["last_download_at"] or "",
        "download_count": row["download_count"] or 0,
        "created_at": row["created_at"],
        "revoked_at": row["revoked_at"] or row["profile_revoked_at"] or "",
        "revoked": revoked,
        "role_id": role_id,
        "access_level": access_level,
        "pli_enabled": bool(row_get(row, "pli_enabled", 1)),
        "role_name": "",
        "groups": [],
        "group_ids": [],
        "portal_path": f"/connect/?u={quote(username)}",
        "qr_path": f"/api/portal-users/qr?id={row['id']}",
    }
    if include_plugin_token:
        item["plugin_api_token"] = row_get(row, "plugin_api_token", "") or ""
    return item


def attach_access_to_users(items):
    if not items:
        return items
    user_ids = [item["id"] for item in items]
    placeholders = ",".join("?" for _ in user_ids)
    with db_connect() as conn:
        role_rows = conn.execute(f"""
            select u.id as user_id, r.name as role_name
            from portal_users u
            left join access_roles r on r.id = u.role_id
            where u.id in ({placeholders})
        """, user_ids).fetchall()
        group_rows = conn.execute(f"""
            select ug.user_id, g.id, g.name, g.description, g.color, g.created_at
            from access_user_groups ug
            join access_groups g on g.id = ug.group_id
            where ug.user_id in ({placeholders})
            order by lower(g.name)
        """, user_ids).fetchall()
    role_names = {row["user_id"]: row["role_name"] or "" for row in role_rows}
    groups_by_user = {user_id: [] for user_id in user_ids}
    for row in group_rows:
        groups_by_user.setdefault(row["user_id"], []).append(row_to_group(row))
    for item in items:
        groups = groups_by_user.get(item["id"], [])
        item["role_name"] = role_names.get(item["id"], "")
        item["groups"] = groups
        item["group_ids"] = [group["id"] for group in groups]
    return items


def list_portal_users():
    with db_connect() as conn:
        rows = conn.execute("""
            select u.*, p.name as profile_name, p.connect_string, p.revoked_at as profile_revoked_at
            from portal_users u
            left join cert_profiles p on p.id = u.cert_profile_id
            order by u.id desc
        """).fetchall()
    return attach_access_to_users([portal_user_row(row) for row in rows])


def find_portal_user(user_id):
    with db_connect() as conn:
        return conn.execute("""
            select u.*, p.name as profile_name, p.connect_string, p.datapackage_file, p.revoked_at as profile_revoked_at
            from portal_users u
            left join cert_profiles p on p.id = u.cert_profile_id
            where u.id = ?
        """, (user_id,)).fetchone()


def find_portal_user_by_username(username):
    with db_connect() as conn:
        return conn.execute("""
            select u.*, p.name as profile_name, p.connect_string, p.datapackage_file, p.revoked_at as profile_revoked_at
            from portal_users u
            left join cert_profiles p on p.id = u.cert_profile_id
            where u.username = ?
        """, ((username or "").strip(),)).fetchone()


def create_portal_user(username, password, display_name="", description="", allow_redownload=False, role_id=None, group_ids=None, access_level=None, assigned_ip="", device_mac=""):
    username = validate_portal_username(username)
    assigned_ip = validate_assigned_ip(assigned_ip)
    device_mac = validate_device_mac(device_mac)
    if len(password or "") < 8:
        raise ValueError("portal password must be at least 8 characters")
    with db_connect() as conn:
        if conn.execute("select id from portal_users where username = ?", (username,)).fetchone():
            raise ValueError("a portal user with that username already exists")
    profile_name = unique_profile_name(username)
    plugin_token = new_plugin_token()
    profile = create_cert_profile(profile_name, description or f"Portal user {username}", plugin_token=plugin_token)
    with db_connect() as conn:
        conn.execute("""
            insert into portal_users
              (username, password_hash, plugin_api_token, display_name, description, assigned_ip, device_mac, cert_profile_id, allow_redownload, created_at, revoked_at, access_level)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, null, ?)
        """, (
            username,
            password_hash(password),
            plugin_token,
            (display_name or username).strip(),
            (description or "").strip(),
            assigned_ip,
            device_mac,
            profile["id"],
            1 if allow_redownload else 0,
            utc_now(),
            validate_access_level(access_level),
        ))
        conn.commit()
        user_id = conn.execute("select id from portal_users where username = ?", (username,)).fetchone()["id"]
    if role_id or group_ids or access_level:
        return set_user_access(user_id, role_id=role_id, group_ids=group_ids, access_level=access_level)
    return attach_access_to_users([portal_user_row(find_portal_user(user_id))])[0]


def authenticate_portal_user(username, password):
    row = find_portal_user_by_username(username)
    if not row or row["revoked_at"] or row["profile_revoked_at"]:
        return None
    if not verify_password(password or "", row["password_hash"]):
        return None
    return row


def create_portal_session(user_id):
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=PORTAL_SESSION_HOURS)
    with db_connect() as conn:
        conn.execute(
            "insert into portal_sessions (token, user_id, created_at, expires_at) values (?, ?, ?, ?)",
            (token, user_id, now.replace(microsecond=0).isoformat().replace("+00:00", "Z"), expires.replace(microsecond=0).isoformat().replace("+00:00", "Z")),
        )
        conn.commit()
    return token


def validate_portal_session(token):
    if not token:
        return None
    with db_connect() as conn:
        row = conn.execute("""
            select s.user_id, s.expires_at
            from portal_sessions s
            join portal_users u on u.id = s.user_id
            left join cert_profiles p on p.id = u.cert_profile_id
            where s.token = ? and u.revoked_at is null and p.revoked_at is null
        """, (token,)).fetchone()
        if not row:
            return None
        expires = parse_utc(row["expires_at"])
        if not expires or expires <= datetime.now(timezone.utc):
            conn.execute("delete from portal_sessions where token = ?", (token,))
            conn.commit()
            return None
    return find_portal_user(row["user_id"])


def portal_logout(token):
    if token:
        with db_connect() as conn:
            conn.execute("delete from portal_sessions where token = ?", (token,))
            conn.commit()


def reset_portal_password(user_id, password):
    if len(password or "") < 8:
        raise ValueError("portal password must be at least 8 characters")
    with db_connect() as conn:
        row = conn.execute("select id from portal_users where id = ?", (user_id,)).fetchone()
        if not row:
            raise ValueError("portal user not found")
        conn.execute("update portal_users set password_hash = ? where id = ?", (password_hash(password), user_id))
        conn.execute("delete from portal_sessions where user_id = ?", (user_id,))
        conn.commit()
    return portal_user_row(find_portal_user(user_id))


def edit_portal_user(user_id, display_name="", description="", assigned_ip="", device_mac=""):
    assigned_ip = validate_assigned_ip(assigned_ip)
    device_mac = validate_device_mac(device_mac)
    with db_connect() as conn:
        row = conn.execute("select id from portal_users where id = ?", (user_id,)).fetchone()
        if not row:
            raise ValueError("portal user not found")
        conn.execute("""
            update portal_users
            set display_name = ?, description = ?, assigned_ip = ?, device_mac = ?
            where id = ?
        """, ((display_name or "").strip(), (description or "").strip(), assigned_ip, device_mac, user_id))
        conn.commit()
    return portal_user_row(find_portal_user(user_id))


def set_portal_redownload(user_id, allow_redownload):
    with db_connect() as conn:
        row = conn.execute("select id from portal_users where id = ?", (user_id,)).fetchone()
        if not row:
            raise ValueError("portal user not found")
        conn.execute("update portal_users set allow_redownload = ? where id = ?", (1 if allow_redownload else 0, user_id))
        conn.commit()
    return portal_user_row(find_portal_user(user_id))


def revoke_portal_user(user_id):
    row = find_portal_user(user_id)
    if not row:
        raise ValueError("portal user not found")
    revoke_cert_profile(row["cert_profile_id"])
    with db_connect() as conn:
        conn.execute("update portal_users set revoked_at = coalesce(revoked_at, ?) where id = ?", (utc_now(), user_id))
        conn.execute("delete from portal_sessions where user_id = ?", (user_id,))
        conn.commit()
    return portal_user_row(find_portal_user(user_id))


def delete_portal_user(user_id, delete_profile=False):
    row = find_portal_user(user_id)
    if not row:
        raise ValueError("portal user not found")
    profile_id = row["cert_profile_id"]
    with db_connect() as conn:
        conn.execute("delete from portal_sessions where user_id = ?", (user_id,))
        conn.execute("delete from portal_users where id = ?", (user_id,))
        conn.commit()
    deleted_profile = None
    if delete_profile and profile_id:
        deleted_profile = delete_cert_profile(profile_id, True)
    return {"deleted": True, "deleted_profile": deleted_profile}


def reissue_portal_user(user_id):
    row = find_portal_user(user_id)
    if not row:
        raise ValueError("portal user not found")
    if row["cert_profile_id"]:
        revoke_cert_profile(row["cert_profile_id"])
    profile_name = unique_profile_name(row["username"])
    plugin_token = row["plugin_api_token"] or new_plugin_token()
    profile = create_cert_profile(profile_name, row["description"] or f"Portal user {row['username']}", plugin_token=plugin_token)
    with db_connect() as conn:
        conn.execute("""
            update portal_users
            set cert_profile_id = ?, plugin_api_token = ?, first_download_at = null, last_download_at = null, download_count = 0, revoked_at = null
            where id = ?
        """, (profile["id"], plugin_token, user_id))
        conn.execute("delete from portal_sessions where user_id = ?", (user_id,))
        conn.commit()
    return portal_user_row(find_portal_user(user_id))


def mark_portal_download(user_id):
    now = utc_now()
    with db_connect() as conn:
        conn.execute("""
            update portal_users
            set first_download_at = coalesce(first_download_at, ?),
                last_download_at = ?,
                download_count = download_count + 1
            where id = ?
        """, (now, now, user_id))
        conn.commit()


def safe_profile_name(name):
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", (name or "").strip()).strip(".-")
    if not safe:
        raise ValueError("profile name is required")
    return safe[:64]


def cert_profile_row(row):
    token = row["download_token"] or ""
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"] or "",
        "download_token": token,
        "public_download_path": f"/connect/{token}.dp.zip" if token else "",
        "connect_string": row["connect_string"],
        "truststore_file": Path(row["truststore_file"]).name,
        "client_cert_file": Path(row["client_cert_file"]).name,
        "datapackage_file": Path(row["datapackage_file"]).name,
        "created_at": row["created_at"],
        "revoked_at": row["revoked_at"] or "",
        "revoked": bool(row["revoked_at"]),
    }


def list_cert_profiles():
    with db_connect() as conn:
        rows = conn.execute("select * from cert_profiles order by id desc").fetchall()
    return [cert_profile_row(row) for row in rows]


def find_cert_profile(profile_id):
    with db_connect() as conn:
        return conn.execute("select * from cert_profiles where id = ?", (profile_id,)).fetchone()


def find_cert_profile_by_token(token):
    if not re.fullmatch(r"[A-Za-z0-9_-]{16,80}", token or ""):
        return None
    with db_connect() as conn:
        return conn.execute("select * from cert_profiles where download_token = ?", (token,)).fetchone()


def client_cert_authorized(common_name):
    if not common_name:
        return not COT_TLS_REQUIRE_CLIENT_CERT
    if ALLOW_LEGACY_CLIENT_CERT and common_name == "taklite-client":
        return True
    with db_connect() as conn:
        row = conn.execute(
            "select revoked_at from cert_profiles where name = ?", (common_name,)
        ).fetchone()
    return bool(row and not row["revoked_at"])


def client_identity_for_cert(common_name):
    common_name = (common_name or "").strip()
    if not common_name:
        return None
    with db_connect() as conn:
        row = conn.execute("""
            select u.id as user_id,
                   u.username,
                   u.revoked_at as user_revoked_at,
                   p.id as cert_profile_id,
                   p.name as cert_name,
                   p.revoked_at as profile_revoked_at
            from cert_profiles p
            left join portal_users u on u.cert_profile_id = p.id
            where p.name = ?
        """, (common_name,)).fetchone()
    if not row or row["profile_revoked_at"] or row["user_revoked_at"] or not row["user_id"]:
        return None
    return {
        "user_id": row["user_id"],
        "username": row["username"],
        "cert_profile_id": row["cert_profile_id"],
        "cert_cn": row["cert_name"],
    }


def cot_delivery_allowed(sender_user_id, target_user_id, enforce=None):
    if enforce is None:
        enforce = ACCESS_CONTROL_ENFORCE
    if not enforce:
        return True
    if not sender_user_id or not target_user_id:
        return False
    return can_subject_send(sender_user_id, target_user_id) or can_subject_see(target_user_id, sender_user_id)


def package_visible_to_user(package, user_id, enforce=None):
    return package_access_for_user(package, user_id, enforce)["allowed"]


def package_explicit_recipient_ids(hash_value):
    hash_value = (hash_value or "").strip()
    if not hash_value:
        return set()
    with db_connect() as conn:
        rows = conn.execute("select target_user_id from datapackage_recipients where package_hash = ?", (hash_value,)).fetchall()
    return {int(row["target_user_id"]) for row in rows}


def set_datapackage_recipients(hash_value, user_ids):
    hash_value = (hash_value or "").strip()
    user_ids = sorted({int(user_id) for user_id in (user_ids or []) if str(user_id).strip()})
    if not hash_value:
        raise ValueError("hash is required")
    with db_connect() as conn:
        conn.execute("delete from datapackage_recipients where package_hash = ?", (hash_value,))
        conn.executemany(
            "insert or ignore into datapackage_recipients (package_hash, target_user_id, created_at) values (?, ?, ?)",
            [(hash_value, user_id, utc_now()) for user_id in user_ids],
        )
        conn.commit()
    return user_ids


def package_access_for_user(package, user_id, enforce=None):
    if enforce is None:
        enforce = ACCESS_CONTROL_ENFORCE
    visibility = (package.get("Visibility") or package.get("Tool") or "private").lower()
    tool = (package.get("Tool") or "").lower()
    if visibility == "private" and tool == "public":
        visibility = "public"
    result = {
        "allowed": False,
        "reason_code": "blocked_unknown",
        "reason": "Blocked by TAKlite package policy.",
    }
    creator_user_id = package.get("CreatorUserId")
    explicit_recipients = package_explicit_recipient_ids(package.get("Hash", ""))
    if explicit_recipients:
        if not user_id:
            result.update({"reason_code": "blocked_no_identity", "reason": "Client identity is required for packages with explicit recipients."})
            return result
        if creator_user_id and int(user_id) == int(creator_user_id):
            result.update({"allowed": True, "reason_code": "allowed_creator", "reason": "User created this package."})
            return result
        if int(user_id) not in explicit_recipients:
            result.update({"reason_code": "blocked_explicit_audience", "reason": "User is not in the package's selected recipient list."})
            return result
    if not enforce:
        result.update({"allowed": True, "reason_code": "allowed_enforcement_off", "reason": "Access enforcement is off."})
        return result
    is_public = visibility == "public" or tool == "public"
    if not user_id:
        if is_public and not creator_user_id:
            result.update({"allowed": True, "reason_code": "allowed_public", "reason": "Public package."})
        else:
            result.update({"reason_code": "blocked_no_identity", "reason": "Client certificate identity is required for this package."})
        return result
    if not access_policy_active():
        result.update({"allowed": True, "reason_code": "allowed_open_default", "reason": "No access policy is assigned; server is in open default mode."})
        return result
    if is_public and not creator_user_id:
        result.update({"allowed": True, "reason_code": "allowed_public", "reason": "Public package."})
        return result
    if not creator_user_id:
        result.update({"reason_code": "blocked_no_creator_identity", "reason": "Private package has no mapped creator identity."})
        return result
    if int(user_id) == int(creator_user_id):
        result.update({"allowed": True, "reason_code": "allowed_creator", "reason": "User created this package."})
        return result
    policy_mode = (package.get("PolicyMode") or "sender").lower()
    allowed_levels = package.get("AllowedLevels") or []
    if isinstance(allowed_levels, str):
        allowed_levels = deserialize_levels(allowed_levels)
    viewer = subject_policy(user_id)
    if policy_mode.startswith("level_") and allowed_levels:
        if viewer and viewer.get("can_see_all"):
            result.update({"allowed": True, "reason_code": "allowed_admin", "reason": "User role can see all packages."})
            return result
        viewer_level = viewer.get("access_level") if viewer else None
        if viewer_level is None or int(viewer_level) not in set(int(level) for level in allowed_levels):
            result.update({
                "reason_code": "blocked_level_policy",
                "reason": f"Package requires {parse_datapackage_policy_label(policy_mode, serialize_levels(allowed_levels))}; user level is {viewer_level or 'not assigned'}.",
            })
            return result
    if not can_subject_send(creator_user_id, user_id):
        result.update({"reason_code": "blocked_sender_policy", "reason": "Package creator is not allowed to send to requester."})
        return result
    if not can_subject_receive(user_id, creator_user_id):
        result.update({"reason_code": "blocked_receive_policy", "reason": "Requester is not allowed to receive from the package creator."})
        return result
    if can_send_datapackage(creator_user_id, user_id):
        result.update({"allowed": True, "reason_code": "allowed_package_policy", "reason": "Package creator can send to requester and requester can receive from creator."})
        return result
    return result


def package_visible_to_request(row, handler):
    return package_visible_to_user(row_to_package(row), handler.authenticated_user_id(), ACCESS_CONTROL_ENFORCE)


def normalize_datapackage_policy(mode, allowed_levels=None, max_level=None):
    mode = (mode or "sender").strip().lower()
    if mode in ("sender", "sender_policy"):
        return {"mode": "sender", "allowed_levels": [], "label": "Sender policy"}
    if mode not in ("level_only", "level_all"):
        raise ValueError("package policy mode must be sender, level_only, or level_all")
    if max_level not in (None, ""):
        levels = [validate_access_level(max_level, allow_empty=False)]
    else:
        levels = [validate_access_level(level, allow_empty=False) for level in (allowed_levels or []) if str(level).strip()]
    levels = sorted(set(levels))
    if not levels:
        raise ValueError("select at least one level for this package policy")
    if mode == "level_all":
        levels = list(range(1, max(levels) + 1))
    return {"mode": mode, "allowed_levels": levels, "label": parse_datapackage_policy_label(mode, serialize_levels(levels))}


def update_datapackage_policy(hash_value, mode, allowed_levels=None, max_level=None):
    hash_value = (hash_value or "").strip()
    if not hash_value:
        raise ValueError("hash is required")
    policy = normalize_datapackage_policy(mode, allowed_levels, max_level)
    with db_connect() as conn:
        row = conn.execute("select Hash from datapackages where Hash = ?", (hash_value,)).fetchone()
        if not row:
            raise ValueError("datapackage not found")
        conn.execute(
            "update datapackages set PolicyMode = ?, AllowedLevels = ? where Hash = ?",
            (policy["mode"], serialize_levels(policy["allowed_levels"]), hash_value),
        )
        conn.commit()
    row = find_package(hash_value)
    return {"ok": True, "package": row_to_package(row)}


def datapackage_access_preview(hash_value):
    row = find_package(hash_value)
    if not row:
        raise ValueError("datapackage not found")
    package = row_to_package(row)
    users = [user for user in list_portal_users() if not user.get("revoked")]
    rows = []
    for user in users:
        access = package_access_for_user(package, user["id"], ACCESS_CONTROL_ENFORCE)
        rows.append({
            "user_id": user["id"],
            "username": user["username"],
            "display_name": user.get("display_name", ""),
            "role_name": user.get("role_name", ""),
            "access_level": user.get("access_level"),
            "groups": user.get("groups", []),
            "allowed": access["allowed"],
            "reason_code": access["reason_code"],
            "reason": access["reason"],
        })
    return {
        "package": package,
        "policy": {
            "mode": package["PolicyMode"],
            "allowed_levels": package["AllowedLevels"],
            "label": package["PolicyLabel"],
        },
        "allowed_count": sum(1 for item in rows if item["allowed"]),
        "blocked_count": sum(1 for item in rows if not item["allowed"]),
        "items": rows,
    }


def record_datapackage_delivery(package_hash, target_user_id=None, status="pending", reason_code="pending_offline", reason="", target_uid="", target_callsign="", increment_attempt=False):
    now = utc_now()
    attempts = 1 if increment_attempt else 0
    with db_connect() as conn:
        conn.execute("""
            insert into datapackage_deliveries
              (package_hash, target_user_id, target_uid, target_callsign, status, reason_code, reason, attempts, created_at, updated_at, delivered_at)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            package_hash,
            target_user_id,
            (target_uid or "").strip(),
            (target_callsign or "").strip(),
            status,
            reason_code,
            reason,
            attempts,
            now,
            now,
            now if status == "sent" else None,
        ))
        conn.commit()
        delivery_id = conn.execute("select last_insert_rowid()").fetchone()[0]
    return delivery_id


def update_datapackage_delivery(delivery_id, status, reason_code, reason, target_uid="", target_callsign="", increment_attempt=True):
    now = utc_now()
    with db_connect() as conn:
        conn.execute("""
            update datapackage_deliveries
            set status = ?,
                reason_code = ?,
                reason = ?,
                target_uid = coalesce(nullif(?, ''), target_uid),
                target_callsign = coalesce(nullif(?, ''), target_callsign),
                attempts = attempts + ?,
                updated_at = ?,
                delivered_at = case when ? = 'sent' then ? else delivered_at end
            where id = ?
        """, (
            status,
            reason_code,
            reason,
            (target_uid or "").strip(),
            (target_callsign or "").strip(),
            1 if increment_attempt else 0,
            now,
            status,
            now,
            delivery_id,
        ))
        conn.commit()


def list_pending_datapackage_deliveries(user_id):
    with db_connect() as conn:
        return conn.execute("""
            select *
            from datapackage_deliveries
            where target_user_id = ?
              and status = 'pending'
            order by id asc
            limit 25
        """, (user_id,)).fetchall()


def delivery_row(row):
    return {
        "id": row["id"],
        "package_hash": row["package_hash"],
        "target_user_id": row["target_user_id"],
        "target_uid": row["target_uid"] or "",
        "target_callsign": row["target_callsign"] or "",
        "status": row["status"],
        "reason_code": row["reason_code"],
        "reason": row["reason"],
        "attempts": row["attempts"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "delivered_at": row["delivered_at"] or "",
    }


def list_datapackage_deliveries(hash_value="", limit=100):
    params = []
    where = ""
    if hash_value:
        where = "where d.package_hash = ?"
        params.append(hash_value)
    params.append(int(limit))
    with db_connect() as conn:
        rows = conn.execute(f"""
            select d.*, u.username, u.display_name
            from datapackage_deliveries d
            left join portal_users u on u.id = d.target_user_id
            {where}
            order by d.id desc
            limit ?
        """, params).fetchall()
    items = []
    for row in rows:
        item = delivery_row(row)
        item["username"] = row["username"] or ""
        item["display_name"] = row["display_name"] or ""
        items.append(item)
    return items


def run_openssl(args):
    result = subprocess.run(["openssl", *args], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or "openssl failed").strip())


P12_CERT_COMPAT_ARGS = [
    "-certpbe", "PBE-SHA1-3DES",
    "-macalg", "sha1",
]
P12_KEY_COMPAT_ARGS = [
    *P12_CERT_COMPAT_ARGS,
    "-keypbe", "PBE-SHA1-3DES",
]


def cert_host_kind(host):
    host = (host or "").strip()
    try:
        ipaddress.ip_address(host)
        return "IP"
    except ValueError:
        return "DNS"


def tls_server_hosts():
    hosts = [
        SERVER_HOST,
        PUBLIC_HOST,
        "localhost",
        "127.0.0.1",
        "taklite.local",
    ]
    seen = set()
    result = []
    for host in hosts:
        host = (host or "").strip()
        if not host or host in ("0.0.0.0", "::"):
            continue
        key = host.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(host)
    return result or ["127.0.0.1", "localhost"]


def subject_alt_name_for_hosts(hosts):
    entries = []
    seen = set()
    for host in hosts:
        kind = cert_host_kind(host)
        value = f"{kind}:{host}"
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        entries.append(value)
    return ",".join(entries)


def cert_identity_set_from_text(text):
    identities = set()
    for value in re.findall(r"IP Address:([^,\n]+)", text or ""):
        identities.add(("IP", value.strip()))
    for value in re.findall(r"DNS:([^,\n]+)", text or ""):
        identities.add(("DNS", value.strip().lower()))
    subject_match = re.search(r"subject=.*?CN\s*=\s*([^,\n/]+)", text or "")
    if subject_match:
        cn = subject_match.group(1).strip()
        identities.add((cert_host_kind(cn), cn if cert_host_kind(cn) == "IP" else cn.lower()))
    return identities


def cert_has_required_hosts(cert_path, hosts):
    if not Path(cert_path).exists():
        return False
    result = subprocess.run([
        "openssl", "x509",
        "-in", str(cert_path),
        "-noout",
        "-subject",
        "-ext", "subjectAltName",
    ], capture_output=True, text=True)
    if result.returncode:
        return False
    identities = cert_identity_set_from_text(result.stdout)
    for host in hosts:
        kind = cert_host_kind(host)
        wanted = (kind, host if kind == "IP" else host.lower())
        if wanted not in identities:
            return False
    return True


def ensure_base_certs():
    ca_cert = CERT_DIR / "taklite-ca.crt"
    ca_key = CERT_DIR / "taklite-ca.key"
    server_csr = CERT_DIR / "taklite-server.csr"
    server_crt = CERT_DIR / "taklite-server.crt"
    server_ext = CERT_DIR / "taklite-server.ext"
    server_hosts = tls_server_hosts()
    server_name = server_hosts[0]

    CERT_DIR.mkdir(parents=True, exist_ok=True)
    if not ca_cert.exists() or not ca_key.exists():
        run_openssl(["genrsa", "-out", str(ca_key), "4096"])
        run_openssl([
            "req", "-x509", "-new", "-nodes",
            "-key", str(ca_key),
            "-sha256", "-days", "3650",
            "-out", str(ca_cert),
            "-subj", "/CN=TAKlite Local CA",
        ])
        ca_key.chmod(0o600)
        ca_cert.chmod(0o644)

    cert_needs_refresh = (
        not HTTPS_CERT.exists()
        or not HTTPS_KEY.exists()
        or not cert_has_required_hosts(HTTPS_CERT, server_hosts)
    )

    if cert_needs_refresh:
        if HTTPS_CERT.exists():
            HTTPS_CERT.replace(HTTPS_CERT.with_suffix(f"{HTTPS_CERT.suffix}.bak.{int(time.time())}"))
        if HTTPS_KEY.exists():
            HTTPS_KEY.replace(HTTPS_KEY.with_suffix(f"{HTTPS_KEY.suffix}.bak.{int(time.time())}"))
        run_openssl(["genrsa", "-out", str(HTTPS_KEY), "3072"])
        run_openssl([
            "req", "-new",
            "-key", str(HTTPS_KEY),
            "-out", str(server_csr),
            "-subj", f"/CN={server_name}",
        ])
        server_ext.write_text(
            "\n".join([
                "authorityKeyIdentifier=keyid,issuer",
                "basicConstraints=CA:FALSE",
                "keyUsage = digitalSignature, keyEncipherment",
                "extendedKeyUsage = serverAuth",
                f"subjectAltName = {subject_alt_name_for_hosts(server_hosts)}",
                "",
            ]),
            encoding="utf-8",
        )
        run_openssl([
            "x509", "-req",
            "-in", str(server_csr),
            "-CA", str(ca_cert),
            "-CAkey", str(ca_key),
            "-CAcreateserial",
            "-out", str(server_crt),
            "-days", "825",
            "-sha256",
            "-extfile", str(server_ext),
        ])
        HTTPS_CERT.write_bytes(server_crt.read_bytes() + ca_cert.read_bytes())
        HTTPS_KEY.chmod(0o600)
        HTTPS_CERT.chmod(0o644)

    ensure_truststore_file()
    packaged_truststore_file()


def ensure_truststore_file():
    ca_cert = CERT_DIR / "taklite-ca.crt"
    truststore = CERT_DIR / "taklite-truststore.p12"
    tmp_truststore = CERT_DIR / ".taklite-truststore.p12.tmp"
    if not ca_cert.exists():
        raise RuntimeError("TAKlite CA is missing; rerun the installer or restore taklite-ca.crt")
    keytool = shutil.which("keytool")
    if keytool:
        if tmp_truststore.exists():
            tmp_truststore.unlink()
        result = subprocess.run([
            keytool,
            "-importcert",
            "-noprompt",
            "-storetype", "PKCS12",
            "-alias", "taklite-ca",
            "-file", str(ca_cert),
            "-keystore", str(tmp_truststore),
            "-storepass", CERT_PASSWORD,
        ], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError((result.stderr or result.stdout or "keytool failed").strip())
        tmp_truststore.replace(truststore)
        truststore.chmod(0o644)
        return truststore
    try:
        run_openssl([
            "pkcs12", "-export",
            "-nokeys",
            "-in", str(ca_cert),
            "-out", str(tmp_truststore),
            "-name", "taklite-ca",
            "-caname", "taklite-ca",
            "-jdktrust", "anyExtendedKeyUsage",
            *P12_CERT_COMPAT_ARGS,
            "-passout", f"pass:{CERT_PASSWORD}",
        ])
    except RuntimeError:
        run_openssl([
            "pkcs12", "-export",
            "-nokeys",
            "-in", str(ca_cert),
            "-out", str(tmp_truststore),
            "-name", "taklite-ca",
            *P12_CERT_COMPAT_ARGS,
            "-passout", f"pass:{CERT_PASSWORD}",
        ])
    tmp_truststore.replace(truststore)
    truststore.chmod(0o644)
    return truststore


def packaged_truststore_file():
    truststore = ensure_truststore_file()
    truststore_name = f"{safe_profile_name(SERVER_HOST)}.p12"
    packaged = CERT_DIR / truststore_name
    if packaged != truststore:
        tmp_packaged = CERT_DIR / f".{truststore_name}.tmp"
        tmp_packaged.write_bytes(truststore.read_bytes())
        tmp_packaged.replace(packaged)
        packaged.chmod(0o644)
    return packaged


def build_server_pref(connect_string, truststore_name, client_cert_name, description="TAKlite"):
    return f"""<?xml version='1.0' encoding='ASCII' standalone='yes'?>
<preferences>
  <preference version="1" name="cot_streams">
    <entry key="count" class="class java.lang.Integer">1</entry>
    <entry key="description0" class="class java.lang.String">{html.escape(description)}</entry>
    <entry key="enabled0" class="class java.lang.Boolean">true</entry>
    <entry key="connectString0" class="class java.lang.String">{html.escape(connect_string)}</entry>
    <entry key="caLocation0" class="class java.lang.String">cert/{html.escape(truststore_name)}</entry>
    <entry key="caPassword0" class="class java.lang.String">{html.escape(CERT_PASSWORD)}</entry>
    <entry key="clientPassword0" class="class java.lang.String">{html.escape(CERT_PASSWORD)}</entry>
    <entry key="certificateLocation0" class="class java.lang.String">cert/{html.escape(client_cert_name)}</entry>
  </preference>
  <preference version="1" name="com.atakmap.app_preferences">
    <entry key="displayServerConnectionWidget" class="class java.lang.Boolean">true</entry>
    <entry key="apiSecureServerPort" class="class java.lang.String">{HTTPS_PUBLIC_PORT}</entry>
    <entry key="apiUnsecureServerPort" class="class java.lang.String">{HTTP_PUBLIC_PORT}</entry>
  </preference>
</preferences>
"""


def build_manifest(uid, display_name, truststore_name, client_cert_name):
    return f"""<MissionPackageManifest version="2">
  <Configuration>
    <Parameter name="uid" value="{html.escape(uid)}"/>
    <Parameter name="name" value="{html.escape(display_name)}"/>
    <Parameter name="onReceiveImport" value="true"/>
    <Parameter name="onReceiveDelete" value="false"/>
  </Configuration>
  <Contents>
    <Content ignore="false" zipEntry="certs/{html.escape(truststore_name)}"/>
    <Content ignore="false" zipEntry="certs/{html.escape(client_cert_name)}"/>
    <Content ignore="false" zipEntry="certs/server.pref"/>
    <Content ignore="false" zipEntry="certs/taklite-plugin.json"/>
  </Contents>
</MissionPackageManifest>
"""


def build_plugin_config(name, plugin_token=""):
    plugin_api_base_url = f"http://{SERVER_HOST}:{HTTP_PUBLIC_PORT}"
    return json.dumps({
        "schema": "taklite-plugin-profile-v1",
        "name": name,
        "server_url": plugin_api_base_url,
        "server_urls": [
            plugin_api_base_url,
            f"https://{SERVER_HOST}:{HTTPS_PUBLIC_PORT}",
        ],
        "connect_string": f"{SERVER_HOST}:{COT_TLS_PUBLIC_PORT}:ssl",
        "ports": {
            "http": HTTP_PUBLIC_PORT,
            "https": HTTPS_PUBLIC_PORT,
            "cot_tcp": COT_PUBLIC_PORT,
            "cot_tls": COT_TLS_PUBLIC_PORT,
        },
        "plugin_token": plugin_token or "",
        "default_audience_mode": "all_allowed",
        "api": {
            "me": "/api/plugin/me",
            "audience": "/api/plugin/audience",
            "preview": "/api/plugin/datapackages/preview",
            "upload": "/api/plugin/datapackages/upload",
            "send": "/api/plugin/datapackages/send",
        },
    }, indent=2) + "\n"


def build_portal_user_plugin_config(user):
    profile_name = row_get(user, "profile_name", "") or row_get(user, "username", "")
    return build_plugin_config(profile_name, row_get(user, "plugin_api_token", "") or "")


def create_cert_profile(name, description="", plugin_token=""):
    name = safe_profile_name(name)
    description = (description or "").strip()
    truststore = packaged_truststore_file()
    ca_cert = CERT_DIR / "taklite-ca.crt"
    ca_key = CERT_DIR / "taklite-ca.key"
    client_key = CERT_DIR / f"{name}.key"
    client_csr = CERT_DIR / f"{name}.csr"
    client_ext = CERT_DIR / f"{name}.ext"
    client_crt = CERT_DIR / f"{name}.crt"
    client_p12 = CERT_DIR / f"{name}.p12"
    dp_zip = CERT_DIR / f"{name}-{SERVER_HOST}.dp.zip"
    connect_string = f"{SERVER_HOST}:{COT_TLS_PUBLIC_PORT}:ssl"
    download_token = secrets.token_urlsafe(18)

    with db_connect() as conn:
        existing = conn.execute("select id from cert_profiles where name = ?", (name,)).fetchone()
        if existing:
            raise ValueError("a connection package with that name already exists")

    run_openssl(["genrsa", "-out", str(client_key), "3072"])
    run_openssl(["req", "-new", "-key", str(client_key), "-out", str(client_csr), "-subj", f"/CN={name}"])
    client_ext.write_text("basicConstraints=CA:FALSE\nkeyUsage = digitalSignature, keyEncipherment\nextendedKeyUsage = clientAuth\n", encoding="utf-8")
    run_openssl([
        "x509", "-req",
        "-in", str(client_csr),
        "-CA", str(ca_cert),
        "-CAkey", str(ca_key),
        "-CAcreateserial",
        "-out", str(client_crt),
        "-days", "825",
        "-sha256",
        "-extfile", str(client_ext),
    ])
    run_openssl([
        "pkcs12", "-export",
        "-inkey", str(client_key),
        "-in", str(client_crt),
        "-certfile", str(ca_cert),
        "-out", str(client_p12),
        "-name", name,
        *P12_KEY_COMPAT_ARGS,
        "-passout", f"pass:{CERT_PASSWORD}",
    ])
    client_key.chmod(0o600)
    client_p12.chmod(0o644)

    display_name = f"TAKlite {name}"
    manifest = build_manifest(f"taklite-{name}", display_name, truststore.name, client_p12.name)
    server_pref = build_server_pref(connect_string, truststore.name, client_p12.name, display_name)
    with zipfile.ZipFile(dp_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("MANIFEST/manifest.xml", manifest)
        zf.write(truststore, f"certs/{truststore.name}")
        zf.write(client_p12, f"certs/{client_p12.name}")
        zf.writestr("certs/server.pref", server_pref)
        zf.writestr("certs/taklite-plugin.json", build_plugin_config(name, plugin_token))
    dp_zip.chmod(0o644)

    with db_connect() as conn:
        conn.execute("""
            insert into cert_profiles
              (name, description, download_token, connect_string, truststore_file, client_cert_file, datapackage_file, created_at, revoked_at)
            values (?, ?, ?, ?, ?, ?, ?, ?, null)
        """, (name, description, download_token, connect_string, str(truststore), str(client_p12), str(dp_zip), utc_now()))
        conn.commit()
        row = conn.execute("select * from cert_profiles where name = ?", (name,)).fetchone()
    return cert_profile_row(row)


def revoke_cert_profile(profile_id):
    with db_connect() as conn:
        row = conn.execute("select * from cert_profiles where id = ?", (profile_id,)).fetchone()
        if not row:
            raise ValueError("connection package not found")
        conn.execute("update cert_profiles set revoked_at = coalesce(revoked_at, ?) where id = ?", (utc_now(), profile_id))
        conn.commit()
        row = conn.execute("select * from cert_profiles where id = ?", (profile_id,)).fetchone()
    disconnected = RELAY.disconnect_cert_cn(row["name"]) if row and row["name"] else 0
    if disconnected:
        print(f"TAKlite disconnected {disconnected} active client(s) for revoked cert_cn={row['name']}", flush=True)
    return cert_profile_row(row)


def delete_cert_profile(profile_id, delete_files=True):
    row = find_cert_profile(profile_id)
    if not row:
        raise ValueError("connection package not found")
    deleted = []
    with db_connect() as conn:
        conn.execute("delete from cert_profiles where id = ?", (profile_id,))
        conn.commit()
    if delete_files:
        cert_root = CERT_DIR.resolve()
        for key in ("client_cert_file", "datapackage_file"):
            path = Path(row[key])
            if path.exists() and path.resolve().is_relative_to(cert_root):
                path.unlink()
                deleted.append(str(path))
    return {"deleted": True, "deleted_files": deleted}


def server_tls_context(request_client_cert=False):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.maximum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(str(HTTPS_CERT), str(HTTPS_KEY))
    if request_client_cert and CLIENT_CA.exists():
        context.load_verify_locations(cafile=str(CLIENT_CA))
        context.verify_mode = ssl.CERT_REQUIRED if COT_TLS_REQUIRE_CLIENT_CERT else ssl.CERT_OPTIONAL
    return context


class CotRelay:
    def __init__(self):
        self.lock = threading.Lock()
        self.clients = {}
        self.last_events = {}

    def add(self, handler):
        remote = handler.remote
        host, port = handler.client_address
        now = utc_now()
        peer_cert = {}
        peer_cert_cn = ""
        if hasattr(handler.request, "getpeercert"):
            try:
                peer_cert = handler.request.getpeercert() or {}
                peer_cert_cn = cert_common_name(peer_cert)
            except OSError:
                peer_cert = {}
        with self.lock:
            self.clients[handler] = {
                "remote": remote,
                "ip": host,
                "port": port,
                "transport": getattr(handler.server, "transport", "tcp"),
                "peer_cert_cn": peer_cert_cn,
                "peer_cert_present": bool(peer_cert),
                "user_id": getattr(handler, "user_id", None),
                "username": "",
                "uid": "",
                "callsign": "",
                "connected_at": now,
                "last_seen": now,
            }
            identity = client_identity_for_cert(peer_cert_cn)
            if identity:
                self.clients[handler]["username"] = identity["username"]
        self.send_recent(handler)
        self.send_to(handler, server_status_event())
        self.deliver_pending(handler)

    def remove(self, handler):
        with self.lock:
            self.clients.pop(handler, None)

    def disconnect_cert_cn(self, cert_cn):
        cert_cn = (cert_cn or "").strip()
        if not cert_cn:
            return 0
        with self.lock:
            handlers = [
                handler
                for handler, info in self.clients.items()
                if (info.get("peer_cert_cn") or "") == cert_cn
            ]
        for handler in handlers:
            try:
                handler.request.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                handler.request.close()
            except OSError:
                pass
        return len(handlers)

    def update_client(self, remote, uid, callsign, user_id=None):
        learned_user_id = user_id
        with self.lock:
            for info in self.clients.values():
                if info["remote"] == remote:
                    learned_user_id = learned_user_id or info.get("user_id")
                    if uid:
                        info["uid"] = uid
                    if callsign:
                        info["callsign"] = callsign
                    info["last_seen"] = utc_now()
        if learned_user_id and uid:
            try:
                learn_portal_user_device(learned_user_id, device_id=uid)
            except ValueError:
                pass

    def snapshot(self):
        with self.lock:
            return list(self.clients.values())

    def remember_event(self, uid, event, user_id=None):
        with self.lock:
            self.last_events[uid] = (time.time(), event, user_id)
            cutoff = time.time() - 300
            for old_uid, (seen, _, _) in list(self.last_events.items()):
                if seen < cutoff:
                    self.last_events.pop(old_uid, None)

    def send_to(self, handler, event):
        try:
            with handler.send_lock:
                previous_timeout = None
                try:
                    previous_timeout = handler.request.gettimeout()
                    handler.request.settimeout(SOCKET_SEND_TIMEOUT_SECONDS)
                    handler.request.sendall(event)
                finally:
                    try:
                        handler.request.settimeout(previous_timeout)
                    except OSError:
                        pass
            return True
        except OSError:
            self.remove(handler)
            return False

    def send_recent(self, handler):
        with self.lock:
            events = [(event, user_id) for _, event, user_id in self.last_events.values()]
        for event, sender_user_id in events:
            if cot_delivery_allowed(sender_user_id, getattr(handler, "user_id", None)):
                self.send_to(handler, event)

    def broadcast(self, sender, event):
        with self.lock:
            handlers = [(handler, dict(info)) for handler, info in self.clients.items()]
        sender_user_id = getattr(sender, "user_id", None) if sender is not None else None
        for handler, info in handlers:
            if sender is not None and handler is sender:
                continue
            if sender is not None and not cot_delivery_allowed(sender_user_id, info.get("user_id")):
                continue
            self.send_to(handler, event)

    def send_to_client_uids(self, event, client_uids=None, send_all=False):
        requested = set(client_uids or [])
        with self.lock:
            handlers = [(handler, dict(info)) for handler, info in self.clients.items()]
        results = []
        matched = set()
        for handler, info in handlers:
            uid = info.get("uid") or ""
            if not send_all and uid not in requested:
                continue
            if uid:
                matched.add(uid)
            sent = self.send_to(handler, event)
            results.append({
                "uid": uid,
                "callsign": info.get("callsign") or "Unknown",
                "ip": info.get("ip") or "",
                "sent": sent,
            })
        missed = sorted(requested - matched)
        return {"sent": sum(1 for item in results if item["sent"]), "results": results, "missed": missed}

    def send_to_user_ids(self, event, user_ids):
        requested = {int(user_id) for user_id in (user_ids or []) if str(user_id).strip()}
        with self.lock:
            handlers = [(handler, dict(info)) for handler, info in self.clients.items()]
        results = []
        matched = set()
        for handler, info in handlers:
            user_id = info.get("user_id")
            if user_id is None or int(user_id) not in requested:
                continue
            matched.add(int(user_id))
            sent = self.send_to(handler, event)
            results.append({
                "user_id": int(user_id),
                "username": info.get("username") or "",
                "uid": info.get("uid") or "",
                "callsign": info.get("callsign") or "Unknown",
                "ip": info.get("ip") or "",
                "sent": sent,
                "reason_code": "sent" if sent else "send_failed_socket",
                "reason": "File-share event sent to connected client." if sent else "Socket closed while sending file-share event.",
            })
        missed = sorted(requested - matched)
        return {"sent": sum(1 for item in results if item["sent"]), "results": results, "missed_user_ids": missed}

    def deliver_pending(self, handler):
        user_id = getattr(handler, "user_id", None)
        if not user_id:
            return
        deliveries = list_pending_datapackage_deliveries(user_id)
        for delivery in deliveries:
            row = find_package(delivery["package_hash"])
            if not row:
                update_datapackage_delivery(delivery["id"], "failed", "package_missing", "Package is no longer available on the server.")
                continue
            package = row_to_package(row)
            access = package_access_for_user(package, user_id, ACCESS_CONTROL_ENFORCE)
            if not access["allowed"]:
                update_datapackage_delivery(delivery["id"], "blocked", access["reason_code"], access["reason"])
                continue
            sent = self.send_to(handler, fileshare_event(package))
            update_datapackage_delivery(
                delivery["id"],
                "sent" if sent else "pending",
                "sent_on_reconnect" if sent else "send_failed_socket",
                "Pending package pushed after client reconnect." if sent else "Client socket closed while retrying pending package.",
            )

    def heartbeat(self):
        self.broadcast(None, server_status_event())


RELAY = CotRelay()


class CotHandler(BaseRequestHandler):
    def setup(self):
        self.remote = f"{self.client_address[0]}:{self.client_address[1]}"
        self.bytes_in = 0
        self.events_in = 0
        self.send_lock = threading.Lock()
        self.user_id = None
        self.cert_cn = ""
        transport = getattr(self.server, "transport", "tcp")
        peer_cert_cn = ""
        if hasattr(self.request, "getpeercert"):
            try:
                peer_cert_cn = cert_common_name(self.request.getpeercert() or {})
            except OSError:
                peer_cert_cn = ""
        if transport == "tls" and not client_cert_authorized(peer_cert_cn):
            print(f"CoT reject {self.remote} transport={transport} cert_cn={peer_cert_cn or 'none'} reason=unauthorized_cert")
            try:
                self.request.close()
            except OSError:
                pass
            return
        identity = client_identity_for_cert(peer_cert_cn)
        self.user_id = identity["user_id"] if identity else None
        self.cert_cn = peer_cert_cn
        if self.user_id:
            try:
                learn_portal_user_device(self.user_id, source_ip=self.client_address[0])
            except ValueError:
                pass
        if ACCESS_CONTROL_ENFORCE and not self.user_id:
            print(f"CoT reject {self.remote} transport={transport} cert_cn={peer_cert_cn or 'none'} reason=missing_policy_identity")
            try:
                self.request.close()
            except OSError:
                pass
            return
        RELAY.add(self)
        cert_note = f" cert_cn={peer_cert_cn}" if peer_cert_cn else " cert_cn=none"
        print(f"CoT connect {self.remote} transport={transport}{cert_note}")

    def handle(self):
        buf = b""
        while True:
            try:
                chunk = self.request.recv(65536)
            except OSError as exc:
                print(f"CoT recv error {self.remote}: {exc}")
                break
            if not chunk:
                break
            self.bytes_in += len(chunk)
            buf += chunk
            if len(buf) > COT_MAX_BUFFER_BYTES:
                print(f"CoT closing {self.remote}: buffered data exceeded {COT_MAX_BUFFER_BYTES} bytes without complete event")
                break
            while EVENT_END in buf:
                end = buf.find(EVENT_END) + len(EVENT_END)
                candidate, buf = buf[:end], buf[end:]
                match = EVENT_RE.search(candidate)
                event = match.group(0) if match else candidate
                self.events_in += 1
                if is_pli_event(event) and not user_pli_enabled(self.user_id):
                    print(f"CoT drop {self.remote} reason=pli_paused")
                    continue
                save_event(event, self.remote, self.user_id)
                RELAY.broadcast(self, event)

    def finish(self):
        RELAY.remove(self)
        print(f"CoT disconnect {self.remote} events={self.events_in} bytes={self.bytes_in}")


class CotServer(ThreadingMixIn, TCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address, handler_class, transport="tcp"):
        self.transport = transport
        super().__init__(server_address, handler_class)


def absolute_base_url(handler):
    host = PUBLIC_HOST or handler.headers.get("Host", f"127.0.0.1:{HTTP_PORT}").split(":")[0]
    if ":" in host:
        return f"http://{host}"
    return f"http://{host}:{HTTP_PORT}"


def dir_size(path):
    total = 0
    if not path.exists():
        return 0
    for item in path.rglob("*"):
        try:
            if item.is_file():
                total += item.stat().st_size
        except FileNotFoundError:
            continue
    return total


def file_size(path):
    try:
        return path.stat().st_size
    except FileNotFoundError:
        return 0


def read_json_file(path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def request_dir_status(path_value):
    request_dir = Path(path_value) if path_value else None
    if not request_dir or not request_dir.is_dir():
        return {
            "enabled": False,
            "request_dir": path_value,
            "pending": False,
            "processing": False,
            "last_status": None,
        }
    return {
        "enabled": True,
        "request_dir": path_value,
        "pending": (request_dir / "request.json").exists(),
        "processing": (request_dir / "processing.json").exists(),
        "last_status": read_json_file(request_dir / "status.json"),
    }


def validate_host(value, label):
    value = (value or "").strip()
    if not value:
        raise ValueError(f"{label} is required")
    if len(value) > 253 or any(ch.isspace() for ch in value):
        raise ValueError(f"{label} is not valid")
    if not re.fullmatch(r"[A-Za-z0-9._:-]+", value):
        raise ValueError(f"{label} contains unsupported characters")
    return value


def validate_url(value, label):
    value = (value or "").strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"{label} must be an http or https URL")
    if len(value) > 500:
        raise ValueError(f"{label} is too long")
    return value


def validate_port(value, label):
    try:
        port = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a port number")
    if port < 1 or port > 65535:
        raise ValueError(f"{label} must be between 1 and 65535")
    return port


def validate_max_upload(value):
    try:
        size = int(value)
    except (TypeError, ValueError):
        raise ValueError("max upload size must be a number of bytes")
    if size < 1024 * 1024 or size > 2 * 1024 * 1024 * 1024:
        raise ValueError("max upload size must be between 1 MB and 2 GB")
    return size


def validate_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value or "").strip().lower()
    if text in ("1", "true", "yes", "on"):
        return True
    if text in ("0", "false", "no", "off", ""):
        return False
    raise ValueError("boolean setting must be true or false")


def editable_settings_status():
    runner = request_dir_status(SETTINGS_REQUEST_DIR)
    values = {
        "public_host": PUBLIC_HOST or SERVER_HOST,
        "server_host": SERVER_HOST,
        "wg_dashboard_url": WG_DASHBOARD_URL,
        "max_upload_bytes": MAX_UPLOAD_BYTES,
        "cot_host_port": COT_PUBLIC_PORT,
        "cot_tls_host_port": COT_TLS_PUBLIC_PORT,
        "http_host_port": HTTP_PUBLIC_PORT,
        "https_host_port": HTTPS_PUBLIC_PORT,
        "access_control_enforce": ACCESS_CONTROL_ENFORCE,
        "cot_tls_require_client_cert": COT_TLS_REQUIRE_CLIENT_CERT,
        "allow_legacy_client_cert": ALLOW_LEGACY_CLIENT_CERT,
    }
    return {
        "values": values,
        "runner": runner,
        "restart_required_fields": [
            "public_host",
            "server_host",
            "wg_dashboard_url",
            "max_upload_bytes",
            "cot_host_port",
            "cot_tls_host_port",
            "http_host_port",
            "https_host_port",
            "access_control_enforce",
            "cot_tls_require_client_cert",
            "allow_legacy_client_cert",
        ],
        "port_warning": "Changing service ports restarts TAKlite and must match WireGuard/firewall exposure.",
    }


def queue_settings_update(payload):
    runner = request_dir_status(SETTINGS_REQUEST_DIR)
    if not runner["enabled"]:
        return {"ok": False, "error": "settings runner is not enabled"}
    if runner["pending"] or runner["processing"]:
        return {"ok": False, "error": "a settings update is already pending or running"}
    values = payload.get("values") if isinstance(payload, dict) else {}
    if not isinstance(values, dict):
        raise ValueError("settings values are required")
    sanitized = {
        "TAKLITE_PUBLIC_HOST": validate_host(values.get("public_host"), "public host"),
        "TAKLITE_SERVER_HOST": validate_host(values.get("server_host"), "server host"),
        "TAKLITE_WGDASHBOARD_URL": validate_url(values.get("wg_dashboard_url"), "WireGuard dashboard URL"),
        "TAKLITE_MAX_UPLOAD_BYTES": str(validate_max_upload(values.get("max_upload_bytes"))),
        "TAKLITE_COT_HOST_PORT": str(validate_port(values.get("cot_host_port"), "plain CoT port")),
        "TAKLITE_COT_TLS_HOST_PORT": str(validate_port(values.get("cot_tls_host_port"), "TLS CoT port")),
        "TAKLITE_HTTP_HOST_PORT": str(validate_port(values.get("http_host_port"), "admin HTTP port")),
        "TAKLITE_HTTPS_HOST_PORT": str(validate_port(values.get("https_host_port"), "HTTPS/Marti port")),
        "TAKLITE_ACCESS_CONTROL_ENFORCE": "true" if validate_bool(values.get("access_control_enforce")) else "false",
        "TAKLITE_COT_TLS_REQUIRE_CLIENT_CERT": "true" if validate_bool(values.get("cot_tls_require_client_cert")) else "false",
        "TAKLITE_ALLOW_LEGACY_CLIENT_CERT": "true" if validate_bool(values.get("allow_legacy_client_cert")) else "false",
    }
    request_dir = Path(SETTINGS_REQUEST_DIR)
    request = {
        "id": secrets.token_urlsafe(12),
        "requested_at": utc_now(),
        "env": sanitized,
    }
    tmp_file = request_dir / f".request-{request['id']}.tmp"
    tmp_file.write_text(json.dumps(request, indent=2))
    tmp_file.replace(request_dir / "request.json")
    return {"ok": True, "queued": True, "request": {"id": request["id"], "requested_at": request["requested_at"]}}


def firewall_status():
    runner = request_dir_status(FIREWALL_REQUEST_DIR)
    last_status = runner.get("last_status") or {}
    service_states = last_status.get("service_states") if isinstance(last_status, dict) else {}
    if not isinstance(service_states, dict):
        service_states = {}
    defaults = {
        "ssh": "vpn",
        "wireguard": "public",
        "wg_dashboard": "vpn",
        "taklite_admin": "vpn",
        "tak_https": "vpn",
        "cot_tcp": "vpn",
        "cot_tls": "vpn",
    }
    services = []
    for key, config in FIREWALL_SERVICES.items():
        state = service_states.get(key) or defaults.get(key, "vpn")
        if state not in FIREWALL_STATES:
            state = defaults.get(key, "vpn")
        services.append({
            "key": key,
            "label": config["label"],
            "protocol": config["protocol"],
            "port": config["port"],
            "state": state,
            "recommended_state": defaults.get(key, "vpn"),
            "lockout_sensitive": bool(config.get("lockout_sensitive")),
        })
    return {
        "runner": runner,
        "services": services,
        "interfaces": {
            "wireguard": WG_INTERFACE,
            "public": PUBLIC_INTERFACE,
        },
        "states": ["public", "vpn", "closed"],
        "warnings": [
            "WireGuard UDP should remain public or remote VPN access will fail.",
            "Closing public SSH can lock you out unless SSH over WireGuard is confirmed.",
            "Firewall changes are separate from TAKlite port settings.",
        ],
    }


def queue_firewall_update(payload):
    runner = request_dir_status(FIREWALL_REQUEST_DIR)
    if not runner["enabled"]:
        return {"ok": False, "error": "firewall runner is not enabled"}
    if runner["pending"] or runner["processing"]:
        return {"ok": False, "error": "a firewall update is already pending or running"}
    services = payload.get("services") if isinstance(payload, dict) else None
    if not isinstance(services, dict):
        raise ValueError("firewall services are required")
    sanitized = {}
    for key, state in services.items():
        if key not in FIREWALL_SERVICES:
            raise ValueError(f"unknown firewall service: {key}")
        state = (state or "").strip().lower()
        if state not in FIREWALL_STATES:
            raise ValueError(f"invalid firewall state for {key}")
        sanitized[key] = state
    if sanitized.get("wireguard") == "closed":
        raise ValueError("WireGuard cannot be closed from the GUI")
    if sanitized.get("ssh") == "closed" and payload.get("confirm_ssh_close") != "SSH_OVER_WG_CONFIRMED":
        raise ValueError("confirm SSH over WireGuard before closing SSH")
    for key in FIREWALL_SERVICES:
        sanitized.setdefault(key, next((item["state"] for item in firewall_status()["services"] if item["key"] == key), "vpn"))
    request_dir = Path(FIREWALL_REQUEST_DIR)
    request = {
        "id": secrets.token_urlsafe(12),
        "requested_at": utc_now(),
        "services": sanitized,
        "interfaces": {"wireguard": WG_INTERFACE, "public": PUBLIC_INTERFACE},
    }
    tmp_file = request_dir / f".request-{request['id']}.tmp"
    tmp_file.write_text(json.dumps(request, indent=2))
    tmp_file.replace(request_dir / "request.json")
    return {"ok": True, "queued": True, "request": {"id": request["id"], "requested_at": request["requested_at"]}}


def runtime_health():
    db_ok = False
    db_error = ""
    counts = {}
    try:
        with db_connect() as conn:
            for table in ("admins", "portal_users", "cert_profiles", "datapackages", "events", "access_roles", "access_groups"):
                counts[table] = int(conn.execute(f"select count(*) from {table}").fetchone()[0])
            conn.execute("select 1").fetchone()
        db_ok = True
    except Exception as exc:
        db_error = str(exc)
    db_size = file_size(DB_PATH)
    wal_path = DB_PATH.with_name(DB_PATH.name + "-wal")
    return {
        "version": VERSION,
        "database": {
            "ok": db_ok,
            "path": str(DB_PATH),
            "bytes": db_size,
            "wal_bytes": file_size(wal_path),
            "counts": counts,
            "error": db_error,
        },
        "storage": {
            "package_dir": str(PACKAGE_DIR),
            "package_bytes": dir_size(PACKAGE_DIR),
            "cert_dir": str(CERT_DIR),
            "cert_bytes": dir_size(CERT_DIR),
        },
        "connections": {
            "clients": len(RELAY.snapshot()),
            "cot_port": COT_PORT,
            "cot_tls_port": COT_TLS_PORT,
            "http_port": HTTP_PORT,
            "https_port": HTTPS_PORT,
        },
        "runtime": {
            "started_at": STARTED_AT,
            "uptime_seconds": int(time.time() - parse_utc(STARTED_AT).timestamp()) if parse_utc(STARTED_AT) else 0,
            "hostname": socket.gethostname(),
            "container_status": "running",
        },
        "config": {
            "server_host": SERVER_HOST,
            "public_host": PUBLIC_HOST or SERVER_HOST,
            "http_bind": HTTP_BIND,
            "https_bind": HTTPS_BIND,
            "cot_bind": COT_BIND,
            "cot_tls_bind": COT_TLS_BIND,
            "max_upload_bytes": MAX_UPLOAD_BYTES,
        },
        "security": {
            "access_enforcement": ACCESS_CONTROL_ENFORCE,
            "cot_tls_require_client_cert": COT_TLS_REQUIRE_CLIENT_CERT,
            "allow_legacy_client_cert": ALLOW_LEGACY_CLIENT_CERT,
            "admin_auth_enabled": bool(ADMIN_TOKEN),
        },
        "wireguard": {
            "dashboard_url": WG_DASHBOARD_URL,
            "visible_from_container": False,
        },
        "updates": {
            **gui_update_status(),
            "release_url": RELEASES_URL,
            "repo_url": "https://github.com/C-OneThirty7/TAKlite.git",
            "preserves": [".env", "taklite/data", "taklite/certs", "taklite/packages", "/etc/wireguard", "/root/taklite-admin", "WGDashboard config"],
        },
    }


def gui_update_status():
    request_dir = Path(GUI_UPDATE_REQUEST_DIR) if GUI_UPDATE_REQUEST_DIR else None
    request_runner = bool(request_dir and request_dir.is_dir())
    command_runner = bool(GUI_UPDATE_COMMAND.strip())
    last_status = read_json_file(request_dir / "status.json") if request_dir else None
    pending = bool(request_dir and (request_dir / "request.json").exists())
    processing = bool(request_dir and (request_dir / "processing.json").exists())
    return {
        "gui_runner_enabled": GUI_UPDATE_ENABLED and (request_runner or command_runner),
        "enabled": GUI_UPDATE_ENABLED and (request_runner or command_runner),
        "configured": request_runner or command_runner,
        "runner_mode": "request" if request_runner else "command" if command_runner else "disabled",
        "workdir": GUI_UPDATE_WORKDIR,
        "request_dir": GUI_UPDATE_REQUEST_DIR,
        "timeout_seconds": GUI_UPDATE_TIMEOUT_SECONDS,
        "pending": pending,
        "processing": processing,
        "last_status": last_status,
    }


def latest_release_status(refresh=False):
    now = time.time()
    if not refresh and UPDATE_STATUS_CACHE["status"] and now - UPDATE_STATUS_CACHE["checked_at"] < UPDATE_STATUS_CACHE_SECONDS:
        return UPDATE_STATUS_CACHE["status"]
    current_parts = version_tuple(VERSION)
    current_tag = version_tag(VERSION)
    status = {
        "current_version": VERSION,
        "current_tag": current_tag,
        "latest_tag": "",
        "latest_version": "",
        "update_available": False,
        "release_url": RELEASES_URL,
        "verified_asset": None,
        "verified_update_available": False,
        "checked_at": utc_now(),
        "check_error": "",
        **gui_update_status(),
    }
    try:
        req = Request(LATEST_RELEASE_API_URL, headers={"Accept": "application/vnd.github+json", "User-Agent": "TAKlite"})
        with urlopen(req, timeout=4) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        latest_tag = payload.get("tag_name", "")
        latest_parts = version_tuple(latest_tag)
        verified_asset = verified_release_asset(payload)
        status.update({
            "latest_tag": latest_tag,
            "latest_version": latest_tag.lstrip("v"),
            "release_url": payload.get("html_url") or RELEASES_URL,
            "update_available": bool(latest_parts and current_parts and latest_parts > current_parts),
            "verified_asset": verified_asset,
            "verified_update_available": bool(verified_asset and latest_parts and current_parts and latest_parts > current_parts),
        })
    except Exception as exc:
        status["check_error"] = str(exc)
    UPDATE_STATUS_CACHE["checked_at"] = now
    UPDATE_STATUS_CACHE["status"] = status
    return status


def verified_release_asset(payload):
    tag = payload.get("tag_name", "")
    expected_names = {f"TAKlite-{tag}.zip"} if tag else set()
    if tag.startswith("v"):
        expected_names.add(f"TAKlite-{tag[1:]}.zip")
    for asset in payload.get("assets") or []:
        name = asset.get("name", "")
        if expected_names and name not in expected_names:
            continue
        digest = asset.get("digest", "")
        match = re.fullmatch(r"sha256:([A-Fa-f0-9]{64})", digest or "")
        url = asset.get("browser_download_url", "")
        if match and url.startswith("https://github.com/"):
            return {"name": name, "url": url, "sha256": match.group(1).lower(), "digest": digest}
    return None


def validate_release_zip_url(url):
    url = (url or "").strip()
    if not re.fullmatch(r"https://github\.com/C-OneThirty7/TAKlite/releases/download/v[0-9]+\.[0-9]+\.[0-9]+/[A-Za-z0-9_.-]+\.zip", url):
        raise ValueError("verified release zip URL is required")
    return url


def validate_sha256(value):
    value = (value or "").strip().lower()
    if not re.fullmatch(r"[a-f0-9]{64}", value):
        raise ValueError("verified release zip SHA-256 is required")
    return value


def run_gui_update(confirm, target_tag="", release_zip_url="", expected_sha256=""):
    if not GUI_UPDATE_ENABLED:
        return {"ok": False, "error": "GUI update runner is disabled"}
    if confirm != "RUN_UPDATE":
        return {"ok": False, "error": "update confirmation is required"}
    request_dir = Path(GUI_UPDATE_REQUEST_DIR) if GUI_UPDATE_REQUEST_DIR else None
    if request_dir and request_dir.is_dir():
        request_file = request_dir / "request.json"
        processing_file = request_dir / "processing.json"
        if request_file.exists() or processing_file.exists():
            return {"ok": False, "error": "an update is already pending or running"}
        try:
            release_zip_url = validate_release_zip_url(release_zip_url)
            expected_sha256 = validate_sha256(expected_sha256)
        except ValueError as exc:
            return {"ok": False, "error": f"{exc}; GUI host updates require a verified release zip"}
        request = {
            "id": secrets.token_urlsafe(12),
            "requested_at": utc_now(),
            "current_version": VERSION,
            "target_tag": target_tag,
            "release_zip_url": release_zip_url,
            "expected_sha256": expected_sha256,
        }
        tmp_file = request_dir / f".request-{request['id']}.tmp"
        tmp_file.write_text(json.dumps(request, indent=2))
        tmp_file.replace(request_file)
        return {"ok": True, "queued": True, "request": request}
    if not GUI_UPDATE_COMMAND.strip():
        return {"ok": False, "error": "GUI update command is not configured"}
    workdir = Path(GUI_UPDATE_WORKDIR) if GUI_UPDATE_WORKDIR else None
    if workdir and not workdir.is_dir():
        return {"ok": False, "error": f"GUI update workdir does not exist: {workdir}"}
    started = utc_now()
    try:
        result = subprocess.run(
            shlex.split(GUI_UPDATE_COMMAND),
            cwd=str(workdir) if workdir else None,
            capture_output=True,
            text=True,
            timeout=GUI_UPDATE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "error": f"GUI update timed out after {GUI_UPDATE_TIMEOUT_SECONDS} seconds",
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "started_at": started,
            "finished_at": utc_now(),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "started_at": started, "finished_at": utc_now()}
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout[-12000:],
        "stderr": result.stderr[-12000:],
        "started_at": started,
        "finished_at": utc_now(),
    }


def heartbeat_loop():
    while True:
        time.sleep(10)
        RELAY.heartbeat()


def parse_upload(handler):
    ctype = handler.headers.get("Content-Type", "")
    length = int(handler.headers.get("Content-Length", "0") or "0")
    if length <= 0:
        raise ValueError("empty upload")
    if length > MAX_UPLOAD_BYTES:
        raise ValueError(f"upload exceeds maximum size of {MAX_UPLOAD_BYTES} bytes")
    body = handler.rfile.read(length)
    if ctype.lower().startswith("multipart/form-data"):
        filename, data = parse_multipart_assetfile(ctype, body)
    else:
        filename, data = None, body
    validate_datapackage_upload(filename, data)
    return filename, data


def parse_multipart_assetfile(ctype, body):
    match = re.search(r'boundary="?([^";]+)"?', ctype, re.IGNORECASE)
    if not match:
        raise ValueError("multipart boundary missing")
    boundary = ("--" + match.group(1)).encode("utf-8")
    fallback_file = None
    for part in body.split(boundary):
        part = part.strip(b"\r\n")
        if not part or part == b"--" or b"\r\n\r\n" not in part:
            continue
        raw_headers, content = part.split(b"\r\n\r\n", 1)
        headers = raw_headers.decode("utf-8", "replace")
        name_match = re.search(r'name="([^"]+)"', headers, re.IGNORECASE)
        filename_match = re.search(r'filename="([^"]*)"', headers)
        filename = filename_match.group(1) if filename_match else None
        if content.endswith(b"\r\n"):
            content = content[:-2]
        field_name = name_match.group(1).lower() if name_match else ""
        if field_name in ("assetfile", "file", "upload", "data", "content", "contents"):
            return filename, content
        if filename and fallback_file is None:
            fallback_file = (filename, content)
    if fallback_file is not None:
        return fallback_file
    raise ValueError("missing multipart field assetfile")


def validate_datapackage_upload(filename, data):
    if not data:
        raise ValueError("empty upload")
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError(f"datapackage exceeds maximum size of {MAX_UPLOAD_BYTES} bytes")
    if data[:4] != b"PK\x03\x04" and data[:4] != b"PK\x05\x06" and data[:4] != b"PK\x07\x08":
        raise ValueError("datapackage must be a zip file")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            entries = zf.infolist()
            if len(entries) > MAX_ZIP_ENTRIES:
                raise ValueError(f"datapackage zip contains too many entries: {len(entries)}")
            total_uncompressed = 0
            total_compressed = 0
            for entry in entries:
                entry_path = PurePosixPath(entry.filename.replace("\\", "/"))
                if entry_path.is_absolute() or ".." in entry_path.parts:
                    raise ValueError(f"datapackage zip contains unsafe entry path: {entry.filename}")
                if entry.flag_bits & 0x1:
                    raise ValueError(f"datapackage zip contains encrypted entry: {entry.filename}")
                total_uncompressed += entry.file_size
                total_compressed += entry.compress_size
            if total_uncompressed > MAX_ZIP_UNCOMPRESSED_BYTES:
                raise ValueError(f"datapackage zip uncompressed size exceeds maximum of {MAX_ZIP_UNCOMPRESSED_BYTES} bytes")
            if total_uncompressed > 0:
                effective_compressed = max(total_compressed, 1)
                if total_uncompressed / effective_compressed > MAX_ZIP_COMPRESSION_RATIO:
                    raise ValueError("datapackage zip compression ratio is too high")
            bad = zf.testzip()
            if bad:
                raise ValueError(f"datapackage zip contains corrupt entry: {bad}")
    except zipfile.BadZipFile as exc:
        raise ValueError("datapackage must be a valid zip file") from exc


def upload_datapackage_from_request(handler, qs, response_url="content"):
    creator_user_id = handler.authenticated_user_id()
    if ACCESS_CONTROL_ENFORCE and not creator_user_id:
        record_audit_event(
            "tak_datapackage_upload",
            actor_type="tak_client",
            remote=handler.client_address[0],
            outcome="blocked",
            reason_code="blocked_no_identity",
            details={"path": handler.path},
        )
        handler.send_json({"error": "client certificate identity required"}, HTTPStatus.FORBIDDEN)
        return
    filename, data = parse_upload(handler)
    hash_value = qs.get("hash", [""])[0]
    query_name = qs.get("filename", qs.get("name", [""]))[0]
    creator_uid = qs.get("creatorUid", qs.get("creatoruid", [""]))[0]
    package_name = normalize_datapackage_name(query_name or filename or f"{hash_value}.dp.zip")
    policy = parse_datapackage_filename_policy(package_name)
    if policy["allowed_levels"] and creator_user_id:
        creator = subject_policy(creator_user_id)
        creator_level = creator.get("access_level") if creator else None
        if creator_level is not None and max(policy["allowed_levels"]) > int(creator_level):
            record_audit_event(
                "tak_datapackage_upload",
                actor_type="portal_user",
                actor_id=creator_user_id,
                remote=handler.client_address[0],
                outcome="blocked",
                reason_code="blocked_level_tag",
                details={"filename": package_name, "policy": policy, "creator_level": creator_level},
            )
            handler.send_json({"error": "datapackage level tag exceeds sender access level"}, HTTPStatus.FORBIDDEN)
            return
    content_url = upsert_package(
        hash_value,
        package_name,
        creator_uid,
        data,
        tak_marti_base_url(),
        creator_user_id=creator_user_id,
        visibility="private",
        policy=policy,
    )
    hash_value = hash_value or hashlib.sha256(data).hexdigest()
    record_audit_event(
        "tak_datapackage_upload",
        actor_type="portal_user" if creator_user_id else "tak_client",
        actor_id=creator_user_id,
        actor_name=creator_uid,
        remote=handler.client_address[0],
        outcome="ok",
        reason_code="uploaded",
        details={"hash": hash_value, "name": package_name, "policy": policy},
    )
    if response_url == "metadata":
        handler.send_text(tak_marti_metadata_tool_url(hash_value))
    else:
        handler.send_text(content_url)


def admin_upload_datapackage(handler, qs):
    filename, data = parse_upload(handler)
    query_name = qs.get("filename", qs.get("name", [""]))[0]
    package_name = normalize_datapackage_name(query_name or filename or "admin-upload.dp.zip")
    hash_value = hashlib.sha256(data).hexdigest()
    policy = parse_datapackage_filename_policy(package_name)
    upsert_package(
        hash_value,
        package_name,
        "TAKlite-Admin",
        data,
        tak_marti_base_url(),
        creator_user_id=None,
        visibility="public",
        policy=policy,
    )
    row = find_package(hash_value)
    record_audit_event(
        "admin_datapackage_upload",
        actor_type="admin",
        remote=handler.client_address[0],
        outcome="ok",
        reason_code="uploaded",
        details={"hash": hash_value, "name": package_name, "policy": policy},
    )
    return {"ok": True, "package": row_to_package(row), "url": tak_marti_content_url(hash_value)}


def datapackage_content_row(handler, qs):
    hash_value = qs.get("hash", [""])[0]
    return datapackage_hash_row(handler, hash_value)


def datapackage_hash_row(handler, hash_value):
    row = find_package(hash_value)
    if not row:
        handler.send_json({"error": "package not found"}, HTTPStatus.NOT_FOUND)
        return None
    if not package_visible_to_request(row, handler):
        package = row_to_package(row)
        access = package_access_for_user(package, handler.authenticated_user_id(), ACCESS_CONTROL_ENFORCE)
        record_audit_event(
            "datapackage_fetch",
            actor_type="tak_client",
            actor_id=handler.authenticated_user_id(),
            remote=handler.client_address[0],
            outcome="blocked",
            reason_code=access["reason_code"],
            details={"hash": hash_value, "name": package.get("Name", ""), "reason": access["reason"]},
        )
        handler.send_json({"error": "package not allowed", "reason_code": access["reason_code"], "reason": access["reason"]}, HTTPStatus.FORBIDDEN)
        return None
    package = Path(row["Path"])
    if not package.exists():
        handler.send_json({"error": "package file missing"}, HTTPStatus.NOT_FOUND)
        return None
    return row


def send_datapackage_to_clients(payload):
    hash_value = str(payload.get("hash", "")).strip()
    if not hash_value:
        raise ValueError("hash is required")
    row = find_package(hash_value)
    if not row:
        raise ValueError("datapackage not found")
    package = row_to_package(row)
    path = Path(row["Path"])
    if not path.exists():
        raise ValueError("datapackage file missing")
    send_all = bool(payload.get("all_clients", False))
    client_uids = [str(uid).strip() for uid in payload.get("client_uids", []) if str(uid).strip()]
    user_ids = []
    for user_id in payload.get("user_ids", []):
        try:
            user_ids.append(int(user_id))
        except (TypeError, ValueError):
            continue
    user_ids = sorted(set(user_ids))
    if user_ids:
        users = {user["id"]: user for user in list_portal_users() if not user.get("revoked")}
        event = fileshare_event(package)
        allowed_ids = []
        results = []
        for user_id in user_ids:
            user = users.get(user_id)
            if not user:
                results.append({
                    "user_id": user_id,
                    "username": "",
                    "status": "failed",
                    "sent": False,
                    "reason_code": "target_not_found",
                    "reason": "Target user does not exist or is revoked.",
                })
                continue
            access = package_access_for_user(package, user_id, ACCESS_CONTROL_ENFORCE)
            if not access["allowed"]:
                record_datapackage_delivery(hash_value, user_id, "blocked", access["reason_code"], access["reason"])
                results.append({
                    "user_id": user_id,
                    "username": user["username"],
                    "status": "blocked",
                    "sent": False,
                    "reason_code": access["reason_code"],
                    "reason": access["reason"],
                })
                continue
            allowed_ids.append(user_id)
        relay_result = RELAY.send_to_user_ids(event, allowed_ids)
        sent_by_user = {item["user_id"]: item for item in relay_result["results"]}
        for user_id in allowed_ids:
            user = users[user_id]
            sent_info = sent_by_user.get(user_id)
            if sent_info and sent_info["sent"]:
                record_datapackage_delivery(
                    hash_value,
                    user_id,
                    "sent",
                    sent_info["reason_code"],
                    sent_info["reason"],
                    target_uid=sent_info.get("uid", ""),
                    target_callsign=sent_info.get("callsign", ""),
                    increment_attempt=True,
                )
                results.append({
                    "user_id": user_id,
                    "username": user["username"],
                    "status": "sent",
                    "sent": True,
                    "uid": sent_info.get("uid", ""),
                    "callsign": sent_info.get("callsign", ""),
                    "reason_code": sent_info["reason_code"],
                    "reason": sent_info["reason"],
                })
            elif sent_info:
                record_datapackage_delivery(
                    hash_value,
                    user_id,
                    "pending",
                    sent_info["reason_code"],
                    sent_info["reason"],
                    target_uid=sent_info.get("uid", ""),
                    target_callsign=sent_info.get("callsign", ""),
                    increment_attempt=True,
                )
                results.append({
                    "user_id": user_id,
                    "username": user["username"],
                    "status": "pending",
                    "sent": False,
                    "uid": sent_info.get("uid", ""),
                    "callsign": sent_info.get("callsign", ""),
                    "reason_code": sent_info["reason_code"],
                    "reason": sent_info["reason"],
                })
            else:
                record_datapackage_delivery(
                    hash_value,
                    user_id,
                    "pending",
                    "pending_offline",
                    "User is not connected; package will be pushed when they reconnect.",
                )
                results.append({
                    "user_id": user_id,
                    "username": user["username"],
                    "status": "pending",
                    "sent": False,
                    "reason_code": "pending_offline",
                    "reason": "User is not connected; package will be pushed when they reconnect.",
                })
        sent_count = sum(1 for item in results if item["status"] == "sent")
        pending_count = sum(1 for item in results if item["status"] == "pending")
        blocked_count = sum(1 for item in results if item["status"] == "blocked")
        failed_count = sum(1 for item in results if item["status"] == "failed")
        return {
            "ok": sent_count > 0 or pending_count > 0,
            "package": package,
            "url": tak_marti_content_url(hash_value),
            "sent": sent_count,
            "pending": pending_count,
            "blocked": blocked_count,
            "failed": failed_count,
            "results": results,
            "deliveries": list_datapackage_deliveries(hash_value, limit=50),
        }
    if not send_all and not client_uids:
        raise ValueError("select at least one connected client")
    result = RELAY.send_to_client_uids(fileshare_event(package), client_uids, send_all=send_all)
    result.update({
        "ok": result["sent"] > 0,
        "package": package,
        "url": tak_marti_content_url(hash_value),
    })
    if not result["ok"]:
        result["error"] = "no matching connected clients"
    return result


class HttpHandler(BaseHTTPRequestHandler):
    server_version = "TAKliteHTTP/0.2"

    def log_message(self, fmt, *args):
        print(f"{self.client_address[0]} - {fmt % args}")

    def bootstrap_authorized(self):
        return bool(admin_count() == 0 and ADMIN_TOKEN and self.headers.get("X-Admin-Token", "") == ADMIN_TOKEN)

    def authorized(self):
        if validate_session(self.headers.get("X-Session-Token", "")):
            return True
        if self.bootstrap_authorized():
            return True
        return False

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        if length > MAX_JSON_BYTES:
            raise ValueError(f"JSON body exceeds maximum size of {MAX_JSON_BYTES} bytes")
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def send_text(self, text, status=HTTPStatus.OK, content_type="text/plain"):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_security_headers(content_type)
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, obj, status=HTTPStatus.OK):
        self.send_text(json.dumps(obj, indent=2), status, "application/json")

    def send_bytes(self, body, status=HTTPStatus.OK, content_type="application/octet-stream", extra_headers=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.send_security_headers(content_type)
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path, filename):
        filename = safe_download_name(filename, "datapackage.zip")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/x-zip-compressed")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(path.stat().st_size))
        self.send_security_headers("application/x-zip-compressed")
        self.end_headers()
        with path.open("rb") as handle:
            shutil.copyfileobj(handle, self.wfile)

    def send_file_head(self, path, filename):
        filename = safe_download_name(filename, "datapackage.zip")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/x-zip-compressed")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(path.stat().st_size))
        self.send_security_headers("application/x-zip-compressed")
        self.end_headers()

    def send_download(self, path, filename, content_type):
        filename = safe_download_name(filename)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(path.stat().st_size))
        self.send_security_headers(content_type)
        self.end_headers()
        with path.open("rb") as handle:
            shutil.copyfileobj(handle, self.wfile)

    def send_static_file(self, path):
        content_types = {
            ".html": "text/html; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".ico": "image/x-icon",
            ".json": "application/json",
        }
        content_type = content_types.get(path.suffix.lower(), "application/octet-stream")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(path.stat().st_size))
        self.send_security_headers(content_type)
        self.end_headers()
        with path.open("rb") as handle:
            shutil.copyfileobj(handle, self.wfile)

    def send_security_headers(self, content_type):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        if content_type.startswith("text/html"):
            self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' blob: data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'")

    def require_auth(self):
        if self.authorized():
            return True
        self.send_json({"error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
        return False

    def require_portal_auth(self):
        user = validate_portal_session(self.headers.get("X-Portal-Token", ""))
        if user:
            return user
        self.send_json({"error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
        return None

    def require_plugin_user(self):
        user = plugin_user_for_request(self)
        if user:
            try:
                learn_portal_user_device(user["id"], source_ip=self.client_address[0], device_id=self.headers.get("X-Axon-Device-Mac", ""))
            except ValueError:
                pass
            return user
        self.send_json({"error": "plugin authentication required"}, HTTPStatus.UNAUTHORIZED)
        return None

    def client_cert_common_name(self):
        if hasattr(self.connection, "getpeercert"):
            try:
                return cert_common_name(self.connection.getpeercert() or {})
            except OSError:
                return ""
        return ""

    def authenticated_user_id(self):
        identity = client_identity_for_cert(self.client_cert_common_name())
        if identity:
            try:
                learn_portal_user_device(identity["user_id"], source_ip=self.client_address[0])
            except ValueError:
                pass
            return identity["user_id"]
        return None

    def do_HEAD(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        qs = parse_qs(parsed.query)
        if path in ("/Marti/sync/content", "/sync/content"):
            row = datapackage_content_row(self, qs)
            if not row:
                return
            self.send_file_head(Path(row["Path"]), row["Name"])
            return
        match = re.match(r"^/(?:Marti/)?api/sync/metadata/([^/]+)/tool$", path)
        if match:
            row = datapackage_hash_row(self, unquote(match.group(1)))
            if not row:
                return
            self.send_file_head(Path(row["Path"]), row["Name"])
            return
        self.send_response(HTTPStatus.NOT_FOUND)
        self.send_header("Content-Length", "0")
        self.send_security_headers("text/plain")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        qs = parse_qs(parsed.query)
        if path == "/":
            index = STATIC_DIR / "index.html"
            if index.exists():
                self.send_static_file(index)
            else:
                self.send_text(INDEX_HTML, content_type="text/html; charset=utf-8")
            return
        if path.startswith("/assets/"):
            rel = Path(path.lstrip("/"))
            static_path = (STATIC_DIR / rel).resolve()
            try:
                static_path.relative_to(STATIC_DIR.resolve())
            except ValueError:
                self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
                return
            if not static_path.is_file():
                self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
                return
            self.send_static_file(static_path)
            return
        if path == "/connect":
            self.send_text(CONNECT_HTML, content_type="text/html; charset=utf-8")
            return
        if path == "/connect/enroll":
            code = qs.get("code", [""])[0]
            self.send_text(enrollment_connect_html(absolute_base_url(self), code), content_type="text/html; charset=utf-8")
            return
        public_match = re.match(r"^/connect/([A-Za-z0-9_-]+)\.dp\.zip$", path)
        if public_match:
            row = find_cert_profile_by_token(public_match.group(1))
            if not row or row["revoked_at"]:
                self.send_json({"error": "connection package not found"}, HTTPStatus.NOT_FOUND)
                return
            package = Path(row["datapackage_file"])
            if not package.exists():
                self.send_json({"error": "connection package file missing"}, HTTPStatus.NOT_FOUND)
                return
            self.send_download(package, package.name, "application/zip")
            return
        if path == "/api/bootstrap/status":
            self.send_json({"has_admin": admin_count() > 0, "token_required": bool(ADMIN_TOKEN)})
            return
        if path == "/api/me":
            if not self.require_auth():
                return
            username = validate_session(self.headers.get("X-Session-Token", "")) or "bootstrap-token"
            self.send_json({"authenticated": True, "username": username, "bootstrap": username == "bootstrap-token"})
            return
        if path == "/api/admin/2fa/status":
            username = validate_session(self.headers.get("X-Session-Token", ""))
            if not username:
                self.send_json({"error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
                return
            self.send_json(admin_totp_status(username))
            return
        if path == "/api/connect/me":
            user = self.require_portal_auth()
            if not user:
                return
            self.send_json({"authenticated": True, "user": portal_user_row(user), "cert_password": CERT_PASSWORD})
            return
        if path == "/api/connect/download":
            user = self.require_portal_auth()
            if not user:
                return
            if user["first_download_at"] and not user["allow_redownload"]:
                self.send_json({"error": "connection package already downloaded; contact your TAKlite admin for re-download"}, HTTPStatus.FORBIDDEN)
                return
            package = Path(user["datapackage_file"] or "")
            if not package.exists():
                self.send_json({"error": "connection package file missing"}, HTTPStatus.NOT_FOUND)
                return
            mark_portal_download(user["id"])
            self.send_download(package, package.name, "application/zip")
            return
        if path == "/api/connect/profile":
            user = self.require_portal_auth()
            if not user:
                return
            if user["first_download_at"] and not user["allow_redownload"]:
                self.send_json({"error": "connection package already downloaded; contact your TAKlite admin for re-download or reissue"}, HTTPStatus.FORBIDDEN)
                return
            body = build_portal_user_plugin_config(user).encode("utf-8")
            filename = safe_download_name("taklite-plugin.json", "taklite-plugin.json")
            self.send_bytes(
                body,
                content_type="application/json",
                extra_headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
            return
        if path in ("/Marti/api/version", "/api/version"):
            self.send_text(VERSION)
            return
        if path in ("/Marti/api/version/config", "/api/version/config"):
            self.send_json({"version": 2, "type": "ServerConfig", "data": {"version": VERSION, "api": "2", "hostname": socket.gethostname()}})
            return
        if path in ("/Marti/api/clientEndPoints", "/api/clientEndPoints"):
            self.send_json(client_endpoints_response())
            return
        if path in ("/Marti/api/groups/groupCacheEnabled", "/api/groups/groupCacheEnabled"):
            self.send_json(False)
            return
        if path in ("/Marti/api/groups/all", "/api/groups/all"):
            self.send_json(marti_groups_response())
            return
        if path in ("/Marti/api/missions/invitations", "/api/missions/invitations"):
            self.send_json(mission_empty_response("MissionInvitationList"))
            return
        if path in ("/Marti/api/missions/all/invitations", "/api/missions/all/invitations"):
            self.send_json(mission_empty_response("MissionInvitationList"))
            return
        if path in ("/Marti/api/missions", "/api/missions"):
            self.send_json(mission_empty_response("MissionList"))
            return
        if re.match(r"^/(?:Marti/)?api/missions/[^/]+/(?:changes|contents|subscriptions|log)$", path):
            self.send_json(mission_empty_response("MissionDetailList"))
            return
        if path in ("/Marti/api/citrap", "/api/citrap"):
            self.send_json({"version": 2, "type": "CitrapList", "data": []})
            return
        if path in ("/Marti/sync/search", "/sync/search"):
            try:
                items = list_packages(self.authenticated_user_id(), ACCESS_CONTROL_ENFORCE)
                self.send_json({"resultCount": len(items), "results": items})
            except Exception as exc:
                print(f"TAKlite GET {path} failed: {exc}", flush=True)
                self.send_json({"error": str(exc), "resultCount": 0, "results": []}, HTTPStatus.BAD_REQUEST)
            return
        match = re.match(r"^/(?:Marti/)?api/sync/metadata/([^/]+)/tool$", path)
        if match:
            try:
                row = datapackage_hash_row(self, unquote(match.group(1)))
                if not row:
                    return
                self.send_file(Path(row["Path"]), row["Name"])
            except Exception as exc:
                print(f"TAKlite GET {path} failed: {exc}", flush=True)
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path in ("/Marti/sync/missionquery", "/sync/missionquery"):
            try:
                hash_value = qs.get("hash", [""])[0]
                row = find_package(hash_value)
                if not row:
                    self.send_json({"error": "package not found"}, HTTPStatus.NOT_FOUND)
                    return
                if not package_visible_to_request(row, self):
                    self.send_json({"error": "package not allowed"}, HTTPStatus.FORBIDDEN)
                    return
                self.send_text(tak_marti_metadata_tool_url(hash_value))
            except Exception as exc:
                print(f"TAKlite GET {path} failed: {exc}", flush=True)
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path in ("/Marti/sync/content", "/sync/content"):
            try:
                row = datapackage_content_row(self, qs)
                if not row:
                    return
                self.send_file(Path(row["Path"]), row["Name"])
            except Exception as exc:
                print(f"TAKlite GET {path} failed: {exc}", flush=True)
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/certs/taklite-truststore.p12":
            if not LEGACY_CERT_DOWNLOADS:
                self.send_json({"error": "legacy cert downloads are disabled"}, HTTPStatus.FORBIDDEN)
                return
            truststore = CERT_DIR / "taklite-truststore.p12"
            if not truststore.exists():
                self.send_json({"error": "truststore not found"}, HTTPStatus.NOT_FOUND)
                return
            self.send_download(truststore, "taklite-truststore.p12", "application/x-pkcs12")
            return
        if path == "/certs/taklite-atak-ssl.dp.zip":
            if not self.require_auth():
                return
            datapackage = CERT_DIR / "taklite-atak-ssl.dp.zip"
            if not datapackage.exists():
                self.send_json({"error": "certificate datapackage not found"}, HTTPStatus.NOT_FOUND)
                return
            self.send_download(datapackage, "taklite-atak-ssl.dp.zip", "application/zip")
            return
        if path == "/certs/taklite-client.p12":
            if not self.require_auth():
                return
            client_cert = CERT_DIR / "taklite-client.p12"
            if not client_cert.exists():
                self.send_json({"error": "client certificate not found"}, HTTPStatus.NOT_FOUND)
                return
            self.send_download(client_cert, "taklite-client.p12", "application/x-pkcs12")
            return
        if path == "/certs/10.66.66.1.p12":
            if not LEGACY_CERT_DOWNLOADS:
                self.send_json({"error": "legacy cert downloads are disabled"}, HTTPStatus.FORBIDDEN)
                return
            atak_truststore = CERT_DIR / "10.66.66.1.p12"
            if not atak_truststore.exists():
                self.send_json({"error": "ATAK truststore not found"}, HTTPStatus.NOT_FOUND)
                return
            self.send_download(atak_truststore, "10.66.66.1.p12", "application/x-pkcs12")
            return
        if path == "/certs/taklite-ca.crt":
            ca_cert = CERT_DIR / "taklite-ca.crt"
            if not ca_cert.exists():
                self.send_json({"error": "ca certificate not found"}, HTTPStatus.NOT_FOUND)
                return
            self.send_download(ca_cert, "taklite-ca.crt", "application/x-x509-ca-cert")
            return
        if path == "/api/health":
            tls_enabled = HTTPS_CERT.exists() and HTTPS_KEY.exists()
            self.send_json({"ok": True, "version": VERSION, "cot_port": COT_PORT, "cot_tls_port": COT_TLS_PORT if tls_enabled else None, "http_port": HTTP_PORT, "https_port": HTTPS_PORT if tls_enabled else None, "clients": len(RELAY.snapshot()), "packages": len(list_packages(enforce=False)), "auth_enabled": bool(ADMIN_TOKEN), "access_enforcement": ACCESS_CONTROL_ENFORCE})
            return
        if path == "/api/system-health":
            if not self.require_auth():
                return
            self.send_json(runtime_health())
            return
        if path == "/api/audit-events":
            if not self.require_auth():
                return
            self.send_json({"items": list_audit_events(qs.get("limit", ["100"])[0], qs.get("type", [""])[0])})
            return
        if path == "/api/settings":
            if not self.require_auth():
                return
            self.send_json(editable_settings_status())
            return
        if path == "/api/firewall/status":
            if not self.require_auth():
                return
            self.send_json(firewall_status())
            return
        if path == "/api/admin/update/status":
            if not self.require_auth():
                return
            self.send_json(latest_release_status(refresh=qs.get("refresh", ["0"])[0] in ("1", "true", "yes")))
            return
        if path == "/api/ui-config":
            self.send_json({"wgDashboardUrl": WG_DASHBOARD_URL})
            return
        if path == "/api/plugin/bootstrap/profile":
            try:
                device_mac = qs.get("mac", qs.get("device_mac", [self.headers.get("X-Axon-Device-Mac", "")]))[0]
                user = find_portal_user_by_device_binding(self.client_address[0], device_mac)
                if not user:
                    record_audit_event(
                        "plugin_profile_bootstrap",
                        actor_type="device",
                        remote=self.client_address[0],
                        outcome="blocked",
                        reason_code="no_matching_device_profile",
                        details={"device_mac_supplied": bool(device_mac)},
                    )
                    self.send_json({"error": "no matching device profile"}, HTTPStatus.NOT_FOUND)
                    return
                record_audit_event(
                    "plugin_profile_bootstrap",
                    actor_type="portal_user",
                    actor_id=user["id"],
                    actor_name=user["username"],
                    remote=self.client_address[0],
                    outcome="ok",
                    reason_code="profile_returned",
                    details={"device_mac_supplied": bool(device_mac)},
                )
                self.send_json(json.loads(build_portal_user_plugin_config(user)))
            except Exception as exc:
                record_audit_event(
                    "plugin_profile_bootstrap",
                    actor_type="device",
                    remote=self.client_address[0],
                    outcome="failed",
                    reason_code="bootstrap_error",
                    details={"error": str(exc)},
                )
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/api/plugin/me":
            user = self.require_plugin_user()
            if not user:
                return
            self.send_json(plugin_context_for_user(user))
            return
        if path == "/api/plugin/admin/snapshot":
            user = self.require_plugin_user()
            if not user:
                return
            try:
                self.send_json(plugin_admin_snapshot(user))
            except Exception as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.FORBIDDEN)
            return
        if path == "/api/field-enrollments":
            if not self.require_auth():
                return
            self.send_json({"items": list_field_enrollments(absolute_base_url(self))})
            return
        if path == "/api/field-enrollments/qr":
            if not self.require_auth():
                return
            enrollment = find_field_enrollment(int(qs.get("id", ["0"])[0] or "0"))
            if not enrollment:
                self.send_json({"error": "field enrollment pass not found"}, HTTPStatus.NOT_FOUND)
                return
            info = enrollment_row(enrollment, absolute_base_url(self))
            result = subprocess.run(["qrencode", "-t", "SVG", "-o", "-", info["join_url"]], capture_output=True)
            if result.returncode:
                self.send_json({"error": (result.stderr or b"qrencode failed").decode("utf-8", "replace")}, HTTPStatus.BAD_REQUEST)
                return
            self.send_bytes(result.stdout, content_type="image/svg+xml")
            return
        if path == "/api/plugin/audience":
            user = self.require_plugin_user()
            if not user:
                return
            payload = {
                "audience_mode": qs.get("audience_mode", qs.get("mode", ["all_allowed"]))[0],
                "user_ids": qs.get("user_ids", qs.get("target_user_ids", [""]))[0],
                "group_ids": qs.get("group_ids", qs.get("team_ids", [""]))[0],
                "levels": qs.get("levels", qs.get("allowed_levels", [""]))[0],
                "include_self": qs.get("include_self", ["false"])[0].lower() in ("1", "true", "yes", "on"),
            }
            result = plugin_datapackage_audience(user["id"], payload)
            record_audit_event(
                "plugin_audience_preview",
                actor_type="portal_user",
                actor_id=user["id"],
                actor_name=user.get("username", ""),
                remote=self.client_address[0],
                outcome="ok",
                reason_code="preview",
                details={"allowed": result["allowed_count"], "blocked": result["blocked_count"], "audience": result["audience"]},
            )
            self.send_json(result)
            return
        if path == "/api/plugin/datapackages/history":
            user = self.require_plugin_user()
            if not user:
                return
            try:
                self.send_json(plugin_datapackage_history(user["id"], qs.get("limit", ["25"])[0]))
            except Exception as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/api/datapackages":
            if not self.require_auth():
                return
            self.send_json({"items": list_packages(enforce=False)})
            return
        if path == "/api/datapackages/preview":
            if not self.require_auth():
                return
            try:
                self.send_json(datapackage_access_preview(qs.get("hash", [""])[0]))
            except Exception as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/api/datapackages/deliveries":
            if not self.require_auth():
                return
            self.send_json({"items": list_datapackage_deliveries(qs.get("hash", [""])[0], limit=100)})
            return
        if path == "/api/clients":
            if not self.require_auth():
                return
            self.send_json({"items": RELAY.snapshot()})
            return
        if path == "/api/cert-profiles":
            if not self.require_auth():
                return
            self.send_json({"items": list_cert_profiles(), "cert_password": CERT_PASSWORD, "server_host": SERVER_HOST})
            return
        if path == "/api/portal-users":
            if not self.require_auth():
                return
            self.send_json({"items": list_portal_users(), "portal_url": f"{absolute_base_url(self)}/connect/"})
            return
        if path == "/api/access-control":
            if not self.require_auth():
                return
            self.send_json(access_summary())
            return
        if path == "/api/access-preview":
            if not self.require_auth():
                return
            self.send_json(access_preview(qs.get("user_id", ["0"])[0]))
            return
        if path == "/api/portal-users/qr":
            if not self.require_auth():
                return
            user_id = int(qs.get("id", ["0"])[0] or "0")
            user = find_portal_user(user_id)
            if not user:
                self.send_json({"error": "portal user not found"}, HTTPStatus.NOT_FOUND)
                return
            url = f"{absolute_base_url(self)}{portal_user_row(user)['portal_path']}"
            result = subprocess.run(["qrencode", "-t", "SVG", "-o", "-", url], capture_output=True)
            if result.returncode:
                self.send_json({"error": (result.stderr or b"qrencode failed").decode("utf-8", "replace")}, HTTPStatus.BAD_REQUEST)
                return
            self.send_bytes(result.stdout, content_type="image/svg+xml")
            return
        if path == "/api/cert-profiles/download":
            if not self.require_auth():
                return
            profile_id = int(qs.get("id", ["0"])[0] or "0")
            row = find_cert_profile(profile_id)
            if not row:
                self.send_json({"error": "connection package not found"}, HTTPStatus.NOT_FOUND)
                return
            if row["revoked_at"]:
                self.send_json({"error": "connection package is revoked"}, HTTPStatus.GONE)
                return
            package = Path(row["datapackage_file"])
            if not package.exists():
                self.send_json({"error": "connection package file missing"}, HTTPStatus.NOT_FOUND)
                return
            self.send_download(package, package.name, "application/zip")
            return
        self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        qs = parse_qs(parsed.query)
        try:
            if path == "/api/bootstrap/admin":
                if admin_count() > 0:
                    raise ValueError("admin user already exists")
                remote = self.client_address[0]
                if login_limited("bootstrap", remote, "bootstrap"):
                    self.send_json({"error": "too many failed attempts; try again later"}, HTTPStatus.TOO_MANY_REQUESTS)
                    return
                if not self.bootstrap_authorized():
                    record_login_failure("bootstrap", remote, "bootstrap")
                    self.send_json({"error": "bootstrap token required"}, HTTPStatus.UNAUTHORIZED)
                    return
                payload = self.read_json()
                username = create_admin(payload.get("username", ""), payload.get("password", ""))
                clear_login_failures("bootstrap", remote, "bootstrap")
                session = create_session(username)
                self.send_json({"ok": True, "username": username, "session": session})
                return
            if path == "/api/login":
                payload = self.read_json()
                remote = self.client_address[0]
                login_user = payload.get("username", "")
                if login_limited("admin", remote, login_user):
                    self.send_json({"error": "too many failed attempts; try again later"}, HTTPStatus.TOO_MANY_REQUESTS)
                    return
                username = authenticate_admin(payload.get("username", ""), payload.get("password", ""), payload.get("totp_code", ""))
                if not username:
                    record_login_failure("admin", remote, login_user)
                    if admin_requires_totp(payload.get("username", ""), payload.get("password", "")):
                        self.send_json({"error": "two-factor code required", "totp_required": True}, HTTPStatus.UNAUTHORIZED)
                    else:
                        self.send_json({"error": "invalid username or password"}, HTTPStatus.UNAUTHORIZED)
                    return
                clear_login_failures("admin", remote, username)
                self.send_json({"ok": True, "username": username, "session": create_session(username)})
                return
            if path == "/api/logout":
                token = self.headers.get("X-Session-Token", "")
                if token:
                    with db_connect() as conn:
                        conn.execute("delete from admin_sessions where token = ?", (token,))
                        conn.commit()
                self.send_json({"ok": True})
                return
            if path == "/api/admin/password":
                token = self.headers.get("X-Session-Token", "")
                username = validate_session(token)
                if not username:
                    self.send_json({"error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
                    return
                payload = self.read_json()
                current_password = payload.get("current_password", "")
                new_password = payload.get("new_password", "")
                confirm_password = payload.get("confirm_password", "")
                if new_password != confirm_password:
                    raise ValueError("new passwords do not match")
                change_admin_password(username, current_password, new_password, token)
                self.send_json({"ok": True, "username": username, "message": "admin password changed"})
                return
            if path == "/api/admin/2fa/setup":
                token = self.headers.get("X-Session-Token", "")
                username = validate_session(token)
                if not username:
                    self.send_json({"error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
                    return
                payload = self.read_json()
                self.send_json(create_admin_totp_setup(username, payload.get("current_password", "")))
                return
            if path == "/api/admin/2fa/enable":
                token = self.headers.get("X-Session-Token", "")
                username = validate_session(token)
                if not username:
                    self.send_json({"error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
                    return
                payload = self.read_json()
                self.send_json(enable_admin_totp(username, payload.get("current_password", ""), payload.get("totp_code", ""), current_token=token))
                return
            if path == "/api/admin/2fa/disable":
                token = self.headers.get("X-Session-Token", "")
                username = validate_session(token)
                if not username:
                    self.send_json({"error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
                    return
                payload = self.read_json()
                self.send_json(disable_admin_totp(username, payload.get("current_password", ""), payload.get("totp_code", ""), current_token=token))
                return
            if path == "/api/connect/login":
                payload = self.read_json()
                remote = self.client_address[0]
                login_user = payload.get("username", "")
                if login_limited("portal", remote, login_user):
                    self.send_json({"error": "too many failed attempts; try again later"}, HTTPStatus.TOO_MANY_REQUESTS)
                    return
                user = authenticate_portal_user(payload.get("username", ""), payload.get("password", ""))
                if not user:
                    record_login_failure("portal", remote, login_user)
                    self.send_json({"error": "invalid username or password"}, HTTPStatus.UNAUTHORIZED)
                    return
                clear_login_failures("portal", remote, user["username"])
                self.send_json({"ok": True, "session": create_portal_session(user["id"]), "user": portal_user_row(user), "cert_password": CERT_PASSWORD})
                return
            if path == "/api/connect/logout":
                portal_logout(self.headers.get("X-Portal-Token", ""))
                self.send_json({"ok": True})
                return
            if path == "/api/admin/update/run":
                if not self.require_auth():
                    return
                payload = self.read_json()
                result = run_gui_update(
                    payload.get("confirm", ""),
                    payload.get("target_tag", ""),
                    payload.get("release_zip_url", ""),
                    payload.get("expected_sha256", ""),
                )
                self.send_json(result, HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_REQUEST)
                return
            if path == "/api/settings/apply":
                if not self.require_auth():
                    return
                result = queue_settings_update(self.read_json())
                self.send_json(result, HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_REQUEST)
                return
            if path == "/api/firewall/apply":
                if not self.require_auth():
                    return
                result = queue_firewall_update(self.read_json())
                self.send_json(result, HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_REQUEST)
                return
            if path == "/api/plugin/datapackages/preview":
                user = self.require_plugin_user()
                if not user:
                    return
                result = plugin_datapackage_audience(user["id"], self.read_json())
                record_audit_event(
                    "plugin_datapackage_preview",
                    actor_type="portal_user",
                    actor_id=user["id"],
                    actor_name=user.get("username", ""),
                    remote=self.client_address[0],
                    outcome="ok",
                    reason_code="preview",
                    details={"allowed": result["allowed_count"], "blocked": result["blocked_count"], "audience": result["audience"]},
                )
                self.send_json(result)
                return
            if path == "/api/plugin/datapackages/send":
                user = self.require_plugin_user()
                if not user:
                    return
                result = plugin_send_datapackage(user["id"], self.read_json())
                self.send_json(result, HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_REQUEST)
                return
            if path == "/api/plugin/datapackages/upload":
                result = plugin_upload_datapackage(self, qs)
                if result is not None:
                    self.send_json(result, HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_REQUEST)
                return
            if path == "/api/plugin/field-enrollments/create":
                user = self.require_plugin_user()
                if not user:
                    return
                result = plugin_create_field_enrollment(user, self.read_json(), absolute_base_url(self))
                self.send_json(result)
                return
            if path == "/api/plugin/field-enroll":
                payload = self.read_json()
                result = redeem_field_enrollment(
                    payload.get("code", payload.get("token", "")),
                    self.client_address[0],
                    payload.get("device_id", payload.get("device_mac", self.headers.get("X-Axon-Device-Mac", ""))),
                    payload.get("display_name", payload.get("callsign", "")),
                    absolute_base_url(self),
                )
                self.send_json(result)
                return
            if path == "/api/plugin/privacy/pli":
                user = self.require_plugin_user()
                if not user:
                    return
                payload = self.read_json()
                try:
                    self.send_json(set_user_pli_enabled(user, payload.get("user_id", user["id"]), validate_bool(payload.get("enabled", True))))
                except Exception as exc:
                    self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            if path == "/api/plugin/policy/test":
                user = self.require_plugin_user()
                if not user:
                    return
                payload = self.read_json()
                try:
                    self.send_json(plugin_policy_test(user, payload.get("source_user_id", user["id"]), payload.get("target_user_id", 0)))
                except Exception as exc:
                    self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            if path == "/api/plugin/admin/revoke-user":
                user = self.require_plugin_user()
                if not user:
                    return
                try:
                    self.send_json(plugin_revoke_user(user, self.read_json().get("user_id", 0)))
                except Exception as exc:
                    self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            if path == "/api/plugin/admin/reissue-user":
                user = self.require_plugin_user()
                if not user:
                    return
                try:
                    self.send_json(plugin_reissue_user(user, self.read_json().get("user_id", 0)))
                except Exception as exc:
                    self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
                return
            if path in ("/Marti/sync/missionupload", "/sync/missionupload"):
                upload_datapackage_from_request(self, qs, response_url="metadata")
                return
            if path in ("/Marti/sync/upload", "/sync/upload", "/Marti/sync/content", "/sync/content"):
                upload_datapackage_from_request(self, qs)
                return
            if path == "/api/datapackages/upload":
                if not self.require_auth():
                    return
                self.send_json(admin_upload_datapackage(self, qs))
                return
            if path == "/api/datapackages/send":
                if not self.require_auth():
                    return
                result = send_datapackage_to_clients(self.read_json())
                record_audit_event(
                    "admin_datapackage_send",
                    actor_type="admin",
                    remote=self.client_address[0],
                    outcome="ok" if result.get("ok") else "failed",
                    reason_code="sent_or_queued",
                    details={"hash": result.get("package", {}).get("Hash", ""), "sent": result.get("sent", 0), "pending": result.get("pending", 0), "blocked": result.get("blocked", 0), "failed": result.get("failed", 0)},
                )
                self.send_json(result, HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_REQUEST)
                return
            if path == "/api/datapackages/policy":
                if not self.require_auth():
                    return
                payload = self.read_json()
                result = update_datapackage_policy(
                    payload.get("hash", ""),
                    payload.get("mode", payload.get("policy_mode", "sender")),
                    payload.get("allowed_levels", []),
                    payload.get("max_level"),
                )
                self.send_json(result)
                return
            if path == "/api/datapackages/delete":
                if not self.require_auth():
                    return
                payload = self.read_json()
                hash_value = payload.get("hash", "")
                if not hash_value:
                    raise ValueError("hash is required")
                self.send_json(delete_package(hash_value, bool(payload.get("delete_file", True))))
                return
            if path == "/api/cert-profiles/create":
                if not self.require_auth():
                    return
                payload = self.read_json()
                self.send_json(create_cert_profile(payload.get("name", ""), payload.get("description", "")))
                return
            if path == "/api/portal-users/create":
                if not self.require_auth():
                    return
                payload = self.read_json()
                self.send_json(create_portal_user(
                    payload.get("username", ""),
                    payload.get("password", ""),
                    payload.get("display_name", ""),
                    payload.get("description", ""),
                    bool(payload.get("allow_redownload", False)),
                    payload.get("role_id"),
                    payload.get("group_ids", []),
                    payload.get("access_level"),
                    payload.get("assigned_ip", ""),
                    payload.get("device_mac", ""),
                ))
                return
            if path == "/api/portal-users/bulk-create":
                if not self.require_auth():
                    return
                payload = self.read_json()
                self.send_json(create_bulk_portal_users(
                    payload.get("prefix", ""),
                    payload.get("count", 0),
                    payload.get("description", ""),
                    bool(payload.get("allow_redownload", False)),
                    absolute_base_url(self),
                    payload.get("role_id"),
                    payload.get("group_ids", []),
                    payload.get("access_level"),
                ))
                return
            if path == "/api/field-enrollments/create":
                if not self.require_auth():
                    return
                payload = self.read_json()
                self.send_json(create_field_enrollment(
                    payload.get("name", ""),
                    payload.get("username_prefix", ""),
                    payload.get("description", ""),
                    payload.get("expires_in_hours", 24),
                    payload.get("max_uses", 1),
                    payload.get("role_id"),
                    payload.get("group_ids", []),
                    payload.get("access_level"),
                    absolute_base_url(self),
                ))
                return
            if path == "/api/field-enrollments/revoke":
                if not self.require_auth():
                    return
                payload = self.read_json()
                self.send_json(revoke_field_enrollment(int(payload.get("id", 0))))
                return
            if path == "/api/access-roles/create":
                if not self.require_auth():
                    return
                payload = self.read_json()
                self.send_json(create_access_role(
                    payload.get("name", ""),
                    payload.get("description", ""),
                    bool(payload.get("can_see_all", False)),
                    bool(payload.get("can_send_all", False)),
                    bool(payload.get("can_see_own_groups", True)),
                    bool(payload.get("can_send_own_groups", True)),
                    bool(payload.get("can_receive_all", payload.get("can_send_all", False))),
                    bool(payload.get("can_receive_own_groups", payload.get("can_send_own_groups", True))),
                ))
                return
            if path == "/api/access-roles/update":
                if not self.require_auth():
                    return
                payload = self.read_json()
                self.send_json(update_access_role(
                    int(payload.get("id", 0)),
                    payload.get("name", ""),
                    payload.get("description", ""),
                    bool(payload.get("can_see_all", False)),
                    bool(payload.get("can_send_all", False)),
                    bool(payload.get("can_see_own_groups", True)),
                    bool(payload.get("can_send_own_groups", True)),
                    bool(payload.get("can_receive_all", payload.get("can_send_all", False))),
                    bool(payload.get("can_receive_own_groups", payload.get("can_send_own_groups", True))),
                ))
                return
            if path == "/api/access-roles/delete":
                if not self.require_auth():
                    return
                payload = self.read_json()
                self.send_json(delete_access_role(int(payload.get("id", 0))))
                return
            if path == "/api/access-groups/create":
                if not self.require_auth():
                    return
                payload = self.read_json()
                self.send_json(create_access_group(payload.get("name", ""), payload.get("description", ""), payload.get("color", "")))
                return
            if path == "/api/access-groups/update":
                if not self.require_auth():
                    return
                payload = self.read_json()
                self.send_json(update_access_group(int(payload.get("id", 0)), payload.get("name", ""), payload.get("description", ""), payload.get("color", "")))
                return
            if path == "/api/access-groups/delete":
                if not self.require_auth():
                    return
                payload = self.read_json()
                self.send_json(delete_access_group(int(payload.get("id", 0))))
                return
            if path == "/api/access-users/set":
                if not self.require_auth():
                    return
                payload = self.read_json()
                access_level = payload["access_level"] if "access_level" in payload else ACCESS_LEVEL_UNCHANGED
                self.send_json(set_user_access(int(payload.get("user_id", 0)), payload.get("role_id"), payload.get("group_ids", []), access_level))
                return
            if path == "/api/access-users/bulk-set":
                if not self.require_auth():
                    return
                payload = self.read_json()
                self.send_json(bulk_set_user_access(
                    payload.get("user_ids", []),
                    payload.get("role_id"),
                    payload.get("group_ids", []),
                    payload.get("group_mode", "replace"),
                    payload.get("access_level"),
                    payload.get("level_mode", "unchanged"),
                    payload.get("role_mode", "unchanged"),
                ))
                return
            if path == "/api/access-links/set":
                if not self.require_auth():
                    return
                payload = self.read_json()
                self.send_json(set_policy_link(
                    int(payload.get("source_group_id", 0)),
                    int(payload.get("target_group_id", 0)),
                    bool(payload.get("can_see", False)),
                    bool(payload.get("can_send", False)),
                    bool(payload.get("can_receive", payload.get("can_send", False))),
                ))
                return
            if path == "/api/portal-users/reset-password":
                if not self.require_auth():
                    return
                payload = self.read_json()
                self.send_json(reset_portal_password(int(payload.get("id", 0)), payload.get("password", "")))
                return
            if path == "/api/portal-users/edit":
                if not self.require_auth():
                    return
                payload = self.read_json()
                self.send_json(edit_portal_user(
                    int(payload.get("id", 0)),
                    payload.get("display_name", ""),
                    payload.get("description", ""),
                    payload.get("assigned_ip", ""),
                    payload.get("device_mac", ""),
                ))
                return
            if path == "/api/portal-users/redownload":
                if not self.require_auth():
                    return
                payload = self.read_json()
                self.send_json(set_portal_redownload(int(payload.get("id", 0)), bool(payload.get("allow_redownload", False))))
                return
            if path == "/api/portal-users/reissue":
                if not self.require_auth():
                    return
                payload = self.read_json()
                self.send_json(reissue_portal_user(int(payload.get("id", 0))))
                return
            if path == "/api/portal-users/revoke":
                if not self.require_auth():
                    return
                payload = self.read_json()
                self.send_json(revoke_portal_user(int(payload.get("id", 0))))
                return
            if path == "/api/portal-users/delete":
                if not self.require_auth():
                    return
                payload = self.read_json()
                self.send_json(delete_portal_user(int(payload.get("id", 0)), bool(payload.get("delete_profile", False))))
                return
            if path == "/api/cert-profiles/revoke":
                if not self.require_auth():
                    return
                payload = self.read_json()
                self.send_json(revoke_cert_profile(int(payload.get("id", 0))))
                return
            if path == "/api/cert-profiles/delete":
                if not self.require_auth():
                    return
                payload = self.read_json()
                self.send_json(delete_cert_profile(int(payload.get("id", 0)), bool(payload.get("delete_files", True))))
                return
            self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            print(f"TAKlite POST {path} failed: {exc}", flush=True)
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        qs = parse_qs(parsed.query)
        if path in ("/Marti/api/missions/citrap/subscription", "/api/missions/citrap/subscription"):
            self.send_json({"version": 2, "type": "MissionSubscription", "data": {"subscribed": True}})
            return
        if path in ("/Marti/sync/missionupload", "/sync/missionupload"):
            try:
                upload_datapackage_from_request(self, qs, response_url="metadata")
            except Exception as exc:
                print(f"TAKlite PUT {path} failed: {exc}", flush=True)
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path in ("/Marti/sync/content", "/sync/content", "/Marti/sync/upload", "/sync/upload"):
            try:
                upload_datapackage_from_request(self, qs)
            except Exception as exc:
                print(f"TAKlite PUT {path} failed: {exc}", flush=True)
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        match = re.match(r"^/(?:Marti/)?api/sync/metadata/([^/]+)/tool$", path)
        if not match:
            self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        hash_value = unquote(match.group(1))
        length = int(self.headers.get("Content-Length", "0") or "0")
        tool = self.rfile.read(length).decode("utf-8", "replace").strip() or "public"
        visibility = tool.lower() if tool.lower() in ("public", "private") else None
        with db_connect() as conn:
            if visibility:
                conn.execute("update datapackages set Tool = ?, Visibility = ? where Hash = ?", (tool, visibility, hash_value))
            else:
                conn.execute("update datapackages set Tool = ? where Hash = ?", (tool, hash_value))
            conn.commit()
        self.send_text("OK")


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TAKlite</title>
<style>
body{margin:0;font-family:system-ui,-apple-system,Segoe UI,sans-serif;background:#f6f7f4;color:#1d231f}
header{box-sizing:border-box;width:100%;background:#17201b;color:white;padding:18px 24px;display:flex;gap:16px;justify-content:space-between;align-items:center}
h1{font-size:20px;margin:0;white-space:nowrap}#health{min-width:0;text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.wrap{box-sizing:border-box;max-width:1180px;margin:0 auto;padding:20px 24px}
button,input{font:inherit;border:1px solid #b9c0ba;border-radius:6px;padding:8px 10px}
button{background:#315c46;color:white;border-color:#315c46;cursor:pointer}button.secondary{background:#eef1ec;color:#1d231f;border-color:#b9c0ba}.danger{background:#8d2d28;border-color:#8d2d28}
button:disabled{opacity:.55;cursor:not-allowed}.grid{display:grid;grid-template-columns:1fr;gap:22px}.section{min-width:0}h2{font-size:16px;margin:18px 0 10px}
table{width:100%;border-collapse:collapse;background:white;border:1px solid #d8ddd8}th,td{text-align:left;padding:9px;border-bottom:1px solid #e6e9e4;font-size:14px;vertical-align:top}
th{background:#eef1ec}code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;word-break:break-all}.muted{color:#66736a}.bar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}.status{min-height:24px;margin:10px 0}.actions{display:flex;gap:7px;flex-wrap:wrap}.empty{padding:14px;background:white;border:1px solid #d8ddd8}.nowrap{white-space:nowrap}.auth{max-width:520px;background:white;border:1px solid #d8ddd8;padding:18px}.auth input,.create input{box-sizing:border-box;width:100%;margin:5px 0 10px}.create{display:grid;grid-template-columns:minmax(170px,240px) 1fr auto;gap:8px;align-items:end}.tag{display:inline-block;padding:2px 7px;border-radius:999px;background:#eef1ec}.revoked{background:#f4d9d7;color:#69201b}
@media(max-width:760px){.create{grid-template-columns:1fr}.wrap{padding:16px 14px}table{display:block;overflow-x:auto;white-space:nowrap}}
</style>
</head>
<body><header><h1>TAKlite</h1><span id="health">checking</span></header>
<main class="wrap"><div id="toolbar" class="bar"></div><div id="status" class="status"></div><div id="content" class="grid">Loading...</div></main>
<script>
const toolbar=document.getElementById('toolbar'),statusEl=document.getElementById('status'),content=document.getElementById('content'),healthEl=document.getElementById('health');
let session=localStorage.getItem('takliteSession')||'';
function headers(extra={}){let h={'Content-Type':'application/json',...extra};if(session)h['X-Session-Token']=session;return h}
async function api(p,o={}){const r=await fetch(p,{...o,headers:{...headers(),...(o.headers||{})}});const b=await r.json();if(!r.ok)throw new Error(b.error||r.statusText);return b}
function esc(s){return String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
function fmtBytes(n){n=Number(n)||0;if(n<1024)return `${n} B`;if(n<1048576)return `${(n/1024).toFixed(1)} KB`;return `${(n/1048576).toFixed(1)} MB`}
function fmtTime(s){if(!s)return '<span class="muted">never</span>';return esc(new Date(s).toLocaleString())}
function fmtUptime(s){if(!s)return '';let ms=Date.now()-new Date(s).getTime();if(!Number.isFinite(ms)||ms<0)ms=0;let sec=Math.floor(ms/1000),h=Math.floor(sec/3600),m=Math.floor((sec%3600)/60);if(h)return `${h}h ${m}m`;if(m)return `${m}m ${sec%60}s`;return `${sec}s`}
async function init(){try{const s=await fetch('/api/bootstrap/status').then(r=>r.json());if(!session){renderAuth(s);return}await load()}catch(e){content.textContent=e.message;statusEl.textContent='Unable to initialize.'}}
function renderAuth(s){toolbar.innerHTML='';healthEl.textContent='login required';statusEl.textContent=s.has_admin?'Sign in to manage TAKlite.':'Create the first admin account with the install token.';content.innerHTML=s.has_admin?loginHtml():setupHtml();bindAuth()}
function loginHtml(){return `<section class="auth"><h2>Admin Login</h2><input id="loginUser" autocomplete="username" placeholder="Username"><input id="loginPass" autocomplete="current-password" type="password" placeholder="Password"><button id="loginBtn">Log In</button></section>`}
function setupHtml(){return `<section class="auth"><h2>First Admin Setup</h2><input id="setupToken" type="password" placeholder="Install token"><input id="setupUser" autocomplete="username" placeholder="Username"><input id="setupPass" autocomplete="new-password" type="password" placeholder="Password"><button id="setupBtn">Create Admin</button></section>`}
function bindAuth(){const login=document.getElementById('loginBtn');if(login)login.onclick=async()=>{try{const b=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:document.getElementById('loginUser').value,password:document.getElementById('loginPass').value})}).then(async r=>{const b=await r.json();if(!r.ok)throw new Error(b.error||r.statusText);return b});session=b.session;localStorage.setItem('takliteSession',session);await load()}catch(e){statusEl.textContent=e.message}};const setup=document.getElementById('setupBtn');if(setup)setup.onclick=async()=>{try{const b=await fetch('/api/bootstrap/admin',{method:'POST',headers:{'Content-Type':'application/json','X-Admin-Token':document.getElementById('setupToken').value},body:JSON.stringify({username:document.getElementById('setupUser').value,password:document.getElementById('setupPass').value})}).then(async r=>{const b=await r.json();if(!r.ok)throw new Error(b.error||r.statusText);return b});session=b.session;localStorage.setItem('takliteSession',session);await load()}catch(e){statusEl.textContent=e.message}}}
async function load(){try{toolbar.innerHTML='<button id="refresh">Refresh</button><button id="logout" class="secondary">Log Out</button>';document.getElementById('refresh').onclick=load;document.getElementById('logout').onclick=logout;const health=await fetch('/api/health').then(r=>r.json());healthEl.textContent=`${health.clients} clients, ${health.packages} packages`;const [packages,clients,profiles,portal]=await Promise.all([api('/api/datapackages'),api('/api/clients'),api('/api/cert-profiles'),api('/api/portal-users')]);render(packages.items||[],clients.items||[],portal.items||[],portal.portal_url);statusEl.textContent=`Loaded ${(clients.items||[]).length} client(s), ${(packages.items||[]).length} package(s), ${(portal.items||[]).length} portal user(s).`}catch(e){if(String(e.message).includes('unauthorized')){session='';localStorage.removeItem('takliteSession');init();return}content.textContent=e.message;statusEl.textContent='Unable to load.'}}
function render(packages,clients,portalUsers,portalUrl){content.innerHTML=`<section class="section"><h2>Connected Clients</h2>${clientTable(clients)}</section><section class="section"><h2>Datapackages</h2>${packageTable(packages)}</section><section class="section"><h2>Connection Users</h2>${portalCreate()}${portalTable(portalUsers,portalUrl)}</section>`;bindActions()}
function clientTable(items){if(!items.length)return '<div class="empty">No connected clients.</div>';let rows=items.map(x=>`<tr><td>${esc(x.callsign||'Unknown')}</td><td><code>${esc(x.uid||'')}</code></td><td class="nowrap">${esc(x.ip||'')}</td><td>${esc(x.transport||'tcp')}</td><td>${esc(x.peer_cert_cn||'')}</td><td class="nowrap">${fmtUptime(x.connected_at)}</td><td>${fmtTime(x.connected_at)}</td><td>${fmtTime(x.last_seen)}</td></tr>`).join('');return `<table><thead><tr><th>Name</th><th>UID</th><th>IP</th><th>Mode</th><th>Client Cert</th><th>Uptime</th><th>Connected</th><th>Last Seen</th></tr></thead><tbody>${rows}</tbody></table>`}
function packageTable(items){if(!items.length)return '<div class="empty">No datapackages yet.</div>';let rows=items.map(x=>`<tr><td>${esc(x.Name)}</td><td><code>${esc(x.Hash)}</code></td><td class="nowrap">${fmtBytes(x.Size)}</td><td>${esc(x.Tool||'')}</td><td>${fmtTime(x.SubmissionDateTime)}</td><td>${esc(x.CreatorUid)}</td><td><div class="actions"><a href="/Marti/sync/content?hash=${encodeURIComponent(x.Hash)}" download="${esc(x.Name)}"><button class="secondary" type="button">Download</button></a><button class="danger" data-hash="${esc(x.Hash)}">Delete</button></div></td></tr>`).join('');return `<table><thead><tr><th>Name</th><th>Hash</th><th>Size</th><th>Tool</th><th>Submitted</th><th>Creator</th><th>Action</th></tr></thead><tbody>${rows}</tbody></table>`}
function profileCreate(){return `<div class="create"><label>Name<input id="profileName" placeholder="e.g. alpha-phone"></label><label>Description<input id="profileDesc" placeholder="Optional note"></label><button id="createProfile">Create DP.zip</button></div>`}
function portalCreate(){return `<div class="create"><label>Username<input id="portalUser" autocomplete="off" placeholder="e.g. alpha-phone"></label><label>Password<input id="portalPass" autocomplete="new-password" type="password" placeholder="User download password"></label><label>Description<input id="portalDesc" placeholder="Optional note"></label><label><input id="portalRedownload" type="checkbox" style="width:auto;margin-right:6px">Allow re-download</label><button id="createPortal">Create User</button></div>`}
function publicUrl(x){return `${location.origin}${x.public_download_path||''}`}
function portalAbs(path){return `${location.origin}${path||'/connect/'}`}
function portalTable(items,portalUrl){let hint=`<p class="muted">Client portal: <code>${esc(portalUrl||portalAbs('/connect/'))}</code></p>`;if(!items.length)return hint+'<div class="empty">No connection users yet.</div>';let rows=items.map(x=>{let url=portalAbs(x.portal_path);return `<tr><td>${esc(x.username)}<br><span class="muted">${esc(x.display_name||'')}</span><br><span class="muted">${esc(x.description||'')}</span></td><td>${x.revoked?'<span class="tag revoked">revoked</span>':'<span class="tag">active</span>'}</td><td><code>${esc(url)}</code><br><code>${esc(x.connect_string||'')}</code></td><td>${x.download_count||0}<br><span class="muted">first ${fmtTime(x.first_download_at)}</span><br><span class="muted">last ${fmtTime(x.last_download_at)}</span></td><td>${x.allow_redownload?'yes':'no'}</td><td><div class="actions"><button class="secondary" data-download-profile="${x.cert_profile_id}" ${x.revoked?'disabled':''}>Download DP.zip</button><button class="secondary" data-copy-url="${esc(url)}" ${x.revoked?'disabled':''}>Copy URL</button><button class="secondary" data-qr-user="${x.id}" ${x.revoked?'disabled':''}>QR</button><button class="secondary" data-edit-user="${x.id}" data-display="${esc(x.display_name||'')}" data-description="${esc(x.description||'')}" ${x.revoked?'disabled':''}>Edit</button><button class="secondary" data-reset-user="${x.id}" ${x.revoked?'disabled':''}>Reset Password</button><button class="secondary" data-toggle-redownload="${x.id}" data-allow="${x.allow_redownload?'0':'1'}" ${x.revoked?'disabled':''}>${x.allow_redownload?'Disable':'Allow'} Re-download</button><button data-reissue-user="${x.id}">Reissue</button><button class="danger" data-revoke-user="${x.id}" ${x.revoked?'disabled':''}>Revoke</button><button class="danger" data-delete-user="${x.id}">Delete</button></div></td></tr>`}).join('');return hint+`<table><thead><tr><th>User</th><th>Status</th><th>Portal / Connection</th><th>Downloads</th><th>Re-download</th><th>Action</th></tr></thead><tbody>${rows}</tbody></table>`}
function profileTable(items,certPassword){let hint=`<p class="muted">Certificate password: <code>${esc(certPassword||'')}</code></p>`;if(!items.length)return hint+'<div class="empty">No connection packages yet.</div>';let rows=items.map(x=>{let url=publicUrl(x);return `<tr><td>${esc(x.name)}</td><td>${x.revoked?'<span class="tag revoked">revoked</span>':'<span class="tag">active</span>'}</td><td><code>${esc(x.connect_string)}</code><br><code>${esc(url)}</code></td><td>${esc(x.description)}</td><td>${fmtTime(x.created_at)}</td><td><div class="actions"><button class="secondary" data-download-profile="${x.id}" ${x.revoked?'disabled':''}>Download DP.zip</button><button class="secondary" data-copy-url="${esc(url)}" ${x.revoked?'disabled':''}>Copy URL</button><button data-revoke-profile="${x.id}" ${x.revoked?'disabled':''}>Revoke</button><button class="danger" data-delete-profile="${x.id}">Delete</button></div></td></tr>`}).join('');return hint+`<table><thead><tr><th>Name</th><th>Status</th><th>Connection / URL</th><th>Description</th><th>Created</th><th>Action</th></tr></thead><tbody>${rows}</tbody></table>`}
function bindActions(){const create=document.getElementById('createProfile');if(create)create.onclick=async()=>{try{await api('/api/cert-profiles/create',{method:'POST',body:JSON.stringify({name:document.getElementById('profileName').value,description:document.getElementById('profileDesc').value})});statusEl.textContent='Connection package created.';await load()}catch(e){statusEl.textContent=e.message}};const createPortal=document.getElementById('createPortal');if(createPortal)createPortal.onclick=async()=>{try{let user=document.getElementById('portalUser').value;await api('/api/portal-users/create',{method:'POST',body:JSON.stringify({username:user,password:document.getElementById('portalPass').value,description:document.getElementById('portalDesc').value,allow_redownload:document.getElementById('portalRedownload').checked})});statusEl.textContent=`Connection user ${user} created.`;await load()}catch(e){statusEl.textContent=e.message}};content.querySelectorAll('button[data-hash]').forEach(btn=>btn.onclick=async()=>{if(!confirm('Delete this datapackage from TAKlite?'))return;await api('/api/datapackages/delete',{method:'POST',body:JSON.stringify({hash:btn.dataset.hash,delete_file:true})});await load();});content.querySelectorAll('button[data-revoke-profile]').forEach(btn=>btn.onclick=async()=>{if(!confirm('Revoke this connection package?'))return;await api('/api/cert-profiles/revoke',{method:'POST',body:JSON.stringify({id:btn.dataset.revokeProfile})});await load()});content.querySelectorAll('button[data-delete-profile]').forEach(btn=>btn.onclick=async()=>{if(!confirm('Delete this connection package and generated files?'))return;await api('/api/cert-profiles/delete',{method:'POST',body:JSON.stringify({id:btn.dataset.deleteProfile,delete_files:true})});await load()});content.querySelectorAll('button[data-download-profile]').forEach(btn=>btn.onclick=()=>downloadProfile(btn.dataset.downloadProfile));content.querySelectorAll('button[data-copy-url]').forEach(btn=>btn.onclick=async()=>{await navigator.clipboard.writeText(btn.dataset.copyUrl);statusEl.textContent='URL copied.'});content.querySelectorAll('button[data-qr-user]').forEach(btn=>btn.onclick=()=>showQr(btn.dataset.qrUser));content.querySelectorAll('button[data-edit-user]').forEach(btn=>btn.onclick=async()=>{let display=prompt('Display name',btn.dataset.display||'');if(display===null)return;let description=prompt('Description / note',btn.dataset.description||'');if(description===null)return;await api('/api/portal-users/edit',{method:'POST',body:JSON.stringify({id:btn.dataset.editUser,display_name:display,description})});await load()});content.querySelectorAll('button[data-reset-user]').forEach(btn=>btn.onclick=async()=>{let password=prompt('New portal password, at least 8 characters');if(!password)return;await api('/api/portal-users/reset-password',{method:'POST',body:JSON.stringify({id:btn.dataset.resetUser,password})});await load()});content.querySelectorAll('button[data-toggle-redownload]').forEach(btn=>btn.onclick=async()=>{await api('/api/portal-users/redownload',{method:'POST',body:JSON.stringify({id:btn.dataset.toggleRedownload,allow_redownload:btn.dataset.allow==='1'})});await load()});content.querySelectorAll('button[data-reissue-user]').forEach(btn=>btn.onclick=async()=>{if(!confirm('Reissue this user with a new certificate package? Old package will be revoked.'))return;await api('/api/portal-users/reissue',{method:'POST',body:JSON.stringify({id:btn.dataset.reissueUser})});await load()});content.querySelectorAll('button[data-revoke-user]').forEach(btn=>btn.onclick=async()=>{if(!confirm('Revoke this user and their certificate package?'))return;await api('/api/portal-users/revoke',{method:'POST',body:JSON.stringify({id:btn.dataset.revokeUser})});await load()});content.querySelectorAll('button[data-delete-user]').forEach(btn=>btn.onclick=async()=>{if(!confirm('Delete this user? Choose OK again to also delete their generated certificate package files.'))return;let deleteProfile=confirm('Delete generated DP.zip/certificate package files too?');await api('/api/portal-users/delete',{method:'POST',body:JSON.stringify({id:btn.dataset.deleteUser,delete_profile:deleteProfile})});await load()})}
async function downloadProfile(id){const r=await fetch(`/api/cert-profiles/download?id=${encodeURIComponent(id)}`,{headers:headers({})});if(!r.ok){let b=await r.json().catch(()=>({error:r.statusText}));throw new Error(b.error||r.statusText)}let blob=await r.blob();let name=(r.headers.get('Content-Disposition')||'').match(/filename="([^"]+)"/)?.[1]||'taklite-connection.dp.zip';let a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
async function showQr(id){const r=await fetch(`/api/portal-users/qr?id=${encodeURIComponent(id)}`,{headers:headers({})});if(!r.ok){let b=await r.json().catch(()=>({error:r.statusText}));throw new Error(b.error||r.statusText)}let blob=await r.blob();let url=URL.createObjectURL(blob);let w=window.open('','takliteQr','width=420,height=460');w.document.write(`<title>TAKlite QR</title><body style="font-family:system-ui;text-align:center;padding:20px"><img src="${url}" style="width:320px;height:320px"><p>Scan after VPN is connected.</p></body>`)}
async function logout(){try{await api('/api/logout',{method:'POST',body:'{}'})}catch(e){}session='';localStorage.removeItem('takliteSession');init()}
init();
setInterval(load,15000);
</script></body></html>"""


def enrollment_connect_html(base_url, code):
    base = (base_url or "").strip().rstrip("/")
    code = (code or "").strip()
    join_url = f"{base}/connect/enroll?code={quote(code)}" if base and code else ""
    axon_url = f"axon://field-enroll?server={quote(base)}&code={quote(code)}" if base and code else ""
    safe_base = html.escape(base)
    safe_code = html.escape(code)
    safe_join_url = html.escape(join_url)
    safe_axon_url = html.escape(axon_url)
    qr_markup = ""
    if join_url:
        result = subprocess.run(["qrencode", "-t", "SVG", "-o", "-", join_url], capture_output=True)
        if result.returncode == 0:
            qr_markup = result.stdout.decode("utf-8", "replace")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Axon Field Enrollment</title>
<style>
body{{margin:0;font-family:system-ui,-apple-system,Segoe UI,sans-serif;background:#09100d;color:#e5ece6}}
header{{background:#0d1712;border-bottom:1px solid rgba(190,214,197,.14);padding:18px 22px}}h1{{font-size:20px;margin:0}}
.wrap{{max-width:620px;margin:0 auto;padding:26px 18px}}.panel{{background:#111d17;border:1px solid rgba(190,214,197,.14);border-radius:12px;padding:18px}}
p{{color:#92a197;line-height:1.45}}label{{display:block;margin-top:16px;color:#92a197;font-size:12px;font-weight:800;text-transform:uppercase}}
code{{display:block;margin-top:6px;padding:12px;border:1px solid rgba(190,214,197,.14);border-radius:10px;background:#09100d;color:#e5ece6;word-break:break-all}}
.qr{{display:flex;justify-content:center;margin:18px 0;padding:14px;background:#f8fbf8;border-radius:14px}}.qr svg{{width:min(72vw,320px);height:auto;display:block}}
a.button{{display:block;margin:18px 0 6px;padding:14px 16px;border-radius:10px;background:#4fb477;color:#07100b;text-decoration:none;text-align:center;font-weight:900}}
</style>
</head>
<body><header><h1>Axon Field Enrollment</h1></header><main class="wrap"><section class="panel">
{f'<div class="qr">{qr_markup}</div>' if qr_markup else ''}
<p>Tap <strong>Open in Axon</strong> on the new device to redeem this pass. If the button is unavailable, open Axon inside ATAK, then go to <strong>Settings -> Profile -> Field Enrollment</strong> and enter the server URL and Join Code below.</p>
{f'<a class="button" href="{safe_axon_url}">Open in Axon</a>' if axon_url else ''}
<label>Server URL</label><code>{safe_base}</code>
<label>Join Code</label><code>{safe_code}</code>
<label>Enrollment URL</label><code>{safe_join_url}</code>
<label>Axon Link</label><code>{safe_axon_url}</code>
<p>This pass may expire or run out of uses. If it fails, ask an admin to create a new Field Enrollment pass.</p>
</section></main></body></html>"""


CONNECT_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TAKlite Connect</title>
<style>
body{margin:0;font-family:system-ui,-apple-system,Segoe UI,sans-serif;background:#f6f7f4;color:#1d231f}
header{background:#17201b;color:white;padding:18px 22px}h1{font-size:20px;margin:0}.wrap{max-width:520px;margin:0 auto;padding:26px 18px}
.panel{background:white;border:1px solid #d8ddd8;border-radius:8px;padding:18px}h2{font-size:18px;margin:0 0 12px}
label{display:block;font-weight:600;margin:12px 0 4px}input,button{box-sizing:border-box;width:100%;font:inherit;border:1px solid #b9c0ba;border-radius:6px;padding:10px}
button{margin-top:14px;background:#315c46;color:white;border-color:#315c46;cursor:pointer}.secondary{background:#eef1ec;color:#1d231f;border-color:#b9c0ba}
.status{min-height:24px;margin:14px 0;color:#455349}.muted{color:#66736a}code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;word-break:break-all}
</style>
</head>
<body><header><h1>TAKlite Connect</h1></header><main class="wrap"><div id="status" class="status"></div><section id="content" class="panel"></section></main>
<script>
const statusEl=document.getElementById('status'),content=document.getElementById('content');
let portalSession=localStorage.getItem('taklitePortalSession')||'';
function esc(s){return String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
function initialUser(){return new URLSearchParams(location.search).get('u')||''}
function portalHeaders(extra={}){let h={'Content-Type':'application/json',...extra};if(portalSession)h['X-Portal-Token']=portalSession;return h}
async function portalApi(p,o={}){const r=await fetch(p,{...o,headers:{...portalHeaders(),...(o.headers||{})}});const b=await r.json();if(!r.ok)throw new Error(b.error||r.statusText);return b}
function renderLogin(){content.innerHTML=`<h2>Download Connection Package</h2><p class="muted">Sign in after WireGuard VPN is connected.</p><label>Username</label><input id="u" autocomplete="username" value="${esc(initialUser())}"><label>Password</label><input id="p" autocomplete="current-password" type="password"><button id="login">Log In</button>`;document.getElementById('login').onclick=login}
async function login(){try{const b=await portalApi('/api/connect/login',{method:'POST',body:JSON.stringify({username:document.getElementById('u').value,password:document.getElementById('p').value})});portalSession=b.session;localStorage.setItem('taklitePortalSession',portalSession);renderUser(b.user,b.cert_password)}catch(e){statusEl.textContent=e.message}}
function renderUser(user,certPassword){let blocked=user.first_download_at&&!user.allow_redownload;content.innerHTML=`<h2>${esc(user.display_name||user.username)}</h2><p class="muted">Connection: <code>${esc(user.connect_string)}</code></p><p class="muted">Certificate password: <code>${esc(certPassword||'')}</code></p><p class="muted">The Connection Package configures ATAK/WinTAK and includes the Axon profile. Use the profile-only download only when Axon needs to be refreshed after support tells you to.</p>${blocked?'<p>This package was already downloaded. Contact your TAKlite admin to allow another download or reissue your package.</p>':'<button id="download">Download DP.zip</button><button id="downloadProfile" class="secondary">Download Axon Profile Only</button>'}<button id="logout" class="secondary">Log Out</button>`;let dl=document.getElementById('download');if(dl)dl.onclick=download;let profile=document.getElementById('downloadProfile');if(profile)profile.onclick=downloadProfile;document.getElementById('logout').onclick=logout;statusEl.textContent='Ready.'}
async function download(){try{const r=await fetch('/api/connect/download',{headers:{'X-Portal-Token':portalSession}});if(!r.ok){let b=await r.json().catch(()=>({error:r.statusText}));throw new Error(b.error||r.statusText)}let blob=await r.blob();let name=(r.headers.get('Content-Disposition')||'').match(/filename="([^"]+)"/)?.[1]||'taklite-connection.dp.zip';let a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1000);statusEl.textContent='Downloaded. Import the DP.zip in ATAK or WinTAK.';setTimeout(check,1000)}catch(e){statusEl.textContent=e.message}}
async function downloadProfile(){try{const r=await fetch('/api/connect/profile',{headers:{'X-Portal-Token':portalSession}});if(!r.ok){let b=await r.json().catch(()=>({error:r.statusText}));throw new Error(b.error||r.statusText)}let blob=await r.blob();let name=(r.headers.get('Content-Disposition')||'').match(/filename="([^"]+)"/)?.[1]||'axon-profile.json';let a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1000);statusEl.textContent='Downloaded Axon profile. Place/import it where Axon can read it, then tap Load Axon Profile.'}catch(e){statusEl.textContent=e.message}}
async function logout(){try{await portalApi('/api/connect/logout',{method:'POST',body:'{}'})}catch(e){}portalSession='';localStorage.removeItem('taklitePortalSession');renderLogin()}
async function check(){if(!portalSession){renderLogin();return}try{const b=await portalApi('/api/connect/me');renderUser(b.user,b.cert_password)}catch(e){portalSession='';localStorage.removeItem('taklitePortalSession');renderLogin()}}
check();
</script></body></html>"""


def main():
    if not CERT_PASSWORD:
        raise RuntimeError("TAKLITE_CERT_PASSWORD is required")
    if AUTO_INIT_CERTS:
        ensure_base_certs()
    init_db()
    cot_server = CotServer((COT_BIND, COT_PORT), CotHandler, "tcp")
    http_server = ThreadingHTTPServer((HTTP_BIND, HTTP_PORT), HttpHandler)
    threading.Thread(target=cot_server.serve_forever, daemon=True).start()
    threading.Thread(target=heartbeat_loop, daemon=True).start()
    if HTTPS_CERT.exists() and HTTPS_KEY.exists():
        cot_tls_context = server_tls_context(request_client_cert=True)
        https_context = server_tls_context(request_client_cert=True)
        cot_tls_server = CotServer((COT_TLS_BIND, COT_TLS_PORT), CotHandler, "tls")
        cot_tls_server.socket = cot_tls_context.wrap_socket(cot_tls_server.socket, server_side=True)
        threading.Thread(target=cot_tls_server.serve_forever, daemon=True).start()
        https_server = ThreadingHTTPServer((HTTPS_BIND, HTTPS_PORT), HttpHandler)
        https_server.socket = https_context.wrap_socket(https_server.socket, server_side=True)
        threading.Thread(target=https_server.serve_forever, daemon=True).start()
        if CLIENT_CA.exists():
            client_cert_mode = "client cert required/verified" if COT_TLS_REQUIRE_CLIENT_CERT else "client cert optional/verified"
        else:
            client_cert_mode = "client cert required; CA missing" if COT_TLS_REQUIRE_CLIENT_CERT else "client cert not verified; CA missing"
        print(f"TAKlite TLS CoT listening on {COT_TLS_BIND}:{COT_TLS_PORT} ({client_cert_mode})")
        print(f"TAKlite HTTPS/Marti listening on {HTTPS_BIND}:{HTTPS_PORT}")
    else:
        print(f"TAKlite HTTPS disabled; missing {HTTPS_CERT} or {HTTPS_KEY}")
    print(f"TAKlite CoT listening on {COT_BIND}:{COT_PORT}")
    print(f"TAKlite HTTP/Marti/Admin listening on {HTTP_BIND}:{HTTP_PORT}")
    http_server.serve_forever()


if __name__ == "__main__":
    main()
