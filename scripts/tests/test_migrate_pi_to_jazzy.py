"""Regression checks for a system-changing script; never invoke real package tools."""

import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "migrate_pi_to_jazzy.py"
SPEC = importlib.util.spec_from_file_location("migration", SCRIPT)
migration = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(migration)


class FakeRunner:
    def __init__(self):
        self.calls = []
        self.responses = {
            ("dpkg", "--print-architecture"): "arm64\n",
            ("dpkg", "--audit"): "",
            ("apt-mark", "showhold"): "",
            ("apt-mark", "showmanual"): "ros-humble-ros-base\n",
            ("locale", "charmap"): "UTF-8\n",
        }
        self.fail = None
        self.effect = None

    def __call__(self, args, **kwargs):
        self.calls.append(tuple(args))
        if self.fail and self.fail(args):
            raise subprocess.CalledProcessError(1, args)
        if self.effect:
            self.effect(args)
        if args[0] == "dpkg-query":
            output = "ros-humble-ros-base\tinstalled\t1.0\nros2-apt-source\tinstalled\t1.0.jammy\n"
            output += "linux-raspi\tinstalled\t5.15\nros-jazzy-ros-base\tinstalled\t1.0\n"
            output += "ros-humble-old\tconfig-files\t1.0\n"
        elif args[0] == "curl" and "%{url_effective}" in args:
            output = "https://github.com/ros-infrastructure/ros-apt-source/releases/tag/1.1.0"
        elif args[0] == "dpkg-deb":
            output = "ros2-apt-source\n" if args[-1] == "Package" else "all\n"
        else:
            output = self.responses.get(tuple(args), "")
        return subprocess.CompletedProcess(args, 0, stdout=output, stderr="")


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.runner = FakeRunner()
        self.subject = migration.Migration(self.root, self.runner)
        self.write("etc/os-release", 'ID=ubuntu\nVERSION_ID="22.04"\nVERSION_CODENAME=jammy\n')
        self.write("proc/device-tree/model", "Raspberry Pi 4 Model B Rev 1.4\0")
        self.write("etc/update-manager/release-upgrades", "[DEFAULT]\nPrompt=normal\n")
        self.stdout = io.StringIO()
        self.redirect = contextlib.redirect_stdout(self.stdout)
        self.redirect.__enter__()
        self.addCleanup(self.redirect.__exit__, None, None, None)

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def test_preflight_rejects_workstation_before_package_operations(self):
        self.subject.path("proc/device-tree/model").unlink()
        with self.assertRaisesRegex(migration.MigrationError, "not a Raspberry Pi"):
            self.subject.preflight()
        self.assertEqual(self.runner.calls, [])
        self.assertFalse(self.subject.path("var/backups").exists())

    def test_preflight_rejects_32bit_and_wrong_os(self):
        self.runner.responses[("dpkg", "--print-architecture")] = "armhf\n"
        with self.assertRaisesRegex(migration.MigrationError, "armhf"):
            self.subject.preflight()
        self.write("etc/os-release", "ID=ubuntu\nVERSION_ID=26.04\nVERSION_CODENAME=resolute\n")
        with self.assertRaisesRegex(migration.MigrationError, "only Ubuntu"):
            self.subject.preflight()
        self.assertFalse(self.subject.path("var/backups").exists())

    def test_preflight_reports_incomplete_and_held_packages(self):
        self.runner.responses[("dpkg", "--audit")] = "broken package\n"
        with self.assertRaisesRegex(migration.MigrationError, "incomplete"):
            self.subject.preflight()
        self.runner.responses[("dpkg", "--audit")] = ""
        self.runner.responses[("apt-mark", "showhold")] = "linux-raspi\n"
        with self.assertRaisesRegex(migration.MigrationError, "linux-raspi"):
            self.subject.preflight()

    def test_check_is_read_only(self):
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(self.subject.preflight(), "jammy")
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertTrue(all(call[0] in ("dpkg", "apt-mark", "df") for call in self.runner.calls))

    def test_mixed_list_preserves_ubuntu_and_comments(self):
        original = ("deb http://ports.ubuntu.com/ubuntu-ports jammy main\n"
                    "deb [signed-by=/key] https://packages.ros.org/ros2/ubuntu jammy main\n"
                    "# deb https://packages.ros.org/ros2/ubuntu jammy main\n")
        output = migration.disable_ros_entries(original, ".list")
        self.assertEqual(output.splitlines()[0], original.splitlines()[0])
        self.assertTrue(output.splitlines()[1].startswith("# Disabled"))
        self.assertEqual(output.splitlines()[2], original.splitlines()[2])
        self.assertEqual(output, migration.disable_ros_entries(output, ".list"))

    def test_deb822_preserves_other_stanza_and_embedded_key(self):
        ubuntu = "Types: deb\nURIs: http://ports.ubuntu.com/ubuntu-ports\nSuites: noble noble-updates\n"
        ros = ("Types: deb\nURIs: https://packages.ros.org/ros2/ubuntu\nSuites: jammy\n"
               "Signed-By:\n -----BEGIN PGP PUBLIC KEY BLOCK-----\n keydata\n -----END PGP PUBLIC KEY BLOCK-----\n")
        output = migration.disable_ros_entries(ubuntu + "\n" + ros, ".sources")
        self.assertTrue(output.startswith(ubuntu + "\n"))
        self.assertIn(" keydata\n", output)
        self.assertEqual(output.count("Enabled: no"), 1)
        self.assertEqual(output, migration.disable_ros_entries(output, ".sources"))

    def test_mixed_uri_stanza_fails_without_rewriting_any_file(self):
        safe = self.write("etc/apt/sources.list", "deb https://packages.ros.org/ros2/ubuntu jammy main\n")
        self.write("etc/apt/sources.list.d/mixed.sources",
                   "URIs: https://packages.ros.org/ros2/ubuntu https://ports.ubuntu.com/ubuntu-ports\n")
        old = safe.read_bytes()
        with self.assertRaisesRegex(migration.MigrationError, "mixes"):
            self.subject.preflight()
        self.assertEqual(safe.read_bytes(), old)

    def test_backup_precedes_removal_and_keeps_source_contents(self):
        source = self.write("etc/apt/sources.list", "deb https://packages.ros.org/ros2/ubuntu jammy main\n")
        original = source.read_bytes()
        self.subject.make_backup()
        self.subject.remove_legacy_ros()
        with tarfile.open(self.subject.backup / "configuration.tar.gz") as archive:
            self.assertEqual(archive.extractfile("etc/apt/sources.list").read(), original)
        self.assertTrue(source.read_text().startswith("# Disabled"))
        removal = next(call for call in self.runner.calls if call[:2] == ("apt-get", "remove"))
        self.assertEqual(removal[2:], ("ros-humble-ros-base", "ros2-apt-source"))
        self.assertFalse(any("autoremove" in call for call in self.runner.calls))

    def test_failed_removal_does_not_disable_sources_or_start_upgrade(self):
        source = self.write("etc/apt/sources.list", "deb https://packages.ros.org/ros2/ubuntu jammy main\n")
        original = source.read_bytes()
        self.runner.fail = lambda args: args[:2] == ["apt-get", "remove"]
        with self.assertRaises(subprocess.CalledProcessError):
            self.subject.migrate("jammy")
        self.assertEqual(source.read_bytes(), original)
        self.assertFalse(any(call[0] == "do-release-upgrade" for call in self.runner.calls))

    def test_backup_preserves_dangling_and_masked_systemd_links(self):
        directory = self.root / "etc/systemd/system/multi-user.target.wants"
        directory.mkdir(parents=True)
        dangling = directory / "grub-initrd-fallback.service"
        dangling.symlink_to("/missing-test-unit/grub-initrd-fallback.service")
        masked = self.root / "etc/systemd/system/masked.service"
        masked.symlink_to("/dev/null")
        target = self.write("usr/lib/systemd/system/valid.service", "[Unit]\nDescription=Test\n")
        valid = directory / "valid.service"
        valid.symlink_to(target)
        self.subject.make_backup()
        with tarfile.open(self.subject.backup / "configuration.tar.gz") as archive:
            for link in (dangling, masked, valid):
                info = archive.getmember(link.relative_to(self.root).as_posix())
                self.assertTrue(info.issym())
                self.assertEqual(info.linkname, str(link.readlink()))
            self.assertNotIn("usr/lib/systemd/system/valid.service", archive.getnames())
        self.assertTrue(dangling.is_symlink())
        self.assertFalse(dangling.exists())

    def test_backup_keeps_a_dangling_top_level_configuration_link(self):
        self.subject.path("etc/os-release").unlink()
        self.subject.path("etc/os-release").symlink_to("../usr/lib/missing-os-release")
        self.subject.make_backup()
        with tarfile.open(self.subject.backup / "configuration.tar.gz") as archive:
            self.assertTrue(archive.getmember("etc/os-release").issym())

    def test_jammy_reboot_boundary_does_not_install_jazzy_or_release_upgrade(self):
        self.write("run/reboot-required", "")
        self.subject.upgrade_jammy()
        self.assertIn("REBOOT REQUIRED", self.stdout.getvalue())
        self.assertFalse(any(call[0] in ("do-release-upgrade", "curl") for call in self.runner.calls))

    def test_apt_update_failure_stops_before_upgrade(self):
        self.runner.fail = lambda args: args[:2] == ["apt-get", "update"]
        with self.assertRaises(subprocess.CalledProcessError):
            self.subject.upgrade_jammy()
        self.assertEqual(self.runner.calls, [("apt-get", "update")])

    def test_successful_release_upgrade_stops_for_reboot_without_ros_install(self):
        def finish(args):
            if args == ["do-release-upgrade"]:
                self.write("etc/os-release", "ID=ubuntu\nVERSION_ID=24.04\nVERSION_CODENAME=noble\n")
        self.runner.effect = finish
        self.subject.upgrade_jammy()
        self.assertEqual(self.runner.calls[-1], ("do-release-upgrade",))
        self.assertIn("Prompt=lts", self.subject.path("etc/update-manager/release-upgrades").read_text())
        self.assertIn("REBOOT REQUIRED", self.stdout.getvalue())

    def test_cancelled_release_upgrade_is_not_reported_as_success(self):
        with self.assertRaisesRegex(migration.MigrationError, "did not finish"):
            self.subject.upgrade_jammy()

    def test_noble_reboot_boundary_does_not_install_ros_yet(self):
        self.write("run/reboot-required", "")
        self.subject.install_jazzy()
        self.assertFalse(any(call[0] in ("curl", "dpkg", "do-release-upgrade") for call in self.runner.calls))

    def test_download_failure_does_not_install_unverified_package(self):
        self.runner.fail = lambda args: args[0] == "curl" and "-fSL" in args
        with self.assertRaises(subprocess.CalledProcessError):
            self.subject.install_ros_repository()
        self.assertFalse(any(call[0] == "dpkg" for call in self.runner.calls))

    def test_noble_installs_jazzy_only_and_preserves_user_shell(self):
        profile = self.write("home/ubuntu/.bashrc", "source ~/turtlebot3_ws/install/setup.bash\n")
        before = profile.read_bytes()
        self.subject.install_jazzy()
        self.assertEqual(profile.read_bytes(), before)
        install = next(call for call in self.runner.calls if "ros-jazzy-ros-base" in call)
        self.assertFalse(any("humble" in arg or "turtlebot" in arg for arg in install))
        self.assertFalse(any(call[0] == "do-release-upgrade" for call in self.runner.calls))
        shell = self.subject.path("usr/local/bin/skala-jazzy-shell")
        self.assertIn("--noprofile --rcfile", shell.read_text())
        self.assertEqual(shell.stat().st_mode & 0o777, 0o755)
        self.assertEqual(self.subject.path("etc/skala").stat().st_mode & 0o777, 0o755)
        self.assertIn("no hardware test", self.stdout.getvalue())

    def test_validation_failure_is_not_reported_as_completed(self):
        self.runner.fail = lambda args: args[0] == "env"
        with self.assertRaises(subprocess.CalledProcessError):
            self.subject.install_jazzy()
        self.assertNotIn("installation verified", self.stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
