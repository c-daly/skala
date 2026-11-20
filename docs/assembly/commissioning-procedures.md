# Skala commissioning procedures

Created 2026-11-20. This page holds step-by-step **configuration and test procedures** for the commissioning gates defined in the [assembly guide, section 13](p0-assembly.md#13-commission-in-stages). The guide owns when each gate applies and what evidence closes it; the [system plan](s1-system-plan.md) owns the requirements. This page gives the commands, expected results, pass/fail criteria and what to record.

**Coverage:** G0 (preserve and inventory the existing installation) and G1 (isolated compute and sensors) are written here. G2–G7 depend on Skala firmware that does not yet exist, on the OS decision made after G0, and on the open power holds H04–H06; they are listed at the end with what is needed before each can be written. None of these procedures has been run on this robot yet.

**Sources:** each command or fact below cites its primary source. Where a vendor documents nothing, the step says so; "from source code" means the behaviour was read from the vendor's code, not observed. Re-check a command against its source if the installed software version differs.

## Recording results

Make one record per gate run: a plain text or Markdown file named `G<n>-<yyyy-mm-dd>.md`, kept together with the saved output files, for example on the backup drive. Copy this template.

```text
Gate / step:            G1.2 camera
Date, operator:
Hardware revisions:     (e.g. Pi 4B board revision, OpenCR revision, P10 print, sensor model/serial)
Software:               (OS release, kernel, ROS distro, driver commit hashes)
Wiring / power state:   (which supplies connected; drive battery absent?)
Commands run:           (paste exactly, or reference the saved log file)
Expected result:
Observed result:        (paste output; attach files)
Pass / fail / blocked:
Deviations / notes:
```

"Blocked" is a valid result: record the reason and stop that step rather than improvising around it. Save raw command output to a file with `| tee <name>.log` so it can be attached unedited.

## Safety state for G0 and G1

- **Drive battery B1 disconnected** and out of the robot. No supply on the OpenCR battery input.
- **Both XL430 TTL leads unplugged** from the OpenCR. Head servos unconnected.
- Pi on its P10 adapter on the bench, supported so no connector or cable carries the board's weight. Open air; no cooler is assumed.
- Compute supply: the official Raspberry Pi supply if available, otherwise the selected owned 5 V/3 A bank. Record which one (model, output port, cable) in every G1 record.

## G0 — preserve and inventory the existing installation

**Purpose:** make a restorable copy of the working TurtleBot3 Pi before anything changes, then record exactly what is installed. No upgrade, reflash, `apt upgrade`, motor reset or firmware upload happens in G0.

### G0.1 Back up the SD card

Raspberry Pi's documentation tells you to back up boot media before an upgrade but documents no host-side imaging procedure; its only listed tool, SD Card Copier, runs on the Pi itself ([raspberrypi/documentation](https://github.com/raspberrypi/documentation), `computers/os/updating.adoc`, `software-sources.adoc`). The method below is ordinary disk imaging, not a vendor procedure.

1. Shut the Pi down cleanly (`sudo shutdown -h now`), wait until the green activity LED stops, then remove power. Remove the microSD card.
2. Image the whole card on a desktop computer, not one partition:
   - **Linux host:** identify the card with `lsblk` (check its size; never guess the device). Then `sudo dd if=/dev/sdX of=skala-pi-g0.img bs=4M status=progress conv=fsync`, replacing `sdX` with the card's whole-disk device. A wrong `if=`/`of=` can overwrite a disk, so read the command twice.
   - **Windows host:** use a disk-imaging tool's *read* (not write) function on the card's drive letter. WSL generally cannot see a USB card reader, so do this from Windows itself.
3. Hash the image (`sha256sum skala-pi-g0.img` on Linux, `Get-FileHash` in PowerShell) and record the hash. Keep two copies on separate drives.
4. **Recommended:** prove the backup restores by writing it to a spare card of at least the same size and booting the Pi from that spare. Until this has been done, treat the backup as unverified.

**Pass:** image file present, hash recorded and two copies kept. **Verified restore** only if step 4 boots.

### G0.2 Record the Pi's software

Re-insert the original card and boot the Pi on its compute supply, with the OpenCR still unplugged. Log in and run the following, saving the output with `tee`:

```sh
{
  cat /proc/device-tree/model; echo
  cat /etc/os-release
  uname -m; uname -r
  ls /opt/ros
  grep -nE 'ROS_DOMAIN_ID|LDS_MODEL|TURTLEBOT3|ROS_|source ' ~/.bashrc
  ls /etc/udev/rules.d/
  systemctl list-unit-files --state=enabled --no-pager
  crontab -l
  ls ~ ~/turtlebot3_ws/src 2>&1
  find ~ -maxdepth 3 \( -name 'opencr_update*' -o -name 'released_*.txt' \) 2>/dev/null
  dpkg -l | grep -E 'turtlebot3|libraspberrypi-bin|libcamera|camera-ros' 
  cat /boot/firmware/config.txt
} 2>&1 | tee g0-pi-inventory.log
```

What to look for, from the TurtleBot3 setup this Pi most likely followed ([SBC setup](https://emanual.robotis.com/docs/en/platform/turtlebot3/sbc_setup/), [bringup](https://emanual.robotis.com/docs/en/platform/turtlebot3/bringup/)):

| Item | Expected from the TurtleBot3 setup | Why it matters |
| --- | --- | --- |
| OS / ROS | Humble on Ubuntu Server 22.04, or Jazzy on Ubuntu Server 24.04 | Decides the camera route; see G0.4 |
| `~/.bashrc` | `source /opt/ros/<distro>/setup.bash`, `source ~/turtlebot3_ws/install/setup.bash`, `ROS_DOMAIN_ID=30`, `LDS_MODEL=LDS-0x` | `TURTLEBOT3_MODEL` is normally exported by hand at bringup, not in `.bashrc`. `LDS_MODEL` refers to TurtleBot3's own LiDAR, not the owned A1 |
| udev | `99-turtlebot3-cdc.rules`: OpenCR (USB 0483:5740) gets permissions only, no `/dev` symlink; USB 10c4:ea60 gets the symlink `/dev/tb3_lidar` | The A1 adapter also uses 10c4:ea60 (see G1.3), so it will appear as `/dev/tb3_lidar` too |
| Autostart | None in the standard setup; bringup is started by hand | Anything enabled beyond the standard setup was added later; record it |
| `opencr_update/` | Present if the OpenCR was flashed from this Pi, in whichever directory the update was run (usually home): `burger.opencr`, `waffle.opencr`, `update.sh`, `released_<version>.txt` | The `released_*.txt` name is the best available record of which firmware package was flashed |

If `vcgencmd` is missing (`command not found`), note it; G1.0 installs it once G0 is complete. Do not install anything during G0.

**Pass:** the log is saved and every row in the table above is recorded, including "not present".

### G0.3 Identify the OpenCR, motors still unplugged

**This step and G0.4 extend the G0 state:** the OpenCR is connected to the Pi by USB only, powered from the compute supply through that cable. Keep B1 disconnected and both TTL leads unplugged; nothing else is connected to the OpenCR. Connect the OpenCR to a Pi USB-A port with the data cable (W08); the OpenCR is then powered from USB only.

```sh
{ lsusb; ls -l /dev/ttyACM*; dmesg | tail -n 20; } 2>&1 | tee g0-opencr-usb.log
```

**Expected:** a device with ID `0483:5740` and a `/dev/ttyACM0` (number may differ). Record the board revision printed on the PCB.

**Firmware version:** ROBOTIS documents no way to read the firmware version from a TurtleBot3 OpenCR. The `opencr_update/released_*.txt` file found in G0.2, if present, is the practical record. From source code, the TurtleBot3 ROS 2 firmware presents itself on USB as a DYNAMIXEL-protocol device (ID 200) with a firmware-version field at address 6, but the standard ROS node never reads or logs it ([OpenCR `turtlebot3_ros2` library](https://github.com/ROBOTIS-GIT/OpenCR/tree/master/arduino/opencr_arduino/opencr/libraries/turtlebot3_ros2), [turtlebot3_node](https://github.com/ROBOTIS-GIT/turtlebot3/tree/humble/turtlebot3_node)). Reading that field needs a small script and is deferred to the G2 firmware work.

**Do not flash** the OpenCR in G0. There is no way to read the existing firmware back off the board; the only recovery is reflashing a package such as `opencr_update`, so record what was installed first.

**Pass:** USB ID, tty device and board revision recorded; firmware package recorded or marked "unknown".

### G0.4 Optional: existing bringup with motors unpowered

Only if G0.2 shows a TurtleBot3 workspace. This shows whether the existing stack still runs; it is not a Skala test. Motors remain unplugged and unpowered.

```sh
export TURTLEBOT3_MODEL=burger      # or the model recorded in G0.2
ros2 launch turtlebot3_bringup robot.launch.py 2>&1 | tee g0-bringup.log
```

**Expected, from source code, not yet observed:** the firmware pings motors 1 and 2 at boot. With them absent, the node logs a WARN containing "Please double check your Dynamixels and Power" and keeps running. "Failed connection with Devices" followed by shutdown means the OpenCR itself was not reached ([turtlebot3_node source](https://github.com/ROBOTIS-GIT/turtlebot3/blob/humble/turtlebot3_node/src/turtlebot3.cpp)). Stop it with Ctrl-C. Do not publish velocity commands.

### G0.5 Decision after G0: the Pi operating system

**The Camera Module 3 cannot be qualified on Ubuntu 22.04.** The 22.04 Raspberry Pi kernel (`linux-raspi` 5.15) contains no IMX708 sensor driver, its libcamera is a 2020 snapshot that predates the sensor, and `rpicam-apps` is not packaged. The Ubuntu fixes for the IMX708 were made for later releases only ([Launchpad #2024434](https://bugs.launchpad.net/bugs/2024434), [#2009826](https://bugs.launchpad.net/bugs/2009826); [linux-raspi jammy tree](https://git.launchpad.net/~ubuntu-kernel/ubuntu/+source/linux-raspi/+git/jammy)). Ubuntu states that the camera stack works on Ubuntu for Raspberry Pi from 25.04 ([Ubuntu Discourse](https://discourse.ubuntu.com/t/59716)).

If G0.2 shows 22.04, choose one of these with the backup in hand. Record the decision before continuing G1's camera step.

| Option | What is established | What remains open |
| --- | --- | --- |
| Ubuntu Server 24.04 + ROS 2 Jazzy | TurtleBot3 publishes a [Jazzy SBC setup](https://emanual.robotis.com/docs/en/platform/turtlebot3/sbc_setup/). The 24.04 kernel includes the IMX708 driver; libcamera 0.2.0 includes IMX708 support | `rpicam-apps` must be built from source. End-to-end camera operation on 24.04 is unverified. The OpenCR firmware package must be matched to Jazzy before G2 |
| Keep 22.04 for now | Existing stack, audio and LiDAR can proceed | The camera stays blocked; it only defers the migration |
| Another OS (e.g. Raspberry Pi OS with ROS in a container) | Raspberry Pi OS supports the camera directly | Not researched for this robot; would need its own source check |

The audio (G1.1) and LiDAR (G1.3) steps can run on whichever OS is installed now. A migration installs onto a **new card** and leaves the G0 card untouched as the fallback.

## G1 — isolated compute and stationary sensors

**Preconditions:** G0 passed; drive battery absent; OpenCR not needed (unplug it). Each sensor is tested on its own first, then all together (G1.4). Secure any sensor whose final mount is not fitted so it cannot fall or short against the boards.

### G1.0 Power and thermal baseline

Before connecting sensors, record the baseline. If G0.2 found no `vcgencmd`, install it first. On Ubuntu it is in the `libraspberrypi-bin` package (`sudo apt install libraspberrypi-bin`); this is the first software change after the G0 backup, so record it. Old fault bits persist until reboot, so reboot first.

```sh
vcgencmd get_throttled; vcgencmd measure_temp
# continuous log for the later steps (leave running in a second terminal):
while true; do date +%T; vcgencmd measure_temp; vcgencmd get_throttled; sleep 5; done | tee g1-power.log
```

Without `vcgencmd`, `cat /sys/class/thermal/thermal_zone0/temp` gives millidegrees Celsius; that `thermal_zone0` is the SoC sensor is assumed, not verified.

`get_throttled` bits ([Raspberry Pi graphics utilities](https://github.com/raspberrypi/documentation/blob/master/documentation/asciidoc/computers/os/graphics-utilities.adoc)):

| Bit value | Meaning now | Bit value | Meaning since boot |
| --- | --- | --- | --- |
| 0x1 | Undervoltage detected | 0x10000 | Undervoltage has occurred |
| 0x2 | Arm frequency capped | 0x20000 | Capping has occurred |
| 0x4 | Currently throttled | 0x40000 | Throttling has occurred |
| 0x8 | Soft temperature limit active | 0x80000 | Soft limit has occurred |

Pi 4 progressively throttles its Arm cores between 80 and 85 °C and throttles Arm and GPU at 85 °C ([frequency management](https://github.com/raspberrypi/documentation/blob/master/documentation/asciidoc/computers/raspberry-pi/frequency-management.adoc)).

**Pass for every G1 step:** `get_throttled` stays `0x0`, and temperature stays below 80 °C. Any undervoltage bit fails the supply, not the sensor: record it under H04/H08 and re-test with the official supply before blaming the sensor.

### G1.1 WM8960 audio HAT

Power off. Seat the HAT on the 40-pin header as in guide step 10A; speakers stay disconnected. The HAT uses I2C1 (GPIO2/3, pins 3/5) with the codec at address 0x1a, and I2S on GPIO18–21 (pins 12, 35, 38, 40) ([kernel overlay source](https://github.com/raspberrypi/linux/blob/rpi-6.12.y/arch/arm/boot/dts/overlays/wm8960-soundcard-overlay.dts); [Pi GPIO](https://github.com/raspberrypi/documentation/blob/master/documentation/asciidoc/computers/raspberry-pi/gpio-on-raspberry-pi.adoc)). Keep those pins reserved, as W11 requires.

**Driver.** Waveshare's installer ([WM8960-Audio-HAT](https://github.com/waveshareteam/WM8960-Audio-HAT)) builds a DKMS kernel module for the running kernel. It edits `/boot/firmware/config.txt` (enables I2C and I2S, adds `dtoverlay=i2s-mmap` and `dtoverlay=wm8960-soundcard`), adds modules to `/etc/modules` and installs a `wm8960-soundcard` systemd service. Its documentation names no Ubuntu support. Raspberry Pi kernels from 5.15 onward, and the Ubuntu 22.04 kernel tree, already contain a `wm8960-soundcard` overlay and codec driver, so the DKMS build may be unnecessary; that is an inference, not tested here.

1. Try the in-kernel route first: add `dtparam=i2c_arm=on`, `dtparam=i2s=on` and `dtoverlay=wm8960-soundcard` to `/boot/firmware/config.txt` (keep a copy of the original), reboot, then run `arecord -l`.
2. If no `wm8960soundcard` card appears, use Waveshare's installer instead. Read `install.sh` before running it, and record the commit. The script copies its overlay file to `/boot/overlays` but edits `/boot/firmware/config.txt`; after it runs, check that `wm8960-soundcard.dtbo` exists in the `overlays` directory next to the `config.txt` that was edited. If not, the overlay will not load on reboot. Then: `git clone https://github.com/waveshareteam/WM8960-Audio-HAT; cd WM8960-Audio-HAT; git rev-parse HEAD; sudo ./install.sh; sudo reboot`.
3. Record 10 seconds, using the card number shown by `arecord -l` in place of `1`:

```sh
arecord -l | tee g1-audio-devices.log
arecord -D hw:1,0 -f S32_LE -r 16000 -c 2 -d 10 g1-audio.wav
```

The format, rate and channel count are Waveshare's documented example. Speak, then tap near each microphone in turn.

If the card is listed but the recording is silent, check the capture controls with `alsamixer -c <card>` (F4 shows capture) before concluding that the driver failed. Waveshare's installer also installs saved mixer-state files and a service to restore them, which the in-kernel route does not provide.

**Pass:** the card is listed, the file lasts 10 s, and on playback (on another computer, since the speakers are disconnected) both channels carry the voice and each tap is louder in its own channel. Record the driver route used (in-kernel or DKMS plus commit).

### G1.2 Camera Module 3

**Blocked on Ubuntu 22.04** (see G0.5). On an OS with IMX708 support:

1. Power off. Fit the CSI ribbon to the Pi camera socket, contacts facing the connector contacts, as in guide step 10D. Support the camera facing a scene with detail at 0.5–3 m.
2. Leave `camera_auto_detect=1` in config.txt; it detects official cameras. Only if it fails, set `camera_auto_detect=0` and add `dtoverlay=imx708` ([camera configuration](https://github.com/raspberrypi/documentation/blob/master/documentation/asciidoc/accessories/camera/rpicam-configuration.adoc)).
3. With `rpicam-apps` available (packaged on Raspberry Pi OS; built from source on Ubuntu 24.04):

```sh
rpicam-hello --list-cameras | tee g1-camera-list.log
rpicam-still --output g1-still.jpg
rpicam-vid -t 10s -o g1-video.h264
```

([rpicam-apps documentation](https://github.com/raspberrypi/documentation/tree/master/documentation/asciidoc/accessories/camera))

4. For ROS: `sudo apt install ros-$ROS_DISTRO-camera-ros`, then `ros2 run camera_ros camera_node`. Its maintainer warns that the packaged libcamera may not fully support Raspberry Pi cameras; building Raspberry Pi's libcamera fork is the documented fallback ([camera_ros](https://github.com/christianrauch/camera_ros)).

**Pass:** the list shows an `imx708` sensor; the still is sharp at the scene distance (autofocus); the 10 s video plays. Record which way up the image is relative to the mount (the CSI connector faces down on P15), for later correction in software.

### G1.3 RPLIDAR A1 and its interface board

Mount or clamp the scanner so the rotor turns freely and the scan plane is clear. Keep fingers and cables away from the rotor.

1. **Identify before connecting** (the guide holds the LiDAR connection until H02 identifies the interface). With nothing plugged in, record the scanner's label (model, revision, serial) and the interface board's markings, connectors, any switches and any auxiliary power input. Photograph both sides of the board. If the board has a separate power input or a switch whose purpose you cannot identify from its markings, stop and record the step as blocked.
2. Plug the interface board into a Pi USB port and check what enumerates:

```sh
{ lsusb; ls -l /dev/ttyUSB* /dev/tb3_lidar /dev/rplidar; } 2>&1 | tee g1-lidar-usb.log
```

**Expected:** USB ID `10c4:ea60` and a `/dev/ttyUSB0`. If the TurtleBot3 rule from G0.2 is present, `/dev/tb3_lidar` also points to it. Steps 1–2 together are the H02 identification.

3. **SDK test without ROS** ([rplidar_sdk](https://github.com/Slamtec/rplidar_sdk)): build with `make` in the SDK root; the binaries go to `output/Linux/Release/`. Run:

```sh
./output/Linux/Release/ultra_simple --channel --serial /dev/ttyUSB0 115200 | tee g1-lidar-sdk.log
```

The README's shorter form is out of date; the program needs `--channel --serial` and the baud rate. A1 uses 115200. Expect a stream of angle/distance lines; Ctrl-C stops it.

4. **ROS driver** ([sllidar_ros2](https://github.com/Slamtec/sllidar_ros2), source-only, not in the ROS package index):

```sh
mkdir -p ~/skala_ws/src && cd ~/skala_ws/src
git clone https://github.com/Slamtec/sllidar_ros2.git && git -C sllidar_ros2 rev-parse HEAD
cd ~/skala_ws && source /opt/ros/$ROS_DISTRO/setup.bash && colcon build --symlink-install
source install/setup.bash
ros2 launch sllidar_ros2 sllidar_a1_launch.py serial_port:=/dev/ttyUSB0
```

`sllidar_a1_launch.py` has no viewer and suits the headless Pi (`view_sllidar_a1_launch.py` also starts rviz2). The default port is `/dev/ttyUSB0` at 115200 baud, frame `laser`. In a second terminal, `ros2 topic list`, then `ros2 topic hz` on the scan topic it lists.

5. **Stable device name:** the repository's `create_udev_rules.sh` refers to a package name that does not exist (`rplidar_ros2`), so install its rule directly. It creates `/dev/rplidar` for USB 10c4:ea60:

```sh
sudo cp ~/skala_ws/src/sllidar_ros2/scripts/rplidar.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Any other device with the same USB-serial chip would match the same rule. Record whether that is acceptable or whether to match by serial number later.

**Pass:** SDK lines stream; the ROS scan topic publishes at a steady rate; a hand held at known distances appears at the right range and bearing. The power log shows no undervoltage at scanner start-up; the start-up current itself is the H02/H08 measurement and needs a USB current meter if one is available.

### G1.4 All sensors together

Run audio recording, camera video and the LiDAR driver at the same time for **10 minutes**, with the power log running and `dmesg -w | tee g1-dmesg.log` in another terminal. If the camera is blocked (G0.5), run audio and LiDAR only and record G1.4 as **partial: camera blocked**; it must be repeated with the camera before G1 closes.

```sh
arecord -D hw:1,0 -f S32_LE -r 16000 -c 2 -d 600 g1-all-audio.wav &
rpicam-vid -t 600s -o g1-all-video.h264 &
ros2 launch sllidar_ros2 sllidar_a1_launch.py serial_port:=/dev/rplidar
# in another terminal, using the scan topic found in G1.3:
ros2 topic hz <scan topic> | tee g1-all-lidar-hz.log
```

**Pass:** the audio and video files each last the full 10 minutes, and the LiDAR rate log shows a steady rate throughout with no gap; `get_throttled` stays `0x0`; temperature stays below 80 °C; `dmesg` shows no USB disconnects or undervoltage messages. Listen for LiDAR motor noise in the audio and record its level; it feeds H08's noise check. Repeat once on the selected owned bank if the first run used the official supply, and record both.

## Later gates — what each needs before it can be written

| Gate | Needed first | Facts already sourced for it |
| --- | --- | --- |
| G2 controller and stop | Skala OpenCR firmware (start disarmed, explicit arm, command expiry, stop input); OS decision from G0.5; H05 relay/stop hardware | TurtleBot3 ROS 2 firmware upload: `opencr_update.tar.bz2` from OpenCR-Binaries, `./update.sh $OPENCR_PORT $OPENCR_MODEL.opencr`, needs `libc6:armhf` on the Pi; recovery is hold SW2, press and release Reset, then release SW2 ([OpenCR setup](https://emanual.robotis.com/docs/en/platform/turtlebot3/opencr_setup/)). The archive is gzip despite its `.bz2` name, so use `tar -xvf`, not `-xjf` |
| G3 motor identity | G2 passed; a way to talk to the motor bus | XL430 control table ([e-Manual](https://emanual.robotis.com/docs/en/dxl/x/xl430-w250/)): ID 7, Baud Rate 8 (3 = 1 Mbps), Operating Mode 11, Temperature Limit 31 (default 72 °C), Max/Min Voltage Limit 32/34 (0.1 V units), Torque Enable 64, Bus Watchdog 98 (×20 ms, active only with torque on), Present Input Voltage 144, Present Temperature 146. Addresses 0–63 are EEPROM and can be written only with torque off. TurtleBot3 uses ID 1 left, ID 2 right, 1 Mbps. No code that forwards USB packets to the motor bus was found in the TurtleBot3 firmware source (not tested), so DYNAMIXEL Wizard 2.0 most likely reaches the motors only via ROBOTIS's `usb_to_dxl` OpenCR example sketch (replacing the TurtleBot3 firmware) or a separate U2D2. ROBOTIS's own motor setup uses the `turtlebot3_setup_motor` sketch ([TurtleBot3 FAQ](https://emanual.robotis.com/docs/en/platform/turtlebot3/faq/)) |
| G4 fault tests | Skala firmware implementing the faults to be injected | — |
| G5–G7 | G4 passed; H04–H06 and H09/H10 progress | — |
| Head servo centring | H03 servo/horn match; a PWM source before head firmware exists | — |
| Wiring continuity and polarity | H05 connector and fuse selection | — |
