# Lessons from the ATM 3D explainer, for the Airacuda Unreal project

Lessons from building the ATM explainer, set out for an Unreal Engine explainer of the Bell YFM-1 Airacuda.

## Where these come from

The session "ATM 3D explainer: code vs Three.js" ran outside the cloud environment this file was written in, so its conversation could not be read. These lessons come from the five pages that project published on 17 September 2026. The pages were read as code; they were not rendered. Comparing the versions shows **what** had to be fixed, not **why**.

| Time (UTC) | Page | Steps | Meshes |
|---|---|---|---|
| 09:45 | CMD-V5 dispensing unit, 3D: a close-up of one cassette's note extractor | 1 loop | 21 |
| 09:56 | Inside an ATM, version 1 | 14 | 26 |
| 10:09 | Inside an ATM, version 2 | 21 | 79 |
| 10:52 | Inside an ATM, version 3 | 29 | 119 |
| 16:46 | Saxon VII K valve gear: a 2D side view, solved live from real dimensions | 8 stages | about 31 parts |

On "code vs Three.js", the pages show three set-ups:
- CMD-V5 and ATM v1 load three.js from a CDN.
- v2 and v3 paste the whole library into the page, taking it from 15 KB to 628 KB.
- The last page (Saxon) uses no three.js at all. It is plain 2D code that solves the linkage, and its "rig notes" are written for a 3D rig built elsewhere.

## The lessons

### 1. Get dimensioned drawings before modelling, and keep one dimensions table

**What happened**
- The ATM was built from the service manual's text alone: "I could read the manual's text but not its drawings."
- v3's footer says "Proportions come from no drawing."
- The cassette rows moved in every version: y = 150/280/410/540, then 130/238/346/454, then 196/300/404/508. Because the cameras were typed in by hand for each step, every move meant re-typing them (lesson 7).
- The Saxon page did it right. All dimensions sit in one table, split into "prototype figures" and "representative values … swap them for the figures off your drawing and the whole solve follows".

**For the Airacuda**
- Collect three-view drawings and photos first, then pick one variant and, ideally, one airframe.
- Sources disagree on basics. Wikipedia's own variant list puts tricycle landing gear on the YFM-1A, while its main text gives it to the YFM-1B. Engine horsepower also differs between sections.
- Keep one DataTable or spreadsheet with these columns: part, dimension, value, source, confidence (drawing / photo estimate / representative). Convert to Unreal units (1 uu = 1 cm) in one place only.

### 2. Orientation and direction mistakes lasted longest: check each against a source

**What happened**
- The bank card was modelled upright in v1 and v2 (`box(86,54,2)` pushed face-first). v3 fixed it: "The card is held flat, not upright." / "Short edge first, into a horizontal slit."
- In v2 the note carriage sat on the exit side of the stack and moved backwards. The CMD-V5 close-up, made 24 minutes earlier, had it right. The whole-machine model appears to have been rebuilt rather than built from that verified close-up.
- Even v3 moves the travelling note lying flat (`bx(150,3,70)`), while the cassette stores notes standing on edge.

**For the Airacuda**
- For every moving part, record its axis and its direction of travel or rotation, with a source. Examples: which way each propeller turns, the landing-gear retraction path, how the nacelle guns traverse and elevate, and the flap and aileron hinge lines.
- Review each mechanism in orthographic views.
- Once a sub-assembly is verified, reuse it; don't rebuild it.

### 3. The captions got ahead of the model

Every part a step names must exist, be connected, and move as described.

**What happened**
- v2's step "One motor for all of them" says a single central motor turns "one long shaft", and adds "Watch: the shaft turns, but nothing else does." There was no shaft mesh, and the animation turned the four rollers instead.
- v2 also lit the gap-adjusting cams to stand in for a magnetic coupling.
- v3 added the motor, belt, pulleys and vertical shaft, but did not connect them:
  - The two pulleys sit on the same axis at overlapping heights: motor pulley at (−175, 196, 120), r 20; driven pulley at (−175, 200, 120), r 24. So the "belt" connects nothing.
  - The short shaft meant to drive each extractor roller ends at x = −121. The roller starts at x = −75, on a different axis.

**For the Airacuda**
- Example: the engines drive the pusher propellers through 5 ft (1.5 m) extension shafts. If a step mentions them, model them and connect them.
- Before a step is done, check each noun in its caption. It needs a component that:
  - exists,
  - is highlighted in that step,
  - shares an axis or pin with whatever drives it,
  - and moves the way the text says.
- A small editor check can catch the connection errors: driving and driven parts are coaxial, and linked pins keep their distance across the motion range.

### 4. Drive each mechanism from one input; calculate everything else

**What happened**
- The ATM pages hand-pick per-frame speeds.
  - In v3 the extractor roller turns 0.22 rad per frame. At 60 fps its surface moves at about 290 units/s, while the note it drives moves 94 units in 5 s (about 19 units/s). That is about 15 times too fast.
  - The pulleys turn at `u*6` and `u*3.4*g`, which doesn't follow from their sizes.
  - All motion changes speed with the monitor's refresh rate.
- The Saxon page does it right.
  - One input, the crank angle, is integrated from speed with a capped time step, and every rod is solved from it each frame.
  - Smaller wheels turn faster by the radius ratio.
  - Its rig note: "drive one custom property (distance rolled) and derive wheel rotation from it. Never keyframe the wheels directly or they will slip".

**For the Airacuda**
- Give each system one control: a Control Rig control, or a Blueprint variable exposed to Sequencer. For example:
  - engine RPM drives propeller rotation through the reduction ratio,
  - gear position from 0 to 1 poses every link of the retraction,
  - gun elevation.
- Keyframe only those controls in Sequencer.
- Base all motion on DeltaTime or Sequencer time.

### 5. Prototype tricky linkages as a quick 2D solve before rigging in 3D

**What happened**
- The last thing made that day was the Saxon valve gear: a 2D solver with real dimensions, a crank scrubber, and live readouts.
- It escalates only as far as each linkage needs:
  - closed form where possible ("no solver needed"),
  - circle intersection for two-link loops ("Take the lower root"),
  - and for the one remaining loop, a numeric search with a rule that picks the physically correct solution.
- Each stage ends with a "Rig note" on how to build it in 3D.

**For the Airacuda**
- Work out the landing-gear retraction, and any other linkage you show, in 2D first.
- Sweep it through its full range and check it never jams or flips.
- Then build it in Control Rig.

### 6. Housings hid the parts the steps were about: plan cutaways from day one

**What happened**
- In v2, three groups of parts sat inside opaque boxes during the very steps about them:
  - the card and read head, inside the reader box,
  - the note stack, carriage and helper roller, inside the cassette,
  - the bundle, inside the stacker.
- v3 made every enclosure a fading "shell" and added an Isolate mode, on by default, which fades parts not in the step to 7%.
- v3 still missed one. "Two boxes, not one" highlights the reject and retract compartments, which sit inside an opaque reject box that stays fully visible.

**For the Airacuda**
- This is the central problem for this aircraft:
  - a gunner sits in the front of each engine nacelle,
  - the engines sit behind the gunners,
  - the auxiliary power unit is in the belly.
- Tag every mesh as Enclosure or Mechanism.
- In each step, ghost or section-cut the skin in front of the focus parts.
- Outline the focus parts with Custom Depth / stencil so they read through anything left in front.
- Check every step's camera view for hidden focus parts, for example with line traces.

### 7. Hand-placed cameras broke whenever the layout moved: frame from the parts

**What happened**
- v1 and v2 used typed camera coordinates per step, e.g. `c:[0,410,60,470,0.95,0.1]`.
- v3 computes the framing from the step's parts: distance = radius / tan(FOV/2) × margin. It also added pan and "Recentre", and widened the zoom and pitch limits.
- The 3D view grew from 430 px tall (v1) to 620 px (v3), plus a "Taller view" option.

**For the Airacuda**
- Frame the union of the focus components' bounds, with per-step yaw, pitch and margin.
- Any user input should cancel the camera glide.
- A Recentre button returns to the step's view.

### 8. Anchor labels to parts and show them per step

**What happened**
- v1 and v2 put labels at fixed points, shown from their step onwards. By the end of v2, all 20 were on screen.
- In CMD-V5 the moving carriage drifts away from its label.
- v3 attaches each label to its part (world position plus offset, every frame) and shows it only in that part's steps.
- v3 still doesn't hide a label whose part is behind something.

**For the Airacuda**
- Use UMG labels projected each frame from sockets on the parts, shown per step, with leader lines.
- Dim or hide a label when its part is hidden.

### 9. Give every part its own material

**What happened**
- In v2 the tamper mesh used the shared highlight material, so fading it made every highlighted part pulse too.
- v3 clones a material per mesh and highlights by tinting its colour.

**For the Airacuda**
- Use a Dynamic Material Instance (or Custom Primitive Data) per component.
- Never change a shared material at runtime.
- Restore defaults when each step starts.

### 10. One idea per step, and expect the step count to double

**What happened**
- The step count grew from 14 to 21 to 29.
- v1's single step "A note is pulled out" packed the carriage, helper roller, ramp, swinging-arm roller, gap and two cams into one paragraph. v3 spreads the same mechanism over six steps: "Inside: notes standing on edge", "The helper roller", "The sloped ramp", "One note is driven out", "The gap does the real work", "Set by hand, with two cams".
- In v1, state leaked between steps: one roller kept spinning for every step after its own.
- v3 stores each step as data:
  - parts to frame, highlight and keep visible,
  - loop length,
  - timed captions,
  - and a reset to the rest pose when the step starts.

**For the Airacuda**
- Use one DataTable row per step and one Level Sequence per step, with "Restore State" on.
- Put captions on an event track.
- Build navigation that copes with 30+ steps from the start.

### 11. Say on screen what is sourced and what is guessed

**What happened**
- Every ATM step carries a source tag: "from the CMD-V5 service manual", "from the CMD-V4 service manual", or "general ATM practice, not model-specific".
- v3's footer says the drive shaft's orientation is not stated in the manual, "so that part is inference".
- CMD-V5 says note thickness is "exaggerated about tenfold".

**For the Airacuda**
- Tag each step as Airacuda-specific source, period practice, or inferred.
- Add an "About accuracy" panel listing what is guessed or exaggerated.
- Given how much the sources disagree, this matters even more here.

### 12. Keep every version and review each one against its captions

**What happened**
- Each ATM revision was published at a new link, so earlier versions stayed available: v1 at 09:56, v2 at 10:09, v3 at 10:52.
- Each revision fixed mismatches visible in the one before.
- Some code still hides problems. v2 and v3 wrap each step's animation in `try{…}catch(e){}`, so a broken step fails silently.

**For the Airacuda**
- Keep the project under source control.
- Note what each review pass fixed.
- Review every step by asking: does the motion show exactly what the caption says?
- Let errors surface instead of swallowing them.

## Starting checklist

1. Gather drawings, manuals and photos. Pick the variant. Build the dimensions table with source and confidence (lessons 1 and 11).
2. List each moving system, its one input, and the axis and direction of every part, each with a source (2 and 4).
3. Solve the linkages in 2D first. Sweep each through its full range (5).
4. Build pivots and hierarchy. Check that driving and driven parts actually connect (3).
5. Tag enclosures and mechanisms. Choose the cutaway method for the nacelles and the belly (6).
6. Write the step table: one idea per step, with focus, highlight and context parts, duration and timed captions (10).
7. Add camera framing from bounds, per-step labels anchored to parts, and per-part materials (7, 8 and 9).
8. Review each step for caption-vs-motion, hidden parts, and orientation, and log what each pass fixed (12).

## Sources

- Airacuda facts (gunner stations, extension shafts, APU, variant discrepancies): [Bell YFM-1 Airacuda, Wikipedia](https://en.wikipedia.org/wiki/Bell_YFM-1_Airacuda).
- ATM, CMD-V5 and Saxon evidence: the five published pages from 17 September 2026, quoted from their code.
