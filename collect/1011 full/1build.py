import os
import json

BASE_DIR = "data/seasons/1011 full"

teams_data = """
North Carolina	ACC
Duke	ACC
Florida St.	ACC
Clemson	ACC
Virginia Tech	ACC
Boston College	ACC
Maryland	ACC
Virginia	ACC
Miami (FL)	ACC
NC State	ACC
Georgia Tech	ACC
Wake Forest	ACC
Vermont	America East
Boston U.	America East
UAlbany	America East
Maine	America East
Stony Brook	America East
Hartford	America East
New Hampshire	America East
Binghamton	America East
UMBC	America East
Xavier	Atlantic 10
Temple	Atlantic 10
Richmond	Atlantic 10
Duquesne	Atlantic 10
George Washington	Atlantic 10
Rhode Island	Atlantic 10
St. Bonaventure	Atlantic 10
Dayton	Atlantic 10
Massachusetts	Atlantic 10
La Salle	Atlantic 10
Saint Louis	Atlantic 10
Saint Joseph's	Atlantic 10
Charlotte	Atlantic 10
Fordham	Atlantic 10
Belmont	ASUN
ETSU	ASUN
Jacksonville	ASUN
Lipscomb	ASUN
Mercer	ASUN
North Florida	ASUN
FGCU	ASUN
Campbell	ASUN
Kennesaw St.	ASUN
Stetson	ASUN
USC Upstate	ASUN
Kansas	Big 12
Texas	Big 12
Texas A&M	Big 12
Kansas St.	Big 12
Missouri	Big 12
Colorado	Big 12
Nebraska	Big 12
Baylor	Big 12
Oklahoma St.	Big 12
Oklahoma	Big 12
Texas Tech	Big 12
Iowa St.	Big 12
Pittsburgh	Big East
Notre Dame	Big East
Syracuse	Big East
Louisville	Big East
St. John's (NY)	Big East
Cincinnati	Big East
West Virginia	Big East
Georgetown	Big East
UConn	Big East
Villanova	Big East
Marquette	Big East
Seton Hall	Big East
Rutgers	Big East
Providence	Big East
South Fla.	Big East
DePaul	Big East
Northern Colo.	Big Sky
Montana	Big Sky
Weber St.	Big Sky
Northern Ariz.	Big Sky
Montana St.	Big Sky
Eastern Wash.	Big Sky
Portland St.	Big Sky
Idaho St.	Big Sky
Sacramento St.	Big Sky
Coastal Carolina	Big South
Liberty	Big South
UNC Asheville	Big South
VMI	Big South
Charleston So.	Big South
Winthrop	Big South
Presbyterian	Big South
High Point	Big South
Gardner-Webb	Big South
Radford	Big South
Ohio St.	Big Ten
Purdue	Big Ten
Wisconsin	Big Ten
Michigan	Big Ten
Illinois	Big Ten
Michigan St.	Big Ten
Penn St.	Big Ten
Northwestern	Big Ten
Minnesota	Big Ten
Iowa	Big Ten
Indiana	Big Ten
Long Beach St.	Big West
Cal Poly	Big West
CSUN	Big West
UC Santa Barbara	Big West
Pacific	Big West
Cal St. Fullerton	Big West
UC Irvine	Big West
UC Riverside	Big West
UC Davis	Big West
George Mason	CAA
Old Dominion	CAA
Hofstra	CAA
VCU	CAA
Drexel	CAA
James Madison	CAA
Delaware	CAA
UNCW	CAA
Georgia St.	CAA
Northeastern	CAA
William & Mary	CAA
Towson	CAA
UAB	CUSA
UTEP	CUSA
Tulsa	CUSA
Memphis	CUSA
Southern Miss.	CUSA
Marshall	CUSA
SMU	CUSA
East Carolina	CUSA
UCF	CUSA
Rice	CUSA
Houston	CUSA
Tulane	CUSA
Utah Valley	Great West
NJIT	Great West
North Dakota	Great West
South Dakota	Great West
Chicago St.	Great West
UTRGV	Great West
Houston Christian	Great West
Cleveland St.	Horizon
Butler	Horizon
Milwaukee	Horizon
Valparaiso	Horizon
Wright St.	Horizon
Detroit Mercy	Horizon
Green Bay	Horizon
Loyola Chicago	Horizon
Youngstown St.	Horizon
UIC	Horizon
N.C. Central	Independent
Savannah St.	Independent
Longwood	Independent
Seattle U	Independent
CSU Bakersfield	Independent
SIUE	Independent
Princeton	Ivy League
Harvard	Ivy League
Yale	Ivy League
Penn	Ivy League
Columbia	Ivy League
Cornell	Ivy League
Brown	Ivy League
Dartmouth	Ivy League
Fairfield	MAAC
Iona	MAAC
Rider	MAAC
Saint Peter's	MAAC
Loyola Maryland	MAAC
Canisius	MAAC
Siena	MAAC
Niagara	MAAC
Manhattan	MAAC
Marist	MAAC
Kent St.	MAC
Miami (OH)	MAC
Akron	MAC
Ohio	MAC
Buffalo	MAC
Bowling Green	MAC
Western Mich.	MAC
Ball St.	MAC
Central Mich.	MAC
NIU	MAC
Eastern Mich.	MAC
Toledo	MAC
Bethune-Cookman	MEAC
Hampton	MEAC
Coppin St.	MEAC
Morgan St.	MEAC
N.C. A&T	MEAC
Norfolk St.	MEAC
Florida A&M	MEAC
South Carolina St.	MEAC
Delaware St.	MEAC
UMES	MEAC
Howard	MEAC
Missouri St.	MVC
Wichita St.	MVC
Indiana St.	MVC
Creighton	MVC
UNI	MVC
Evansville	MVC
Drake	MVC
Southern Ill.	MVC
Illinois St.	MVC
Bradley	MVC
San Diego St.	Mountain West
BYU	Mountain West
UNLV	Mountain West
Colorado St.	Mountain West
New Mexico	Mountain West
Air Force	Mountain West
Utah	Mountain West
Wyoming	Mountain West
TCU	Mountain West
LIU	NEC
Quinnipiac	NEC
Robert Morris	NEC
Central Conn. St.	NEC
St. Francis Brooklyn	NEC
Wagner	NEC
Mount St. Mary's	NEC
Bryant	NEC
Saint Francis	NEC
Sacred Heart	NEC
Monmouth	NEC
FDU	NEC
Murray St.	OVC
Morehead St.	OVC
Austin Peay	OVC
Tennessee Tech	OVC
Tennessee St.	OVC
Eastern Ky.	OVC
UT Martin	OVC
Southeast Mo. St.	OVC
Eastern Ill.	OVC
Jacksonville St.	OVC
Arizona	Pac-10
UCLA	Pac-10
Washington	Pac-10
Southern California	Pac-10
California	Pac-10
Washington St.	Pac-10
Oregon	Pac-10
Stanford	Pac-10
Oregon St.	Pac-10
Arizona St.	Pac-10
Bucknell	Patriot
American	Patriot
Holy Cross	Patriot
Lehigh	Patriot
Lafayette	Patriot
Navy	Patriot
Colgate	Patriot
Army West Point	Patriot
Florida	SEC
Kentucky	SEC
Vanderbilt	SEC
Georgia	SEC
Tennessee	SEC
South Carolina	SEC
Alabama	SEC
Mississippi St.	SEC
Ole Miss	SEC
Arkansas	SEC
Auburn	SEC
LSU	SEC
Western Caro.	SoCon
Chattanooga	SoCon
App State	SoCon
Elon	SoCon
UNC Greensboro	SoCon
Samford	SoCon
Col. of Charleston	SoCon
Wofford	SoCon
Furman	SoCon
Davidson	SoCon
The Citadel	SoCon
Ga. Southern	SoCon
McNeese	Southland
Northwestern St.	Southland
Southeastern La.	Southland
Nicholls	Southland
Lamar University	Southland
Central Ark.	Southland
Sam Houston	Southland
Texas St.	Southland
SFA	Southland
UTSA	Southland
UT Arlington	Southland
A&M-Corpus Christi	Southland
Oakland	Summit League
Oral Roberts	Summit League
IU Indy	Summit League
Purdue Fort Wayne	Summit League
South Dakota St.	Summit League
Kansas City	Summit League
North Dakota St.	Summit League
Southern Utah	Summit League
Western Ill.	Summit League
Centenary (LA)	Summit League
Fla. Atlantic	Sun Belt
Middle Tenn.	Sun Belt
Western Ky.	Sun Belt
South Alabama	Sun Belt
Troy	Sun Belt
FIU	Sun Belt
Arkansas St.	Sun Belt
Louisiana	Sun Belt
Denver	Sun Belt
North Texas	Sun Belt
Little Rock	Sun Belt
ULM	Sun Belt
Texas Southern	SWAC
Jackson St.	SWAC
Mississippi Val.	SWAC
Alabama St.	SWAC
Alabama A&M	SWAC
Grambling	SWAC
Prairie View	SWAC
Ark.-Pine Bluff	SWAC
Alcorn	SWAC
Southern U.	SWAC
Utah St.	WAC
Boise St.	WAC
Idaho	WAC
New Mexico St.	WAC
Hawaii	WAC
Nevada	WAC
Fresno St.	WAC
San Jose St.	WAC
Louisiana Tech	WAC
Saint Mary's (CA)	WCC
Gonzaga	WCC
San Francisco	WCC
Santa Clara	WCC
Portland	WCC
Pepperdine	WCC
LMU (CA)	WCC
San Diego	WCC
"""

for line in teams_data.strip().splitlines():
    if not line.strip() or line.startswith("#"):
        continue
    # Split on tab
    team, conf = line.split("\t")
    
    # Build the folder path exactly as written (keeps periods and parentheses)
    team_dir = os.path.join(BASE_DIR, conf, team)
    
    # Make directories
    os.makedirs(team_dir, exist_ok=True)
    
    # Create empty games.json if it doesn't exist
    games_path = os.path.join(team_dir, "games.json")
    if not os.path.exists(games_path):
        with open(games_path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)

print("✅ All conferences and teams created cleanly with periods and parentheses preserved.")