import os
import json

BASE_DIR = "data/seasons/0910 full"

teams_data = """
Duke	ACC
Maryland	ACC
Florida St.	ACC
Virginia Tech	ACC
Wake Forest	ACC
Clemson	ACC
Georgia Tech	ACC
Boston College	ACC
Virginia	ACC
North Carolina	ACC
NC State	ACC
Miami (FL)	ACC
Stony Brook	America East
Vermont	America East
Maine	America East
Boston U.	America East
Binghamton	America East
Hartford	America East
New Hampshire	America East
UMBC	America East
UAlbany	America East
Temple	Atlantic 10
Xavier	Atlantic 10
Richmond	Atlantic 10
Saint Louis	Atlantic 10
Rhode Island	Atlantic 10
Charlotte	Atlantic 10
Dayton	Atlantic 10
St. Bonaventure	Atlantic 10
Duquesne	Atlantic 10
George Washington	Atlantic 10
Massachusetts	Atlantic 10
Saint Joseph's	Atlantic 10
La Salle	Atlantic 10
Fordham	Atlantic 10
Lipscomb	ASUN
Jacksonville	ASUN
Belmont	ASUN
Campbell	ASUN
ETSU	ASUN
Mercer	ASUN
North Florida	ASUN
Kennesaw St.	ASUN
USC Upstate	ASUN
FGCU	ASUN
Stetson	ASUN
Kansas	Big 12
Kansas St.	Big 12
Baylor	Big 12
Texas A&M	Big 12
Missouri	Big 12
Texas	Big 12
Oklahoma St.	Big 12
Colorado	Big 12
Texas Tech	Big 12
Oklahoma	Big 12
Iowa St.	Big 12
Nebraska	Big 12
Syracuse	Big East
Pittsburgh	Big East
West Virginia	Big East
Villanova	Big East
Marquette	Big East
Louisville	Big East
Notre Dame	Big East
Georgetown	Big East
South Fla.	Big East
Seton Hall	Big East
Cincinnati	Big East
UConn	Big East
St. John's (NY)	Big East
Rutgers	Big East
Providence	Big East
DePaul	Big East
Weber St.	Big Sky
Northern Colo.	Big Sky
Montana St.	Big Sky
Montana	Big Sky
Northern Ariz.	Big Sky
Portland St.	Big Sky
Eastern Wash.	Big Sky
Idaho St.	Big Sky
Sacramento St.	Big Sky
Coastal Carolina	Big South
Radford	Big South
Winthrop	Big South
UNC Asheville	Big South
High Point	Big South
Liberty	Big South
Charleston So.	Big South
VMI	Big South
Gardner-Webb	Big South
Presbyterian	Big South
Ohio St.	Big Ten
Purdue	Big Ten
Michigan St.	Big Ten
Wisconsin	Big Ten
Illinois	Big Ten
Minnesota	Big Ten
Northwestern	Big Ten
Michigan	Big Ten
Iowa	Big Ten
Indiana	Big Ten
Penn St.	Big Ten
UC Santa Barbara	Big West
Pacific	Big West
Long Beach St.	Big West
UC Davis	Big West
Cal St. Fullerton	Big West
Cal Poly	Big West
UC Irvine	Big West
CSUN	Big West
UC Riverside	Big West
Old Dominion	CAA
Northeastern	CAA
William & Mary	CAA
George Mason	CAA
VCU	CAA
Drexel	CAA
Hofstra	CAA
Towson	CAA
UNCW	CAA
Georgia St.	CAA
James Madison	CAA
Delaware	CAA
UTEP	CUSA
Memphis	CUSA
UAB	CUSA
Marshall	CUSA
Tulsa	CUSA
Southern Miss.	CUSA
Houston	CUSA
SMU	CUSA
UCF	CUSA
East Carolina	CUSA
Tulane	CUSA
Rice	CUSA
South Dakota	Great West
Houston Christian	Great West
Utah Valley	Great West
North Dakota	Great West
NJIT	Great West
Chicago St.	Great West
UTRGV	Great West
Butler	Horizon
Wright St.	Horizon
Green Bay	Horizon
Milwaukee	Horizon
Cleveland St.	Horizon
Valparaiso	Horizon
Detroit Mercy	Horizon
Loyola Chicago	Horizon
UIC	Horizon
Youngstown St.	Horizon
Seattle U	Independent
Savannah St.	Independent
Longwood	Independent
CSU Bakersfield	Independent
N.C. Central	Independent
Cornell	Ivy League
Princeton	Ivy League
Harvard	Ivy League
Yale	Ivy League
Columbia	Ivy League
Brown	Ivy League
Penn	Ivy League
Dartmouth	Ivy League
Siena	MAAC
Fairfield	MAAC
Iona	MAAC
Saint Peter's	MAAC
Rider	MAAC
Niagara	MAAC
Canisius	MAAC
Loyola Maryland	MAAC
Manhattan	MAAC
Marist	MAAC
Kent St.	MAC
Akron	MAC
Buffalo	MAC
Miami (OH)	MAC
Ohio	MAC
Bowling Green	MAC
Central Mich.	MAC
Eastern Mich.	MAC
Western Mich.	MAC
Ball St.	MAC
NIU	MAC
Toledo	MAC
Winston-Salem	MEAC
Morgan St.	MEAC
Delaware St.	MEAC
South Carolina St.	MEAC
Norfolk St.	MEAC
Hampton	MEAC
UMES	MEAC
Bethune-Cookman	MEAC
Howard	MEAC
N.C. A&T	MEAC
Florida A&M	MEAC
Coppin St.	MEAC
UNI	MVC
Wichita St.	MVC
Illinois St.	MVC
Creighton	MVC
Bradley	MVC
Indiana St.	MVC
Missouri St.	MVC
Drake	MVC
Southern Ill.	MVC
Evansville	MVC
New Mexico	Mountain West
BYU	Mountain West
UNLV	Mountain West
San Diego St.	Mountain West
Colorado St.	Mountain West
Utah	Mountain West
TCU	Mountain West
Wyoming	Mountain West
Air Force	Mountain West
Quinnipiac	NEC
Robert Morris	NEC
Mount St. Mary's	NEC
LIU	NEC
FDU	NEC
Saint Francis	NEC
Central Conn. St.	NEC
Monmouth	NEC
St. Francis Brooklyn	NEC
Sacred Heart	NEC
Wagner	NEC
Bryant	NEC
SIUE	OVC
Murray St.	OVC
Morehead St.	OVC
Austin Peay	OVC
Eastern Ill.	OVC
Eastern Ky.	OVC
Tennessee Tech	OVC
Jacksonville St.	OVC
Tennessee St.	OVC
Southeast Mo. St.	OVC
UT Martin	OVC
California	Pac-10
Arizona St.	Pac-10
Washington	Pac-10
Arizona	Pac-10
UCLA	Pac-10
Oregon St.	Pac-10
Southern California	Pac-10
Stanford	Pac-10
Oregon	Pac-10
Washington St.	Pac-10
Lehigh	Patriot
Bucknell	Patriot
Lafayette	Patriot
American	Patriot
Navy	Patriot
Colgate	Patriot
Holy Cross	Patriot
Army West Point	Patriot
Kentucky	SEC
Vanderbilt	SEC
Tennessee	SEC
Florida	SEC
South Carolina	SEC
Georgia	SEC
Mississippi St.	SEC
Ole Miss	SEC
Arkansas	SEC
Alabama	SEC
Auburn	SEC
LSU	SEC
App State	SoCon
Western Caro.	SoCon
Chattanooga	SoCon
UNC Greensboro	SoCon
Samford	SoCon
Elon	SoCon
Wofford	SoCon
Col. of Charleston	SoCon
Davidson	SoCon
The Citadel	SoCon
Furman	SoCon
Ga. Southern	SoCon
SFA	Southland
Southeastern La.	Southland
Nicholls	Southland
Northwestern St.	Southland
McNeese	Southland
Central Ark.	Southland
Sam Houston	Southland
A&M-Corpus Christi	Southland
Texas St.	Southland
UTSA	Southland
UT Arlington	Southland
Lamar University	Southland
Oakland	Summit League
IU Indy	Summit League
Oral Roberts	Summit League
South Dakota St.	Summit League
Purdue Fort Wayne	Summit League
North Dakota St.	Summit League
Western Ill.	Summit League
Kansas City	Summit League
Centenary (LA)	Summit League
Southern Utah	Summit League
Troy	Sun Belt
Middle Tenn.	Sun Belt
Western Ky.	Sun Belt
Fla. Atlantic	Sun Belt
South Alabama	Sun Belt
FIU	Sun Belt
North Texas	Sun Belt
Arkansas St.	Sun Belt
Denver	Sun Belt
Louisiana	Sun Belt
ULM	Sun Belt
Little Rock	Sun Belt
LSU New Orleans	Sun Belt
Jackson St.	SWAC
Ark.-Pine Bluff	SWAC
Alabama St.	SWAC
Prairie View	SWAC
Texas Southern	SWAC
Alabama A&M	SWAC
Mississippi Val.	SWAC
Grambling	SWAC
Southern U.	SWAC
Alcorn	SWAC
Utah St.	WAC
Nevada	WAC
New Mexico St.	WAC
Louisiana Tech	WAC
Fresno St.	WAC
San Jose St.	WAC
Idaho	WAC
Boise St.	WAC
Hawaii	WAC
Gonzaga	WCC
Saint Mary's (CA)	WCC
Portland	WCC
San Francisco	WCC
LMU (CA)	WCC
San Diego	WCC
Santa Clara	WCC
Pepperdine	WCC
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