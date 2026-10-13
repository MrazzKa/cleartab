# Discovery and access problems - Tucson and Phoenix hospitals

Evidence for H1 (data availability) and the compliance scoreboard (proposal Table 12). Checked on
2026-10-12 from this machine with the ClearTab user agent, 1 request per second per domain, robots.txt
respected (RFC 9309). Raw evidence: research/registry/recheck.csv, data/processed/robots_snapshots.csv,
data/processed/hospital_registry.csv (columns head_status, last_modified, content_length, head_at).

Scope: 46 general acute care hospitals (8 Tucson, 38 Phoenix). No file contents were read in this phase;
dates are HTTP Last-Modified headers, which show when the server copy changed, not the date inside the file.

Rules referenced (45 CFR 180.50, text checked on law.cornell.edu 2026-10-12): (d)(3) access without barriers,
including to automated searches and direct file downloads; (d)(5) file name `<ein>_<hospital-name>_standardcharges.[json|csv]`;
(d)(6) a .txt file in the website root naming each location, its source page and a direct file link; (e) update
at least once every 12 months.

| # | Problem type | CCN | Hospital | URL | Evidence | Date checked |
|---|---|---|---|---|---|---|
| 1 | Missing from cms-hpt.txt | 030037 | HonorHealth Tempe Medical Center | https://www.honorhealth.com/cms-hpt.txt | cms-hpt.txt lists 8 HonorHealth locations (incl. Florence) but not Tempe. File found on the price page instead: .../2023-12/860181654_honorhealthtmc_standardcharges.csv | 2026-10-12 |
| 2 | Wrong hospital in cms-hpt.txt | 030153 | East Valley ER & Hospital | https://eastvalleyhospital.com/cms-hpt.txt | The only entry is "Oklahoma ER & Hospital" with an okerhospital.com file | 2026-10-12 |
| 3 | File URL changed, old link dead | 030153 | East Valley ER & Hospital | https://eastvalleyhospital.com/csv-download/862195601_east-valley-hospital-llc_standardcharges_in | The URL recorded in the audit now returns HTTP 404. Current file on the price page: .../wp-content/uploads/2026/08/ev_standard_charges_862195601_east-valley-hospital-llc_standardcharges_in-1.csv (Last-Modified 2026-08-23) | 2026-10-12 |
| 4 | Non-standard file name | 030153 | East Valley ER & Hospital | same as above | Name starts with "ev_standard_charges_" instead of the EIN, contrary to the (d)(5) naming convention. Price page also links a "shoppable" PDF | 2026-10-12 |
| 5 | cms-hpt.txt served with an error status and points to a page, not a file | 030108 | The CORE Institute Specialty Hospital | https://www.thecoreinstitutehospital.com/cms-hpt.txt | Returns HTTP 404 with a body; its mrf-url is https://thecoreinstitutehospital.com/price-transparency (an HTML page), not a file | 2026-10-12 |
| 6 | Non-standard file name; old file still linked | 030108 | The CORE Institute Specialty Hospital | https://www.thecoreinstitutehospital.com/patients-visitors/billing-options/ | Page links 2026-09 CSVs named THE-CORE-INSTITUTE-SPECIALTY-HOSPITAL-STANDARDCHARGES.csv and 2026-...-MRF-INPATIENT.csv (no EIN), plus a 2021 "Machine-Readable-File-06.11.21.csv". The audit's 2019 XLSX finding is superseded | 2026-10-12 |
| 7 | robots.txt blocks the price file | 030085, 030114, 030148 | Northwest Medical Center, Oro Valley Hospital, Northwest Medical Center Sahuarita | https://www.healthiertucson.com/robots.txt | `disallow: /Uploads/*` for all agents; all three files are under /Uploads/. Conflicts with (d)(3)(iv) | 2026-10-12 |
| 8 | robots.txt blocks the whole site | 030006 | Tucson Medical Center | https://www.tmcaz.com/robots.txt | `User-Agent: *` `Disallow: /` covers cms-hpt.txt and the price page. Conflicts with (d)(3)(iv) | 2026-10-12 |
| 9 | Site refuses automated agent | 030138 | City of Hope Cancer Center Phoenix | https://www.cityofhope.org/robots.txt | HTTP 403 for robots.txt and for the price transparency page. No file found for the Phoenix location yet | 2026-10-12 |
| 10 | Site not reachable | 030112 | Arizona Orthopedic and Surgical Specialty Hospital | https://www.azosh.com/cms-hpt.txt | TLS handshake failure over HTTPS; Cloudflare "error code: 1001" (DNS resolution error) over HTTP | 2026-10-12 |
| 11 | Download goes through a third-party portal | 030022 | Valleywise Health Medical Center | https://valleywise.pt.panaceainc.com/MRFDownload/valleywise/valleywise | Listed in cms-hpt.txt. Redirects to https://mrf.panaceainc.com/Download.aspx?...; 539,835,870 bytes; no Last-Modified header; URL does not follow the (d)(5) name pattern | 2026-10-12 |
| 12 | File larger than the 2 GB design limit (F3) | 030103 | Mayo Clinic Hospital (Phoenix) | https://mcorgstatic.blob.core.windows.net/cms-price/860800150_mayo-clinic-arizona_standardcharges.csv | Content-Length 21,529,997,739 bytes (about 21.5 GB). Not a compliance problem; an engineering one | 2026-10-12 |
| 13 | Folder or file name date looks stale, server date is recent | 030014, 030037, 030038, 030087, 030092, 030121, 030123, 030146 | HonorHealth (8 hospitals) | https://www.honorhealth.com/sites/default/files/2023-12/... | Files sit in a 2023-12 folder; Last-Modified 2026-04-02 for all. HEAD reports Content-Length 20 bytes, which is not a real price file size; to be checked on download | 2026-10-12 |
| 14 | Folder or file name date looks stale, server date is recent | 030024, 030036, 030119, 030136, 030139 | Dignity Health (5 hospitals) | https://www.commonspirit.org/content/dam/commonspiritorg/en/dharz/ceaz/finance/price-transparency/ | Audit noted file names dated 2025.07.01; Last-Modified is 2026-06-11. No Content-Length on HEAD. Whether the content is older than 12 months is decided in Phase 2 from the date inside the file | 2026-10-12 |
| 15 | File name does not match the hospital | 030036, 030119 | Chandler Regional Medical Center, Mercy Gilbert Medical Center | commonspirit.org file URLs | Chandler Regional's file is named "dignity-community-care", Mercy Gilbert's "dignity-health"; the hospital names do not appear in the file names | 2026-10-12 |
| 16 | Older than 12 months | none | - | - | No reachable file had a Last-Modified older than 2025-10-12 (oldest: Banner UMC South 2026-03-04). The manually downloaded TMC and Northwest files are dated 2026-04-30 and 2026-04-01 inside the file | 2026-10-13 |
| 17 | File found is for a different location | 030138 | City of Hope Cancer Center Phoenix | City of Hope price transparency page (browser) | The file a team member downloaded, 951683875_city-of-hope-national-medical-center-_standardcharges.json, names City of Hope Helford Clinical Research Hospital, Duarte, CA. No file for the Phoenix (Goodyear) location was found | 2026-10-12 |
| 18 | Hospital domain no longer the hospital's site | 030112 | Arizona Orthopedic and Surgical Specialty Hospital | https://www.azosh.com/ (browser) | The address shows a vendor's page offering to produce CMS machine-readable files and chargemaster reviews, not the hospital; no price file found | 2026-10-12 |
| 19 | Hospital not in the CMS base list | - | TMC Rincon Hospital (5755 S. Houghton Road, Tucson) | TMC price transparency page (browser) | TMC publishes a separate file for Rincon Hospital (license H13332, same NPI as TMC); it is not in the CMS Hospital General Information list the registry was built from | 2026-10-12 |

Earlier audit findings carried over unchanged (not re-tested here because they are text on pages, not
machine checks): website terms of use restrict reproduction for 35 hospitals; CommonSpirit terms ban
automated harvesting (5 hospitals). Terms for Northwest, Arizona Spine and Joint, Exceptional, East Valley,
CORE, City of Hope, TMC and AZOSH are still "Not checked" and need a human read.

Note for the team: proposal reference [20] and the Feature 3 legal-basis paragraph cite 45 CFR 180.50(b)(3)
for "accessible without barriers" and 180.50(d) for the .txt file. The current text puts these at (d)(3)
and (d)(6). The data-use memo already uses (d)(3) and (d)(6). Fix the citation in the paper.
