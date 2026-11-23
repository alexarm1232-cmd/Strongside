import os
import json

BASE_DIR = "data/seasons/0809 full"

teams_data = """
North Carolina	ACC
Wake Forest	ACC
Duke	ACC
Florida St.	ACC
Clemson	ACC
Boston College	ACC
Maryland	ACC
Virginia Tech	ACC
Miami (FL)	ACC
NC State	ACC
Virginia	ACC
Georgia Tech	ACC
Binghamton	America East
Vermont	America East
Boston U.	America East
New Hampshire	America East
Stony Brook	America East
UMBC	America East
UAlbany	America East
Maine	America East
Hartford	America East
Xavier	Atlantic 10
Dayton	Atlantic 10
Rhode Island	Atlantic 10
Temple	Atlantic 10
Duquesne	Atlantic 10
La Salle	Atlantic 10
Richmond	Atlantic 10
Saint Joseph's	Atlantic 10
Saint Louis	Atlantic 10
Massachusetts	Atlantic 10
St. Bonaventure	Atlantic 10
Charlotte	Atlantic 10
George Washington	Atlantic 10
Fordham	Atlantic 10
Jacksonville	ASUN
ETSU	ASUN
Belmont	ASUN
Lipscomb	ASUN
Mercer	ASUN
Campbell	ASUN
Stetson	ASUN
USC Upstate	ASUN
FGCU	ASUN
North Florida	ASUN
Kennesaw St.	ASUN
Kansas	Big 12
Oklahoma	Big 12
Missouri	Big 12
Kansas St.	Big 12
Texas	Big 12
Texas A&M	Big 12
Oklahoma St.	Big 12
Nebraska	Big 12
Baylor	Big 12
Iowa St.	Big 12
Texas Tech	Big 12
Colorado	Big 12
Louisville	Big East
Pittsburgh	Big East
UConn	Big East
Villanova	Big East
Marquette	Big East
Syracuse	Big East
West Virginia	Big East
Providence	Big East
Cincinnati	Big East
Notre Dame	Big East
Seton Hall	Big East
Georgetown	Big East
St. John's (NY)	Big East
South Fla.	Big East
Rutgers	Big East
DePaul	Big East
Weber St.	Big Sky
Portland St.	Big Sky
Montana	Big Sky
Idaho St.	Big Sky
Northern Colo.	Big Sky
Montana St.	Big Sky
Eastern Wash.	Big Sky
Northern Ariz.	Big Sky
Sacramento St.	Big Sky
Radford	Big South
VMI	Big South
Liberty	Big South
UNC Asheville	Big South
Gardner-Webb	Big South
Winthrop	Big South
Coastal Carolina	Big South
Charleston So.	Big South
High Point	Big South
Presbyterian	Big South
Michigan St.	Big Ten
Illinois	Big Ten
Purdue	Big Ten
Wisconsin	Big Ten
Ohio St.	Big Ten
Penn St.	Big Ten
Michigan	Big Ten
Minnesota	Big Ten
Northwestern	Big Ten
Iowa	Big Ten
Indiana	Big Ten
CSUN	Big West
Pacific	Big West
Long Beach St.	Big West
UC Riverside	Big West
UC Santa Barbara	Big West
UC Irvine	Big West
Cal St. Fullerton	Big West
UC Davis	Big West
Cal Poly	Big West
VCU	CAA
George Mason	CAA
Old Dominion	CAA
Northeastern	CAA
Hofstra	CAA
Drexel	CAA
James Madison	CAA
Georgia St.	CAA
Delaware	CAA
William & Mary	CAA
Towson	CAA
UNCW	CAA
Memphis	CUSA
Tulsa	CUSA
UAB	CUSA
UTEP	CUSA
Houston	CUSA
UCF	CUSA
Marshall	CUSA
Tulane	CUSA
East Carolina	CUSA
Rice	CUSA
Southern Miss.	CUSA
SMU	CUSA
Butler	Horizon
Green Bay	Horizon
Cleveland St.	Horizon
Wright St.	Horizon
Milwaukee	Horizon
Youngstown St.	Horizon
UIC	Horizon
Loyola Chicago	Horizon
Valparaiso	Horizon
Detroit Mercy	Horizon
Utah Valley	Independent
Chicago St.	Independent
Longwood	Independent
Savannah St.	Independent
UTRGV	Independent
Bryant	Independent
CSU Bakersfield	Independent
Houston Christian	Independent
N.C. Central	Independent
NJIT	Independent
Cornell	Ivy League
Princeton	Ivy League
Yale	Ivy League
Columbia	Ivy League
Dartmouth	Ivy League
Harvard	Ivy League
Penn	Ivy League
Brown	Ivy League
Siena	MAAC
Niagara	MAAC
Rider	MAAC
Manhattan	MAAC
Fairfield	MAAC
Saint Peter's	MAAC
Iona	MAAC
Loyola Maryland	MAAC
Canisius	MAAC
Marist	MAAC
Bowling Green	MAC
Buffalo	MAC
Miami (OH)	MAC
Akron	MAC
Kent St.	MAC
Ohio	MAC
Ball St.	MAC
Central Mich.	MAC
Western Mich.	MAC
Eastern Mich.	MAC
NIU	MAC
Toledo	MAC
Winston-Salem	MEAC
Morgan St.	MEAC
South Carolina St.	MEAC
Bethune-Cookman	MEAC
N.C. A&T	MEAC
Norfolk St.	MEAC
Coppin St.	MEAC
Hampton	MEAC
Florida A&M	MEAC
Howard	MEAC
Delaware St.	MEAC
UMES	MEAC
Creighton	MVC
UNI	MVC
Illinois St.	MVC
Bradley	MVC
Evansville	MVC
Wichita St.	MVC
Southern Ill.	MVC
Drake	MVC
Indiana St.	MVC
Missouri St.	MVC
BYU	Mountain West
Utah	Mountain West
New Mexico	Mountain West
San Diego St.	Mountain West
UNLV	Mountain West
Wyoming	Mountain West
TCU	Mountain West
Colorado St.	Mountain West
Air Force	Mountain West
Robert Morris	NEC
Mount St. Mary's	NEC
Sacred Heart	NEC
LIU	NEC
Quinnipiac	NEC
Central Conn. St.	NEC
Wagner	NEC
St. Francis Brooklyn	NEC
Monmouth	NEC
FDU	NEC
Saint Francis	NEC
UT Martin	OVC
Austin Peay	OVC
Murray St.	OVC
Morehead St.	OVC
Eastern Ky.	OVC
Tennessee St.	OVC
Eastern Ill.	OVC
Tennessee Tech	OVC
Jacksonville St.	OVC
Southeast Mo. St.	OVC
SIUE	OVC
Washington	Pac-10
UCLA	Pac-10
California	Pac-10
Arizona St.	Pac-10
Arizona	Pac-10
Southern California	Pac-10
Washington St.	Pac-10
Oregon St.	Pac-10
Stanford	Pac-10
Oregon	Pac-10
American	Patriot
Holy Cross	Patriot
Navy	Patriot
Army West Point	Patriot
Lehigh	Patriot
Colgate	Patriot
Bucknell	Patriot
Lafayette	Patriot
Tennessee	SEC
South Carolina	SEC
Florida	SEC
Kentucky	SEC
Vanderbilt	SEC
Georgia	SEC
LSU	SEC
Auburn	SEC
Mississippi St.	SEC
Alabama	SEC
Ole Miss	SEC
Arkansas	SEC
Western Caro.	SoCon
Chattanooga	SoCon
Samford	SoCon
App State	SoCon
Elon	SoCon
UNC Greensboro	SoCon
Davidson	SoCon
Col. of Charleston	SoCon
The Citadel	SoCon
Wofford	SoCon
Ga. Southern	SoCon
Furman	SoCon
SFA	Southland
Nicholls	Southland
Southeastern La.	Southland
McNeese	Southland
Northwestern St.	Southland
Central Ark.	Southland
Sam Houston	Southland
A&M-Corpus Christi	Southland
UT Arlington	Southland
UTSA	Southland
Texas St.	Southland
Lamar University	Southland
North Dakota St.	Summit League
Oral Roberts	Summit League
Oakland	Summit League
IU Indy	Summit League
Southern Utah	Summit League
Purdue Fort Wayne	Summit League
South Dakota St.	Summit League
Centenary (LA)	Summit League
Western Ill.	Summit League
Kansas City	Summit League
Western Ky.	Sun Belt
Troy	Sun Belt
Middle Tenn.	Sun Belt
South Alabama	Sun Belt
FIU	Sun Belt
Fla. Atlantic	Sun Belt
Little Rock	Sun Belt
North Texas	Sun Belt
Denver	Sun Belt
Louisiana	Sun Belt
ULM	Sun Belt
LSU New Orleans	Sun Belt
Arkansas St.	Sun Belt
Alabama St.	SWAC
Jackson St.	SWAC
Prairie View	SWAC
Ark.-Pine Bluff	SWAC
Southern U.	SWAC
Mississippi Val.	SWAC
Texas Southern	SWAC
Alabama A&M	SWAC
Grambling	SWAC
Alcorn	SWAC
Utah St.	WAC
Nevada	WAC
Idaho	WAC
Boise St.	WAC
New Mexico St.	WAC
Louisiana Tech	WAC
San Jose St.	WAC
Hawaii	WAC
Fresno St.	WAC
Gonzaga	WCC
Saint Mary's (CA)	WCC
Portland	WCC
Santa Clara	WCC
San Diego	WCC
Pepperdine	WCC
San Francisco	WCC
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