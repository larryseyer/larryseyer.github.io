# OSC reference page generator

`pages/projects/larry-seyer-drums-osc.html` is generated from the Larry Seyer Drums
app source. Do not edit it by hand.

## Re-sync after the app's OSC changes

    python3 tools/osc/build_osc_page.py --check   # report only
    python3 tools/osc/build_osc_page.py           # write the page

`--src` defaults to `~/AudioDevelopment/LarrySeyerDrums/src`. The app source is only read.

The build stops (exit 1) and lists what to fix in `osc_descriptions.json` when:

- `NO DESCRIPTION`: the app gained an address. Add a row to a section, or a leaf to a family.
- `STALE description`: an address was removed or renamed. Delete or rename the row.
- `UNANNOTATED runtime condition`: an address is registered inside an `if`. Check where it
  really exists and add a `notes.<leaf>.reviewed` entry (plus `exclude` or `only` if needed).
- `BANNED WORD`: page text names a third-party product, trademark, or a price.
- `UNRESOLVED`: the extractor could not work out an address expression. Extend `extract_osc.py`.

Addresses listed under `withheld` are left off the page on purpose (their names contain
third-party names). Withheld addresses and banned words are stored only as hashes
(`sha256(lowercase text)[:16]`) so those names never appear in this repo; `_about_hashes`
in the JSON shows how to add one.

## Files

- `extract_osc.py`: reads every `ControlEntry` registration and `sendReply` address
  (`python3 extract_osc.py` prints them; `--json out.json` saves them).
- `osc_descriptions.json`: wording, families (shared parameter sets), sections, withheld list.
- `build_osc_page.py`: joins the two and writes the page, reusing the header and footer
  of `larry-seyer-drums-updates.html`.
