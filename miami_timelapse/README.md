# Miami 3D Timelapse: research dataset (500 BC to 2026)

Historical data for a low-poly 3D timelapse of Miami, in the style of the Lisbon and Moscow reference videos. Every entry carries its sources and a confidence level, so the script and the Blender scene can be checked against it.

| File | What it holds |
|---|---|
| `data/events.json` | 91 dated events: wars, disasters, construction, land changes, migrations, unrest. Coordinates included. |
| `data/war_sequences.json` | 15 conflict/military sequences broken into animation beats: who, how they arrived (sea, river, land, air), vessels, aircraft, weapons, numbers, and what **not** to show. Also a catalogue of every vessel and aircraft type to model. |
| `data/structures.json` | 56 hero structures with appear/remove years, heights and coordinates. This drives what exists in each frame. |
| `data/population.json` | Counter series (estimates to 1896, then census) plus the city and Miami Beach series. |

Research date: September 2026. Anything marked "2026" reflects status as of that month.

## Confidence levels
- **high**: confirmed by two or more independent sources, or one authoritative source (NHC, Census, Library of Congress, NPS).
- **medium**: one source, or inferred from confirmed facts (the inference is written in the entry).
- **disputed**: sources disagree; see the table below.
- Values labelled *illustrative* in `population.json` are placeholders for the counter, not sourced facts. Caption them as estimates or replace them.

## The most important finding about the wars
**Miami was never bombed, shelled, or attacked from the air.** Every conflict that reached the city was one of these:

| Era | How it was fought | What moves on screen |
|---|---|---|
| 1566–1570 | Spanish ships to the river mouth; small garrison; Tequesta burn their village and withdraw | Sailing ships, stockade, fire, canoes |
| 1704–1763 | Slave raids from the north (land and canoe); Spanish evacuation ships to Cuba | Canoes, departing ships, village emptying |
| 1836 | Seminole raid on the Cape Florida Lighthouse (island, so they came by water); Navy schooners rescue the keeper | Musket smoke, burning tower, night explosion, schooner |
| 1836–1842 | Fort Dallas; Navy "Mosquito Fleet" schooners and canoes; Harney's 16-canoe raid up the Miami River | Blockhouses, schooners on the bay, canoe line going west |
| 1861–1865 | Sabotage of the lighthouse; Union blockade offshore | Beam goes dark, gunboat on the horizon |
| 1898 | Coastal fort with 2 guns; 7,000 troops by train; no combat | Earth bunker, tent grid, trains |
| 1942–1945 | U-boats sink tankers offshore (one burned in sight of Miami Beach); blimps and subchasers escort convoys; the city trains soldiers | Burning tanker at night, blimps, subchasers, marching troops, dim-out |
| 1961–1963 | Covert CIA operations; a disguised B-26 lands at MIA; the invasion itself was in Cuba | One B-26 landing; exiles |
| Oct 1962 | Over 181 F-100 jets and 10,000+ troops at Homestead; HAWK/Nike missile batteries; **no shots fired** | Swept-wing jets climbing south, missile launchers, tents |

So animate small jets (F-100 Super Sabres, F-102 Delta Daggers, RF-101 Voodoos) **taking off, patrolling and heading south toward Cuba**, never attacking Miami. That is both accurate and dramatic. The only aircraft actually lost in a fight near Miami was blimp K-74, shot down by anti-aircraft fire from U-134 in the Florida Straits on July 18, 1943.

The strongest "siege-style" sequences, which fit the reference videos' four beats (arrive, surround, destroy, aftermath), are:
1. **1836 Cape Florida Lighthouse attack**: arrival, fire, last stand, night explosion, rescue.
2. **May 14, 1942 Potrero del Llano**: a dark city after the dim-out, a torpedo, a burning tanker drifting north, crowds on the beach, PC-536 rescue.
3. **1926 Great Miami Hurricane**: storm, the deadly calm of the eye, surge over the causeway, the end of the boom.
4. **1992 Hurricane Andrew**: the strongest winds, mostly south of the main frame.

## Suggested scene frames
- **Main frame**: about 25.73–25.82 N, 80.24–80.12 W (river mouth, downtown, Brickell, the bay islands, South Beach).
- **Wide frame**: extend to 25.65 N to include Key Biscayne and Cape Florida.
- **Off-map** (use a minimap inset or an arrow/flight path leaving the frame): Homestead AFB, NAS Richmond / JM/WAVE, Opa-locka, the Nike/HAWK sites, the Potrero del Llano position (about 20 km SE), Hard Rock Stadium, Surfside, the Everglades.

All coordinates are approximate (typically within a few hundred metres) and are meant for placement. Snap them to OpenStreetMap when building the scene. A few are marked "rough, verify".

## Sensitive chapters
The riots (1968, 1980, 1982, 1989), I-95's destruction of Overtown, the Elián González raid and the Surfside collapse involve real victims within living memory. `war_sequences.json` gives a sober treatment for each: smoke, curfew darkness, captions. No combat choreography, and none of the jokey caption tone used elsewhere.

## Discrepancies found (decide before scripting)
| Topic | Source A | Source B | Suggested use |
|---|---|---|---|
| 1896 incorporation voters | 368 voters, 162 Black (miami-history.com, Florida History Network) | 502 voters, 100 Black (Wikipedia, History of Miami) | 368 / 162 (most cited) |
| 1567 stockade location | North bank (miami-history.com) | South bank (Wikipedia Tequesta; Legends of America) | Place at the river mouth; caption without naming the bank |
| 1743 mission duration | 1743–1744 (Wikipedia, History of Miami) | "Less than three months" (Wikipedia, Tequesta) | "A few months" |
| Seminole raiders at Cape Florida | About 12 (Thompson's account as reported) | 30–40 (other retellings) | Small band, about 12–40 |
| 1926 hurricane deaths | 372 (Red Cross) | 539+ (later estimates) | "Hundreds" or "372–539+" |
| Julia Tuttle Causeway | Opened Dec 12, 1959 | I-195 fully open Dec 22, 1961 | 1959 for the causeway |
| Panorama Tower completion | 2017 | 2018 | 2017–18 |
| Mariel numbers | About 125,000 Cubans | 150,000 (Wikipedia, History of Miami; likely includes about 25,000 Haitians) | 125,000 Cubans plus about 25,000 Haitians |
| Potrero del Llano time | "07:17 hours" on uboat.net | No time zone given; U-boat logs usually use German time, which means local night, matching eyewitness accounts of it burning for hours | Night, marked "verify" |
| I-95 displacement | About 12,000 residents | 8,500 households by 1968 | "About 12,000 residents" |

## Gaps (not found or not confirmed)
- Tequesta weapons and exact canoe types; ship types at the 1566/1567 landings.
- Named Union ships in Biscayne Bay during the Civil War.
- Exact coordinates of the HAWK and Nike batteries inside Miami (HM-12, HM-39, HM-95).
- The exact location of the pre-1909 Miami River rapids.
- Biscayne House of Refuge removal date.

## Main sources
Wikipedia (History of Miami, Timeline of Miami, Tequesta, Miami Circle, Cape Florida Light, Fort Dallas, Second Seminole War, 1926 Miami hurricane, Hurricane Andrew, Hurricane King, SS Potrero del Llano, NAS Richmond, JMWAVE, Homestead ARB, 1980 Miami riots, List of tallest buildings in Miami, and others); miami-history.com (Casey Piket); HistoryMiami; Florida Historical Society; Florida Memory; NOAA/NHC and the NWS Miami office; uboat.net; the Historical Marker Database; National Park Service; JFK Library; CIA; FIFA; Inter Miami CF; Florida YIMBY. Each entry lists its own URLs.
