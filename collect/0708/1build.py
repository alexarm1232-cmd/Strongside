import os
import json

BASE_DIR = "data/seasons/0708"

teams_data = """
North Carolina	ACC
Duke	ACC
Clemson	ACC
Virginia Tech	ACC
Miami (FL)	ACC
Maryland	ACC
Georgia Tech	ACC
Wake Forest	ACC
Florida St.	ACC
Virginia	ACC
Boston College	ACC
NC State	ACC
UMBC	America East
Hartford	America East
UAlbany	America East
Vermont	America East
Binghamton	America East
Boston U.	America East
New Hampshire	America East
Stony Brook	America East
Maine	America East
Xavier	Atlantic 10
Temple	Atlantic 10
Massachusetts	Atlantic 10
Saint Joseph's	Atlantic 10
Charlotte	Atlantic 10
Richmond	Atlantic 10
Dayton	Atlantic 10
La Salle	Atlantic 10
Rhode Island	Atlantic 10
Duquesne	Atlantic 10
Saint Louis	Atlantic 10
Fordham	Atlantic 10
George Washington	Atlantic 10
St. Bonaventure	Atlantic 10
Belmont	ASUN
Jacksonville	ASUN
ETSU	ASUN
Stetson	ASUN
Gardner-Webb	ASUN
Lipscomb	ASUN
Kennesaw St.	ASUN
Mercer	ASUN
FGCU	ASUN
Campbell	ASUN
USC Upstate	ASUN
North Florida	ASUN
Texas	Big 12
Kansas	Big 12
Kansas St.	Big 12
Oklahoma	Big 12
Baylor	Big 12
Texas A&M	Big 12
Nebraska	Big 12
Texas Tech	Big 12
Oklahoma St.	Big 12
Missouri	Big 12
Iowa St.	Big 12
Colorado	Big 12
Georgetown	Big East
Louisville	Big East
Notre Dame	Big East
UConn	Big East
West Virginia	Big East
Marquette	Big East
Pittsburgh	Big East
Villanova	Big East
Syracuse	Big East
Cincinnati	Big East
Seton Hall	Big East
Providence	Big East
DePaul	Big East
St. John's (NY)	Big East
South Fla.	Big East
Rutgers	Big East
Portland St.	Big Sky
Northern Ariz.	Big Sky
Weber St.	Big Sky
Montana	Big Sky
Idaho St.	Big Sky
Montana St.	Big Sky
Northern Colo.	Big Sky
Eastern Wash.	Big Sky
Sacramento St.	Big Sky
UNC Asheville	Big South
Winthrop	Big South
High Point	Big South
Liberty	Big South
VMI	Big South
Coastal Carolina	Big South
Radford	Big South
Charleston So.	Big South
Wisconsin	Big Ten
Purdue	Big Ten
Indiana	Big Ten
Michigan St.	Big Ten
Ohio St.	Big Ten
Minnesota	Big Ten
Penn St.	Big Ten
Iowa	Big Ten
Michigan	Big Ten
Illinois	Big Ten
Northwestern	Big Ten
Cal St. Fullerton	Big West
UC Santa Barbara	Big West
CSUN	Big West
Pacific	Big West
UC Irvine	Big West
Cal Poly	Big West
UC Riverside	Big West
Long Beach St.	Big West
UC Davis	Big West
VCU	CAA
UNCW	CAA
George Mason	CAA
Old Dominion	CAA
William & Mary	CAA
Northeastern	CAA
Delaware	CAA
Hofstra	CAA
Towson	CAA
Drexel	CAA
James Madison	CAA
Georgia St.	CAA
Memphis	CUSA
UAB	CUSA
Houston	CUSA
Southern Miss.	CUSA
UCF	CUSA
UTEP	CUSA
Tulsa	CUSA
Marshall	CUSA
Tulane	CUSA
East Carolina	CUSA
SMU	CUSA
Rice	CUSA
Butler	Horizon
Cleveland St.	Horizon
Wright St.	Horizon
UIC	Horizon
Milwaukee	Horizon
Valparaiso	Horizon
Green Bay	Horizon
Loyola Chicago	Horizon
Youngstown St.	Horizon
Detroit Mercy	Horizon
UTRGV	Independent
Utah Valley	Independent
Savannah St.	Independent
Chicago St.	Independent
Longwood	Independent
CSU Bakersfield	Independent
Presbyterian	Independent
N.C. Central	Independent
NJIT	Independent
Cornell	Ivy League
Brown	Ivy League
Penn	Ivy League
Columbia	Ivy League
Yale	Ivy League
Dartmouth	Ivy League
Harvard	Ivy League
Princeton	Ivy League
Siena	MAAC
Rider	MAAC
Niagara	MAAC
Loyola Maryland	MAAC
Fairfield	MAAC
Marist	MAAC
Iona	MAAC
Manhattan	MAAC
Saint Peter's	MAAC
Canisius	MAAC
Kent St.	MAC
Akron	MAC
Ohio	MAC
Miami (OH)	MAC
Bowling Green	MAC
Buffalo	MAC
Western Mich.	MAC
Central Mich.	MAC
Eastern Mich.	MAC
Toledo	MAC
Ball St.	MAC
NIU	MAC
Winston-Salem	MEAC
Morgan St.	MEAC
Hampton	MEAC
Norfolk St.	MEAC
Delaware St.	MEAC
N.C. A&T	MEAC
Florida A&M	MEAC
Coppin St.	MEAC
South Carolina St.	MEAC
Bethune-Cookman	MEAC
Howard	MEAC
UMES	MEAC
Drake	MVC
Illinois St.	MVC
Southern Ill.	MVC
Creighton	MVC
UNI	MVC
Bradley	MVC
Missouri St.	MVC
Indiana St.	MVC
Wichita St.	MVC
Evansville	MVC
BYU	Mountain West
UNLV	Mountain West
New Mexico	Mountain West
San Diego St.	Mountain West
Air Force	Mountain West
Utah	Mountain West
TCU	Mountain West
Wyoming	Mountain West
Colorado St.	Mountain West
Robert Morris	NEC
Wagner	NEC
Sacred Heart	NEC
Mount St. Mary's	NEC
Quinnipiac	NEC
Central Conn. St.	NEC
LIU	NEC
Monmouth	NEC
FDU	NEC
St. Francis Brooklyn	NEC
Saint Francis	NEC
Austin Peay	OVC
Murray St.	OVC
Morehead St.	OVC
UT Martin	OVC
Samford	OVC
Tennessee St.	OVC
Tennessee Tech	OVC
Eastern Ky.	OVC
Eastern Ill.	OVC
Jacksonville St.	OVC
Southeast Mo. St.	OVC
UCLA	Pac-10
Stanford	Pac-10
Washington St.	Pac-10
Southern California	Pac-10
Arizona St.	Pac-10
Oregon	Pac-10
Arizona	Pac-10
Washington	Pac-10
California	Pac-10
Oregon St.	Pac-10
American	Patriot
Navy	Patriot
Colgate	Patriot
Lehigh	Patriot
Army West Point	Patriot
Lafayette	Patriot
Bucknell	Patriot
Holy Cross	Patriot
Tennessee	SEC
Kentucky	SEC
Vanderbilt	SEC
Florida	SEC
South Carolina	SEC
Georgia	SEC
Mississippi St.	SEC
Arkansas	SEC
Ole Miss	SEC
LSU	SEC
Alabama	SEC
Auburn	SEC
App State	SoCon
Chattanooga	SoCon
UNC Greensboro	SoCon
Elon	SoCon
Western Caro.	SoCon
Davidson	SoCon
Ga. Southern	SoCon
Col. of Charleston	SoCon
Wofford	SoCon
Furman	SoCon
The Citadel	SoCon
Lamar University	Southland
Southeastern La.	Southland
Northwestern St.	Southland
McNeese	Southland
Nicholls	Southland
Central Ark.	Southland
SFA	Southland
Sam Houston	Southland
UT Arlington	Southland
UTSA	Southland
Texas St.	Southland
A&M-Corpus Christi	Southland
Oral Roberts	Summit League
IU Indy	Summit League
Oakland	Summit League
North Dakota St.	Summit League
Southern Utah	Summit League
Purdue Fort Wayne	Summit League
Western Ill.	Summit League
Kansas City	Summit League
Centenary (LA)	Summit League
South Dakota St.	Summit League
South Alabama	Sun Belt
Western Ky.	Sun Belt
Middle Tenn.	Sun Belt
Fla. Atlantic	Sun Belt
FIU	Sun Belt
Troy	Sun Belt
Little Rock	Sun Belt
Louisiana	Sun Belt
North Texas	Sun Belt
LSU New Orleans	Sun Belt
Denver	Sun Belt
Arkansas St.	Sun Belt
ULM	Sun Belt
Alabama St.	SWAC
Mississippi Val.	SWAC
Alabama A&M	SWAC
Jackson St.	SWAC
Southern U.	SWAC
Ark.-Pine Bluff	SWAC
Grambling	SWAC
Prairie View	SWAC
Alcorn	SWAC
Texas Southern	SWAC
Utah St.	WAC
Nevada	WAC
New Mexico St.	WAC
Boise St.	WAC
Hawaii	WAC
Idaho	WAC
Fresno St.	WAC
San Jose St.	WAC
Louisiana Tech	WAC
Gonzaga	WCC
Saint Mary's (CA)	WCC
San Diego	WCC
Santa Clara	WCC
San Francisco	WCC
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