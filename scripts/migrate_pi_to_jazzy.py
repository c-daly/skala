#!/usr/bin/env python3
"""Move a Pi 4 from Ubuntu Jammy/Humble to Noble/native Jazzy.

Run `python3 migrate_pi_to_jazzy.py check`, then run with sudo and `migrate`.
Rerun `migrate` after each requested reboot. A fresh Noble install skips the
Ubuntu release upgrade. Requires only Python's standard library (Python 3.10+).

Package removals, full upgrades and do-release-upgrade remain interactive.
Configuration backups are NOT a whole-card image or a backup of workspaces.
Keep important files off the card and disconnect drive power before starting.

Sources, checked 2026-11-22:
https://ubuntu.com/server/docs/how-to/software/upgrade-your-release/
https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html
https://github.com/ros-infrastructure/ros-apt-source
"""

import argparse
import datetime
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tarfile
import tempfile
from urllib.parse import urlparse


class MigrationError(RuntimeError):
    pass


def os_release(path):
    values = {}
    for line in path.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            fields = shlex.split(value)
            values[key] = fields[0] if fields else ""
    return values


def ros_uri(uri):
    parsed = urlparse(uri)
    return (
        parsed.hostname == "packages.ros.org"
        and parsed.path.rstrip("/") in ("/ros2/ubuntu", "/ros2-testing/ubuntu")
    ) or (parsed.hostname == "snapshots.ros.org" and parsed.path.startswith("/humble/"))


def disable_ros_entries(text, suffix):
    """Disable only ROS 2 source entries; keep other repositories intact."""
    if suffix == ".list":
        lines = []
        for line in text.splitlines(keepends=True):
            active = line.lstrip()
            if re.match(r"deb(?:-src)?\s", active):
                uris = re.findall(r"https?://[^\s]+", active.split("#", 1)[0])
                if any(ros_uri(uri) for uri in uris):
                    line = "# Disabled by Skala ROS migration: " + line
            lines.append(line)
        return "".join(lines)

    chunks = re.split(r"(\n[ \t]*\n)", text)
    for index in range(0, len(chunks), 2):
        stanza = chunks[index]
        fields = {}
        key = None
        for line in stanza.splitlines():
            if line.lstrip().startswith("#"):
                continue
            if line[:1].isspace() and key:
                fields[key] += " " + line.strip()
            elif ":" in line:
                key, value = line.split(":", 1)
                key = key.lower()
                fields[key] = value.strip()
        uris = fields.get("uris", "").split()
        if not any(ros_uri(uri) for uri in uris):
            continue
        if not all(ros_uri(uri) for uri in uris):
            raise MigrationError("A .sources stanza mixes ROS and other URIs; split it before migrating.")
        if re.search(r"^Enabled:", stanza, re.M | re.I):
            stanza = re.sub(r"^Enabled:.*$", "Enabled: no", stanza, flags=re.M | re.I)
        else:
            stanza = stanza.rstrip("\n") + "\nEnabled: no\n"
        chunks[index] = stanza
    return "".join(chunks)


def lts_prompt(text):
    if re.search(r"^\s*Prompt\s*=", text, re.M):
        return re.sub(r"^\s*Prompt\s*=.*$", "Prompt=lts", text, flags=re.M)
    return text.rstrip() + "\nPrompt=lts\n"


class Migration:
    def __init__(self, root=Path("/"), runner=subprocess.run):
        self.root = root
        self.runner = runner
        self.backup = None

    def path(self, name):
        return self.root / name.lstrip("/")

    def run(self, *args, capture=False):
        print("+ " + shlex.join(args), flush=True)
        if self.backup:
            with (self.backup / "commands.log").open("a") as log:
                log.write(shlex.join(args) + "\n")
        result = self.runner(list(args), check=True, text=True, capture_output=capture)
        return result.stdout if capture else ""

    def preflight(self):
        release = os_release(self.path("/etc/os-release"))
        version = release.get("VERSION_ID")
        codename = release.get("UBUNTU_CODENAME", release.get("VERSION_CODENAME"))
        if release.get("ID") != "ubuntu" or (version, codename) not in (
            ("22.04", "jammy"), ("24.04", "noble")
        ):
            raise MigrationError("This script accepts only Ubuntu 22.04 Jammy or 24.04 Noble.")
        model = self.path("/proc/device-tree/model")
        if not model.exists() or "Raspberry Pi 4 Model B" not in model.read_text().strip("\0\n"):
            raise MigrationError("This is not a Raspberry Pi 4B. No changes made.")
        if self.run("dpkg", "--print-architecture", capture=True).strip() != "arm64":
            raise MigrationError("64-bit arm64 userspace is required; armhf cannot upgrade to Noble.")
        if self.run("dpkg", "--audit", capture=True).strip():
            raise MigrationError("dpkg reports incomplete package operations; repair them first.")
        held = self.run("apt-mark", "showhold", capture=True).strip()
        if held:
            raise MigrationError("Review held packages before migrating:\n" + held)
        self.source_changes()  # Validate mixed source stanzas before any mutation.
        print(f"Detected Ubuntu {version} ({codename}) on Raspberry Pi 4B, arm64.")
        self.run("df", "-h", "/", "/boot/firmware")
        return codename

    def source_changes(self):
        paths = [self.path("/etc/apt/sources.list")]
        directory = self.path("/etc/apt/sources.list.d")
        paths += sorted(directory.glob("*.list")) + sorted(directory.glob("*.sources"))
        changes = []
        for path in paths:
            if path.is_file():
                original = path.read_text()
                updated = disable_ros_entries(original, path.suffix)
                if updated != original:
                    changes.append((path, updated))
        return changes

    def packages(self):
        output = self.run(
            "dpkg-query", "-W", "-f=${binary:Package}\t${db:Status-Status}\t${Version}\n",
            capture=True,
        )
        installed = []
        for line in output.splitlines():
            name, status, _version = line.split("\t", 2)
            if status == "installed":
                installed.append(name)
        return output, installed

    def make_backup(self):
        base = self.path("/var/backups/skala-jazzy")
        base.mkdir(parents=True, exist_ok=True, mode=0o700)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ-")
        self.backup = Path(tempfile.mkdtemp(prefix=stamp, dir=base))
        package_text, _ = self.packages()
        (self.backup / "packages.tsv").write_text(package_text)
        (self.backup / "manual-packages.txt").write_text(
            self.run("apt-mark", "showmanual", capture=True)
        )
        # Preserve links (including dangling units and /dev/null masks). Following
        # them can fail on missing targets and changes systemd configuration semantics.
        with tarfile.open(self.backup / "configuration.tar.gz", "w:gz", dereference=False) as archive:
            for name in (
                "etc/apt", "etc/update-manager", "etc/default/locale", "etc/udev/rules.d",
                "etc/netplan", "etc/systemd/system", "boot/firmware/config.txt",
                "boot/firmware/cmdline.txt", "etc/os-release",
            ):
                path = self.path(name)
                if path.exists() or path.is_symlink():
                    archive.add(path, arcname=name)
        print(f"Configuration/package backup: {self.backup}")
        print("This backup does not include your files/workspaces or provide whole-card rollback.")

    def remove_legacy_ros(self):
        _, installed = self.packages()
        old = [name for name in installed if name.split(":")[0].startswith("ros-humble-")
               or name.split(":")[0] == "ros2-apt-source"]
        if old:
            # Deliberately keep APT's removal review and never run autoremove.
            self.run("apt-get", "remove", *old)
        # Re-read after removing ros2-apt-source: it may own/delete a source file.
        for path, updated in self.source_changes():
            path.write_text(updated)
            print(f"Disabled old ROS repository entries in {path}")

    def reboot_needed(self):
        return self.path("/run/reboot-required").exists()

    @staticmethod
    def reboot_message():
        print("REBOOT REQUIRED: run sudo reboot, reconnect, then rerun this script with migrate.")

    def upgrade_jammy(self):
        self.run("apt-get", "update")
        self.run("apt-get", "dist-upgrade", "-o", "APT::Get::Always-Include-Phased-Updates=true")
        self.run("apt-get", "install", "-y", "update-manager-core")
        if self.reboot_needed():
            self.reboot_message()
            return
        settings = self.path("/etc/update-manager/release-upgrades")
        settings.write_text(lts_prompt(settings.read_text()))
        print("Accept only Ubuntu 24.04 LTS (Noble). Review Ubuntu's prompts; do not select another target.")
        # Keep the release upgrader on the user's terminal; never force -d or unattended mode.
        self.run("do-release-upgrade")
        release = os_release(self.path("/etc/os-release"))
        if release.get("VERSION_ID") != "24.04":
            raise MigrationError("Ubuntu did not finish upgrading to 24.04; review /var/log/dist-upgrade.")
        self.reboot_message()

    def install_ros_repository(self):
        latest = self.run(
            "curl", "-fsSL", "--proto", "=https", "--proto-redir", "=https",
            "-o", "/dev/null", "-w", "%{url_effective}",
            "https://github.com/ros-infrastructure/ros-apt-source/releases/latest", capture=True,
        ).strip()
        prefix = "https://github.com/ros-infrastructure/ros-apt-source/releases/tag/"
        if not latest.startswith(prefix):
            raise MigrationError("Could not resolve the official ros-apt-source release.")
        version = latest[len(prefix):]
        if not re.fullmatch(r"[0-9][A-Za-z0-9_.-]*", version):
            raise MigrationError("Unexpected ros-apt-source release version.")
        url = ("https://github.com/ros-infrastructure/ros-apt-source/releases/download/"
               f"{version}/ros2-apt-source_{version}.noble_all.deb")
        with tempfile.TemporaryDirectory(prefix="skala-ros-apt-") as directory:
            deb = str(Path(directory) / "ros2-apt-source.deb")
            self.run("curl", "-fSL", "--proto", "=https", "--proto-redir", "=https", "-o", deb, url)
            package = self.run("dpkg-deb", "-f", deb, "Package", capture=True).strip()
            arch = self.run("dpkg-deb", "-f", deb, "Architecture", capture=True).strip()
            if package != "ros2-apt-source" or arch != "all":
                raise MigrationError("Downloaded package metadata does not match ros2-apt-source.")
            self.run("dpkg", "-i", deb)

    def install_shell(self):
        rc = self.path("/etc/skala/jazzy.bashrc")
        launcher = self.path("/usr/local/bin/skala-jazzy-shell")
        rc.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
        launcher.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
        rc.parent.chmod(0o755)
        rc.write_text("source /opt/ros/jazzy/setup.bash\n"
                      "printf 'Jazzy shell: legacy shell startup files were not loaded.\\n'\n")
        rc.chmod(0o644)
        launcher.write_text("""#!/bin/sh
# Enter Jazzy without sourcing inherited Humble/TurtleBot3 workspace setup files.
exec env -u AMENT_PREFIX_PATH -u CMAKE_PREFIX_PATH -u COLCON_PREFIX_PATH \\
  -u LD_LIBRARY_PATH -u PYTHONPATH -u VIRTUAL_ENV -u CONDA_PREFIX \\
  -u ROS_DISTRO -u ROS_VERSION -u ROS_PYTHON_VERSION -u BASH_ENV -u ENV \\
  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \\
  /bin/bash --noprofile --rcfile /etc/skala/jazzy.bashrc -i
""")
        launcher.chmod(0o755)

    def install_jazzy(self):
        self.run("apt-get", "update")
        self.run("apt-get", "install", "-y", "ca-certificates", "curl", "locales", "software-properties-common")
        self.run("add-apt-repository", "-y", "universe")
        self.run("apt-get", "update")
        self.run("apt-get", "dist-upgrade", "-o", "APT::Get::Always-Include-Phased-Updates=true")
        if self.reboot_needed():
            self.reboot_message()
            return
        if self.run("locale", "charmap", capture=True).strip().upper() != "UTF-8":
            self.run("locale-gen", "en_US.UTF-8")
            self.run("update-locale", "LANG=en_US.UTF-8")
        self.install_ros_repository()
        self.run("apt-get", "update")
        self.run("apt-get", "install", "-y", "ros-jazzy-ros-base", "ros-jazzy-camera-ros",
                 "ros-jazzy-rosbag2", "alsa-utils", "v4l-utils", "git", "build-essential")
        self.install_shell()
        self.run(
            "env", "-u", "AMENT_PREFIX_PATH", "-u", "CMAKE_PREFIX_PATH", "-u", "COLCON_PREFIX_PATH",
            "-u", "LD_LIBRARY_PATH", "-u", "PYTHONPATH", "-u", "ROS_DISTRO", "-u", "ROS_VERSION",
            "-u", "ROS_PYTHON_VERSION", "-u", "BASH_ENV", "-u", "ENV", "LANG=C.UTF-8", "LC_ALL=C.UTF-8",
            "/bin/bash", "--noprofile", "--norc", "-c",
            'set -e; source /opt/ros/jazzy/setup.bash; test "$ROS_DISTRO" = jazzy; '
            'ros2 --help >/dev/null; python3 -c "import rclpy; from sensor_msgs.msg import Image"',
        )
        print("Jazzy installation verified (CLI and Python imports; no hardware test).")
        print("As your normal user, run: skala-jazzy-shell")
        print("Camera libcamera integration, WM8960/A1 drivers and OpenCR firmware remain separate work.")
        print("Existing workspace files and shell startup files were preserved; no TurtleBot3 stack installed.")

    def migrate(self, codename):
        self.make_backup()
        self.remove_legacy_ros()
        if codename == "jammy":
            self.upgrade_jammy()
        elif codename == "noble":
            self.install_jazzy()
        else:
            raise MigrationError("Unexpected release; refusing to migrate.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=("check", "migrate"), nargs="?", default="check")
    args = parser.parse_args()
    # Never run root package commands through a user-supplied search path.
    os.environ["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    os.umask(0o077)
    migration = Migration()
    try:
        codename = migration.preflight()
        if args.action == "check":
            print("Check only: no files or packages changed.")
            print("Next: back up important files off-card; use stable power with drive power disconnected.")
            print("Run with sudo and migrate. Ubuntu/APT prompts remain interactive; rerun after reboots.")
            return 0
        if os.geteuid() != 0:
            raise MigrationError("Run migrate with sudo.")
        if not sys.stdin.isatty():
            raise MigrationError("Run migrate from an interactive terminal for APT and Ubuntu upgrade prompts.")
        migration.migrate(codename)
        return 0
    except (MigrationError, OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"STOPPED: {error}", file=sys.stderr)
        if migration.backup:
            print(f"Backup and command log: {migration.backup}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
