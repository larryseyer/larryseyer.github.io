---
title: "Songs: Arranging"
summary: "Pills, the pill pool, fills, lifts, banks and playing live."
---

> Temporary quick-start for TestFlight testers until the tutorial videos are ready.

## A tour of the Songs page

The Songs page is the arranger -- this is where you build a song of your own, and where you can go beyond what Quick Pick offers. Four **player pill rows** (P1 through P4) run as timelines. Below or beside them is the **pill pool**: one column per player, showing that player's mode and style, and the section pills (**Intro**, **Verse**, **Chorus**, **Bridge**) you drag onto a lane. **Blank 120** is a silent style for building from nothing. If the timeline is empty, a faint line across the lanes says **Drag a section from below onto a lane**.

You can arrive here with a Quick Pick song already on Player 1 (one looping pill, the other players empty) and add to it, or start from a blank song: three-dot menu, **Song** group, **New**, then **New** in the **New Song?** dialog.

Along the ruler you'll find **Click**, **Undo**, **Redo** and **+** (a new blank pattern). The **edit cursor** is the green triangle. The **play cursor** is the yellow line. Under the bar ruler is the meter and tempo strip.

Follow-scrolling keeps the playhead in view while you play; if you scroll yourself, your scroll wins. You can zoom with pinch, the scroll wheel, or Z and Shift+Z on a keyboard.

With nothing selected in a pool column, you're browsing styles. With a pill selected, changing the column restyles that pill. You can mix styles in one song. Tap a pill's bar count to type a new length, and use the section-name picker to rename it.

::: iphone
On iPhone the page has three useful layouts: upright (a timeline per player), landscape, and a compact P1–P4 launcher.

![Songs page on an iPhone in the compact P1–P4 launcher layout](images/s26-iphone-songs-compact.png "The compact landscape Songs launcher, with P1 through P4 as large buttons.")
:::

::: mac
![Songs page with Pretty Shuffle on Player 1, Intro through Bridge placed, and the yellow play cursor](images/s12-songs-page-cursors.png "Pretty Shuffle sections on Player 1, from Intro through Bridge. The yellow line is the play cursor.")
:::


## Placing, moving and resizing pills

Drag from the pill pool onto a player's row. Pills snap to bars.

- **The first pill on an empty lane starts at bar 1.** After that, a pill lands exactly where you drop it.
- **Gaps are legal.** If you leave space, that space plays silence for that player.
- **If pills collide:** the dropped pill keeps its landing. An earlier pill it overlaps is clipped back to the drop point. Later pills it overlaps ripple forward.

Move pills by dragging, or nudge them with the left and right arrow keys. The same landing rules apply.

You can resize in three ways: drag a single edge; type a new length (that numeric length stops at the next pill); or resize a group from the edge, which has its own adjacency rules.

Delete or Backspace removes a pill. Double-click an empty gap to select it, then Command+Delete (or the matching menu item) closes the gap.

## Pill corners

Each pill has four corners and a mute:

- **Top left:** the bar count.
- **Top right: Loop.** On Player 1, the whole song repeats that section. On Players 2 through 4, only that pill loops.
- **Bottom left: Pre-Fill.** On the first pill, this adds a pre-roll bar. That's different from the count-in you get when recording into the Pattern Editor.
- **Bottom right: Post-Fill.**
- **Top centre: Mute.** A muted pill sends no MIDI and exports silent.

Fills follow the pill's energy and feel. The fill tint on a pill is not the same indication as the card's manual Fill button.

On a keyboard: L for loop, P for pre-fill, F for post-fill, and Command+M for mute.

A good test: loop the Pretty Shuffle Chorus, then release it into a Post-Fill.

::: mac
![Close-up of a Chorus pill on Pretty Shuffle, with the four corner controls visible](images/s13-pill-corners.png "Pretty Shuffle 120 Chorus. The four corners are the bar count and Loop at the top, Pre-Fill and Post-Fill at the bottom. Post-Fill is not turned on in this picture.")
:::

::: iphone
![Close-up of a Verse pill on an iPhone, with the four corner controls visible](images/s31-iphone-pill-corners.png "A Verse pill on P1 in iPhone portrait. The corners are the bar count and Loop at the top, Pre-Fill and Post-Fill at the bottom.")
:::


## The pill menu and working with many pills

Right-click a pill, or press and hold it, for the pill menu: Edit, Mute, Move, Copy, Duplicate, Paste, Split (Option+S), Delete, Delete with Ripple, Rename (Command+R), Export MIDI, Energy Levels, Feel (As Written or Triplet), Playback Speed (1/4x to 4x — the pill keeps its length), and Colour (Shift+C).

You can rubber-band a group of pills, or Select All Pills (Command+A). The multi-select menu can mute, move, copy, duplicate, paste, combine, delete, rename or export the group. **Combine** (Command+G) joins pills when the app is willing; it will decline when that wouldn't make sense.

You can also insert measures at the edit cursor (Command+I) and work with a time selection. Undo and Redo are one history for the whole app.

## Meter, tempo and lifts

Meter tags live in their own strip under the ruler. Long-press or right-click to insert a meter or set a tempo. Double-tap bar 1's tag to type the opening meter. When the app is a plug-in on Host Sync, it takes the host's tempo map instead.

A **lift** is a small drummer pickup into the next bar. Double-tap the ruler to place one (you'll see a caret). A lift is played on the groove's own voice and follows the pill's energy. You can't place a lift before bar 1, and a pattern with no snare or stick won't play one.

App Settings has **Auto Lifts** if you want them generated on a phrase length, with a short recipe for what the lift plays. From a controller, control change 18 places a lift.

Try Pretty Shuffle with Auto Lifts every four bars, then compare that with a couple of hand-placed lifts.

## Playing a song live

When the transport is stopped, tapping a pill or a phrase tab jumps there. When it's playing, the tap is **armed** — a white ring blinks — and the jump happens according to **Launch Quantization**: Immediate, Next Beat, Next Bar, or End of Pill. Tap again for the end of the bar; tap the playing pill to cancel.

**Auto Fill on Pill Change** can throw a fill as you jump. You can loop a section until you're ready, then release it. Stop returns both cursors to the start of the current pill.

On iPhone, the phrase tabs are the main live surface.

## Songs, banks and set lists

Songs live in **banks** of slots **0 through 99**. The slot number is also the Program Change number, so a controller can recall a song by that number.

From the three-dot menu's **Song** group you can New, Save, Save As, Rename, Load, Export and Delete. The bank grid is one column of a hundred slots; tap to load or save. A per-slot menu includes **Lock** -- a locked slot has a badge and can't be saved over or deleted.

You can have up to 127 banks. Use the previous/next arrows, the add-bank button, and the bank menu (jump, add, rename, delete). The song stepper only steps to occupied slots and never wraps across banks. Tap the name for the bank list; hold the name to rename the song in place. **Find Song** (Command+F on Mac and iPad) searches across banks.

The standalone app still remembers the last slot you were in, but that is not the first thing you see. If **Show Quick Pick at startup** is on (the default), Quick Pick opens first; **Edit in Full App** then puts you in the full app with the Quick Pick song. Testers can turn that switch off in the three-dot menu, under **App Settings** → **Quick Pick**; the app then opens on the last song instead.

A good test: make a new bank, put three short songs in it, and step through them while the app is playing.

---

[Previous: Energy and Feel](05-energy.md) · [Index](index.md) · [Next: The Pattern Editor](07-pattern-editor.md)
