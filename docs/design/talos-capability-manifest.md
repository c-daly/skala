# talos Capability Manifest — Design Note

A body connecting to LOGOS through talos describes its own capabilities at runtime; talos defines only how that description is structured and exchanged, never which capabilities exist. Skala is a planned body integration; its repository currently contains requirements, not a live body implementation.

The generic interface proposal dates from 2026-10-24; it is historical design context, not an assessment of the current shared Talos implementation. The Skala S1 profile below is maintained with the current robot decisions (reviewed 2026-11-07). Reuse and check the actual maintained Talos interfaces before implementing the Skala adapter; do not build a competing protocol from this earlier sketch.

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

What talos leaves to the body: the parameter vocabulary, how progress is measured, and whether the behaviour is scripted, reactive or learned. A future articulated Skala could offer a `climb_step` behavior, using feedback available from its eventual qualified joints. It is outside current S1 scope; XL430 inferred load is not measured current. A different body might offer a behavior backed by a policy network. The agent sees the same four events either way.

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
| `reflex_only` | subscribe, state | link lost; Skala stops and disarms locally. Power-off position holding is not provided |
| `fault` | subscribe, state, clear_fault | a fault flag is set that blocks motion |
| `estop` | subscribe, state | hardware e-stop; cleared only physically |

**Faults** are flags, not exceptions: several can be set at once, each declares whether it self-clears, and the agent reads them from state. Examples: `servo_overcurrent[n]`, `tip_over`, `battery_low`, `clock_drift`, `sensor_stale[name]`.

**Link loss, seen from both sides.** The body misses heartbeats and enters `reflex_only` on its own policy. The talos client on the agent side misses heartbeats and marks the body `unreachable` locally, closes open behaviour handles with `aborted(reason=link_lost)`, and keeps the last state snapshot tagged stale. On reconnect the body sends state and (if changed) manifest first, before any samples, so the agent re-synchronises before trusting new data.

**Episodic integrity.** Samples carry `seq`, so a gap is a gap, not a smooth line. Stale state is marked stale. Clock drift is a fault. The rule is that anything stored into episodic memory can be trusted to the degree the envelope says, and no more.

**What the agent must never assume:** that a command took effect (watch the echo), that a behaviour finished (wait for `done`), that the body is still there (watch the heartbeat), or that a capability still exists (watch `manifest_version`).

## Skala S1 capability plan

The [first platform](physical-design-spec.md) has two fixed tracks and retains LiDAR, camera and microphone input. This is a driver contract to implement, not a live capability announcement. Publish only installed, exercised devices and measured operating limits.

| Capability | S1 requirement |
| --- | --- |
| Drive actuation | Two independently identified XL430 velocity channels; limits and acceleration bounds determined by bench/load tests |
| Drive feedback | Actual position/velocity, temperature, voltage and inferred load; label load as inferred, never measured current |
| IMU and power state | Available OpenCR measurements with units, calibration, capture times and fault/staleness semantics |
| LiDAR scan | Selected A1 capture format, angles/ranges and validity; capture timing, gaps and measured body-frame transform |
| Camera | Selected format/resolution, frame timestamps and measured camera pose; declare moving frame only when pan/tilt is implemented |
| Audio | Selected sample format/rate/channels, capture clock, sample positions, gaps and restart boundaries |
| State | Ready/fault/link/stop state and explicit recovery rules |

Skala profile reviewed 2026-11-22. Owned hardware is Pi 4B, Camera Module 3 Standard, WM8960 onboard stereo microphones and A1 with cable/external interface board. Camera substitution is allowed after mounting/power/driver checks; publish the device actually selected and exercised. A1/interface revision, HAT mounting and cooling remain unresolved. The [current system plan](../assembly/s1-system-plan.md) owns power, wiring and commissioning requirements. No Skala runtime exists under this repo's firmware/software directories yet. The user confirms the owned Pi's prior TurtleBot3 installation is ROS 2 Humble on Ubuntu 22.04 (Jammy), correcting the earlier Jazzy recollection; OpenCR previously ran these motors. Back up and inventory the installed versions as a hardware baseline. The clean-start recommendation is Noble with native Jazzy; Skala leaves the TurtleBot3 application behind and may reuse useful low-level libraries without migrating its launches/navigation. An owned 5 V/3 A bank is planned to supply the Pi and downstream sensors, including WM8960 through the header; its loaded behavior remains to qualify. Do not publish invented stream rates, latency, fixed scan lengths or pose coordinates. Keep drive identities stable and update the manifest/frame map when modules are relocated or a pair is added.

Pitch/lateral actuators, stance/climb/self-right behaviors and camera pan/tilt are not S1 capabilities until their hardware/control is implemented and exercised. The ultimate destination is four tracked legs with independently controlled pitch and lateral movement. Use stable per-leg drive/pitch/lateral identities and measured joint feedback as each axis is installed; the exact lateral axis/frame is not yet selected. Two-leg and pitch-only stages must report their actual installed topology, not an eight-axis placeholder manifest. MG90S camera servos, if used, have no measured position echo; report commanded setpoints explicitly as such. A transported scan is not automatically a Cliste-native representation.

Capture must preserve request, acknowledgement, actual feedback and outcome as separate records. A latest-value snapshot alone cannot establish ordered audio/video or body-event history. Follow the [audio handoff](../research/2026-10-25-audio-memory-handoff.md) for capture and replay requirements.

## Open questions

The questions below were recorded with the original 2026-10-24 interface proposal. They are historical design questions, not a claim that current Talos lacks a schema or transport. Resolve Skala's remaining adapter choices against the maintained shared implementation and the current S1 system plan.

- [ ] **Where the body driver lives.** `talos/bodies/skala` inside talos, or the skala repo depending on talos. The interface is the same either way; this is about who owns releases.
- [ ] **Schema language.** JSON Schema for `params` and `fields` (portable, verbose) versus Python dataclasses with runtime validation (concise, Python-only). LOGOS is Python; is anything else ever going to publish a manifest?
- [ ] **Raw versus abstracted streams for perception.** The manifest above exposes raw samples. Should talos also define a standard way for a body to offer *derived* streams (a detected-edge event, a pose estimate), or is every derived thing a body-specific sensor with tags?
- [ ] **Sample encoding for large streams.** Camera frames and scans over ZeroMQ: raw bytes with a dtype/shape header is simplest; is there a reason to pick Arrow or similar now?
- [ ] **Behaviour compatibility matrix.** `uses` gives a conservative rule (overlapping actuators conflict). Is an explicit "these two may run together" list worth the complexity in v0.1?
- [ ] **Multi-body.** One agent, several bodies on one timeline is designed in via `body` in the envelope. Should talos also aggregate manifests into a single view, or does cognition keep them separate?
- [ ] **Learning hooks.** Does talos record anything itself (a ring buffer of samples around each behaviour event, say) or is recording entirely the agent's job? The former makes every body self-documenting for episodic memory; the latter keeps talos thin.
- [ ] **Versioning across the boundary.** When `talos_version` moves, which side bends? Proposal: the client supports N and N−1 and bodies pin one.

Current Skala sequence: preserve and inventory the existing hardware software, qualify stationary sensors and power/stop behavior, adapt two-track control, then map the exercised devices into the maintained Talos interfaces. Implement a Skala-specific adapter and recorder where needed; do not assume a new shared manifest schema or library is required.
