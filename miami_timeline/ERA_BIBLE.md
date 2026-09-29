# Miami — Walking Through Time: Era Bible

First-person POV walk through Miami, from c. 2,000 years ago to **September 2026**: 23 scenes, 6:56 at 30 fps (12,480 frames), under the 7-minute limit.
One continuous walk along a fixed route; the city transforms around you.

**How to read confidence tags**
- **[S]** = supported by a source found during research (linked at the bottom).
- **[G]** = general historical knowledge, *not* verified in this research. Check before finalising.
- **[D]** = a creative/design decision, not a historical claim.
- Lines of dialogue are **written for the film** unless marked as a real quote. They are drafts: have Spanish, Bahamian-English and period-English lines reviewed by native speakers or historians.

---

## 0. Global design

### The route (spatial anchor)
Mouth of the Miami River / Brickell Point (south bank) → cross to the north bank (Fort Dallas, later Royal Palm Hotel) → inland along Avenue D (today's S Miami Ave) and Flagler St → Biscayne Blvd and the Freedom Tower site → back to the Brickell skyline.
Cutaways (Miami Beach, Coral Gables, Homestead, Liberty City, Surfside) are short and always return to the route.

### POV rules [D]
- Eye height ~1.6 m, walking pace ~1.3 m/s, gentle head-bob, no cuts inside a scene; the "cut" is the transformation.
- You have **hands**. In every scene a person hands you (or you pick up) one **hand-off object**. The object is the scene's "explainer".
- People "explain the era" by **doing**, not lecturing: 2–3 explainers per scene, each doing one clear action within ~3 m of the path. A spoken line is optional and never longer than ~6 seconds.
- On-screen text (bottom-left event list, bottom-centre year + census) follows the Tokyo/London format.

### The bookend [D]
**Opening:** you arrive in a **dugout canoe** poled up the mouth of the Miami River at dawn (this replaces Tokyo's cart; a dugout is the Tequesta vehicle and is Miami's own). Your first hand-off is a **shell drinking cup** (shell cups are documented Tequesta tools [S]).
**Closing:** you walk down W Flagler St past the Museum of Miami's 1926-hurricane exhibit, step onto a Brickell crosswalk, and the last hand-off is a **cafecito cup**, then the title card **MIAMI 2026**. Shell cup → coffee cup: the same gesture across ~2,000 years.
Alternate opening if the canoe is too costly: wade across seagrass flats onto the Brickell Point shell midden at first light.

### Transformation vocabulary [D]
Pick one or two per transition, so they don't all feel the same:
structures grow/decay in time-lapse · vegetation reclaims · sun/moon sweep · weather front rolls through · water level rises/falls · smoke/dust/mist wipe · objects in your hands morph into the next hand-off.

### Cast & sensitivity notes
- **Tequesta:** no reliable record of their language exists in the sources I found. **Do not invent Tequesta words.** Use non-verbal action, ambient sound and text cards. Consider consulting HistoryMiami and Miami-Dade County historic-preservation staff on depiction. [D]
- **Seminole / Miccosukee:** consult the tribes' cultural/historic-preservation offices for clothing, body language and any spoken lines. [D]
- **Enslaved people at Fitzpatrick's plantation:** show them as people with names and work, not as scenery. Their removal by Fitzpatrick in Jan 1836 is documented [S].
- **Black Miami (Colored Town / Overtown):** 162 of the 368 voters at incorporation were Black, and over half of those Bahamian [S]. This is a foundation of the city, so keep it visible.
- **Riots (1980) and Surfside (2021):** aftermath and memorial only. No re-enactment of violence or collapse. Do not use real victims' likenesses. [D]

### Blender implementation hints [D]
- Sky: Nishita/Hosek sky with sun-elevation and haze per scene (values below). Add volumetric fog for dawn/mist/smoke.
- Per-era **film look**: add a LUT/colour-balance node stack in compositing (warm sepia-green for 1500s–1890s; sun-bleached for 1898–1926; low-contrast desaturated for 1942; Kodachrome-ish for 1959–65; faded 35 mm for 1980; video-camcorder softness for 1997; clean digital for 2010s). Fine grain amount rises then falls across the film.
- Rain/wind/dust: particle systems with a shared wind force field so the transformations between storms feel continuous.
- Crowds: low-poly rigged NPC variants + Mixamo-style walk/idle/work loops; hero NPCs only within ~5 m of the path.

---

## 1. c. 2,000 years ago — Tequesta village and the Miami Circle
**Slot:** 0:00–0:18 (18 s) · **Type:** — · **Overlay:** none · **Route:** river mouth, Brickell Point (south bank)

**Atmosphere [D]:** first light, low tide, ground mist on the water; sun at ~5° elevation, warm 3200–3800 K light against cool blue shadow; palette = mangrove green, silver water, ochre limestone, smoke grey. Slow, quiet, almost documentary. Very light grain.
**Sound [D]:** water lapping the canoe hull, mullet jumping, ospreys, cicadas starting, wind in palm fronds. **No music, no speech.**
**Who's there [S]:** men fishing and hunting from dugouts (sharks, sailfish, manatee, porpoises); women and children collecting clams, conchs, oysters and turtle eggs in the shallows. Manatee was a delicacy reserved mainly for chiefs and leaders.
**Look [S]:** very little clothing: breechcloths (possibly palmetto fibre) for men, Spanish-moss skirts for women.
**Environment [S]:** palmetto-thatch roofs (like Seminole chickees) on temporary woven-mat walls; coontie plants (roots ground to flour after removing toxins, made into unleavened bread); saw palmetto, sea grape, cocoplum, prickly pear, pigeon plum, cabbage palm.
**Tools/props [S]:** shell and shark-tooth hammers, chisels, fishhooks, drinking cups and spearheads; dugout canoes.
**The Miami Circle [S]:** a 38-ft ring of post holes cut into limestone at Brickell Point, discovered in 1998; radiocarbon on wood ~1,800–2,000 years old, with published estimates for the site from 500 BC to AD 750 (dating is debated). Show a round palmetto-thatched structure on the ring, with post holes visible at the footing. Use a title like "c. 2,000 years ago" and **not** a fake-precise year.
**Hand-off:** a Tequesta woman hands you a **conch or clam-shell cup** of water.
**Text:** "TEQUESTA · BISCAYNE BAY" (title card in first 8 s) · bottom-left: "Miami Circle — a 38-ft ring of post holes in bedrock".
**Transformation out:** mangrove shoreline recedes, a Spanish longboat's hull replaces the dugout under you.
**Confidence:** diet/tools/clothing [S]; the exact look of a Tequesta house is [D]. Conch-shell trumpet is *not* verified for the Tequesta [G] → leave it out.

---

## 2. 1513–1570 — Spanish contact and the first mission
**Slot:** 0:18–0:38 (20 s) · **Type:** — · **Overlay:** none · **Route:** river mouth, south bank

**Atmosphere [D]:** heavy midday tropical light (sun ~70°, 5500 K, hard shadows), humid haze; palette = whitewashed sail, black cassock, pine-log brown, Spanish red-gold. The scene is short, so it plays as two beats: 1513 sail on the horizon, then March 1567 at the stockade.
**Sound [D]:** creaking rigging, hammering, Spanish murmuring, Latin prayer, a bell. Cicadas underneath.
**Facts [S]:** Ponce de León is said to have reached "Chequescha" in 1513 (traditional account; historians debate the exact landing). In March 1567 Menéndez de Avilés left 30 soldiers and the Jesuit brother **Francisco Villareal** at a stockaded mission on the south bank of the river, below the Tequesta village. The soldiers built palisades, a **cross made from a pine tree** at the centre, and **28 huts**. The chief's brother had gone to Spain (converted); the chief's nephew went to Havana with the Jesuits. Soldiers killed the chief's uncle, trust collapsed, and Villareal abandoned the mission in **1570**.
**Look [G]:** soldiers in morion helmets, breastplates or leather jerkins, slashed doublets and arquebuses; Villareal in a plain dark Jesuit habit.
**Explainers [D]:** Villareal teaching a few Tequesta words with a slate; a soldier stacking pine logs on the palisade; a Tequesta elder watching from outside the wall.
**Hand-off:** Villareal presses a **wrought-iron nail** (or a string of glass beads) into your palm. [G] on the exact trade goods.
**Speech (draft, for review):** Villareal in 16th-century Spanish, e.g. *"Hermano, aquí no venimos a tomar, sino a dar."* (Brother, we are not here to take, but to give.) · Subtitled. [D]
**Text:** "1513 — Ponce de León reaches 'Chequescha'" · "1567 — Jesuit mission, south bank" · "1570 — mission abandoned".
**Transformation out:** the stockade rots and burns in time-lapse; mangrove and sea grape reclaim it; the year counter skips through the empty centuries.
**Confidence:** events [S]; clothing/armour [G]; dialogue [D].

---

## 3. 1836 — Second Seminole War: Fort Dallas and Cape Florida
**Slot:** 0:38–0:56 (18 s) · **Type:** War · **Overlay:** none · **Route:** north bank of the river

**Atmosphere [D]:** two beats. (a) Dawn: cold-blue light on an **abandoned plantation** with unharvested fields, then the army lands. (b) Night: a **red-orange fire** across the bay at Key Biscayne. Palette = olive, dull blue wool, whitewashed logs, then fire orange on black. Slight film grain, slight vignette.
**Sound [D]:** bugle, drum, oars in rowlocks, bullfrogs at night, then distant gunfire and one **muffled explosion** across the water.
**Facts [S]:** the fort was built on **Richard Fitzpatrick's plantation** (north bank) in 1836 and named for Commodore Alexander Dallas. Fitzpatrick had **removed his enslaved workers in Jan 1836** and closed the plantation. The first commander was Lt. Powell. The fort had **ten barracks, blockhouses, stables, a blacksmith forge, a hospital tent, kitchen and bake house**; garrison of **51 soldiers** in one account. The Army occupied it much of the time 1836–1857. After the war, Fitzpatrick's nephew **William English** restarted the plantation. On **23 July 1836** Seminoles attacked the **Cape Florida lighthouse**; assistant keeper **John W. B. Thompson** and **Aaron Carter** (an African American man) held out, Thompson dropping a **keg of gunpowder** down the tower; Carter died of his wounds; the light stayed dark until 1846.
**Look [S/G]:** Seminole men in **turbans made of shawls, calico shirts, breechcloths and neckerchiefs**, often with silver bands [S]. US soldiers in dark-blue wool coats and sky-blue trousers [G].
**Explainers [D]:** a soldier hauling a barrel up a plank; a carpenter squaring a log for a blockhouse; an empty row of plantation cabins with tools left behind.
**Hand-off:** a soldier passes you a **tin canteen**.
**Speech (draft):** a sergeant, in plain 1830s American English: *"Keep the cartridge boxes dry. They'll not wait for the rain."* [D]
**Text:** "1836 — Fort Dallas built on the Fitzpatrick plantation" · "23 July 1836 — Cape Florida lighthouse attacked".
**Transformation out:** the fort's log walls weather and shrink; the fire fades to a lamp; a trading post's lamp lights inside.
**Caution:** sources conflict on whether the coquina building at the site dates from the war or from English's plantation (1840s). Use **log/frame buildings** for 1836 and reserve coquina for 1840s if you show it. [S/G]

---

## 4. 1871–1892 — Brickell's trading post and the barefoot mailman
**Slot:** 0:56–1:12 (16 s) · **Type:** — · **Overlay:** none · **Route:** river mouth, south bank (store and home)

**Atmosphere [D]:** late-afternoon gold (sun ~25°, 3500 K), dust in the air, smoke from a cooking fire; palette = warm brown, cream, faded blue calico. Feels like an old daguerreotype turned to colour.
**Sound [D]:** hides being stacked, a rasp of a mill at the rapids, poling canoes, a screen door, cicadas.
**Facts [S]:** William and Mary Brickell settled at the river mouth in **1871** (arrival on 10 Jan is quoted on a heritage page, treat the exact day as medium-confidence) with a home and trading post. They **bought deer skins, alligator hides, egret plumes and coontie roots** from Seminole/Miccosukee traders, who came down the river from the Everglades, and paid in **cash**. **Coontie** was milled at the rapids near the south fork: Miami's early cash crop. Mary served as **postmaster**; the post office was in the store. The **barefoot mailman** route (1885–1892) ran ~68 miles from Palm Beach to Miami: about **28 miles by rowing** different boats, the rest **walking barefoot** on firm sand at the water's edge.
**Look [G]:** William in a wide-brim hat and rolled sleeves; Mary in a long cotton dress and apron; Seminole/Miccosukee traders in calico shirts and turbans [S for garments, G for date-specific detail].
**Explainers [D]:** a trader spreading alligator hides on the counter; a woman weighing coontie flour in a scale; the **barefoot mailman** arriving sunburned with a canvas pouch, pants rolled.
**Hand-off:** the mailman hands you a **letter** from the pouch.
**Text:** "1871 — Brickell trading post" · "1885–92 — the barefoot mailman, Palm Beach to Miami".
**Transformation out:** the sky turns a sharp winter blue and the air cools.
**Confidence:** events [S]; how the Seminole patchwork looked in the 1870s is [G]; patchwork clothing came later, so stick to calico and turbans.

---

## 5. Dec 1894 – Feb 1895 — The Great Freeze
**Slot:** 1:12–1:28 (16 s) · **Type:** Disaster · **Overlay:** none · **Route:** north bank; Tuttle's house at Fort Dallas

**Atmosphere [D]:** unusually **cold, clear, pale-blue** morning; sun low, 6500 K, crisp shadows; people in wool coats and visible breath; palette = ice blue, wet green, pale gold. This is the coldest look in the film.
**Sound [D]:** north wind, dry palm fronds rattling, a distant train whistle from the north (no track yet, only rumour), a pen scratching.
**Facts [S]:** freezes on **24 and 28 Dec 1894 and 6 Feb 1895**; temps below 20°F across much of Florida; citrus collapsed from ~6 million boxes to ~100,000. Far South Florida was spared. **Julia Tuttle** (arrived from Cleveland in 1891) owned **644 acres** on the north bank including Fort Dallas and had converted the old house into a show place with a river-and-bay view. She lobbied **Henry Flagler**; he sent **James Ingraham** to investigate. The famous **orange-blossom box is disputed** (a legend, debunked in 1913): do **not** show it as fact.
**Explainers [D]:** Tuttle at a desk on the porch writing a letter; a Black worker wrapping a young grove tree in burlap out of habit, though it is unneeded; an exhausted trader arriving from the north with a story of dead groves.
**Hand-off:** Tuttle gives you a **sealed letter** addressed to Flagler.
**Text:** "1894–95 — The Great Freeze spares Biscayne Bay".
**Transformation out:** hammering begins; a trail widens into a cleared street.

---

## 6. 1896 — The railway, the Black labourers, incorporation
**Slot:** 1:28–1:44 (16 s) · **Type:** — · **Overlay:** "368 voters" · **Route:** Avenue D / Flagler St, north bank

**Atmosphere [D]:** blazing midday, blue-white sky, dusty red street, steam smoke drifting across; palette = pine-lumber yellow, cotton white, locomotive black, sweat-dark shirts. Loud, busy, optimistic.
**Sound [D]:** steam whistle, hammers and saws, a school of "95er" voices, Southern and **Bahamian English**, hymn-singing floating over from a church.
**Facts [S]:** a town was already rising on the north bank along **Avenue D**, which Tuttle had cleared; she built the large **Miami Hotel** for newcomers; "**95ers**" threw up huts in the woods. Twelve Black labourers hand-picked by John Sewell cleared the way, including **A. W. Brown, Philip Bowman, Jim Hawkins, Warren Merridy, Richard Mangrom, Romeo Fashaw, Scipio Coleman, Sim Anderson, Dave Heartley, J. B. Brown, William Collier and Joe Thompson**. The railroad reached town in mid-April 1896 (sources give 7, 13, 15 and 22 April; show "April 1896"). The city incorporated on **28 July 1896**: **368 registered voters**, of whom **162 were Black, over half of those Bahamian**. The **Royal Palm Hotel** rose on the north bank (opening date disputed: 31 Dec 1896 or 16 Jan 1897; show "1897" or leave it in the background).
**Look [G]:** straw and felt hats, suspenders, shirtwaists and long skirts; Bahamian workers in cotton shirts and felt hats.
**Explainers [D]:** a surveyor calling out stakes; two of the named labourers hauling a rail; a Bahamian carpenter framing a house; a woman hanging laundry beside a tent.
**Hand-off:** a foreman hands you a **railway ticket** (or a pencil-marked voter list). A ticket is safer visually. [D]
**Text:** "April 1896 — The railroad arrives" · "28 July 1896 — Miami incorporates: 368 voters, 162 of them Black" · overlay "368 voters".
**Sources conflict on population** (~300, ~700). Do not put a population number on screen; use the voter count.
**Transformation out:** the street fills with tents in rows; a bugle sounds.

---

## 7. 1898 — Camp Miami (Spanish–American War)
**Slot:** 1:44–2:02 (18 s) · **Type:** War · **Overlay:** 1900 census: 1,681 · **Route:** Biscayne Blvd ↔ NW 2nd Ave, south to NE 2nd St, beside the FEC station on the future Freedom Tower site

**Atmosphere [D]:** hot, hazy afternoon with a summer thunderhead building; sun 60°, 5000 K, dust; palette = canvas tan, blue wool, red clay, olive. Evening: **campfire smoke and heat lightning**.
**Sound [D]:** **bugle calls**, marching cadence, canvas snapping, Southern accents (Alabama, Louisiana, Texas), a band practising.
**Facts [S]:** first soldiers arrived **24 June 1898**; within about two weeks **7,000+ volunteers from Alabama, Louisiana and Texas** were camped across the northern downtown. Flagler offered the Royal Palm Hotel and the town; the camp abutted the **FEC station**. The Army built **Fort Brickell** (formally Fort Robert W. Davis): an **earth mound about 45 ft across and 20 ft high** near today's Brickell Ave and 18th Road, with **two heavy guns**. **300 locals** formed the **Miami Minutemen** and drilled at the Royal Palm. The war ended around **12 Aug 1898**, and **none of the Miami soldiers saw combat**. Records suggest sanitation at the Florida camps was comparatively good.
**Look [G]:** blue wool volunteer uniforms and slouch hats, canvas leggings; townsfolk in straw hats.
**Explainers [D]:** a private writing a letter home on a drum head; Minutemen drilling with mismatched rifles; a shopkeeper selling lemonade over a crate.
**Hand-off:** a private hands you a **tin cup of coffee**, or a letter he wants mailed.
**Text:** "24 June 1898 — Camp Miami: 7,000+ volunteers" · "The war ends before they ever ship out".
**Transformation out:** tents fold like paper; the earth mound settles into a hill; the sky brightens to sea-blue.
**Caveat:** I could not read the full camp article (the site was blocked in my session), and one summary said the Army first rejected Miami. Confirm the camp's boundaries and closing date before you model tents.

---

## 8. 1913–1915 — Collins Bridge and Miami Beach
**Slot:** 2:02–2:18 (16 s) · **Type:** — · **Overlay:** 1910 census: 5,471 · **Route:** on the wooden bridge over Biscayne Bay (cutaway from the river mouth)

**Atmosphere [D]:** bright, breezy, sun 45°, sparkling blue-green bay; palette = timber silver, straw yellow, white linen, turquoise. Optimistic, "postcard" grade.
**Sound [D]:** boots and hooves on planks, a **steam dredge**, seagulls, a Model T engine, wind in the rails.
**Facts [S]:** the **Collins Bridge opened 12 June 1913**: a **2.5-mile wooden bridge**, then the **longest wooden bridge in the world**. Miami Beach had been mangrove, pine and wild coconut palms; **John S. Collins** and Pancoast cleared land, dug canals and planted **avocados** and other crops. **Carl Fisher** arrived in 1913 and promoted the Beach with stunts including **speedboat races** and **bathing-beauty publicity**; he wanted the "prettiest girls" in tight, short suits. **Collins, Lummus and Fisher incorporated the Town of Miami Beach on 26 March 1915**. Elephants working the Beach came later (1920s), so leave them out of this scene.
**Look [G]:** straw boaters, white linen, women in long skirts with parasols, workers in denim and caps; the first bathing suits, still knee-length wool.
**Explainers [D]:** a Black labourer bent over a mangrove stump with a chain; a dredge operator waving; a family walking to see the island for the first time.
**Hand-off:** a farmer hands you an **avocado** from Collins's groves.
**Text:** "12 June 1913 — Collins Bridge opens" · "26 March 1915 — Miami Beach incorporates".
**Transformation out:** the bridge planks thicken to concrete; car horns replace hooves.

---

## 9. 1920–Jan 1926 — The boom
**Slot:** 2:18–2:34 (16 s) · **Type:** — · **Overlay:** 1920 census: 29,571 · **Route:** Flagler St, the river, Avenue G/Second Ave (Colored Town), the future Freedom Tower; cutaway to Coral Gables

**Atmosphere [D]:** saturated, sun-bleached and loud; sun 55°, dazzling white Mediterranean-Revival stucco, coral and turquoise trim; palette = cream, coral, teal, gold. Film look: slightly over-saturated 1920s postcard.
**Sound [D]:** brass jazz drifting from Avenue G, **binder boys shouting**, car horns, hammers, ship horns from the harbour, an auctioneer.
**Facts [S]:** Miami's population went from just under 30,000 (1920) to over 100,000 by 1930. **Binder boys** (~25,000 in Miami at the 1925 peak) traded receipts for deposits on the sidewalks, buying lots on margin, "holding the receipt books and the pencil in hand". **Prohibition:** Dade County was a **rum-running capital**, with shootouts on the Miami River; runners loaded boats in the Bahamas and met smaller boats at the **three-mile line**. **Colored Town** (later Overtown) and **Avenue G / Second Ave** had jazz and blues; Miami's Black population was the most foreign-born of any US city, mostly Bahamian, and Black workers were the main labour force for decades. The **County (MacArthur) Causeway** was completed in **1920**. **Coral Gables** incorporated **29 April 1925** (**Venetian Pool** 1924, from a 4-acre quarry); the **Biltmore** opened **14 Jan 1926**. The **Freedom Tower** (originally the **Miami News Tower**) was completed in **1925**. On **10 Jan 1926** the **steel schooner *Prinz Valdemar*** sank in the harbour turning basin, closing the port for over a month with **~100 ships waiting** with 45 million board feet of building material. **This is a boom-time image, not part of the hurricane**: an upturned hull at the harbour mouth.
**Look [G]:** northern speculators in suits and straw boaters; women in cloche hats and drop-waist dresses; Bahamian and Black workers in work shirts and caps.
**Explainers [D]:** a **binder boy** at a card table; a Bahamian bricklayer laying stucco block; a waiter rushing past with a tray of clinking glasses (rum-running detail, whispered).
**Hand-off:** a binder boy stuffs a **binder receipt** in your hand.
**Speech (draft):** *"Ten percent down, mister — by Friday it's worth double!"* [D]
**Text:** "1920 — County Causeway" · "1925 — Freedom Tower · Coral Gables" · "10 Jan 1926 — the *Prinz Valdemar* blocks the harbour".
**Transformation out:** the sky darkens from the east; palm fronds begin to bend.

---

## 10. 18 September 1926 — The Great Miami Hurricane
**Slot:** 2:34–2:52 (18 s) · **Type:** Disaster · **Overlay:** 1920 → 1930: 110,637 during the morph · **Route:** downtown streets near the river

**Atmosphere [D]:** bruised green-grey sky, near-black horizontal rain; then an **eerie eye-lull**: sudden stillness, yellow-white light, trapped birds; then the second wall. Colour drains to green-grey and sepia; contrast up; heavy grain.
**Sound [D]:** roaring wind, tearing metal, breaking glass, then near silence in the eye (one bell, one dog), then the roar again.
**Facts [S]:** Category 4, **~140–150 mph**, **$100 million** damage (1926 USD); **deaths reported between ~370 and 540+** depending on source (Red Cross counted 373 with 6,381 injured, other counts at least 497); it **ended the boom**; the mayor downplayed the damage and the Red Cross disagreed, and relief money came up short. Many deaths were from flooding near Lake Okeechobee, so **you will not see most of them from downtown**.
**Look [G]:** people in rain-soaked 1920s dress, some barefoot.
**Explainers [D]:** a shopkeeper nailing boards; a family carrying a child through waist-deep water; a man hauling an oar out of a lobby (boats in the street).
**Hand-off:** a woman hands you a **kerosene lantern**.
**Text:** "18 Sept 1926 — Great Miami Hurricane" · "Hundreds dead (estimates vary); the boom ends".
**Transformation out:** the water recedes into the streets; the wreckage is swept into piles; the light shifts to a flat post-storm grey, then early Depression sepia.
**Caveat:** eyewitness details of the eye-lull are [D] (typical of hurricanes) since I found no specific first-hand account for Miami.

---

## 11. 1942 — WWII: Miami Beach Training Center
**Slot:** 2:52–3:10 (18 s) · **Type:** War · **Overlay:** 1940 census: 172,172 · **Route:** cutaway to Miami Beach; parade on a golf course; oil-stained beach

**Atmosphere [D]:** hazy pale dawn, cold-steel sea, **tar-stained sand**; muted desaturated look with slight blue-green cast; grain on. Later a **searchlight** sweeping over the water.
**Sound [D]:** **cadence calls**, boots on pavement, a big-band tune from a radio, a distant ship's horn and a muffled **explosion offshore**.
**Facts [S]:** the Miami Beach training centre opened **Feb 1942**; **~85% of hotel rooms** and **300+ hotels and apartment buildings** were used by the military; **600,000+ troops** trained in 1942–45 (nearly half a million Army trainees in one count; roughly a quarter of the Army Air Forces' officers and a fifth of its enlisted men); restaurants became **mess halls**, golf courses and parks became **parade grounds**, and **troops replaced sunbathers on the beach**. **U-boats** sank ships off the coast and landed saboteurs; **tar and oil** stained the beaches; gas rationing cut tourism.
**Look [G]:** khaki uniforms, garrison caps, seersucker civilians, women in wartime dresses and headscarves.
**Explainers [D]:** a sergeant drilling recruits on a golf fairway; a woman cleaning tar from a child's feet with a rag; a civilian volunteer scanning the horizon with binoculars.
**Hand-off:** a shopkeeper hands you a **ration book**.
**Text:** "Feb 1942 — Miami Beach becomes a training centre" · "600,000+ troops; U-boats offshore".
**Caveat:** the coastal **dimout/blackout** rule was imposed on the East Coast in 1942 [G]; I did not verify its Miami specifics. Add it as an *atmospheric* touch only (blacked-out headlights, curtains), not as a caption.
**Transformation out:** hotel windows brighten; uniforms are replaced with civilian clothes; postwar chrome cars roll through.

---

## 12. 1959–1965 — The Cuban exile wave and the Freedom Tower
**Slot:** 3:10–3:26 (16 s) · **Type:** — · **Overlay:** 1960 census: 291,688 · **Route:** Biscayne Blvd and the Freedom Tower, then west toward Little Havana

**Atmosphere [D]:** golden late afternoon, sun 20°, warm 3200 K, soft exhaust haze; palette = butter yellow, tropical pink, faded turquoise, chrome. **Kodachrome-ish** grade with slightly lifted blacks.
**Sound [D]:** rapid **Cuban Spanish**, a portable radio playing Cuban son/boleros, car engines, a Greyhound air-brake sigh, the low hum of a crowd in a queue.
**Facts [S]:** **Operation Pedro Pan** brought **14,000+ unaccompanied Cuban minors** (ages 6–18) in 1960–62. The **Freedom Tower** (1925) served as the **Cuban Refugee Center, 1962–74**, called the **"Ellis Island of the South"**; help included English classes, small loans, childcare, housing help and job training. Most exiles settled **around the Freedom Tower**, and **Little Havana** became the "it" place for new arrivals; large-scale settlement there was in the **1960s**. **Freedom Flights** began **1 Dec 1965**: about **10 flights a week from Varadero, averaging 85 people**, for eight years (~175,000 people between Dec 1965 and Dec 1969).
**Look [G]:** exiles in their best clothes, dressed up for travel: guayaberas and light suits, women in modest dresses and gloves, children in school uniforms.
**Explainers [D]:** a mother gripping two suitcases and a child's hand; a caseworker in a Refugee Center office stamping a form; a man showing a family photo to a stranger.
**Hand-off:** a caseworker hands you a **refugee registration card** (or a suitcase handle).
**Speech (draft):** a mother, in Cuban Spanish: *"Mira, mi amor, ya llegamos."* (Look, my love, we've arrived.) [D]
**Text:** "1960–62 — Operation Pedro Pan: 14,000+ children" · "1962–74 — Freedom Tower: Cuban Refugee Center" · "Dec 1965 — Freedom Flights begin".
**Caveat:** **cafecito walk-up windows (ventanitas)** in the early 1960s are [G] and unverified. Use them as a light touch or as a later addition.
**Transformation out:** the queues thin out and, on a radio, an announcer's voice turns urgent.

---

## 13. 1961–1962 — Bay of Pigs and the Cuban Missile Crisis
**Slot:** 3:26–3:52 (26 s: ~10 s + ~16 s) · **Type:** War · **Overlay:** 1960 census held · **Route:** a Little Havana living room, then a street and church; **cutaway to Homestead AFB**; ends at the Orange Bowl

### Beat A — 17 April 1961: Bay of Pigs, from Miami (~10 s)
**Atmosphere [D]:** night vigil; lamplight, a TV's blue glow; near-monochrome warm-amber and steel-blue; static and slight tape hiss in the sound. Claustrophobic, close, few wide shots.
**Sound [D]:** a Spanish-language **radio bulletin**, static, women praying the rosary, a child asking a question, a door opening.
**Facts [S]:** **Brigade 2506** was a **CIA-sponsored group of Cuban exiles formed in 1960**. It landed at the **Bay of Pigs on 17 April 1961** and was **defeated within two days**. Fighting happened in Cuba, not in Miami: Miami's story is the **exile community waiting and grieving**. Do not show combat.
**Explainers [D]:** an older man gripping a transistor radio; a woman with rosary beads; a teenager looking at a wall map.
**Hand-off:** an older man **presses his transistor radio into your hands** so you hear the bulletin.
**Text:** "17 April 1961 — Brigade 2506 lands at the Bay of Pigs" · "Defeated in two days; families wait in Miami".
**Transformation:** the radio's static turns into a military convoy engine.

### Beat B — October 1962: the Cuban Missile Crisis (~16 s)
**Atmosphere [D]:** heavy, still, oppressive: sun high, glare, then a hushed hazy dusk with jet contrails; palette = drab olive, white church, faded shirt-blue. Slightly desaturated and bleached.
**Sound [D]:** convoy engines, jet fly-bys, church bells, school bell, a portable radio carrying a **presidential address** (Kennedy's 22 Oct 1962 television address, public record).
**Facts [S]:** **Homestead AFB** swelled to **tens of thousands** of personnel, including a **tent city for 10,000+ Army troops**; **three air-defence missile battalions** arrived on **20 Oct 1962**, two days before Kennedy's broadcast. **Nike Hercules** batteries sat in the Everglades. **Fallout shelters** were stocked; **schoolchildren did duck-and-cover drills**; residents **filled gas tanks and stocked food**; **troops stayed at Lockhart Stadium**; the exile community gathered in **Little Havana** and **packed churches** to pray. **Transformation out (real event):** after the Bay of Pigs prisoners were released for **$53 million in baby food and medicine** (Dec 1962), **40,000 people** filled the **Orange Bowl**, where President Kennedy accepted a **replica of the brigade's battle flag** and said, **"I can assure you that this flag will be returned to the brigade in a free Havana"** (real quote). One source dates the ceremony to **Jan 1963**; commonly it is given as late Dec 1962. Show it as "Dec 1962–Jan 1963".
**Look [G]:** crew cuts, short-sleeve shirts, shirtdresses, olive-drab fatigues.
**Explainers [D]:** a teacher leading a duck-and-cover drill; a soldier hauling a crate of survival biscuits; a priest lighting candles in a packed church.
**Hand-off:** a volunteer hands you a **fallout-shelter sign** (the yellow-black trefoil) or a **survival-biscuit tin** [G].
**Text:** "20 Oct 1962 — missile battalions arrive in South Florida" · "Homestead: 10,000+ troops in a tent city" · "Orange Bowl: 40,000 welcome the brigade home".
**Transformation out:** the tent city turns into a stadium crowd; the crowd noise is the last thing that fades.

---

## 14. 1980 — Mariel boatlift
**Slot:** 3:52–4:08 (16 s) · **Type:** — · **Overlay:** 1980 census: 346,865 · **Route:** the Miami River **under the I-95 overpass** (exact Tent City location), then the Orange Bowl

**Atmosphere [D]:** blazing hot, concrete glare, deep shade under the overpass; sun 75°, near-white, high contrast; palette = bleached concrete, tent olive-green, sun-faded fabrics. **35 mm, slightly faded**, mid-grain.
**Sound [D]:** boat engines idling, **Spanish voices calling names**, helicopters, generators, a PA announcing numbers, a child crying and then laughing.
**Facts [S]:** **125,266 Cubans** arrived by boat from **Mariel** between **15 April and 31 October 1980**; Castro **opened the port on 20 April**. **Tent City** was under the **I-95 overpass by the Miami River** (**1,000+ moved in; 4,000+ passed through**); a second tent city was at the **Orange Bowl**. The influx **overwhelmed government, schools and services**; some newcomers committed crimes and the boatlift **stoked racial and ethnic tension**, contributing to the unrest that followed (next scene). Twenty-five years later most stories were of success.
**Look [G]:** 1980 polyester shirts and bell-bottoms, mismatched donated clothes, plastic bags of belongings.
**Explainers [D]:** a volunteer handing out sandwiches; a man reading names off a clipboard through a megaphone; two relatives embracing at the fence.
**Hand-off:** a volunteer hands you a **paper cup of water**, or a blanket.
**Text:** "15 Apr–31 Oct 1980 — Mariel boatlift: 125,266 arrive" · "Tent City under I-95".
**Transformation out:** the tent flaps close; the shade under the overpass turns to nightfall.

---

## 15. 17 May 1980 — The McDuffie verdict and the Liberty City riots
**Slot:** 4:08–4:24 (16 s) · **Type:** Unrest · **Overlay:** 1980 census held · **Route:** **dawn-after cutaway** to a Liberty City/Overtown street. **Do not re-enact the violence**

**Atmosphere [D]:** grey dawn, ash and smoke in the air, no direct sun; palette = charred black, wet-street grey, fading orange. Very still after a loud night. Subdued; **no music**.
**Sound [D]:** a distant siren, a radio in a doorway, a broom on concrete, a National Guard truck idling, murmured conversation.
**Facts [S]:** an **all-white jury acquitted all officers on 17 May 1980** in the death of **Arthur McDuffie**, a 33-year-old Black insurance agent beaten after a motorcycle chase. Rioting hit **Liberty City, Overtown, West Coconut Grove and Brownsville** for about **three days (to 20 May)**; **at least 18 people died** and damage was estimated at **$80–100 million**. **The Florida National Guard** was called in; **black smoke** rose from a burning tyre company at **NW 27th Ave and 54th St**. Liberty City's businesses were slow to return.
**Explainers [D]:** a shopkeeper sweeping glass; a pastor and neighbours passing out water; a teenager holding a handmade "Justice for Arthur McDuffie" sign.
**Hand-off:** a neighbour hands you a **broom** (you are joining the clean-up), or a **water bottle**.
**Text:** "17 May 1980 — All officers acquitted in Arthur McDuffie's death" · "Riots (to 20 May): 18+ dead".
**Caveat:** damage figures vary ($80M vs $100M), and I did not verify curfew details. Get the tone right with a local historian (HistoryMiami; Black Archives).
**Transformation out:** the smoke thins into a hazy morning, then the storm-yellow sky of 1992 begins to build.

---

## 16. 24 August 1992 — Hurricane Andrew
**Slot:** 4:24–4:42 (18 s) · **Type:** Disaster · **Overlay:** 1990 census: 358,648 · **Route:** Brickell Ave (outer-band damage), then a **cutaway to Homestead / South Dade**

**Atmosphere [D]:** Saturday night: **sickly yellow-green** sky, stuffy air, lines of headlights; then pitch-black night with a deafening wind; then the morning after, a hard bright sun on wrecked houses. The scene's colour arc is green → black → white glare.
**Sound [D]:** a **TV weather broadcast** (WTVJ's Bryan Norcross broadcast for ~23 hours straight [S]; do **not** invent his words), hammering plywood, a supermarket line, then roaring wind, then chainsaws and helicopters.
**Facts [S]:** Andrew made landfall **early on 24 Aug 1992 near Homestead**, **20 miles south of downtown**, with **165 mph sustained winds, 177 mph gusts and a 17-ft surge**; **65 deaths**, **63,000 homes destroyed**, **~$26 billion** damage, **160,000+ homeless in Dade**. The **Miami Herald played down the threat** that Saturday morning. The outer edge of the storm blew through **Brickell's high-rises**, **sucking furniture out of apartments**. **Kate Hale**, Miami-Dade's emergency director, said on national TV: **"We have a catastrophic disaster, please come down and help us… Where the hell is the cavalry on this one?"** (real quote). **20,000 National Guard** troops arrived; **FEMA tent cities** appeared in Homestead.
**Look [G]:** early-90s windbreakers, jeans, big glasses; masking-tape "X"s on windows.
**Explainers [D]:** a family taping X's on a plate-glass window; a man carrying a 4×8 plywood sheet; an emergency worker on TV; in the cutaway, a family under a blue tarp and a National Guard soldier handing out water.
**Hand-off:** a neighbour hands you a **roll of masking tape** and a **flashlight**.
**Text:** "24 Aug 1992 — Hurricane Andrew: eye passes over Homestead, 20 miles south of downtown" · "65 dead · 63,000 homes destroyed".
**Transformation out:** the storm clears in a time-lapse; blue tarps replace roofs; then a fresh new skyline rises.

---

## 17. 12 May 1997 — The downtown tornado
**Slot:** 4:42–4:58 (16 s) · **Type:** Disaster · **Overlay:** 1990 census held · **Route:** **exactly your route**: East Little Havana → over the Miami River and I-95 → downtown → Biscayne Bay → Miami Beach

**Atmosphere [D]:** midday, a **dark thunderhead** with a green-grey underbelly and a narrow funnel; ordinary office life in the foreground. Mid-90s video look: slightly blown highlights, soft focus.
**Sound [D]:** a low **freight-train roar**, distant sirens, people shouting "Look!", a car alarm; then a **waterspout** hiss on the bay.
**Facts [S]:** touchdown **Monday 12 May 1997, 1:53–2:08 pm**; a rare, **weak (F1)** tornado that stayed on the ground about **8 miles**: from Shenandoah through **East Little Havana**, across the **Miami River and I-95**, through **downtown**, over **Biscayne Bay** (churning the water to foam) and into **Miami Beach**. **12 injuries**, **$525,000** in damage.
**Look [G]:** 90s office wear, ties and lanyards; someone in a hard hat.
**Explainers [D]:** a crowd of office workers on a sidewalk **filming with camcorders**; a bus driver stopping traffic; a street vendor covering his stand.
**Hand-off:** a man hands you his **camcorder** ("Get this!"). [D]
**Text:** "12 May 1997 — Tornado crosses downtown Miami in 15 minutes".
**Transformation out:** the funnel thins over the bay and ends at the Beach; blue sky returns.

---

## 18. 2000 — Elián González and the recount
**Slot:** 4:58–5:14 (16 s) · **Type:** — · **Overlay:** 2000 census: 362,470 · **Route:** Little Havana street (April); a downtown government corridor (November)

**Atmosphere [D]:** two beats. (a) **Pre-dawn April**: blue-black sky, sodium-yellow streetlights, then sunrise over a crowd; (b) **November**: harsh fluorescent light, cream walls, a tense hallway. Digital-video crispness; slightly cool.
**Sound [D]:** chanting in Spanish, whistles, helicopters, a bullhorn; then in the corridor, shuffling feet, a ringing phone, a muffled shout.
**Facts [S]:** **Elián** was found clinging to an inner tube off Florida after his mother drowned (Thanksgiving 1999) and stayed with relatives in **Little Havana**. **4 April 2000**: protesters formed a human chain around the house. **10 April**: candlelight vigil. **22 April 2000**, at roughly **4:30–5:15 a.m.** (sources vary), **armed federal agents** took him, using **tear gas**; crowds **blocked traffic and lit small fires**. He returned to Cuba in **June 2000**. **22 November 2000**: the **Brooks Brothers riot**, a demonstration by Republican staffers at a **Miami-Dade canvassing board** meeting during the presidential recount, after which officials **halted the recount**. Bush led statewide by **1,784 votes** on election night.
**Look [G]:** shorts, guayaberas, Cuban and American flags on shoulders; then 2000 business-casual and khakis.
**Explainers [D]:** a grandmother clutching a rosary and a small flag; a shopkeeper closing his shutters; a man holding a punch-card ballot up to the light.
**Hand-off:** a woman hands you a **small Cuban flag**; in the next beat a clerk hands you a **punch-card ballot** with a hanging chad. [D]
**Text:** "22 Apr 2000 — Elián González raid, Little Havana" · "22 Nov 2000 — Miami-Dade recount halted".
**Transformation out:** the flags fold into ballots; the corridor's fluorescent light softens to warm gallery light.
**Caveats:** raid time varies by source; keep it as "before dawn". Politically charged: **stay descriptive**, and no caricatures.

---

## 19. 24 October 2005 — Hurricane Wilma
**Slot:** 5:14–5:32 (18 s) · **Type:** Disaster · **Overlay:** 2000 → 2010: 399,457 in the morph · **Route:** downtown streets after the storm

**Atmosphere [D]:** a brilliant hard blue morning-after, sun 45°, glare on broken glass, and then a **star-filled night with no city lights**. The contrast between the two is the point.
**Sound [D]:** generators, chainsaws, honking at dark intersections, people arguing in a gas line, no air-conditioner hum.
**Facts [S]:** Wilma crossed South Florida on **24 Oct 2005** with winds up to **125 mph**; it **shattered windows in downtown skyscrapers**, **peeled roofs** and cut power to **up to 6 million people**. Of Miami's **2,600 traffic lights, only 18 worked**. People **waited for hours for free water, ice and food**, and gas lines stretched **for blocks**, with arguments over cutting in line. Florida damage **~$19 billion, 30 deaths**; **at least 2,059 Miami-Dade homes** were uninhabitable.
**Look [G]:** shorts and T-shirts, damp and dirty, baseball caps, plastic gas cans.
**Explainers [D]:** a police officer directing traffic at a dead light; a family in a line for ice; a maintenance worker taping cardboard over a shattered lobby window.
**Hand-off:** an emergency volunteer hands you a **bag of ice**.
**Text:** "24 Oct 2005 — Hurricane Wilma: 6 million without power" · "18 of Miami's 2,600 traffic lights working".
**Transformation out:** the lights snap back on floor by floor; the skyline gets taller.
**Caveat:** the "downtown at night with stars" image is [D]; it is likely across the region, but I did not find a source for a Miami-specific night scene.

---

## 20. 2014–2016 — Sunny-day flooding and Brickell City Centre
**Slot:** 5:32–5:48 (16 s) · **Type:** Disaster · **Overlay:** 2010 census held · **Route:** cutaway to Miami Beach (Alton Rd / 10th St / 5th St), then Brickell City Centre

**Atmosphere [D]:** **cloudless, brilliantly clear** sky with **sea water on the street**: the irony is the image. Sun 60°, mirror-clean reflections; palette = crisp blue, glass, clean white. Clean digital look, sharp.
**Sound [D]:** water sloshing at ankle depth, **pump hum**, bicycle bells, phones snapping photos, laughter and a note of unease.
**Facts [S]:** during **king tides** (2014–15), **Alton Road at 10th and 5th Streets** was underwater at high tide on clear days; **cars stalled**, people **rolled up their pants and waded knee-deep** or rode bikes. Miami Beach set aside **$300–400 million** for **up to 50 pumps**, storm sewers and raised roads; in later tides repaired streets stayed dry. **Brickell City Centre** opened **3 Nov 2016**: **Saks Fifth Avenue** anchor, **~500,000 sq ft of retail**, **REACH and RISE** residential towers, the **EAST Miami** hotel and two office towers.
**Look [G]:** 2010s casual: rolled chinos, flip-flops, sundresses; some in rubber boots.
**Explainers [D]:** a man carrying his bike across a flooded intersection; a city worker beside a pump truck; a couple taking a selfie beside a stalled car.
**Hand-off:** a passer-by hands you a pair of **flip-flops**, or a phone to take a photo.
**Text:** "2014–15 — King tides flood Miami Beach on sunny days" · "3 Nov 2016 — Brickell City Centre opens".
**Transformation out:** the water drains to the sea; polished stone replaces the street; glass towers rise.

---

## 21. 10 September 2017 — Hurricane Irma
**Slot:** 5:48–6:06 (18 s) · **Type:** Disaster · **Overlay:** 2010 census held · **Route:** Brickell Ave, Biscayne Blvd, and the site at **300 Biscayne Blvd**

**Atmosphere [D]:** grey-green dusk, sheeting rain, water in the streets **like rivers**; palette = slate, steel, muted green with the only colour from emergency lights. A heavy sound mix.
**Sound [D]:** howling wind, car alarms, rain on glass, a **crane creaking** overhead, sirens.
**Facts [S]:** on **10 Sept 2017 Irma** flooded **Brickell Avenue with ~3 ft of water** and **Biscayne Blvd to knee-height**. About **20–25 construction cranes** stood over downtown; **at least two collapsed**: one at **300 Biscayne Blvd** (a 30-storey Property Markets Group tower) and one at the **GranParaiso** tower on NE 31st St. Storm-surge flooding turned downtown streets into rivers.
**Look [G]:** rain jackets, ponchos, some in life vests.
**Explainers [D]:** a security guard hauling a sandbag; a woman wading with a dog in a bag; a firefighter pointing at a swaying crane.
**Hand-off:** a firefighter hands you a **flashlight** (and points at the crane).
**Text:** "10 Sept 2017 — Hurricane Irma floods Brickell; cranes collapse".
**Transformation out:** the water recedes; broken glass turns to a memorial-like stillness.

---

## 22. 24 June 2021 — Surfside (memorial only)
**Slot:** 6:06–6:22 (16 s) · **Type:** Disaster · **Overlay:** 2020 census: 442,241 · **Route:** cutaway to Surfside, a **memorial fence** across the street from the collapsed building

**Atmosphere [D]:** soft **overcast morning light**, still air, flowers and a quiet hush; palette = muted whites, soft pinks, greys. **No music.** Slow, almost frozen camera.
**Sound [D]:** distant surf, quiet voices, a flag or cloth flapping, footsteps on grass.
**Facts [S]:** **Champlain Towers South**, a **12-storey** beachfront condominium in Surfside, partially collapsed at about **1:22 a.m. on 24 June 2021**; **98 people died**, ages **1 to 92**. Investigators (NIST) found the collapse **began in the pool deck**. A **memorial** grew along a **tennis-court fence** across the street: **photos, drawings, shoes, books, candles, posters, T-shirts, stuffed animals, hundreds of bouquets and flags**; **HistoryMiami** later catalogued and preserved the items.
**Explainers [D]:** an older woman placing flowers; a young man tying a ribbon on the fence; a volunteer straightening candles.
**Hand-off:** someone hands you a **single flower** to place on the fence.
**Text:** "24 June 2021 — Surfside: 98 lives lost" (minimal, dignified).
**Ethics [D]:** **do not depict the collapse**, and **do not use real victims' photos or names**. Use abstract, generic mementos. Consider asking HistoryMiami and the community about acceptable depiction.
**Transformation out:** the flowers on the fence blur into flowers and bunting on a restored white tower.

---

## 23. September 2025 – September 2026 — Miami now (finale)
**Slot:** 6:22–6:56 (34 s: ~10 s + ~10 s + ~14 s) · **Type:** — (major events) · **Overlay:** 2020 census held (442,241; I did not add a post-2020 figure) · **Route:** Freedom Tower and Biscayne Blvd → Bayfront Park → W Flagler St → Brickell crosswalk

Three beats, each anchored to something documented and close to the walking route. Hard Rock Stadium is in Miami Gardens, so keep it to a short cutaway or a sound cue.

### Beat A — Sept 2025: the Freedom Tower reopens for its centennial (~10 s)
**Atmosphere [D]:** late-afternoon golden light on a freshly restored cream-and-tan facade; palette = warm cream, terracotta, sky blue. Warm, ceremonial, clean.
**Sound [D]:** murmured Spanish and English, soft applause, a single trumpet, shoes on stone.
**Facts [S]:** the **Freedom Tower** (1925; first the Miami News headquarters, then the Cuban Refugee Center) **reopened to the public on 16 Sept 2025** after a **$25 million restoration**, with **four new exhibitions**. This closes the loop with scene 12.
**Explainers [D]:** an elderly woman resting her palm on the wall; a child craning to see the tower; a docent handing out programmes.
**Hand-off:** the docent hands you an **exhibition ticket / programme**.
**Text:** "16 Sept 2025 — Freedom Tower reopens for its centennial".

### Beat B — June–July 2026: the FIFA World Cup (~10 s)
**Atmosphere [D]:** blue-hour evening at Bayfront Park, floodlights and giant LED glow on the water; palette = saturated team colours against deep blue. Festival energy.
**Sound [D]:** chanting in several languages, drums and horns, a concert bass beat, a cheer rippling through the crowd.
**Facts [S]:** the **FIFA Fan Festival at Bayfront Park** ran **13 June – 5 July 2026** (free; **436,000 sq ft**; giant LED screens; a **10,000-capacity amphitheatre**; concerts, food, and **water-powered jetpack demonstrations over Biscayne Bay**). **Hard Rock Stadium** (called **"Miami Stadium"** during the tournament) hosted **seven matches, 15 June – 18 July 2026**; the group stage there featured **Brazil, Portugal, Colombia and Uruguay**, and Miami was the **only host city for the third-place match on 18 July**.
**Explainers [D]:** a Brazilian family in yellow; a Colombian fan with a painted face; a jetpack pilot rising over the bay.
**Hand-off:** a fan hands you a **team scarf** (a blend of colours works, so no single team is favoured).
**Text:** "13 June – 5 July 2026 — FIFA Fan Festival, Bayfront Park" · "Miami hosts the bronze final, 18 July 2026".
**Do not show a match result.** One search summary gave a third-place score that looks wrong, and I did not verify it.

### Beat C — July–September 2026: 130 years, and 100 years since 1926 (~14 s)
**Atmosphere [D]:** golden hour into blue hour: sun ~10° with amber glass reflections, then neon magenta and teal as the sky deepens; palette = teal, magenta, gold, glass blue. Clean, saturated, cinematic. A **thin film of water** in a low curb (Sept 2026 king-tide advisories and rain were in the news [S: CBS Miami]) reflects the towers.
**Sound [D]:** layered Spanish and English chatter, a Latin pop bassline from a passing car, a **Metromover** overhead [G], scooters, gulls, sea-air wind. Music: a warm, quiet build.
**Facts [S]:** the City of Miami turned **130** on **28 July 2026** (incorporated 28 July 1896). On **18 Sept 2026**, exactly a century after the hurricane, the **Museum of Miami** (101 W. Flagler St) opened **"Caught in the Eye: Remembering the 1926 Hurricane"**: **100 photographs**, film footage, newspapers, letters and first-hand accounts. The National Weather Service and the Old Post Office LLC also placed a **state historical marker** for the storm. **Panorama Tower** (topped out late 2017) and **Brickell City Centre** frame the Brickell skyline. The **2026 Atlantic hurricane season had no hurricanes by its peak** (Wikipedia summary; reconfirm before publishing), so this is a calm modern Miami.
**Explainers [D]:** a museum visitor pausing at a window of black-and-white hurricane photographs (an echo of scene 10); a **cafecito** window server; a pair chatting in Spanglish; a woman on an e-scooter.
**Hand-off (closes the loop):** the server passes you a **cafecito** in a small paper cup, matching the shell cup you were handed 2,000 years ago. **Raise it. Cut to the title card.**
**Text:** "28 July 2026 — Miami turns 130" · "18 Sept 2026 — 100 years since the Great Miami Hurricane" · title card **"MIAMI 2026"** (last 6 s).
**Caveat:** Metromover, scooters, Cuban-coffee windows and bilingual signage are present-day observations [G]; verify with on-site reference footage.

**Left out to stay under 7:00 (available as swaps for Beat A or B):**
- **9 Dec 2025:** Eileen Higgins elected mayor (first Democrat since 1997, first woman mayor; took office 18 Dec 2025) [S]. Politically charged, so use a neutral caption if included.
- **14 June 2025:** Inter Miami vs Al Ahly opens the FIFA Club World Cup at Hard Rock (14 June – 1 July 2025) [S].
- **14 July 2024:** Copa América final at Hard Rock: gate breach, 82-minute delay, Argentina 1–0 Colombia [S].
- **July 2023:** Messi joins Inter Miami (Fort Lauderdale, not Miami) [S].

---

## Verification log: conflicts and corrections found in research

| Item | What sources say | How to handle |
|---|---|---|
| Railway arrival, 1896 | 7, 13, 15 and 22 April all appear (construction reached, first train, "completed", regular service) | Show "April 1896" |
| Incorporation, 28 Jul 1896 | 368 voters; population figures of ~300 and ~700 both quoted; 162 Black voters, over half Bahamian | Show voters, not population |
| Royal Palm Hotel opening | 31 Dec 1896 vs 16 Jan 1897 | Show "1897" or no date |
| Orange-blossom story (Tuttle → Flagler) | Disputed; debunked as early as 1913 | Do not show as fact |
| *Prinz Valdemar* | Sank 10 Jan 1926, **before** the hurricane | Boom-scene image only |
| 1926 death toll | 372–539+ (or 373–497) by source | "Hundreds (estimates vary)" |
| Fort Dallas building | Coquina structure dated to the war in one source, to the English plantation in others | Use logs/frame for 1836 |
| Orange Bowl brigade ceremony | Late Dec 1962 vs "January 1963" | "Dec 1962–Jan 1963" |
| 1980 riots | Damage $80M vs $100M; deaths "at least 18" | Give a range |
| Elián raid time | ~4:30 a.m. in one source; commonly ~5:15 a.m. | "Before dawn" |
| Wilma | 30 deaths in Florida; ≥2,059 Miami-Dade homes uninhabitable | As stated |
| World Cup bronze match, 18 July 2026 | One search summary gave a score; I could not corroborate it and it looks implausible | Do not show a score |
| Hard Rock Stadium location | In Miami Gardens, not Miami proper | Cutaway or sound cue only |
| 2026 hurricane season | Wikipedia summary says no hurricanes by the peak (strong El Niño) | Calm-year finale; reconfirm before publishing |
| Camp Miami | Source dates (24 June 1898; 7,000+); one summary said the Army first rejected Miami; I couldn't read the full page | Recheck before modelling |

**Items not verified at all** (all tagged [G] above): 16th-century Spanish and 1830s US Army uniform details, 1898 volunteer uniforms, 1960s ventanitas, dimout details, Metromover and other present-day street details in 2026, the exact look of every era's street furniture and signage. For visuals, use **archival photographs** (HistoryMiami, Florida Memory, Library of Congress, Sanborn fire-insurance maps).

---

## Sources
- History of Miami — https://en.wikipedia.org/wiki/History_of_Miami
- Tequesta — https://en.wikipedia.org/wiki/Tequesta · https://fcit.usf.edu/florida/lessons/tequest/tequest1.htm · https://education.pbchistory.org/native-americans/early-tribes/tequesta/
- Miami Circle — https://en.wikipedia.org/wiki/Miami_Circle · https://www.trailoffloridasindianheritage.org/miami-circle/
- Spanish missions on the Miami River — https://www.miami-history.com/p/spanish-missions-on-miami-river-part-1-of-2 · https://communitynewspapers.com/biscayne-bay/miamis-jesuit-missions/
- Fort Dallas — https://en.wikipedia.org/wiki/Fort_Dallas · https://www.legendsofamerica.com/fort-dallas-florida/
- Cape Florida Light — https://en.wikipedia.org/wiki/Cape_Florida_Light
- Seminole clothing — http://www.nativetech.org/seminole/turbans/index.php · https://www.semtribe.com/culture/seminole-clothing
- William Brickell — https://en.wikipedia.org/wiki/William_Brickell · https://www.uflib.ufl.edu/ingraham/expedition/BrickellM.htm
- Barefoot mailman — https://en.wikipedia.org/wiki/Barefoot_mailman
- Great Freeze / Tuttle — https://en.wikipedia.org/wiki/Great_Freeze · https://en.wikipedia.org/wiki/Julia_Tuttle · https://jitneybooks.com/henry-flagler-orange-blossom-myth/
- 1896 — https://baillylectures.com/sources/miami-1896-incorporation/ · https://www.storyofmiami.com/episodes/2020/6/27/episode-21-1896 · http://www.floridahistorynetwork.com/april-15-1896---henry-flaglers-railroad-arrives-in-miami-for-first-time.html
- Camp Miami / Fort Brickell — https://www.miami-history.com/p/miami-and-the-spanish-american-war-part-1-of-3 · https://www.miami-history.com/p/a-splendid-little-fort-in-miami-1898
- Miami Beach / Collins Bridge — https://www.miamibeachfl.gov/this-month-in-miami-beach-history-the-bridge-that-built-a-city/ · https://en.wikipedia.org/wiki/Collins_Bridge · https://miamibeach411.com/History/bio_fisher.htm
- 1920s boom — https://stars.library.ucf.edu/cgi/viewcontent.cgi?article=3777&context=fhq · https://www.miaminewtimes.com/news/sixty-years-before-the-cocaine-cowboys-miami-was-the-wild-west-of-prohibition-8269399/ · https://en.wikipedia.org/wiki/Overtown_(Miami) · https://en.wikipedia.org/wiki/Prinz_Valdemar
- 1926 hurricane — https://en.wikipedia.org/wiki/1926_Miami_hurricane · https://www.aoml.noaa.gov/hurricane-of-1926/
- Coral Gables / Biltmore — https://en.wikipedia.org/wiki/Coral_Gables,_Florida · https://en.wikipedia.org/wiki/Miami_Biltmore_Hotel
- WWII Miami Beach — https://www.museumoffloridahistory.com/explore/exhibits/permanent-exhibits/world-war-ii/historical-sites/southeast-listing/miami-beach-hotels/ · https://www.life.com/history/when-miami-beach-went-to-war/
- Freedom Tower / Freedom Flights — https://en.wikipedia.org/wiki/Freedom_Tower_(Miami) · https://en.wikipedia.org/wiki/Freedom_Flights · https://en.wikipedia.org/wiki/Operation_Peter_Pan
- Bay of Pigs — https://history.state.gov/milestones/1961-1968/bay-of-pigs · https://www.jfklibrary.org/learn/about-jfk/jfk-in-history/the-bay-of-pigs
- Missile Crisis — https://www.wlrn.org/this-miami-life/2012-10-24/how-the-cuban-missile-crisis-shaped-miami · https://www.afhistory.af.mil/FAQs/Fact-Sheets/Article/458954/1962-cuban-missile-crisis/
- Mariel — https://en.wikipedia.org/wiki/Mariel_boatlift · https://www.latinamericanstudies.org/mariel/triumph.htm
- 1980 riots — https://en.wikipedia.org/wiki/1980_Miami_riots · https://www.wlrn.org/news/2015-05-17/smoldering-liberty-city-remembering-the-mcduffie-riots
- Hurricane Andrew — https://courses.ems.psu.edu/earth107/book/export/html/1603 · https://www.axios.com/local/miami/2022/08/23/hurricane-andrew-anniversary-miami
- 1997 tornado — https://en.wikipedia.org/wiki/1997_Miami_tornado
- Elián / recount — https://www.miaminewtimes.com/news/elian-gonzalez-today-2025-marks-anniversary-of-miami-raid-11626762/ · https://en.wikipedia.org/wiki/Brooks_Brothers_riot
- Wilma — https://www.nhc.noaa.gov/data/tcr/AL252005_Wilma.pdf · https://www.npr.org/2005/10/25/4973258/wilma-surprises-miami-halts-transportation
- King tides / Brickell CC — https://www.npr.org/2014/10/10/355051011/miami-uses-pumps-to-battle-flooding-from-sea-level-rise · https://en.wikipedia.org/wiki/Brickell_City_Centre
- Irma — https://www.npr.org/2017/09/11/550058360/hurricane-irma-hits-miami-causing-major-flooding · https://www.nbcnews.com/storyline/hurricane-irma/hurricane-irma-cranes-collapse-downtown-miami-n800106
- Surfside — https://en.wikipedia.org/wiki/Surfside_condominium_collapse · https://www.wlrn.org/news/2021-08-27/surfsides-memorial-to-champlain-towers-south-victims-will-come-down-to-preserve-mementos
- Census — https://en.wikipedia.org/wiki/Demographics_of_Miami
- Freedom Tower reopening, 2025 — https://www.wlrn.org/development/2025-09-16/miamis-freedom-tower-marks-its-centennial-with-its-the-re-opening
- 2026 World Cup in Miami — https://www.hardrockstadium.com/events/fifa-world-cup-2026/ · https://miamifwc26.com/match-schedule/ · https://www.timeout.com/miami/things-to-do/2026-fifa-world-cup
- Miami turns 130 — https://www.nbcmiami.com/news/local/1896-to-2026-celebrating-130-years-of-miami/3839271/ · https://www.key2mia.com/post/miami-turns-130
- 1926 centennial — https://www.local10.com/features/2026/09/18/100-years-later-miami-museum-exhibit-looks-back-at-devastating-1926-hurricane/ · https://www.weather.gov/news/260915-great-miami-hurricane
- 2026 hurricane season / king tides — https://en.wikipedia.org/wiki/2026_Atlantic_hurricane_season · https://www.cbsnews.com/miami/news/south-florida-weather-forecast-miami-fort-lauderdale-miami-dade-broward-september-10-2026/
- 2025 mayoral election — https://en.wikipedia.org/wiki/2025_Miami_mayoral_election
- FIFA Club World Cup 2025 — https://www.hardrockstadium.com/events/fifa-club-world-cup-2025/
- 2024 Copa América final — https://www.wlrn.org/sports/2024-07-15/chaos-at-hard-rock-stadium-as-fans-breach-security-gates-ahead-of-copa-america-final
