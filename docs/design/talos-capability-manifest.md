# talos Capability Manifest — Design Note

A body connecting to LOGOS through talos describes its own capabilities at runtime; talos defines only how that description is structured and exchanged, never which capabilities exist. Skala is the first body written against it.

This note belongs to talos (the LOGOS hardware-interface layer) and is mirrored here because skala is the first body written against it. Design date 2026-10-24; editable original https://claude.ai/artifact/Bpau2znAarDhkKruEdU6iF.

## Problem and principles

There is no way to know in advance what a given piece of hardware can do, so talos cannot be a catalogue of capabilities; it has to be the grammar in which a body states its own.

The analogy is tool discovery in MCP: a client connects to a server it has never seen, receives a list of tools with names, schemas and descriptions, and composes from there. talos plays the client-protocol role; each body plays the server. LOGOS consumes whatever arrives.

Principles that follow:

- **talos defines mechanics, not vocabulary.** It specifies how to describe a sensor, an actuator, a behaviour and a state, and how messages flow. It never names a specific device, joint or action.
- **Bodies are self-describing and authoritative.** The manifest a body publishes is the truth about it. Nothing in LOGOS is allowed to assume a capability the manifest did not advertise.
- **Few kinds, rich description.** Four primitive kinds, distinguished by their mechanics. Everything else ("LiDAR", "motor", "gimbal") is descriptive metadata for humans and for learning, not a type the machinery branches on.
- **Low level always present, high level optional.** Every body exposes raw actuators and sensors. Behaviours are an optional layer on top, so motor-babbling and learned control are possible against the same interface as scripted verbs.
- **Meaning is the agent's problem.** Two bodies may both offer something called `drive` with different conventions. talos does not reconcile this; cognition learns what a verb does by using it and watching the streams, which is the point of a pretextual agent.
- **Degradation is explicit.** When a body loses its link, trips a fault or drops to reflex-only mode, the agent sees that as state, not as silence.

Out of scope here: the transport (ZeroMQ, serial, in-process) and the on-wire encoding. The manifest and lifecycle are defined so that any transport can carry them.

## The four primitive kinds

A capability is one of four kinds, chosen by how the agent interacts with it, not by what the hardware is.

| Kind | Agent interaction | Produces | Examples (all the same kind) |
| --- | --- | --- | --- |
| **sensor** | subscribe at a rate | a stream of typed samples | IMU, 2D scan, camera frames, a servo's current, battery voltage, a bump switch |
| **actuator** | command a setpoint | acknowledgement, then its own sensor echo | pitch servo (position), track drive (velocity), a light (binary), a gripper (effort) |
| **behaviour** | invoke with parameters | started / progress / done / aborted events | set_stance, climb_step, self_right, look_at, dock |
| **state** | query, or receive on change | a typed snapshot | mode, fault flags, battery level, link quality, which behaviour is running |

The test for adding a fifth kind: does it need different *mechanics* than subscribe, command, invoke or query? A new device never passes this test. Something like a shared memory region or a bidirectional negotiation might. Until one does, four is the number.

**Why behaviours are a kind and not just "actuators with sequencing."** An actuator setpoint is instantaneous and idempotent; a behaviour has duration, internal state, can fail partway, and can be aborted. The agent needs to know which it is holding. Keeping them separate also lets a body advertise zero behaviours and still be fully drivable.

**Why state is separate from sensors.** State changes rarely and the agent needs the current value, not a history; faults and modes gate whether other commands will be honoured. Modelling it as a slow sensor would work mechanically but hides that distinction.

## Manifest structure

A manifest is a document with a header and four lists. Every entry has a stable `name` unique within the body, a human `description`, and free-form `tags`; the rest of the fields depend on the kind.

**Header**

| Field | Meaning |
| --- | --- |
| `body` | stable identifier for this body (e.g. `skala-p0`) |
| `manifest_version` | increments whenever the manifest changes; the agent re-reads on change |
| `talos_version` | the schema version this manifest conforms to |
| `clock` | how timestamps are produced: `monotonic_ns` on the body, plus an offset to the agent's clock negotiated at connect |
| `frames` | named coordinate frames the body uses (`base`, `lidar`, `camera`), each with its pose relative to `base` |

**sensor**

| Field | Meaning |
| --- | --- |
| `dtype`, `shape` | element type and shape per sample (`f32 [3]` for an accelerometer, `f32 [360]` for a scan, `u8 [480,640,3]` for a frame) |
| `units` | per element or per axis, SI unless stated |
| `rate_hz` | nominal rate; `0` means on-change |
| `frame` | which named frame the data is expressed in |
| `latency_ms` | typical sensing-to-publish delay, so the agent can align streams |
| `source` | optional: name of the actuator this sensor echoes (a servo's position or current) |

**actuator**

| Field | Meaning |
| --- | --- |
| `command` | `position`, `velocity`, `effort`, or `binary` |
| `units` | of the setpoint |
| `range` | `[min, max]` the body will accept; outside is rejected, not clipped |
| `rate_limit` | max change per second, if the body enforces one |
| `echo` | name of the sensor that reports this actuator's actual value |
| `group` | optional: actuators that must be commanded together (the four pitch servos, say) |

**behaviour**

| Field | Meaning |
| --- | --- |
| `params` | schema of the invocation parameters (JSON Schema or equivalent) |
| `events` | the progress events it emits beyond the standard four, with payload schemas |
| `preconditions` | state predicates that must hold to invoke (`mode == ready`, `battery > 20%`) |
| `uses` | actuators and sensors it drives, so the agent knows what is unavailable while it runs |
| `abortable` | whether abort is honoured mid-run, and what the body does on abort (hold, return, stop) |
| `typical_duration_s` | for the agent's planning, not a guarantee |

**state**

| Field | Meaning |
| --- | --- |
| `fields` | typed fields in the snapshot, with units |
| `modes` | the enumerated modes and which commands each accepts |
| `faults` | the enumerated fault flags, each with a human description and whether it self-clears |

**Tags versus kinds.** `tags: [lidar, 2d, range]` on a sensor tells a human what it is and gives cognition something to cluster on across bodies. Nothing in talos reads tags to decide behaviour. If two bodies tag something `lidar` with different `shape`, that is fine; the shape is what the machinery uses.

## Lifecycle and event envelope

The exchange is five verbs, and every message after the first travels in the same envelope.

1. **connect** — the agent opens a session; body and agent exchange clocks (three round trips, take the median offset) and the agent learns `talos_version`.
2. **manifest** — the body sends its manifest. The agent may receive a new one at any time (`manifest_version` increments) if hardware is hot-plugged or a behaviour becomes unavailable.
3. **subscribe** — the agent asks for named sensors, optionally at a decimated rate or with a filter the body advertises (region of a scan, downsampled frame). The body streams samples.
4. **command** — the agent sets an actuator (or a group). The body acknowledges accept/reject with a reason; the result is observed through the actuator's `echo` sensor, not through the ack.
5. **invoke** — the agent starts a behaviour with parameters and receives a handle; events for that handle follow until `done` or `aborted`. `abort(handle)` is the one mutation of a running behaviour.

**Envelope**

| Field | Meaning |
| --- | --- |
| `body` | which body sent it |
| `kind` | `sample`, `ack`, `event`, `state`, `manifest` |
| `name` | capability name (or behaviour handle for events) |
| `t_body` | body monotonic time in ns when the data was captured (not sent) |
| `t_agent` | agent-time estimate, filled in by the talos client using the negotiated offset |
| `seq` | per-stream sequence number, so drops are visible |
| `payload` | typed per the manifest |

**Timing rules**

- `t_body` is the capture time, not the publish time; the sensor's `latency_ms` is for the agent to use if it wants capture-to-perception alignment.
- Episodic memory keys on `t_agent`; two bodies on one agent share a timeline without each knowing the other exists.
- Clock re-sync happens on every heartbeat; drift beyond a threshold is reported in state as a fault, not silently corrected.

**Heartbeat** runs both ways at a rate the body declares (skala: 2 Hz). The body entering reflex-only mode on a missed heartbeat is a body policy, published in its state modes; talos only guarantees the agent will see the mode change.

## Behaviours as opaque affordances

A behaviour is a verb the body offers without explaining what it means. The agent learns its meaning from the sensor streams that change while it runs, which is the intended relationship between body and cognition.

What talos fixes about every behaviour:

- **Invocation** returns a handle immediately, or a rejection naming the failed precondition.
- **Four standard events** on the handle: `started`, `progress` (payload: a 0–1 fraction plus any body-specific fields), `done` (payload: an outcome enum the body defines), `aborted` (payload: who aborted and the body's resulting posture). Bodies may add events; they cannot remove these.
- **One behaviour per resource.** A behaviour declares the actuators it `uses`; invoking a second behaviour that overlaps is rejected unless the body marks the pair as compatible. The agent can always see what is busy.
- **Abort is a request.** The body decides how to stop safely and reports what it did. A stair climber half-way up a step should not simply release.
- **Direct actuator commands during a behaviour** are rejected for the actuators it uses. The body owns them until the handle closes.

What talos leaves to the body: the parameter vocabulary, how progress is measured, and whether the behaviour is scripted, reactive or learned. Skala's `climb_step` will be a scripted state machine over IMU pitch and servo current; a later body might offer a behaviour backed by a policy network. The agent sees the same four events either way.

**Composition** is not a talos concern. If the agent wants "climb the whole flight," it invokes `climb_step` repeatedly and watches state, or the body offers `climb_flight` as its own verb. Both are legitimate; the second is a body author deciding the sequence is stable enough to package.

This is also where the pretextual framing bites: nothing stops cognition from learning that the sensor signature of `climb_step` on skala resembles that of some other body's `step_up`, without either body ever telling it so.

## State, modes and failure semantics

The agent should never have to infer that something is wrong from an absence of data; every degradation is a state change it receives.

**Modes** are an enumeration the body publishes, each with the set of verbs it honours. talos requires only that the set is declared; the names are the body's. Skala's will be roughly:

| Mode | Honours | Entered when |
| --- | --- | --- |
| `booting` | manifest, state | power-on until the reflex layer reports healthy |
| `ready` | everything | reflex layer healthy, link up, no faults |
| `busy` | subscribe, state, abort; commands on unused actuators | a behaviour is running |
| `reflex_only` | subscribe, state | link to the agent lost; the body holds position and stops drives on its own |
| `fault` | subscribe, state, clear_fault | a fault flag is set that blocks motion |
| `estop` | subscribe, state | hardware e-stop; cleared only physically |

**Faults** are flags, not exceptions: several can be set at once, each declares whether it self-clears, and the agent reads them from state. Examples: `servo_overcurrent[n]`, `tip_over`, `battery_low`, `clock_drift`, `sensor_stale[name]`.

**Link loss, seen from both sides.** The body misses heartbeats and enters `reflex_only` on its own policy. The talos client on the agent side misses heartbeats and marks the body `unreachable` locally, closes open behaviour handles with `aborted(reason=link_lost)`, and keeps the last state snapshot tagged stale. On reconnect the body sends state and (if changed) manifest first, before any samples, so the agent re-synchronises before trusting new data.

**Episodic integrity.** Samples carry `seq`, so a gap is a gap, not a smooth line. Stale state is marked stale. Clock drift is a fault. The rule is that anything stored into episodic memory can be trusted to the degree the envelope says, and no more.

**What the agent must never assume:** that a command took effect (watch the echo), that a behaviour finished (wait for `done`), that the body is still there (watch the heartbeat), or that a capability still exists (watch `manifest_version`).

## Skala's manifest (prototype 0)

The first concrete instance. Everything here is what the skala body driver on the Pi will publish; the OpenCR firmware exposes the joints and IMU underneath it. Shown in YAML for readability; the wire form is whatever the transport uses.

```yaml
body: skala-p0
manifest_version: 1
talos_version: 0.1
clock: { source: monotonic_ns, heartbeat_hz: 2 }
frames:
  base:   { parent: null }
  lidar:  { parent: base, xyz: [0.0, 0.0, 0.12], rpy: [0, 0, 0] }
  camera: { parent: base, xyz: [0.04, 0.0, 0.14], rpy: [0, 0, 0], moving: [cam_pan, cam_tilt] }   # pose follows the pan/tilt setpoints

sensors:
  - { name: imu,            dtype: f32, shape: [9],   units: [m/s2, m/s2, m/s2, rad/s, rad/s, rad/s, rad, rad, rad], rate_hz: 50, frame: base, latency_ms: 5, tags: [imu, accel, gyro, rpy] }
  - { name: pitch_pos,      dtype: f32, shape: [2],   units: deg,  rate_hz: 50, source: pitch,  tags: [servo, echo] }
  - { name: pitch_current,  dtype: f32, shape: [2],   units: mA,   rate_hz: 50, source: pitch,  tags: [servo, current] }
  - { name: drive_vel,      dtype: f32, shape: [2],   units: rpm,  rate_hz: 50, source: drive,  tags: [servo, echo] }
  - { name: drive_current,  dtype: f32, shape: [2],   units: mA,   rate_hz: 50, source: drive,  tags: [servo, current] }
  - { name: battery_v,      dtype: f32, shape: [1],   units: V,    rate_hz: 1,  tags: [power] }
  - { name: scan,           dtype: f32, shape: [360], units: m,    rate_hz: 8,  frame: lidar, latency_ms: 60, tags: [lidar, 2d, range] }
  - { name: camera,         dtype: u8,  shape: [480, 640, 3], units: rgb, rate_hz: 15, frame: camera, latency_ms: 80, tags: [camera, rgb, forward] }
  - { name: cam_pan_set,    dtype: f32, shape: [1],   units: deg,  rate_hz: 0,  source: cam_pan,  tags: [servo, echo, setpoint-only] }
  - { name: cam_tilt_set,   dtype: f32, shape: [1],   units: deg,  rate_hz: 0,  source: cam_tilt, tags: [servo, echo, setpoint-only] }

actuators:
  - { name: pitch, command: position, units: deg, range: [-200, 200], rate_limit: 180, echo: pitch_pos, group: arms, shape: [2], tags: [flipper, front] }
  - { name: drive, command: velocity, units: rpm, range: [-80, 80],   rate_limit: 400, echo: drive_vel, group: arms, shape: [2], tags: [track, front] }
  - { name: cam_pan,  command: position, units: deg, range: [-90, 90], rate_limit: 180, echo: cam_pan_set,  tags: [camera, pan,  open-loop] }
  - { name: cam_tilt, command: position, units: deg, range: [-45, 30], rate_limit: 180, echo: cam_tilt_set, tags: [camera, tilt, open-loop] }

behaviours:
  - name: set_stance
    params: { stance: { enum: [flat, stance, climb_ready, tucked] } }
    uses: [pitch]
    preconditions: [mode in (ready, busy:set_stance)]
    abortable: { honoured: true, on_abort: hold }
    typical_duration_s: 2
  - name: drive_velocity
    params: { v_mps: { type: number, range: [-0.5, 0.5] }, w_radps: { type: number, range: [-2, 2] } }
    uses: [drive]
    preconditions: [mode == ready]
    abortable: { honoured: true, on_abort: stop }
    typical_duration_s: null        # runs until aborted or re-invoked
  - name: climb_step
    params: { rise_mm: { type: number, range: [50, 120] } }
    uses: [pitch, drive]
    preconditions: [mode == ready, imu.pitch < 10deg]
    events: [{ name: phase, payload: { enum: [approach, catch, pull, level] } }]
    abortable: { honoured: true, on_abort: hold }
    typical_duration_s: 8

state:
  fields: { mode: enum, faults: flags, battery_pct: f32, link_rtt_ms: f32, running: [behaviour_handle] }
  modes: [booting, ready, busy, reflex_only, fault, estop]
  faults:
    - { name: servo_overcurrent, indexed: true,  self_clears: false }
    - { name: tip_over,          indexed: false, self_clears: false }
    - { name: battery_low,       indexed: false, self_clears: true }
    - { name: clock_drift,       indexed: false, self_clears: true }
    - { name: sensor_stale,      indexed: true,  self_clears: true }
```

Notes on choices:

- `shape: [2]` on the actuators means prototype 0 has two driven arms; prototype 1 bumps it to 4 and `manifest_version` to 2, and nothing in talos or LOGOS changes.
- `drive_velocity` is a behaviour, not an actuator, because it embeds track kinematics (v, ω → per-side rpm). The raw `drive` actuator is still exposed for babbling and learned control.
- The RPLidar A1 appears only as a `scan` sensor; stair detection in P0 is the body's business inside `climb_step`, from IMU and current, and the agent sees it as `phase` events.
- The camera rides a two-servo pan/tilt. MG90S servos have no position feedback, so their `echo` sensors report the commanded setpoint, tagged `setpoint-only`; the agent should treat them as less trustworthy than a Dynamixel echo. The `camera` frame is declared as moving with those actuators.

## Open questions

These need a decision before the manifest schema becomes code. None blocks the OpenCR firmware.

- [ ] **Where the body driver lives.** `talos/bodies/skala` inside talos, or the skala repo depending on talos. The interface is the same either way; this is about who owns releases.
- [ ] **Schema language.** JSON Schema for `params` and `fields` (portable, verbose) versus Python dataclasses with runtime validation (concise, Python-only). LOGOS is Python; is anything else ever going to publish a manifest?
- [ ] **Raw versus abstracted streams for perception.** The manifest above exposes raw samples. Should talos also define a standard way for a body to offer *derived* streams (a detected-edge event, a pose estimate), or is every derived thing a body-specific sensor with tags?
- [ ] **Sample encoding for large streams.** Camera frames and scans over ZeroMQ: raw bytes with a dtype/shape header is simplest; is there a reason to pick Arrow or similar now?
- [ ] **Behaviour compatibility matrix.** `uses` gives a conservative rule (overlapping actuators conflict). Is an explicit "these two may run together" list worth the complexity in v0.1?
- [ ] **Multi-body.** One agent, several bodies on one timeline is designed in via `body` in the envelope. Should talos also aggregate manifests into a single view, or does cognition keep them separate?
- [ ] **Learning hooks.** Does talos record anything itself (a ring buffer of samples around each behaviour event, say) or is recording entirely the agent's job? The former makes every body self-documenting for episodic memory; the latter keeps talos thin.
- [ ] **Versioning across the boundary.** When `talos_version` moves, which side bends? Proposal: the client supports N and N−1 and bodies pin one.

What to do next, in order: settle the first two questions, write `manifest.py` with the four kinds and a validator, write skala's manifest as its test fixture, then write the OpenCR firmware against the actuators and sensors it must expose.
