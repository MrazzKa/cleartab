# Manual downloads (robots.txt or the site blocks ClearTab's automated downloader)

The pipeline does not fetch these. A team member should open each URL in a normal browser, download the
file once, and save it unchanged into `data/raw/manual/` using the file name shown. Then record in the table
the date, and where on the page the link was. Do not rename the content or open and re-save it in Excel.

Checked 2026-10-12 from this machine (see research/registry/recheck.csv and data/processed/robots_snapshots.csv).

| CCN | Hospital | Why automated access was not used | What to open | Save as |
|---|---|---|---|---|
| 030085 | Northwest Medical Center (Tucson) | robots.txt: `disallow: /Uploads/*`; the file is under /Uploads/ | https://www.healthiertucson.com/Uploads/Public/Documents/charge-masters/charge-masters-2024/621762430_northwest-medical-center-tucson_standardcharges.csv (about 534 MB per the 2026-10-12 HEAD, see note) | data/raw/manual/030085_<original file name> |
| 030114 | Oro Valley Hospital | same robots.txt rule | https://www.healthiertucson.com/Uploads/Public/Documents/charge-masters/charge-masters-2024/522379881_oro-valley-hospital_standardcharges.csv | data/raw/manual/030114_<original file name> |
| 030148 | Northwest Medical Center Sahuarita | same robots.txt rule | https://www.healthiertucson.com/Uploads/Public/Documents/charge-masters/charge-masters-2024/384088744_northwest-medical-center-sahuarita_standardcharges.csv | data/raw/manual/030148_<original file name> |
| 030006 | Tucson Medical Center | robots.txt: `User-Agent: *  Disallow: /` (whole site) | https://www.tmcaz.com/cms-hpt.txt first, then https://www.tmcaz.com/en/price-transparency | data/raw/manual/030006_<original file name>, and paste the cms-hpt.txt text into data/raw/manual/030006_cms-hpt.txt |
| 030138 | City of Hope Cancer Center Phoenix (Goodyear) | site returns HTTP 403 to ClearTab's downloader for robots.txt and the price page | https://www.cityofhope.org/cms-hpt.txt, then the City of Hope price transparency page; look for the Phoenix (Goodyear) location | data/raw/manual/030138_<original file name>, or write "not found" in the table below |
| 030112 | Arizona Orthopedic and Surgical Specialty Hospital | www.azosh.com fails the TLS handshake and returns Cloudflare error 1001 over HTTP (site not reachable from this machine) | https://www.azosh.com/cms-hpt.txt; if the site is down for you too, search for the hospital's current website | data/raw/manual/030112_<original file name>, or "not found" |

Note on the Northwest HEAD requests: on 2026-10-12 a first version of the robots.txt checker did not
understand the `*` wildcard and sent one HEAD request (headers only, no body) to each of the three Northwest
file URLs. The checker was replaced with an RFC 9309 matcher (pipeline/robots.py, tests/test_robots.py) and the
requests were not repeated. The 534 MB figure comes from that HEAD and is shown only to help the human plan the
download.

Valleywise (030022) was removed from this list: its portal refused two GET requests on 2026-10-12 but the
third, in the first ETL run, succeeded.

## Record of manual downloads

| CCN | Downloaded by | Date | Page where the link was | File name | Notes |
|---|---|---|---|---|---|
| | | | | | |
