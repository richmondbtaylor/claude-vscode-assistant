"""
Append categorized transactions to the Bishop AI expense tracking sheet.
Appends new rows, then re-sorts entire sheet by date (oldest first).
"""
import gspread
import json
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SHEET_ID = "1QnrGd5O5pEwlZv-eAMbrtyeZsrr3s8BflSw4o0Cl3Pw"
TOKEN_PATH = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "gspread", "authorized_user.json")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def get_credentials():
    with open(TOKEN_PATH) as f:
        token_data = json.load(f)
    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=SCOPES,
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def categorize(desc, amount):
    """Return (Category, Business/Personal) based on description."""
    d = desc.upper()
    amt = float(amount)

    # Business/R&D Software
    if any(k in d for k in ["CLAUDE.AI", "OPENAI", "BROWSERFLOW", "NAME-CHEAP.COM", "WWW.PERPLEXITY.AI", "AUTISMHELPAPP.COM"]):
        return "Business/R&D Software", "Business"

    # Business - Freelance
    if "UPWORK" in d:
        return "Business - Freelance", "Business"

    # Personal - Dining
    dining_keywords = [
        "CHICK-FIL-A", "MCDONALD", "TACO BELL", "SUBWAY", "CHIPOTLE", "WENDY",
        "PANERA", "JERSEY MIKE", "SWEETGREEN", "EARLS", "EARL?S", "MOXIES",
        "BAKAN", "BARCELONA WYNWOOD", "CERVECERIA", "SABOR A PERU",
        "BLUE LAVENDER", "NOVELA CAF", "NOVELA C", "GRAZIANO", "COYO TAC",
        "STARBUCKS", "JOE & THE JUICE", "DONUT DEN", "TRUCKING DELICIOUS",
        "MR KABAB", "WAKEY MONKEY", "HIGHLAND BREWING", "RYE KNOT",
        "PURPLE ONION", "VAN LEEUWEN", "4D GELATERIA", "ROSETTA BAKER",
        "SALON DU CAFE", "PASION DEL CI", "CREMA DOWNTOWN", "BOUGAINVILLEA",
        "BAYSHORE HOSPITALITY", "RESTAURANT AT INTERC", "SPORTS GRILL",
        "BOBE", "WORLD OF BEER", "ABBEY BREWING", "BURIAL BEER",
        "ANTIDOTE BAR", "BWI PERI PERI", "HOU AIRP GASTROHUB", "ESPANOLITA",
        "ITALICA", "SALT AND STRAW", "SUNLIFE", "MICHELANGELO", "CASA LA",
        "SKY COFF", "CAFFE UM", "ROSEMARY", "SAVAGE LABS", "NINO GORDO",
        "1800 LUCKY", "MIAMI WYNWOOD K", "CANTINA", "JONATHANS GRILLE",
        "DEEP CULTURE", "LAKESIDE LOUNGE", "BAR LOUI", "FROTHY MONKEY",
        "ODIES", "SONNY'S PATIO", "LOSERS", "GARCIA'S TAQUERIA", "CHIVANADA",
        "BAJA BUR", "MOES #", "TACO STA", "TACO STAND", "LA SANDWICHERIE",
        "AULD DUBLIN", "THE AULD", "TRATTORI", "GBH BAYSHORE", "GBH BAYS",
        "SPO*TRUEBARIS", "SP_COFFEEC", "WELL COFFEEHOUSE", "ELIXR COFFEE",
        "SILVER FOX", "SILVER F", "MAGDALENA COF", "MADELEINE & C",
        "SHEPHERD ARTI", "UNDER THE MAN", "HNS PARTNERS",
        "SPO*BOUGAINVILLEA", "MAMAN", "CAVA GR", "DORAL YA",
        "TAP 42", "CUCINA", "MR. BAGUETTE", "MIKE'S MIAMI",
        "THE SYLVESTER", "COCONUT CHARLIE", "URBAN COWBOY",
        "LSU THE BRIGHT", "CK AT BIRD"
    ]
    for kw in dining_keywords:
        if kw in d:
            return "Personal - Dining", "Personal"

    # Personal - Groceries
    if any(k in d for k in ["WINN DIXIE", "WINN-DIXIE", "PUBLIX", "KROGER", "WHOLEFDS",
                             "INGLES MARKET", "FERNANDEZ FOOD", "FASTOP MARKET", "365 MARKET"]):
        # Make sure it's not KROGER FUEL
        if "KROGER FUEL" not in d:
            return "Personal - Groceries", "Personal"

    # Personal - Gas/Travel
    if any(k in d for k in ["KROGER FUEL", "CHEVRON", "EXXONMOBIL", "BP ", "BUC-EE",
                             "LOVE'S", "MARATHON", "RACEWAY", "RACETRAC", "CITGO", "TWICE DAILY"]):
        return "Personal - Gas/Travel", "Personal"
    if "CIRCLE K" in d:
        return "Personal - Gas/Travel", "Personal"

    # Personal - Shopping/Clothing
    if any(k in d for k in ["TARGET", "T J MAXX", "DICK'S SPORT", "NORDSTROM", "ROSS ",
                             "WAL-MART", "URBAN OUTFITTERS", "DSW SHOE", "POSHMARK",
                             "LBSTORE", "M A PACE GENERAL", "SPORTIVE II", "HUDSONNEWS",
                             "RAINRETAIL", "ELDER'S ACE"]):
        return "Personal - Shopping", "Personal"

    # Personal - Transportation
    if any(k in d for k in ["UBER", "BRIGHTLINE", "SOUTHWEST AIR", "BIRD APP", "SPIRIT AL DIRECT"]):
        return "Personal - Transportation", "Personal"

    # Personal - Fitness
    if any(k in d for k in ["CLASSPASS", "SOCCER CAGE", "BRICKELL SOCCER", "LA FITNESS",
                             "CRUNCH", "SPOND", "STADIO", "MIAMI BEACH GOLF", "MCCABE GOLF",
                             "JACKED RABBIT", "FUTBAR", "WODIFY", "GREEN RIVER ADVENTUR"]):
        return "Personal - Fitness", "Personal"

    # Personal - Entertainment
    if any(k in d for k in ["FEVERUP", "UNIVERSAL", "VIZCAYA", "BILLFOLD", "EB *MOVEMENT",
                             "BEANS CREEK", "BEER CITY", "GROUPON", "JASON ALDEAN",
                             "MEGACENTER", "PARLOR SOCIAL", "STANDARD MIAMI", "FB THE MOORE",
                             "AMC ", "SEE TICKETS", "BIRD BOWL", "BEN & DANNY",
                             "REGATTA GROVE", "THE LANDING", "SUNDAY APP"]):
        return "Personal - Entertainment", "Personal"

    # Personal - Pharmacy/Health
    if any(k in d for k in ["WALGREENS", "VITAMIN SHOPP", "BRICKELL SUPERCUTS"]):
        return "Personal - Pharmacy/Health", "Personal"

    # Personal - Bills/Utilities
    if "ATT BILL PAYMENT" in d:
        return "Personal - Bills/Utilities", "Personal"

    # Personal - Fees/Fines
    if any(k in d for k in ["COURT-TRAFFIC", "NIC*-DOS DIVISION", "PY *ECOGUARD", "CASH ADVANCE FEE"]):
        return "Personal - Fees/Fines", "Personal"

    # Personal - Lodging
    if any(k in d for k in ["GAYLORD OPRYLAND", "THOMPSON HOTEL", "EAST GREENVILLE",
                             "HATLEY POINTE", "FSP*HISTORIC"]):
        return "Personal - Lodging", "Personal"

    # Personal - Other (kava, liquor, parking, convenience, etc.)
    if any(k in d for k in ["LANIER PARKING", "PNFBYTPS", "601 NW 2ND", "8518 SW 40",
                             "6691 BIRD", "2020 NW 17", "5343 NW 7", "267 INDIAN LA",
                             "EDGEWATER LIQ", "SUPERNATURALK", "BRICK LLC", "7-ELEVEN",
                             "ELIXIR KAVA", "KAVA GARDEN", "SOUTH POINTE",
                             "SIPWITHME", "BT*SIPWITHME"]):
        return "Personal - Other", "Personal"

    # Fallback
    return "Personal - Other", "Personal"


def parse_transactions():
    """Parse the CSV data and return categorized rows."""
    # All transaction data from the three CSV files
    raw_data = """08/24/2025,UBER,21.64
08/24/2025,GARCIA'S TAQUERIA GRHENDERSONVLLE       TN,24.84
08/24/2025,PANERA BREAD        HENDERSONVILLE      TN,21.82
08/24/2025,TST* LOSERS - MIDTOWNASHVILLE           TN,30.65
08/23/2025,CHICK-FIL-A #01481 0HENDERSONVLLE       TN,5.43
08/23/2025,KROGER FUEL #9571 00HENDERSONVILL       TN,57.10
08/23/2025,KROGER NASHVILLE    HENDERSONVILLE      TN,20.80
08/23/2025,MCCABE GOLF COURSE  NASHVILLE           TN,14.00
08/23/2025,MCCABE GOLF COURSE  NASHVILLE           TN,28.59
08/23/2025,MCCABE GOLF COURSE *ATLANTA             GA,0.32
08/23/2025,MCCABE GOLF COURSE *ATLANTA             GA,0.66
08/23/2025,TST* ODIES 00225330 NASHVILLE           TN,17.56
08/23/2025,TST* SONNY'S PATIO PNASHVILLE           TN,51.34
08/22/2025,AplPay TST* BAR LOUINASHVILLE           TN,54.88
08/22/2025,TST* FROTHY MONKEY -NASHVILLE           TN,29.21
08/22/2025,TWICE DAILY W BISON NASHVILLE           TN,3.73
08/22/2025,WODIFY* STRIPE PI DEDENVER              CO,16.99
08/21/2025,AplPay MOES #645 066HENDERSONVILL       TN,12.06
08/20/2025,AplPay JACKED RABBITMIAMI               FL,-83.06
08/20/2025,AplPay TST* SILVER FNASHVILLE           TN,12.02
08/19/2025,AplPay CLASSPASS* MOMISSOULA            MT,59.00
08/19/2025,AplPay FUTBAR* SUNDALOUISVILLE          KY,8.00
08/19/2025,AplPay JACKED RABBITMIAMI               FL,-83.06
08/19/2025,AplPay PANERA BREAD HENDERSONVILLE      TN,14.26
08/18/2025,AplPay 267 INDIAN LAHENDERSONVILLE      TN,40.00
08/18/2025,AplPay MOES #645 066HENDERSONVILL       TN,12.06
08/18/2025,UBER,18.26
08/17/2025,AplPay CHIVANADA II Baltimore           MD,15.36
08/17/2025,AplPay FUTBAR* HENDELOUISVILLE          KY,7.00
08/17/2025,AplPay JERSEY MIKES NASHVILLE           TN,18.38
08/17/2025,UBER,5.40
08/17/2025,UBER,25.54
08/16/2025,AplPay JACKED RABBITMIAMI               FL,83.06
08/16/2025,UBER,21.84
08/16/2025,UBER,28.69
08/16/2025,DEEP CULTURE (BAR)  NASHVILLE           TN,15.70
08/16/2025,DEEP CULTURE (BAR)  NASHVILLE           TN,28.13
08/16/2025,DEEP CULTURE (BAR)  NASHVILLE           TN,29.13
08/15/2025,DEEP CULTURE (BAR)  NASHVILLE           TN,15.57
08/15/2025,DEEP CULTURE (BAR)  NASHVILLE           TN,29.13
08/15/2025,DEEP CULTURE (BAR)  NASHVILLE           TN,32.56
08/15/2025,JONATHANS GRILLE-GERNASHVILLE           TN,37.08
08/15/2025,TST* LAKESIDE LOUNGENASHVILLE           TN,6.59
08/14/2025,ATT BILL PAYMENT    DALLAS              TX,60.58
08/14/2025,AplPay 10096 CAVA GRNASHVILLE           TN,20.19
08/14/2025,AplPay TST* BAJA BURBERRY HILL          TN,13.00
08/14/2025,BUC-EE'S #52/UNBRANDCALHOUN             GA,2.77
08/14/2025,DEEP CULTURE (BAR)  NASHVILLE           TN,23.00
08/14/2025,WAL-MART SUPERCENTERNASHVILLE           TN,3.18
08/13/2025,AplPay CHIPOTLE     ORLANDO             FL,14.64
08/13/2025,AplPay CIRCLE K # 21GAINESVILLE         FL,6.32
08/13/2025,AplPay RAINRETAIL*DEWILLISTON           FL,37.45
08/13/2025,BUC-EE'S #52 OUTSIDECALHOUN             GA,37.99
08/13/2025,CHEVRON 0390046/CHEVTIFTON              GA,2.07
08/13/2025,CHEVRON 0390046/CHEVTIFTON              GA,49.61
08/13/2025,MARATHON 21741 0000 ORLANDO             FL,50.33
08/13/2025,RAINRETAIL*DEVILS DEWILLISTON           FL,5.35
08/12/2025,AplPay SOCCER CAGE DMIAMI               FL,3.55
08/12/2025,AplPay SOCCER CAGE DMIAMI               FL,12.84
08/11/2025,CHEVRON 0047636/CHEVMIAMI               FL,66.21
08/10/2025,AplPay HNS PARTNERS1MIAMI BEACH         FL,11.97
08/10/2025,AplPay SALON DU CAFEMIAMI BEACH         FL,7.66
08/10/2025,AplPay SOUTH POINTE Miami Beach         FL,6.45
08/10/2025,AplPay TST* THE AULDMIAMI               FL,12.68
08/10/2025,LSU THE BRIGHTSIDE MMIAMI               FL,45.80
08/08/2025,AplPay WINN DIXIE   MIAMI               FL,25.04
08/07/2025,AplPay MCDONALD'S   MIAMI               FL,7.47
08/07/2025,AplPay SPOND* AULD DPEMBROKE PINES      VA,16.55
08/07/2025,AplPay TST* TACO STAMIAMI               FL,14.99
08/06/2025,BROWSERFLOW         UTRECHT             UT,18.95
08/06/2025,CLAUDE.AI SUBSCRIPTISAN FRANCISCO       CA,21.95
08/06/2025,JOE & THE JUICE MIAMNEW YORK            NY,13.59
08/06/2025,SPO*BOUGAINVILLEA'SOSOUTH MIAMI         FL,4.49
08/05/2025,SEE TICKETS* DEEP TRBEVERLY HILLS       CA,59.43
08/05/2025,SOCCER CAGE DOWNTOWNMIAMI               FL,16.05
08/04/2025,TACO BELL           MIAMI               FL,11.43
08/03/2025,AplPay WINN DIXIE   MIAMI               FL,26.10
08/03/2025,LA FITNESS          949-255-8100        CA,42.79
08/03/2025,TST* THE SYLVESTER 3MIAMI               FL,46.62
08/02/2025,AplPay UNDER THE MANMiami Beach         FL,28.49
08/02/2025,BRICKELL SUPERCUTS  MIAMI               FL,36.00
08/02/2025,MOXIES MIAMI 6500000MIAMI               FL,9.60
08/02/2025,TST* MAMAN - BRICKELMIAMI               FL,5.95
08/02/2025,TST* ROSEMARYS MIAMIMIAMI               FL,42.88
08/02/2025,TST* SAVAGE LABS 001MIAMI               FL,102.08
08/02/2025,WHOLEFDS SBE 10285 0MIAMI BEACH         FL,16.66
08/01/2025,AplPay TST* NOVELA CMIAMI               FL,5.08
08/01/2025,MCDONALD'S          MIAMI               FL,10.47
08/01/2025,TST* MAMAN - BRICKELMIAMI               FL,5.08
07/31/2025,AplPay CHEVRON 00476MIAMI               FL,50.00
07/31/2025,AplPay DICK'S SPORTICORAOPOLIS          PA,54.84
07/31/2025,AplPay SPOND* IGWM  MIAMI BEACH         FL,21.72
07/30/2025,AplPay TST* CAFFE UMMIAMI BEACH         FL,4.92
07/29/2025,AplPay WINN-DIXIE   MIAMI               FL,13.53
07/28/2025,AplPay SABOR A PERU MIAMI               FL,57.21
07/27/2025,AplPay TST* TRATTORIMIAMI BEACH         FL,14.83
07/27/2025,AplPay WINN DIXIE   MIAMI               FL,11.04
07/27/2025,TST* MIAMI WYNWOOD KMIAMI               FL,33.28
07/27/2025,WINN DIXIE          MIAMI               FL,43.13
07/26/2025,AplPay ROSETTA BAKERMIAMI BEACH         FL,15.81
07/26/2025,AplPay SHEPHERD ARTIMIAMI BEACH         FL,5.06
07/26/2025,AplPay SPOND* IGWM  MIAMI BEACH         FL,21.72
07/26/2025,PUBLIX              MIAMI BEACH         FL,5.87
07/26/2025,TST* 1800 LUCKY 0000MIAMI               FL,29.72
07/26/2025,TST* NINO GORDO 0022MIAMI               FL,153.72
07/25/2025,AplPay PUBLIX       CORAL GABLES        FL,13.71
07/25/2025,AplPay TST* GBH BAYSMIAMI               FL,12.64
07/23/2025,TST* TACO STAND MIAMMIAMI               FL,31.61
07/22/2025,AplPay AMC 0278 TAMIMIAMI               FL,35.26
07/21/2025,CHEVRON 0047636/CHEVMIAMI               FL,61.85
07/21/2025,SEE TICKETS* DEEP TRHOLLYWOOD           CA,238.85
07/20/2025,AplPay VAN LEEUWEN IMiami Beach         FL,9.31
07/20/2025,AplPay WINN DIXIE   MIAMI               FL,54.69
07/19/2025,AplPay CLASSPASS* MOMISSOULA            MT,59.00
07/19/2025,AplPay ELIXIR KAVA BMIAMI BEACH         FL,12.47
07/19/2025,AplPay MCDONALD'S   MIAMI               FL,5.34
07/19/2025,AplPay SPOND* IGWM  MIAMI BEACH         FL,21.72
07/19/2025,AplPay TST* CASA LA MIAMI               FL,33.28
07/19/2025,AplPay UNDER THE MANMiami Beach         FL,19.26
07/19/2025,TST* LA SANDWICHERIEMIAMI BEACH         FL,13.13
07/19/2025,WALGREENS           MIAMI BEACH         FL,6.15
07/18/2025,AplPay TST* SKY COFFMIAMI               FL,9.09
07/18/2025,NAME-CHEAP.COM* XPIOPHOENIX             AZ,9.98
07/17/2025,AplPay TST* TACO STAMIAMI               FL,11.19
07/17/2025,AplPay WENDY'S      MIAMI               FL,8.87
07/17/2025,LA FITNESS  *ANNUALF949-255-8100        CA,63.13
07/16/2025,AplPay BLUE LAVENDERMIAMI BEACH         FL,15.24
07/16/2025,AplPay CHEVRON 00476MIAMI               FL,35.00
07/16/2025,AplPay JACKED RABBITMIAMI               FL,83.06
07/16/2025,AplPay Southwest AirDALLAS              TX,4.85
07/15/2025,AplPay VITAMIN SHOPPMIAMI               FL,3.79
07/14/2025,ATT BILL PAYMENT    DALLAS              TX,131.24
07/14/2025,UBER,36.05
07/14/2025,AplPay WINN DIXIE   MIAMI               FL,23.90
07/13/2025,AUTISMHELPAPP.COM   DUBLIN              CO,0.50
07/13/2025,AplPay BWI PERI PERIELLICOTT CITY       MD,16.95
07/13/2025,AplPay HUDSONNEWS  SGREER               SC,6.49
07/13/2025,TST* ANTIDOTE BAR 30ASHEVILLE           NC,7.38
07/12/2025,AplPay BURIAL BEER CAsheville           NC,8.99
07/12/2025,AplPay WAKEY MONKEY Saluda              NC,3.50
07/12/2025,BURIAL BEER CO.     Asheville           NC,8.99
07/12/2025,GREEN RIVER ADVENTURSaluda              NC,5.34
07/12/2025,M A PACE GENERAL STOSALUDA              NC,22.00
07/11/2025,UBER,21.99
07/11/2025,HOU AIRP GASTROHUB FHOUSTON             TX,36.15
07/10/2025,AplPay CHICK-FIL-A #PINECREST           FL,9.90
07/10/2025,EARLS DADELAND      MIAMI               FL,57.67
07/09/2025,AplPay WINN-DIXIE   MIAMI               FL,2.88
07/09/2025,TST* GBH BAYSHORE CLMIAMI               FL,75.60
07/08/2025,AplPay CK AT BIRD & MIAMI               FL,13.36
07/08/2025,AplPay SOCCER CAGE DMIAMI               FL,12.84
07/07/2025,AplPay WINN-DIXIE   MIAMI               FL,7.99
07/06/2025,AplPay HNS PARTNERS1MIAMI BEACH         FL,11.97
07/06/2025,CLAUDE.AI SUBSCRIPTISAN FRANCISCO       CA,21.95
07/06/2025,TST* ESPANOLITA 3006MIAMI BEACH         FL,47.30
07/05/2025,AplPay UNDER THE MANMiami Beach         FL,4.01
07/05/2025,AplPay UNDER THE MANMiami Beach         FL,15.73
07/05/2025,MCDONALD'S          MIAMI               FL,9.93
07/05/2025,NIC*-DOS DIVISION OF850-245-6939        FL,125.00
07/05/2025,TST* ITALICA MIDTOWNMIAMI               FL,14.72
07/05/2025,TST* MR. BAGUETTE - MIAMI               FL,16.35
07/04/2025,AplPay TST* NOVELA CMIAMI               FL,5.08
07/04/2025,AplPay TST* NOVELA CMIAMI               FL,7.93
07/04/2025,TARGET        021881MIAMI               FL,23.16
07/04/2025,THE ABBEY BREWING COMIAMI BEACH         FL,21.20
07/03/2025,AplPay SP_COFFEEC* CMARINA DEL REY      CA,37.23
07/03/2025,LA FITNESS          MIAMI               FL,85.58
07/02/2025,AplPay SWEETGREEN COCORAL GABLES        FL,19.00
07/02/2025,AplPay WINN DIXIE   MIAMI               FL,7.18
07/02/2025,AplPay WINN DIXIE   MIAMI               FL,54.36
07/02/2025,SPO*BOUGAINVILLEA'SOSOUTH MIAMI         FL,11.66
07/01/2025,AplPay CHIPOTLE     MIAMI               FL,15.14
07/01/2025,AplPay WINN DIXIE   MIAMI               FL,18.47
07/01/2025,CHEVRON 0202650/CHEVMIAMI               FL,60.93
06/30/2025,MCDONALD'S F1789 000MIAMI               FL,7.16
06/30/2025,SABOR A PERU 0000   MIAMI               FL,13.31
06/29/2025,AplPay HNS PARTNERS1MIAMI BEACH         FL,16.77
06/29/2025,AplPay MICHELANGELO Miami Beach         FL,21.40
06/29/2025,AplPay TST* NOVELA CMIAMI               FL,24.34
06/29/2025,AplPay TST* SUNLIFE MIAMI BEACH         FL,21.80
06/29/2025,TST* SALT AND STRAW MIAMI               FL,16.65
06/29/2025,TST* TACO STAND MIAMMIAMI BEACH         FL,16.01
06/28/2025,BAKAN RESTAURANT 068MIAMI               FL,42.84
06/28/2025,BARCELONA WYNWOOD (B715-8982200         FL,51.20
06/28/2025,BLUE LAVENDER CAFE &MIAMI BEACH         FL,13.08
06/28/2025,WALGREENS           MIAMI BEACH         FL,13.80
06/27/2025,AplPay POSHMARK     support@poshmark.comCA,25.55
06/27/2025,MOXIES MIAMI 6500000MIAMI               FL,49.04
06/27/2025,TST* GBH BAYSHORE CLMIAMI               FL,21.76
06/26/2025,AplPay DSW SHOE WAREMIAMI               FL,60.02
06/26/2025,AplPay NORDSTROM RACCORAL GABLES        FL,53.44
06/26/2025,AplPay SPO*TRUEBARISMIAMI               FL,9.46
06/26/2025,AplPay VITAMIN SHOPPMIAMI               FL,60.06
06/25/2025,AplPay SPO*TRUEBARISMIAMI               FL,11.12
06/25/2025,AplPay WINN DIXIE   MIAMI               FL,15.86
06/24/2025,AplPay TST* DORAL YADORAL               FL,20.32
06/24/2025,AplPay TST* GRAZIANOCORAL GABLES        FL,11.83
06/23/2025,AplPay SPO*TRUEBARISMIAMI               FL,5.01
06/23/2025,AplPay SPO*TRUEBARISMIAMI               FL,14.74
06/23/2025,AplPay WINN DIXIE   MIAMI               FL,65.60
06/22/2025,HNS PARTNERS19650 LLMIAMI BEACH         FL,11.97
06/22/2025,TST* THE AULD DUBLINMIAMI               FL,38.06
06/21/2025,AplPay TST* TRATTORIMIAMI BEACH         FL,4.31
06/21/2025,CHEVRON 0047636/CHEVMIAMI               FL,61.15
06/20/2025,AplPay CK AT BIRD & MIAMI               FL,13.36
06/20/2025,AplPay PASION DEL CICoral Gables        FL,7.80
06/20/2025,AplPay TST* TAP 42 -CORAL GABLES        FL,34.34
06/20/2025,TST* TACO STAND MIAMMIAMI BEACH         FL,9.58
06/18/2025,AplPay TST* GRAZIANOCORAL GABLES        FL,6.46
06/18/2025,AplPay WINN DIXIE   MIAMI               FL,22.39
06/18/2025,MCDONALD'S          MIAMI               FL,7.27
06/18/2025,NAME-CHEAP.COM* SNTPPHOENIX             AZ,11.26
06/17/2025,AplPay SWEETGREEN COCORAL GABLES        FL,18.46
06/16/2025,AplPay JACKED RABBITMIAMI               FL,83.06
06/16/2025,AplPay WINN DIXIE   MIAMI               FL,37.68
06/15/2025,AplPay 4D GELATERIA MIAMI BEACH         FL,7.41
06/15/2025,AplPay SHEPHERD ARTIMIAMI BEACH         FL,12.34
06/15/2025,AplPay TST* CANTINA CORAL GABLES        FL,15.86
06/14/2025,BEN & DANNY INC.    MIAMI BEACH         FL,5.34
06/14/2025,CHICK-FIL-A #00073 0MIAMI               FL,27.25
06/14/2025,CREMA DOWNTOWN DADELKendall             FL,11.07
06/14/2025,CREMA DOWNTOWN DADELKendall             FL,12.00
06/14/2025,DICK'S SPORTING GOODCORAOPOLIS          PA,18.18
06/14/2025,EARLS DADELAND      MIAMI               FL,19.77
06/14/2025,REGATTA GROVE       Miami               FL,35.91
06/14/2025,URBAN OUTFITTERS 000MIAMI               FL,36.38
06/13/2025,TST* GBH BAYSHORE CLMIAMI               FL,130.56
06/12/2025,AplPay TST* COYO TACCORAL GABLES        FL,16.20
06/12/2025,AplPay WINN DIXIE   MIAMI               FL,29.50
06/11/2025,AplPay TST* COYO TACCORAL GABLES        FL,16.20
06/11/2025,AplPay TST* GRAZIANOCORAL GABLES        FL,11.87
06/11/2025,TST* MIKE'S MIAMI 30MIAMI               FL,8.46
06/10/2025,MARATHON 171058 0000MIAMI               FL,60.80
06/08/2025,AplPay TST* NOVELA CMIAMI               FL,24.61
06/08/2025,AplPay WINN DIXIE   MIAMI               FL,24.36
06/07/2025,AplPay MCDONALD'S   MIAMI               FL,7.27
06/07/2025,AplPay TST* GRAZIANOCORAL GABLES        FL,4.31
06/07/2025,AplPay WINN DIXIE   MIAMI               FL,47.55
06/07/2025,EARL?S RESTAURANT (MMiami               FL,37.26
06/06/2025,AplPay TST* CUCINA MMIRAMAR             FL,27.61
06/06/2025,AplPay WORLD OF BEERMIRAMAR             FL,90.53
06/06/2025,PY *ECOGUARD TENNESSMOUNT JULIET        TN,144.00
06/05/2025,AplPay SUBWAY       CORAL GABLES        FL,16.35
06/05/2025,AplPay TST* GRAZIANOCORAL GABLES        FL,6.46
06/05/2025,WWW.PERPLEXITY.AI   SAN FRANCISCO       CA,5.49
06/04/2025,AplPay CHIPOTLE     MIAMI               FL,10.00
06/04/2025,AplPay TST* GRAZIANOCORAL GABLES        FL,6.46
06/02/2025,WINN DIXIE          MIAMI               FL,90.07
06/01/2025,BAYSHORE HOSPITALITYMiami               FL,20.56
06/01/2025,BOUGAINVILLEA'S OLD SOUTH MIAMI         FL,8.48
06/01/2025,REGATTA GROVE       Miami               FL,30.24
05/31/2025,BIRD BOWL           MIAMI               FL,24.85
05/31/2025,RESTAURANT AT INTERCMIAMI               FL,30.87
05/31/2025,SPORTIVE II  INC    Miami               FL,58.83
05/31/2025,STARBUCKS 75866 STARMIAMI               FL,3.76
05/31/2025,TST* BOBE 00200628  MIAMI               FL,86.92
05/30/2025,BIRD BOWL ARCADE 000MIAMI               FL,20.00
05/30/2025,BOUGAINVILLEA'S OLD SOUTH MIAMI         FL,23.52
05/30/2025,OPENAI              SAN FRANCISCO       CA,10.98
05/30/2025,TST* SPORTS GRILL - CORAL GABLES        FL,61.85
05/25/2025,THE LANDING         Saint Petersburg    FL,-50.00
05/24/2025,CHEVRON 0378723/CHEVLARGO               FL,-8.42
05/24/2025,CHICK-FIL-A #01609 0SARASOTA            FL,-9.29
05/24/2025,CIRCLE K # 07785/CIRSARASOTA            FL,-59.75
05/24/2025,CIRCLE K # 07785/CIRSARASOTA            FL,-22.13
05/24/2025,COCONUT CHARLIE'S   ST PETE BEACH       FL,-58.61
05/24/2025,COCONUT CHARLIE'S   ST PETE BEACH       FL,-30.82"""

    rows = []
    for line in raw_data.strip().split("\n"):
        # Parse: date, description, amount
        parts = line.split(",")
        date_str = parts[0]
        amount_str = parts[-1]
        description = ",".join(parts[1:-1]).strip()

        # Skip MOBILE PAYMENT rows
        if "MOBILE PAYMENT" in description.upper():
            continue

        category, biz_personal = categorize(description, amount_str)

        # Format date as YYYY-MM-DD for sorting
        month, day, year = date_str.split("/")
        formatted_date = f"{year}-{month}-{day}"

        rows.append([formatted_date, description, float(amount_str), category, biz_personal])

    return rows


def main():
    print("Authenticating...")
    creds = get_credentials()
    gc = gspread.authorize(creds)

    print("Opening spreadsheet...")
    sh = gc.open_by_key(SHEET_ID)
    ws = sh.worksheet("Bishop AI")

    # Get existing data to find where to append
    existing = ws.get_all_values()
    print(f"Existing rows (including header): {len(existing)}")

    # Parse new transactions
    new_rows = parse_transactions()
    print(f"New transactions to append: {len(new_rows)}")

    # Append new rows
    if new_rows:
        ws.append_rows(new_rows, value_input_option="USER_ENTERED")
        print(f"Appended {len(new_rows)} rows.")

    # Now re-sort the entire sheet by date (column A), oldest first
    # Get updated row count
    all_data = ws.get_all_values()
    total_rows = len(all_data)
    print(f"Total rows after append: {total_rows}")

    if total_rows > 1:
        # Sort by column A (date), ascending, skipping header row
        ws.sort((1, 'asc'), range=f"A2:E{total_rows}")
        print("Sorted entire sheet by date (oldest first).")

    print("Done!")


if __name__ == "__main__":
    main()
