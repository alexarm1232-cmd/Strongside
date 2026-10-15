import os
import json

BASE_DIR = "data/seasons/1213"

teams_data = """
Miami (FL)	ACC
Duke	ACC
North Carolina	ACC
NC State	ACC
Virginia	ACC
Florida St.	ACC
Maryland	ACC
Boston College	ACC
Georgia Tech	ACC
Wake Forest	ACC
Clemson	ACC
Virginia Tech	ACC
Stony Brook	America East
Vermont	America East
Boston U.	America East
Hartford	America East
UAlbany	America East
Maine	America East
New Hampshire	America East
UMBC	America East
Binghamton	America East
Saint Louis	Atlantic 10
VCU	Atlantic 10
Butler	Atlantic 10
La Salle	Atlantic 10
Temple	Atlantic 10
Massachusetts	Atlantic 10
Xavier	Atlantic 10
Charlotte	Atlantic 10
Saint Joseph's	Atlantic 10
Richmond	Atlantic 10
Dayton	Atlantic 10
St. Bonaventure	Atlantic 10
George Washington	Atlantic 10
Rhode Island	Atlantic 10
Fordham	Atlantic 10
Duquesne	Atlantic 10
Mercer	ASUN
FGCU	ASUN
Stetson	ASUN
USC Upstate	ASUN
Jacksonville	ASUN
Northern Ky.	ASUN
North Florida	ASUN
ETSU	ASUN
Lipscomb	ASUN
Kennesaw St.	ASUN
Kansas	Big 12
Kansas St.	Big 12
Oklahoma St.	Big 12
Oklahoma	Big 12
Iowa St.	Big 12
Baylor	Big 12
Texas	Big 12
West Virginia	Big 12
Texas Tech	Big 12
TCU	Big 12
Louisville	Big East
Georgetown	Big East
Marquette	Big East
Pittsburgh	Big East
Syracuse	Big East
Notre Dame	Big East
UConn	Big East
Villanova	Big East
Cincinnati	Big East
Providence	Big East
St. John's (NY)	Big East
Rutgers	Big East
Seton Hall	Big East
South Fla.	Big East
DePaul	Big East
Montana	Big Sky
Weber St.	Big Sky
North Dakota	Big Sky
Montana St.	Big Sky
Northern Colo.	Big Sky
Sacramento St.	Big Sky
Southern Utah	Big Sky
Northern Ariz.	Big Sky
Eastern Wash.	Big Sky
Portland St.	Big Sky
Idaho St.	Big Sky
High Point	Big South
VMI	Big South
Radford	Big South
Campbell	Big South
Liberty	Big South
Longwood	Big South
Charleston So.	Big South
Gardner-Webb	Big South
UNC Asheville	Big South
Coastal Carolina	Big South
Winthrop	Big South
Presbyterian	Big South
Indiana	Big Ten
Ohio St.	Big Ten
Michigan St.	Big Ten
Michigan	Big Ten
Wisconsin	Big Ten
Iowa	Big Ten
Illinois	Big Ten
Minnesota	Big Ten
Purdue	Big Ten
Nebraska	Big Ten
Northwestern	Big Ten
Penn St.	Big Ten
Long Beach St.	Big West
Pacific	Big West
Cal Poly	Big West
UC Irvine	Big West
Hawaii	Big West
UC Davis	Big West
UC Santa Barbara	Big West
Cal St. Fullerton	Big West
CSUN	Big West
UC Riverside	Big West
Northeastern	CAA
Towson	CAA
Delaware	CAA
James Madison	CAA
George Mason	CAA
Georgia St.	CAA
Drexel	CAA
William & Mary	CAA
UNCW	CAA
Hofstra	CAA
Old Dominion	CAA
Memphis	CUSA
Southern Miss.	CUSA
UTEP	CUSA
East Carolina	CUSA
UCF	CUSA
Tulsa	CUSA
Houston	CUSA
UAB	CUSA
Tulane	CUSA
Marshall	CUSA
SMU	CUSA
Rice	CUSA
NJIT	Great West
UTRGV	Great West
Houston Christian	Great West
Utah Valley	Great West
Chicago St.	Great West
Valparaiso	Horizon
Detroit Mercy	Horizon
Wright St.	Horizon
Green Bay	Horizon
UIC	Horizon
Youngstown St.	Horizon
Loyola Chicago	Horizon
Cleveland St.	Horizon
Milwaukee	Horizon
CSU Bakersfield	Independent
LSU New Orleans	Independent
Harvard	Ivy League
Princeton	Ivy League
Yale	Ivy League
Brown	Ivy League
Penn	Ivy League
Cornell	Ivy League
Dartmouth	Ivy League
Columbia	Ivy League
Niagara	MAAC
Loyola Maryland	MAAC
Rider	MAAC
Canisius	MAAC
Iona	MAAC
Fairfield	MAAC
Manhattan	MAAC
Marist	MAAC
Siena	MAAC
Saint Peter's	MAAC
Akron	MAC
Ohio	MAC
Kent St.	MAC
Buffalo	MAC
Bowling Green	MAC
Miami (OH)	MAC
Western Mich.	MAC
Toledo	MAC
Ball St.	MAC
Eastern Mich.	MAC
Central Mich.	MAC
NIU	MAC
Norfolk St.	MEAC
N.C. Central	MEAC
Savannah St.	MEAC
Hampton	MEAC
Morgan St.	MEAC
N.C. A&T	MEAC
Delaware St.	MEAC
Bethune-Cookman	MEAC
Florida A&M	MEAC
Coppin St.	MEAC
Howard	MEAC
South Carolina St.	MEAC
UMES	MEAC
Creighton	MVC
Wichita St.	MVC
UNI	MVC
Evansville	MVC
Indiana St.	MVC
Illinois St.	MVC
Bradley	MVC
Drake	MVC
Missouri St.	MVC
Southern Ill.	MVC
New Mexico	Mountain West
Colorado St.	Mountain West
UNLV	Mountain West
San Diego St.	Mountain West
Boise St.	Mountain West
Air Force	Mountain West
Fresno St.	Mountain West
Wyoming	Mountain West
Nevada	Mountain West
Robert Morris	NEC
Bryant	NEC
Wagner	NEC
LIU	NEC
Mount St. Mary's	NEC
Quinnipiac	NEC
Central Conn. St.	NEC
St. Francis Brooklyn	NEC
Sacred Heart	NEC
Monmouth	NEC
Saint Francis	NEC
FDU	NEC
Belmont	OVC
Eastern Ky.	OVC
Tennessee St.	OVC
Jacksonville St.	OVC
Morehead St.	OVC
Tennessee Tech	OVC
Murray St.	OVC
Southeast Mo. St.	OVC
Eastern Ill.	OVC
SIUE	OVC
UT Martin	OVC
Austin Peay	OVC
UCLA	Pac-12
Arizona	Pac-12
Oregon	Pac-12
California	Pac-12
Colorado	Pac-12
Arizona St.	Pac-12
Stanford	Pac-12
Washington	Pac-12
Southern California	Pac-12
Utah	Pac-12
Oregon St.	Pac-12
Washington St.	Pac-12
Bucknell	Patriot
Lehigh	Patriot
Lafayette	Patriot
Army West Point	Patriot
Colgate	Patriot
American	Patriot
Holy Cross	Patriot
Navy	Patriot
Florida	SEC
Ole Miss	SEC
Alabama	SEC
Kentucky	SEC
Missouri	SEC
Tennessee	SEC
Arkansas	SEC
LSU	SEC
Georgia	SEC
Vanderbilt	SEC
Texas A&M	SEC
South Carolina	SEC
Mississippi St.	SEC
Auburn	SEC
Elon	SoCon
App State	SoCon
Western Caro.	SoCon
Samford	SoCon
Chattanooga	SoCon
UNC Greensboro	SoCon
Davidson	SoCon
Col. of Charleston	SoCon
Ga. Southern	SoCon
Wofford	SoCon
The Citadel	SoCon
Furman	SoCon
SFA	Southland
Northwestern St.	Southland
Oral Roberts	Southland
Southeastern La.	Southland
Sam Houston	Southland
Nicholls	Southland
McNeese	Southland
Central Ark.	Southland
A&M-Corpus Christi	Southland
Lamar University	Southland
South Dakota St.	Summit League
Western Ill.	Summit League
North Dakota St.	Summit League
Oakland	Summit League
Purdue Fort Wayne	Summit League
Omaha	Summit League
South Dakota	Summit League
Kansas City	Summit League
IU Indy	Summit League
Middle Tenn.	Sun Belt
South Alabama	Sun Belt
FIU	Sun Belt
Western Ky.	Sun Belt
Fla. Atlantic	Sun Belt
Troy	Sun Belt
Arkansas St.	Sun Belt
Little Rock	Sun Belt
Louisiana	Sun Belt
North Texas	Sun Belt
ULM	Sun Belt
Texas Southern	SWAC
Southern U.	SWAC
Ark.-Pine Bluff	SWAC
Jackson St.	SWAC
Prairie View	SWAC
Alabama St.	SWAC
Alcorn	SWAC
Alabama A&M	SWAC
Mississippi Val.	SWAC
Grambling	SWAC
Louisiana Tech	WAC
Denver	WAC
New Mexico St.	WAC
Utah St.	WAC
UT Arlington	WAC
Idaho	WAC
Texas St.	WAC
UTSA	WAC
San Jose St.	WAC
Seattle U	WAC
Gonzaga	WCC
Saint Mary's (CA)	WCC
BYU	WCC
Santa Clara	WCC
San Francisco	WCC
San Diego	WCC
Pepperdine	WCC
Portland	WCC
LMU (CA)	WCC
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