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

## 2. Demo: scan a real EOB, then My visits (2.5 min, Timur)
1. Home, "Scan a bill or EOB", tick the consent box, "Upload a photo or PDF", choose a real insurer EOB PDF (names
   removed; keep it on the demo laptop, never in the repository). The table shows every line read from the PDF;
   the reader copies the amounts and fixed rules put them under the printed column headers.
2. Result for an ER visit where the family had met its out-of-pocket maximum: "Your EOB says you owe $0", what to do
   if a bill still arrives, the network discount the provider may not bill, a blood draw bundled into the ER visit.
3. My visits, "See an example" (or "+ New visit" and type: Bill Banner UMC Tucson $1,222.30; EOB Banner UMC Tucson
   $1,154.80; Bill Emergency physicians group $652; EOB Emergency physicians group $82; Bill Radiology Ltd $95; Bill
   Tucson Fire Department $1,950).
4. Result: bills ask for $3,919.30; you really owe $1,236.80 now; $637.50 in question; the radiology and ambulance bills
   wait for the EOB. Show "Share summary with family" and the collector letter.

## 3. Demo: Lower my bill (1.5 min, Nikita)
- Banner Desert Medical Center, household of 3, $45,000 a year, insurance paid part. Answer: you may qualify for free
  care (100% off the balance after insurance). Show the documents checklist, the 501(r) collections rule and the letter.

## 4. Demo: ambulance bill, in Spanish (1.5 min, Danil)
- Switch to Español. "Creo que está mal": Una factura, Sí tengo seguro, $1,950; Fuera de la red; Ambulancia terrestre,
  Tucson Fire Department, ALS, 4 miles, "No me llevaron". Result: the ADHS-approved ALS rate is $1,569.36 and A.R.S.
  36-2239 forbids charging more; refused transport may be free under 36-2239(K).

## 5. Research and next steps (2 min, Timur)
- R2: can AI check a bill? Synthetic bills with planted errors; rules vs open-weights models (pilot results on the
  slide).
- R1: statewide financial assistance policies. R3: usability study (find the amount owed, spot the error).
- Asks: contacts in hospital billing or patient financial services; students for the usability study.

## Backup
- If the API is down: screenshots in docs/demo/ (take them the day before).
- If asked "is this legal advice": no; each finding says "ask about this" and links the official rule; the letter
  asks to put the account on hold, not to refuse payment.
