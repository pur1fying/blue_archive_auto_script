# Global: Chair Makoto's Lux Summer Getaway

This event supports the normal daily activity sweep entry. Configure quest numbers
and sweep counts in the existing activity settings. Selected quests must already
have three stars; normal BAAS AP and sweep availability checks remain in use.

The event module delegates directly to `activity_sweep`. No manual Quest-page
entry, auto-clear/story/challenge implementation, mini-game automation or team
selection behavior is added.

`mission` contains 12 null placeholders solely because the native sweep helper
uses its length for quest-number OCR. No enemy attributes have been inferred;
auto-clear is deliberately not exported. The AP table is indexed from 1, with
quests 1–4 costing 10 AP, 5–8 costing 15, and 9–12 costing 20.

The 1280×720 entry templates use character art from the top-right event icon and
bottom-left banner, excluding localized text and the remaining-days label.
They are registered for all Global locales; recognition was validated against
English screenshots only. Korean and Traditional Chinese still need live checks.
The in-event mini-game icon is not registered as an activity entrance.

Data reference: https://bluearchive.hatenablog.com/entry/2026/08/05/201254

Offline checks (no device, game account, OCR server or AP needed):

```sh
python -m unittest develop_tools.test.test_makoto_event
```

Optional screenshot regression: set `BAAS_MAKOTO_SCREENSHOTS` to a local directory
containing `makoto-ref-home.png`, `makoto-ref-story.png`, and `makoto-ref-quest.png`
at 1280×720. Account screenshots are not included in this repository. Full live
sweep transitions have not been tested.
