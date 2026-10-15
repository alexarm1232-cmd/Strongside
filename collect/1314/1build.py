import os
import json

BASE_DIR = "data/seasons/1314"

teams_data = """
Louisville	American
Cincinnati	American
UConn	American
SMU	American
Memphis	American
Houston	American
Rutgers	American
UCF	American
Temple	American
South Fla.	American
Virginia	ACC
Syracuse	ACC
Duke	ACC
North Carolina	ACC
Pittsburgh	ACC
Clemson	ACC
Florida St.	ACC
NC State	ACC
Maryland	ACC
Miami (FL)	ACC
Wake Forest	ACC
Georgia Tech	ACC
Notre Dame	ACC
Boston College	ACC
Virginia Tech	ACC
Vermont	America East
Stony Brook	America East
Hartford	America East
UAlbany	America East
UMass Lowell	America East
UMBC	America East
Binghamton	America East
Maine	America East
New Hampshire	America East
Saint Louis	Atlantic 10
VCU	Atlantic 10
George Washington	Atlantic 10
Saint Joseph's	Atlantic 10
Massachusetts	Atlantic 10
Dayton	Atlantic 10
Richmond	Atlantic 10
La Salle	Atlantic 10
St. Bonaventure	Atlantic 10
Duquesne	Atlantic 10
Rhode Island	Atlantic 10
George Mason	Atlantic 10
Fordham	Atlantic 10
Mercer	ASUN
FGCU	ASUN
USC Upstate	ASUN
ETSU	ASUN
Lipscomb	ASUN
North Florida	ASUN
Jacksonville	ASUN
Northern Ky.	ASUN
Stetson	ASUN
Kennesaw St.	ASUN
Kansas	Big 12
Oklahoma	Big 12
Iowa St.	Big 12
Texas	Big 12
Kansas St.	Big 12
Baylor	Big 12
West Virginia	Big 12
Oklahoma St.	Big 12
Texas Tech	Big 12
TCU	Big 12
Villanova	Big East
Creighton	Big East
Providence	Big East
Xavier	Big East
St. John's (NY)	Big East
Marquette	Big East
Georgetown	Big East
Seton Hall	Big East
Butler	Big East
DePaul	Big East
Weber St.	Big Sky
Montana	Big Sky
North Dakota	Big Sky
Northern Ariz.	Big Sky
Northern Colo.	Big Sky
Portland St.	Big Sky
Eastern Wash.	Big Sky
Sacramento St.	Big Sky
Montana St.	Big Sky
Idaho St.	Big Sky
Southern Utah	Big Sky
High Point	Big South
VMI	Big South
Radford	Big South
Campbell	Big South
Liberty	Big South
Longwood	Big South
Coastal Carolina	Big South
Winthrop	Big South
Gardner-Webb	Big South
UNC Asheville	Big South
Charleston So.	Big South
Presbyterian	Big South
Michigan	Big Ten
Wisconsin	Big Ten
Michigan St.	Big Ten
Nebraska	Big Ten
Ohio St.	Big Ten
Iowa	Big Ten
Minnesota	Big Ten
Illinois	Big Ten
Indiana	Big Ten
Penn St.	Big Ten
Northwestern	Big Ten
Purdue	Big Ten
UC Irvine	Big West
UC Santa Barbara	Big West
Long Beach St.	Big West
Hawaii	Big West
CSUN	Big West
Cal Poly	Big West
Cal St. Fullerton	Big West
UC Riverside	Big West
UC Davis	Big West
Delaware	CAA
Towson	CAA
William & Mary	CAA
Drexel	CAA
Northeastern	CAA
Col. of Charleston	CAA
James Madison	CAA
Hofstra	CAA
UNCW	CAA
Southern Miss.	CUSA
Louisiana Tech	CUSA
Middle Tenn.	CUSA
Tulsa	CUSA
UTEP	CUSA
Old Dominion	CUSA
Tulane	CUSA
UAB	CUSA
Charlotte	CUSA
FIU	CUSA
North Texas	CUSA
East Carolina	CUSA
Fla. Atlantic	CUSA
Marshall	CUSA
UTSA	CUSA
Rice	CUSA
Green Bay	Horizon
Cleveland St.	Horizon
Wright St.	Horizon
Valparaiso	Horizon
Milwaukee	Horizon
Oakland	Horizon
Youngstown St.	Horizon
Detroit Mercy	Horizon
UIC	Horizon
NJIT	Independent
Harvard	Ivy League
Yale	Ivy League
Princeton	Ivy League
Columbia	Ivy League
Brown	Ivy League
Dartmouth	Ivy League
Penn	Ivy League
Cornell	Ivy League
Iona	MAAC
Manhattan	MAAC
Quinnipiac	MAAC
Canisius	MAAC
Siena	MAAC
Rider	MAAC
Saint Peter's	MAAC
Marist	MAAC
Monmouth	MAAC
Fairfield	MAAC
Niagara	MAAC
Buffalo	MAC
Akron	MAC
Ohio	MAC
Miami (OH)	MAC
Kent St.	MAC
Bowling Green	MAC
Toledo	MAC
Western Mich.	MAC
Eastern Mich.	MAC
NIU	MAC
Central Mich.	MAC
Ball St.	MAC
N.C. Central	MEAC
Hampton	MEAC
Norfolk St.	MEAC
Morgan St.	MEAC
Savannah St.	MEAC
Florida A&M	MEAC
Coppin St.	MEAC
Delaware St.	MEAC
South Carolina St.	MEAC
N.C. A&T	MEAC
Howard	MEAC
Bethune-Cookman	MEAC
UMES	MEAC
Wichita St.	MVC
Indiana St.	MVC
UNI	MVC
Missouri St.	MVC
Illinois St.	MVC
Southern Ill.	MVC
Bradley	MVC
Drake	MVC
Evansville	MVC
Loyola Chicago	MVC
San Diego St.	Mountain West
New Mexico	Mountain West
UNLV	Mountain West
Nevada	Mountain West
Boise St.	Mountain West
Wyoming	Mountain West
Fresno St.	Mountain West
Utah St.	Mountain West
Colorado St.	Mountain West
Air Force	Mountain West
San Jose St.	Mountain West
Robert Morris	NEC
Wagner	NEC
Bryant	NEC
St. Francis Brooklyn	NEC
Mount St. Mary's	NEC
Central Conn. St.	NEC
Saint Francis	NEC
FDU	NEC
LIU	NEC
Sacred Heart	NEC
Belmont	OVC
Eastern Ky.	OVC
Morehead St.	OVC
Tennessee Tech	OVC
Jacksonville St.	OVC
Tennessee St.	OVC
Murray St.	OVC
Southeast Mo. St.	OVC
Eastern Ill.	OVC
SIUE	OVC
Austin Peay	OVC
UT Martin	OVC
Arizona	Pac-12
UCLA	Pac-12
Oregon	Pac-12
Colorado	Pac-12
Stanford	Pac-12
Arizona St.	Pac-12
California	Pac-12
Utah	Pac-12
Washington	Pac-12
Oregon St.	Pac-12
Washington St.	Pac-12
Southern California	Pac-12
Boston U.	Patriot
American	Patriot
Holy Cross	Patriot
Bucknell	Patriot
Army West Point	Patriot
Lehigh	Patriot
Colgate	Patriot
Loyola Maryland	Patriot
Lafayette	Patriot
Navy	Patriot
Florida	SEC
Kentucky	SEC
Georgia	SEC
Tennessee	SEC
Arkansas	SEC
Missouri	SEC
LSU	SEC
Ole Miss	SEC
Texas A&M	SEC
Vanderbilt	SEC
Alabama	SEC
Auburn	SEC
South Carolina	SEC
Mississippi St.	SEC
Davidson	SoCon
Chattanooga	SoCon
Wofford	SoCon
Elon	SoCon
Western Caro.	SoCon
UNC Greensboro	SoCon
Ga. Southern	SoCon
Samford	SoCon
App State	SoCon
Furman	SoCon
The Citadel	SoCon
SFA	Southland
A&M-Corpus Christi	Southland
Sam Houston	Southland
Northwestern St.	Southland
UIW	Southland
Oral Roberts	Southland
Nicholls	Southland
McNeese	Southland
LSU New Orleans	Southland
Southeastern La.	Southland
Central Ark.	Southland
Lamar University	Southland
Abilene Christian	Southland
Houston Christian	Southland
North Dakota St.	Summit League
Purdue Fort Wayne	Summit League
South Dakota St.	Summit League
Denver	Summit League
South Dakota	Summit League
Omaha	Summit League
Western Ill.	Summit League
IU Indy	Summit League
Georgia St.	Sun Belt
Western Ky.	Sun Belt
Louisiana	Sun Belt
Arkansas St.	Sun Belt
Little Rock	Sun Belt
UT Arlington	Sun Belt
ULM	Sun Belt
Troy	Sun Belt
South Alabama	Sun Belt
Texas St.	Sun Belt
Southern U.	SWAC
Alabama St.	SWAC
Texas Southern	SWAC
Ark.-Pine Bluff	SWAC
Alabama A&M	SWAC
Alcorn	SWAC
Jackson St.	SWAC
Prairie View	SWAC
Mississippi Val.	SWAC
Grambling	SWAC
Utah Valley	WAC
New Mexico St.	WAC
Grand Canyon	WAC
Chicago St.	WAC
Idaho	WAC
Kansas City	WAC
Seattle U	WAC
CSU Bakersfield	WAC
UTRGV	WAC
Gonzaga	WCC
BYU	WCC
San Francisco	WCC
Saint Mary's (CA)	WCC
Pepperdine	WCC
San Diego	WCC
Portland	WCC
Pacific	WCC
Santa Clara	WCC
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