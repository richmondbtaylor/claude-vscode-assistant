"""Tunable parameters for the whole pipeline. Nothing here does work."""
import pathlib

ROOT = pathlib.Path(__file__).parent
DATA = ROOT / "data"

# Lane 2a sweep grid. 25 metros chosen for population and Maps density.
METROS = [
    "New York NY", "Los Angeles CA", "Chicago IL", "Dallas TX", "Houston TX",
    "Atlanta GA", "Miami FL", "Phoenix AZ", "Philadelphia PA", "Boston MA",
    "Seattle WA", "Denver CO", "Charlotte NC", "Nashville TN", "Austin TX",
    "Tampa FL", "Orlando FL", "San Diego CA", "Minneapolis MN", "Detroit MI",
    "Portland OR", "Las Vegas NV", "Kansas City MO", "Columbus OH", "Raleigh NC",
]

# Vertical-agnostic basket. Chosen for businesses where real money moves
# through vendor bills, payroll and card spend.
MAPS_CATEGORIES = [
    "roofing contractor", "hvac contractor", "plumber", "electrician",
    "general contractor", "landscaping company", "pest control service",
    "concrete contractor", "painting contractor", "auto repair shop",
    "commercial cleaning service", "moving company", "medical spa",
    "dental clinic", "veterinary clinic", "physical therapy clinic",
    "marketing agency", "law firm", "accounting firm", "staffing agency",
    "printing company", "machine shop", "wholesale distributor",
    "catering company", "security system installer",
]

# Lane 1 intent basket. A paid hire in any of these implies real payroll.
JOB_TITLES = [
    "bookkeeper", "staff accountant", "controller", "accounts payable",
    "accounts receivable", "office manager", "billing specialist",
    "business manager",
]

ATS_HOSTS = [
    "boards.greenhouse.io", "jobs.lever.co", "apply.workable.com",
    "jobs.ashbyhq.com", "jobs.smartrecruiters.com",
]

# Score weights per family. Must sum to 100.
WEIGHTS = {"money": 40, "scale": 25, "signal": 25, "reach": 10}

# A company must clear this to reach Master, and must have evidence in at
# least this many families, so review count alone can never qualify anyone.
SCORE_FLOOR = 11
MIN_FAMILIES = 2

TIER1_FRACTION = 0.20
TARGET_MASTER_ROWS = 1000

# SBA sources, verified live 2026-08-26.
SBA_7A_URL = ("https://data.sba.gov/sites/default/files/uploaded_resources/"
              "FOIA_7a_FY2020_Present_asof_260630.csv")
PPP_150K_URL = ("https://data.sba.gov/sites/default/files/distribution/"
                "SBA-OCA-2022-07-001/public_150k_plus_240930.csv")

# Revenue-proxy floors for SBA rows.
MIN_JOBS_SUPPORTED = 5
MIN_GROSS_APPROVAL = 150_000

APIFY_BUDGET_USD = 10.0
