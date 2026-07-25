"""Source definitions for the visa-information corpus (v6)."""

SOURCES = {
    "USCISPM": {
        "seeds": ["https://www.uscis.gov/policy-manual/volume-2"],
        "allow": [r"^https://www\.uscis\.gov/policy-manual/volume-2"],
        "deny": [],
        "visa_hint": ["H1B", "F1", "B2", "L1", "O1"],
        "max_pages": 100,
    },
    "I129": {
        "seeds": ["https://www.uscis.gov/i-129"],
        "allow": [
            r"^https://www\.uscis\.gov/i-129",
            r"^https://www\.uscis\.gov/sites/default/files/document/forms/i-129.*\.pdf",
        ],
        "deny": [r"i-129f"],
        "visa_hint": ["H1B", "L1", "O1"],
        "max_pages": 10,
    },
    "I539": {
        "seeds": ["https://www.uscis.gov/i-539"],
        "allow": [
            r"^https://www\.uscis\.gov/i-539",
            r"^https://www\.uscis\.gov/sites/default/files/document/forms/i-539.*\.pdf",
        ],
        "deny": [],
        "visa_hint": ["F1", "B2", "H4", "F2", "L2"],
        "max_pages": 10,
    },
    "SEVP": {
        "seeds": [
            "https://studyinthestates.dhs.gov/students",
            "https://studyinthestates.dhs.gov/stem-opt-hub",
        ],
        "allow": [r"^https://studyinthestates\.dhs\.gov/"],
        "deny": [r"/blog", r"/school-search", r"/filter", r"/privacy", r"/site/", r"/20\d\d/"],
        "visa_hint": ["F1", "F2"],
        "max_pages": 55,
    },
    "CFR": {
        "seeds": [
            "https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-214",
            "https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-214/subpart-A/section-214.1",
            "https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-214/subpart-A/section-214.2",
            "https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-214/subpart-A/section-214.3",
            "https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-214/subpart-A/section-214.4",
            "https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-214/subpart-A/section-214.5",
            "https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-214/subpart-A/section-214.6",
            "https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-214/subpart-A/section-214.7",
            "https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-214/subpart-A/section-214.8",
            "https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-214/subpart-A/section-214.9",
            "https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-214/subpart-A/section-214.10",
            "https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-214/subpart-A/section-214.11",
            "https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-214/subpart-A/section-214.12",
            "https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-214/subpart-A/section-214.13",
            "https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-214/subpart-A/section-214.14",
            "https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-214/subpart-A/section-214.15",
        ],
        "allow": [r"^https://www\.ecfr\.gov/current/title-8/chapter-I/subchapter-B/part-214"],
        "deny": [],
        "visa_hint": ["H1B", "F1", "B2", "L1", "O1", "H4", "F2", "L2"],
        "max_pages": 25,
    },
    "FAM": {
        "seeds": [
            "https://fam.state.gov/FAM/09FAM/09FAM040201.html",
            "https://fam.state.gov/FAM/09FAM/09FAM040202.html",
            "https://fam.state.gov/FAM/09FAM/09FAM040203.html",
            "https://fam.state.gov/FAM/09FAM/09FAM040204.html",
            "https://fam.state.gov/FAM/09FAM/09FAM040205.html",
            "https://fam.state.gov/FAM/09FAM/09FAM040206.html",
            "https://fam.state.gov/FAM/09FAM/09FAM040207.html",
            "https://fam.state.gov/FAM/09FAM/09FAM040208.html",
            "https://fam.state.gov/FAM/09FAM/09FAM040209.html",
            "https://fam.state.gov/FAM/09FAM/09FAM040210.html",
            "https://fam.state.gov/FAM/09FAM/09FAM040211.html",
            "https://fam.state.gov/FAM/09FAM/09FAM040212.html",
            "https://fam.state.gov/FAM/09FAM/09FAM040213.html",
            "https://fam.state.gov/FAM/09FAM/09FAM040214.html",
            "https://fam.state.gov/FAM/09FAM/09FAM040215.html",
            "https://fam.state.gov/FAM/09FAM/09FAM040216.html",
            "https://fam.state.gov/FAM/09FAM/09FAM040217.html",
        ],
        "allow": [r"^https://fam\.state\.gov/FAM/09FAM/09FAM0402\d+\.html"],
        "deny": [],
        "visa_hint": ["H1B", "F1", "B2", "L1", "O1"],
        "max_pages": 45,
    },
    "USCISTOPICS": {
        "seeds": [
            "https://www.uscis.gov/visit-the-united-states",
            "https://www.uscis.gov/working-in-the-united-states",
        ],
        "allow": [r"^https://www\.uscis\.gov/(visit-the-united-states|working-in-the-united-states)"],
        "deny": [],
        "visa_hint": ["H1B", "F1", "B2", "L1", "O1"],
        "max_pages": 15,
    },
}

# Global exclusions (proposal 7.1): never crawl these anywhere
GLOBAL_DENY = [
    r"login", r"signin", r"sign-in", r"account", r"casestatus", r"case-status",
    r"mailto:", r"\.(jpg|jpeg|png|gif|svg|css|js|ico|mp4|zip)(\?|$)",
    r"/es($|/)", r"/es-", r"lang=es",
]
