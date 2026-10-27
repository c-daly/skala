# Audio memory evidence for Skala

2026-10-25. **Skala is not built yet.** Cliste's audio/visual memory experiments can
inform capture and later teaching activities while construction and remote-control
play proceed independently. Processing can run on a central host; onboard cognition
is not required. No hardware or Sophia integration is claimed by these results.

The separate Sophia image-memory connection was already exercised on October 23
with numerical and trained codecs, including teaching and native workspace restart.
The [shared milestones](../../../vault/20-areas/research/Cognition%20and%20Embodiment.md#milestones)
tracks that integration alongside Skala. This handoff concerns transferring the
later audio result to physical capture; it does not restart the image integration.

## What Skala can reuse

The [Cliste evidence index](../../../cliste/docs/audio-compatibility/README.md)
and [latest result](../../../cliste/docs/audio-compatibility/sequence-result.md)
provide methods, all conditions, figures, saved-home replay and original failures.
The [shared programme](../../../vault/20-areas/research/Cognition%20and%20Embodiment.md)
and [LOGOS/Sophia/Talos handoff](../../../vault/10-projects/LOGOS/experiments/2026-10-25-cliste-audio-transfer.md)
record ownership and prospective integration requirements.

Four ordered half-second sounds retrieve an associated retained visual experience.
On new qualification source recordings, moderate recall is 213/216 with no wrong
positive answers; +80 ms offsets are 24/24. Environmental false recognition is
1/100, and shuffled/repeated sequences are refused in all 24 cases each. All 108
earlier memories survive growth to 300. Removing order raises environmental false
recognition to 26/100 without changing positive decisions.

All bounded usability floors pass, but the overall verdict remains partial:
challenge gain is 8.3 points against a 15-point target, and strong noise accepts
only 1/24. These are distorted cues from enrolled recordings, not recognition of
new birds, voices or objects. A loudspeaker replay captured by a microphone is a
new acoustic condition requiring qualification. Sound-to-sight recall does not
yet locate a sound or tell the robot where to turn.

## Current platform state

The repository contains actual parametric CAD and generated P0 assemblies:
[dimensions](../../cad/params.py), [assembly code](../../cad/assembly_p0.py), and
[CAD instructions](../../cad/README.md). The inspected `firmware/opencr_reflex/`
and `software/talos/` trees contain planning READMEs, not executable drivers.
The user's not-built status concerns the physical robot; it does not erase the
existing CAD work. No physical microphone, camera, room or motor test occurred.

The added [P0 design](../../../vault/10-projects/skala/2026-10-24-physical-design-spec.md)
and [Talos capability manifest](../../../vault/10-projects/LOGOS/talos/2026-10-24-capability-manifest-design.md)
now give the integration a concrete contract: body-defined sensors, actuators,
behaviours and state, with separate acknowledgements, feedback and outcomes.
The draft P0 sensor list includes IMU, servo feedback, battery and 2D scan; camera
and microphone are absent. Their addition and capture qualification must be
explicit before running this audio game. Neither the manifest nor these audio
results establish native VSA encodings for the other body signals.

## Capture requirements for a future adapter

These are proposed obligations, not a claim that capture is implemented:

| Preserve | Reason and current evidence |
| --- | --- |
| Audio sample rate, channel mapping, capture clock and sample positions | Current replay uses mono 16 kHz. Log any resampling/downmixing explicitly and keep the encoder calibration/version fixed during comparisons. |
| Camera timestamps and measured audio/video clock relation | Supplied sound/frame correspondence is what the memory experiment tests. Arrival order alone must not invent correspondence. |
| Gaps, duplicates, reordering and restart boundaries | Missing data is not silence. A latest-value snapshot interface alone does not guarantee an ordered audio stream. |
| Gain/AGC settings, clipping, microphone placement and operating condition | The selected encoder handles some simulated distortions, but physical channel changes and motor noise have not been measured. Relative level is not calibrated sound pressure. |
| Observed versus recalled provenance and uncertain status | A recalled picture is a memory, not a camera reading. A candidate similarity is not confirmed recognition. |
| Body/capability identity, manifest version, `t_body`, mapped `t_agent`, sequence numbers and action events | Use the existing Talos manifest design. Keep requested action, acknowledgement, measured feedback and completion/abort distinct when pairing sound with a body episode. |

Keep raw capture bounded and separate from persistent learned memory. A replayable
bench capture can use explicit recording files with provenance without requiring
the robot to retain its entire lifelong stream. Use Talos for sensing/action
interfaces; reuse Cliste's maintained encoder and memory instead of copying them
into `software/talos/`. The local body-layer folder and the LOGOS Talos repository
are related responsibilities, not evidence that their integration exists.

## Bounded replay contract and costs

Use the native API or the [documented CLI command](../../../cliste/docs/audio-compatibility/sequence-result.md#cost-use-and-validation)
with sequence run 002's home and explicit `policy.json`. The tested policy is
score .15, margin .005, order advantage .01, minimum block .10; generic defaults
differ. The CLI requires 33,280 PCM16 mono samples at 16 kHz: 80 ms prelude plus
2 seconds of sound. Temporary query state supports chunk delivery and restart;
it is not autonomous event segmentation or indefinite streaming.

Three 0/40/80 ms alignment hypotheses are alternatives, not extra votes. Four
native contexts 50 ticks apart provide the tested sequence path; device-clock
mapping must be defined and checked by a future adapter. The index is bounded to
512 auditory rows/1,024 contexts; the measured life has 300 encounters.

Acquiring a query takes 2.08 seconds. Processing and visual readback then took a
median 577 ms on the tested host, excluding startup and file I/O. The saved home
is 604.5 MiB; final audio rows occupy 37.5 MiB and the disposable index adds about
37.5 MiB RAM. Full costs and the 240-test validation scope are in Cliste's record.
Measure throughput and tail latency on the chosen deployment host before designing
interaction timing around this. Motor/reflex control must have its own timing
requirements rather than waiting on this recall query.

## Proposed experiment sequence

This is the audio branch of the [recentered experiment agenda](../../../vault/20-areas/research/2026-10-25-sophia-cliste-experiments.md).
The shared body-memory path first checks truthful event delivery (T1), then recall
of one action episode with qualified sensory input (T2). This audio sequence can
support that path or remain a separate teaching game; it does not gate P0's
remote control, scripted behaviours or the existing Sophia image integration.

The offline sound/appearance association and native restart checks already have
results. The work below transfers that function to the selected host, transport and
physical channel. Reuse the recorded reference; no new audio study or full Sophia
deployment is required to begin the transport comparison.

1. Replay the frozen Cliste home and supplied queries on the intended central host.
   Preserve accepted/refused decisions, decoded visual content and the old-memory
   checks. This requires no robot and no Sophia integration.
2. Once a capture path exists, compare direct-file and transported delivery of the
   same samples, including chunk boundaries, delays, missing data and restart.
   Measure sample/frame alignment; preserve four disjoint blocks as evidence.
3. When microphone/camera hardware is available, record a fixed bench panel:
   enrolled sounds and new recordings, unfamiliar sounds, silence, distance/gain,
   reverberation, clipping and background noise. Separate calibration recordings
   from fresh confirmation. Add motor-off/on comparisons when an assembled platform
   can produce the relevant operating noise.
4. After this passes prospective use-specific floors, try the bounded teaching game:
   co-observe an appearance and sound, later cue with sound, inspect the recalled
   appearance or explicit refusal. Keep supplied episode boundaries visible.
5. Treat recall-guided looking followed by a confirming or contradicting observation
   as a subsequent closed-loop experiment. Generalizing to unfamiliar birdsong
   requires acquired auditory/visual groupings and their relationships first.

These are future experiments, not authorized implementation or completed tests.
Set acceptance floors, drift alerts and optimization targets before each comparison;
record false acceptance and false refusal together, with storage and latency.
Retain failed attempts and old criteria. Cliste's next research target is weak-block
handling under strong noise while preserving order-sensitive refusal.
