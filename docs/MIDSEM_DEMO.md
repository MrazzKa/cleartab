# Mid-semester demo script (Nov 9, about 8 minutes)

Before: start Postgres, the API and the web app (README "Run locally"); open the app on a phone-sized window and on
the projector. Load nothing in advance; every step below is live.

## 1. The problem (1 min, Timur)
- "We set out to compare hospital prices. H2 said prices vary 2x or more; the pooled median was 1.92, so it was not
  met. The bigger finding: price depends on the health system."
- "Then we asked the UA Campus Health insurance office what students struggle with. Not choosing a hospital: the
  bill afterwards. People can't read the explanation of benefits and can't tell if a bill is right."
- KFF: 41% of US adults have medical debt; 44% of them did not pay a bill in full because they were not sure it was
  correct.

## 2. Demo: quick check (2 min, Nikita)
1. Home, "Check a bill". "What did you get?" -> "A bill and an EOB".
2. Not an emergency. Amounts: bill asks $35, EOB says you owe $35, already paid $35 at check-in.
3. In network, no ambulance, "Check my bill".
4. Result: "We found 1 likely error worth up to $35": the payment was not subtracted. "What to do now", then
   "Get a ready-to-send letter": type a name, copy the letter.
- Point out: nothing is stored; every finding cites its source (CMS).

## 3. Demo: deeper check (2 min, Danil)
1. "Enter the lines", load "Knee MRI and blood test at a Tucson hospital".
2. Results: bill $67.50 above the EOB; the blood test billed twice; a blood draw the insurer never saw; and the MRI
   allowed amount ($1,150) above every rate Banner published for this insurer ($712.68-$950.22), with a link to the
   hospital's own file.
3. Mention the CMS rules behind it: 3.1 million NCCI code pairs and the MUE unit limits.

## 4. Demo: help paying (1 min, Artyom)
- "Help paying": household of 2, $40,000, no insurance. Banner, HonorHealth, Dignity and Mayo: free care. Tenet and
  Northwest do not publish income limits.
- Finding: the same Banner policy gives free care below 200% of the poverty level in Arizona and up to 250% in
  Colorado, because of Colorado law.

## 5. Research and next steps (2 min, Timur)
- R2: can AI check a bill? Synthetic bills with planted errors; rules vs open-weights models (pilot results on the
  slide).
- R1: statewide financial assistance policies. R3: usability study (find the amount owed, spot the error).
- Asks: contacts in hospital billing or patient financial services; students for the usability study.

## Backup
- If the API is down: screenshots in docs/demo/ (take them the day before).
- If asked "is this legal advice": no; each finding says "ask about this" and links the official rule; the letter
  asks to put the account on hold, not to refuse payment.
