import os
import json

BASE_DIR = "data/seasons/1112 full"

teams_data = """
North Carolina	ACC
Duke	ACC
Florida St.	ACC
Virginia	ACC
NC State	ACC
Miami (FL)	ACC
Clemson	ACC
Maryland	ACC
Virginia Tech	ACC
Wake Forest	ACC
Georgia Tech	ACC
Boston College	ACC
Stony Brook	America East
Vermont	America East
Boston U.	America East
UAlbany	America East
New Hampshire	America East
Hartford	America East
Maine	America East
UMBC	America East
Binghamton	America East
Temple	Atlantic 10
Saint Louis	Atlantic 10
Xavier	Atlantic 10
St. Bonaventure	Atlantic 10
Massachusetts	Atlantic 10
La Salle	Atlantic 10
Dayton	Atlantic 10
Saint Joseph's	Atlantic 10
Duquesne	Atlantic 10
Richmond	Atlantic 10
Charlotte	Atlantic 10
George Washington	Atlantic 10
Rhode Island	Atlantic 10
Fordham	Atlantic 10
Belmont	ASUN
Mercer	ASUN
USC Upstate	ASUN
ETSU	ASUN
North Florida	ASUN
FGCU	ASUN
Lipscomb	ASUN
Stetson	ASUN
Jacksonville	ASUN
Kennesaw St.	ASUN
Kansas	Big 12
Missouri	Big 12
Baylor	Big 12
Iowa St.	Big 12
Kansas St.	Big 12
Texas	Big 12
Oklahoma St.	Big 12
Oklahoma	Big 12
Texas A&M	Big 12
Texas Tech	Big 12
Syracuse	Big East
Marquette	Big East
Notre Dame	Big East
Georgetown	Big East
Cincinnati	Big East
South Fla.	Big East
Louisville	Big East
West Virginia	Big East
Seton Hall	Big East
UConn	Big East
Rutgers	Big East
St. John's (NY)	Big East
Pittsburgh	Big East
Villanova	Big East
Providence	Big East
DePaul	Big East
Montana	Big Sky
Weber St.	Big Sky
Portland St.	Big Sky
Eastern Wash.	Big Sky
Montana St.	Big Sky
Idaho St.	Big Sky
Sacramento St.	Big Sky
Northern Colo.	Big Sky
Northern Ariz.	Big Sky
UNC Asheville	Big South
Coastal Carolina	Big South
Charleston So.	Big South
Campbell	Big South
Liberty	Big South
VMI	Big South
Presbyterian	Big South
High Point	Big South
Winthrop	Big South
Gardner-Webb	Big South
Radford	Big South
Ohio St.	Big Ten
Michigan St.	Big Ten
Michigan	Big Ten
Wisconsin	Big Ten
Indiana	Big Ten
Purdue	Big Ten
Northwestern	Big Ten
Iowa	Big Ten
Minnesota	Big Ten
Illinois	Big Ten
Nebraska	Big Ten
Penn St.	Big Ten
Long Beach St.	Big West
Cal St. Fullerton	Big West
UC Santa Barbara	Big West
Cal Poly	Big West
UC Riverside	Big West
UC Irvine	Big West
Pacific	Big West
CSUN	Big West
UC Davis	Big West
Drexel	CAA
VCU	CAA
George Mason	CAA
Old Dominion	CAA
Delaware	CAA
Georgia St.	CAA
Northeastern	CAA
James Madison	CAA
UNCW	CAA
William & Mary	CAA
Hofstra	CAA
Towson	CAA
Memphis	CUSA
Southern Miss.	CUSA
UCF	CUSA
Tulsa	CUSA
Marshall	CUSA
UAB	CUSA
Rice	CUSA
Houston	CUSA
UTEP	CUSA
East Carolina	CUSA
SMU	CUSA
Tulane	CUSA
Utah Valley	Great West
North Dakota	Great West
NJIT	Great West
UTRGV	Great West
Houston Christian	Great West
Chicago St.	Great West
Valparaiso	Horizon
Cleveland St.	Horizon
Detroit Mercy	Horizon
Butler	Horizon
Milwaukee	Horizon
Youngstown St.	Horizon
Green Bay	Horizon
Wright St.	Horizon
UIC	Horizon
Loyola Chicago	Horizon
CSU Bakersfield	Independent
Seattle U	Independent
Longwood	Independent
Harvard	Ivy League
Penn	Ivy League
Princeton	Ivy League
Yale	Ivy League
Cornell	Ivy League
Columbia	Ivy League
Brown	Ivy League
Dartmouth	Ivy League
Iona	MAAC
Loyola Maryland	MAAC
Manhattan	MAAC
Fairfield	MAAC
Rider	MAAC
Siena	MAAC
Niagara	MAAC
Marist	MAAC
Saint Peter's	MAAC
Canisius	MAAC
Akron	MAC
Buffalo	MAC
Ohio	MAC
Kent St.	MAC
Bowling Green	MAC
Miami (OH)	MAC
Eastern Mich.	MAC
Toledo	MAC
Ball St.	MAC
Western Mich.	MAC
Central Mich.	MAC
NIU	MAC
Savannah St.	MEAC
Norfolk St.	MEAC
Delaware St.	MEAC
Bethune-Cookman	MEAC
N.C. Central	MEAC
Coppin St.	MEAC
N.C. A&T	MEAC
Hampton	MEAC
Howard	MEAC
Morgan St.	MEAC
Florida A&M	MEAC
UMES	MEAC
South Carolina St.	MEAC
Wichita St.	MVC
Creighton	MVC
Illinois St.	MVC
UNI	MVC
Drake	MVC
Evansville	MVC
Missouri St.	MVC
Indiana St.	MVC
Southern Ill.	MVC
Bradley	MVC
New Mexico	Mountain West
San Diego St.	Mountain West
UNLV	Mountain West
Colorado St.	Mountain West
TCU	Mountain West
Wyoming	Mountain West
Air Force	Mountain West
Boise St.	Mountain West
LIU	NEC
Wagner	NEC
Robert Morris	NEC
St. Francis Brooklyn	NEC
Quinnipiac	NEC
Central Conn. St.	NEC
Monmouth	NEC
Sacred Heart	NEC
Mount St. Mary's	NEC
Saint Francis	NEC
FDU	NEC
Bryant	NEC
Murray St.	OVC
Tennessee St.	OVC
Morehead St.	OVC
Tennessee Tech	OVC
Southeast Mo. St.	OVC
Jacksonville St.	OVC
Austin Peay	OVC
Eastern Ky.	OVC
SIUE	OVC
Eastern Ill.	OVC
UT Martin	OVC
Washington	Pac-12
California	Pac-12
Oregon	Pac-12
Arizona	Pac-12
Colorado	Pac-12
UCLA	Pac-12
Stanford	Pac-12
Oregon St.	Pac-12
Washington St.	Pac-12
Arizona St.	Pac-12
Utah	Pac-12
Southern California	Pac-12
Bucknell	Patriot
Lehigh	Patriot
American	Patriot
Holy Cross	Patriot
Lafayette	Patriot
Army West Point	Patriot
Colgate	Patriot
Navy	Patriot
Kentucky	SEC
Florida	SEC
Vanderbilt	SEC
Tennessee	SEC
Alabama	SEC
Mississippi St.	SEC
Ole Miss	SEC
LSU	SEC
Arkansas	SEC
Auburn	SEC
Georgia	SEC
South Carolina	SEC
UNC Greensboro	SoCon
Elon	SoCon
Western Caro.	SoCon
Samford	SoCon
App State	SoCon
Chattanooga	SoCon
Davidson	SoCon
Wofford	SoCon
Ga. Southern	SoCon
Col. of Charleston	SoCon
Furman	SoCon
The Citadel	SoCon
Lamar University	Southland
McNeese	Southland
Northwestern St.	Southland
Nicholls	Southland
Southeastern La.	Southland
Central Ark.	Southland
UT Arlington	Southland
SFA	Southland
UTSA	Southland
Sam Houston	Southland
Texas St.	Southland
A&M-Corpus Christi	Southland
Oral Roberts	Summit League
South Dakota St.	Summit League
Oakland	Summit League
North Dakota St.	Summit League
Western Ill.	Summit League
Southern Utah	Summit League
IU Indy	Summit League
Purdue Fort Wayne	Summit League
South Dakota	Summit League
Kansas City	Summit League
Middle Tenn.	Sun Belt
South Alabama	Sun Belt
Western Ky.	Sun Belt
Fla. Atlantic	Sun Belt
Troy	Sun Belt
FIU	Sun Belt
Little Rock	Sun Belt
Denver	Sun Belt
Louisiana	Sun Belt
North Texas	Sun Belt
Arkansas St.	Sun Belt
ULM	Sun Belt
Mississippi Val.	SWAC
Southern U.	SWAC
Texas Southern	SWAC
Prairie View	SWAC
Alabama St.	SWAC
Ark.-Pine Bluff	SWAC
Alcorn	SWAC
Alabama A&M	SWAC
Jackson St.	SWAC
Grambling	SWAC
Nevada	WAC
New Mexico St.	WAC
Idaho	WAC
Utah St.	WAC
Louisiana Tech	WAC
Hawaii	WAC
Fresno St.	WAC
San Jose St.	WAC
Saint Mary's (CA)	WCC
Gonzaga	WCC
BYU	WCC
LMU (CA)	WCC
San Francisco	WCC
San Diego	WCC
Pepperdine	WCC
Portland	WCC
Santa Clara	WCC
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