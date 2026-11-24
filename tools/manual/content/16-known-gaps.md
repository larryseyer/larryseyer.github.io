---
title: "Known Gaps in This Beta"
summary: "What is unfinished, provisional, or not in this build."
---

> Temporary quick-start for TestFlight testers until the tutorial videos are ready.

This is the honest list of things I don't want you to treat as surprises or as bugs you have to rediscover. If you hit something that isn't on this list, please [report it](17-how-to-report-problems.md).

## Not in this TestFlight build

- **VST3, CLAP and the installer AU plug-in** are not included. This beta is the standalone app on Mac, iPad and iPhone, plus the AUv3 plug-in.
- **Windows and Linux** come later.
- There is **no native AAX** build for Pro Tools.
- **Kit Packs** are planned for summer 2027 and are not available yet.
- There is **no trial or purchase flow** to test. This TestFlight build is fully unlocked, on purpose.
- **Sync Folder** (a shared-folder sync in App Settings → Storage) is hidden in this build.
- **“Marked section”** in audio export is not ready.
- **Sharing one song from the bank grid** is planned, not in this build.
- A full REAPER-style multi-select (Command-click toggling, keyboard cut and copy of pills) is planned, not in this build.
- **MIDI Learn** is on mixer faders only. There is no global bindings pane, and you can't learn arbitrary controls yet.
- Some bigger sync ideas (a companion plug-in, bidirectional folder sync) are parked and not in this beta.

## In the build, but provisional or unfinished

- **The Sounds page may change.** Kits, Morph and the synth machines work, but the page is not frozen. Synth 3 is being corrected, and the other synth kits are still waiting on my listening pass.
- **Plugin Auto routing.** In a plug-in, Auto is meant to use extra outputs once the host has enabled them. In this beta it still keeps the mix on the main stereo pair. Use **Force Multi-Out** for separate outputs. See [Using the Plug-in in a Host](12-using-the-plugin.md).
- **Force Multi-Out on a running Mac plug-in** may stay stereo until you press **Rescan Outputs** or reload the plug-in. On iPhone and iPad, reload the plug-in in the host; Rescan Outputs does not apply the change there.
- **Quantize** has new tools I'm still A/B'ing. If it feels wrong, tell me.
- **Device power budgets** on iPhone and iPad are calibrated and still marked provisional in the code. The messages and the load meter are real; the exact limits may still move.
- **Recording into a pill** from the iOS app while it is attached to an AUv3, and some attached-editing paths, are still being retested.
- **Dragging MIDI files** onto a pill row or pool column is still being retested. Use Import → MIDI File if a drag doesn't take.
- Host-specific steps (Logic Pro, REAPER, Ableton Live, Cubase, Studio One, Bitwig, GarageBand, AUM and others) have not all been demonstrated end-to-end for the finished tutorials. If a named host behaves unexpectedly, that report is especially useful — please include the host name, version and plug-in format.

## Things that can look like bugs, but are how it works

- **Save is what makes an edit permanent.** Done in an editor is not the same as Save.
- **Gaps on a pill row are legal** and play silence for that player.
- **Factory Asleep** is silent, so it plays no fill. The name itself is not a mute; an edited level can change that.
- **Lock** freezes preset, kit, energy, pill and swing, and it disables the card's volume and Fill gestures. Mute and Solo stay live, and a MIDI Fill still works.
- **A player preset leaves Energy alone.** It restores sound and mix only.
- **Ableton Link** shares tempo and phase. Start/stop sync is a separate option.
- **Output names** in a host are defaults, not fixed destinations. FX returns default to the main pair.
- **Per-drum multi-out** sums all four players' kicks on one pair, and it bypasses player-bus and master processing.
- **Summed stems need not equal the master mix**, because the master has its own processing. The click is never exported.
- **Quick Pick's remembered pair** is not the same thing as a Song you saved.
- A feature called **Morph** is controlled in App Settings, not from the MORPH chip. The chip only reports On, Off or Building. The kick does not morph.
- On the Sounds page, a pad labelled in a way that looks like “Chime” may not be the same thing as the Chime row. If a chime or bell comes out somewhere unexpected, tell me, and mention whether you struck a pad, played a pattern, or used Energy's Bells choice.

---

[Previous: Saving and Backups](15-saving-and-backups.md) · [Index](index.md) · [Next: How to Report Problems](17-how-to-report-problems.md)
