"""The 70 CMS-specified shoppable services, transcribed from Table 3 of the CY 2020 hospital price
transparency final rule (84 FR 65524, pages 65571-65572), retrieved from
https://www.federalregister.gov/documents/full_text/text/2019/11/27/2019-24931.txt on 2026-10-12.
Ranges and "or" entries are expanded to each code. Section names are the rule's own."""
SOURCE_URL = "https://www.federalregister.gov/documents/full_text/text/2019/11/27/2019-24931.txt"

CMS70 = {
    "Evaluation & management services": ["90832", "90834", "90837", "90846", "90847", "90853", "99203", "99204",
                                         "99205", "99243", "99244", "99385", "99386"],
    "Laboratory & pathology services": ["80048", "80053", "80055", "80061", "80069", "80076", "81000", "81001",
                                        "81002", "81003", "84153", "84154", "84443", "85025", "85027", "85610",
                                        "85730"],
    "Radiology services": ["70450", "70553", "72110", "72148", "72193", "73721", "74177", "76700", "76805",
                           "76830", "77065", "77066", "77067"],
    "Medicine and surgery services": ["216", "460", "470", "473", "743", "19120", "29826", "29881", "42820",
                                      "43235", "43239", "45378", "45380", "45385", "45391", "47562", "49505",
                                      "55700", "55866", "59400", "59510", "59610", "62322", "62323", "64483",
                                      "66821", "66984", "93000", "93452", "95810", "97110"],
}
MS_DRG = {"216", "460", "470", "473", "743"}
