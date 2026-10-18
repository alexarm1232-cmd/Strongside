import os
import json

BASE_DIR = "data/seasons/1516 full"

teams_data = """
Temple	American
SMU	American
Houston	American
Cincinnati	American
Tulsa	American
UConn	American
Memphis	American
UCF	American
East Carolina	American
South Fla.	American
Tulane	American
North Carolina	ACC
Virginia	ACC
Miami (FL)	ACC
Louisville	ACC
Duke	ACC
Notre Dame	ACC
Virginia Tech	ACC
Clemson	ACC
Pittsburgh	ACC
Syracuse	ACC
Florida St.	ACC
Georgia Tech	ACC
NC State	ACC
Wake Forest	ACC
Boston College	ACC
Stony Brook	America East
UAlbany	America East
Vermont	America East
New Hampshire	America East
UMass Lowell	America East
Binghamton	America East
Hartford	America East
Maine	America East
UMBC	America East
Dayton	Atlantic 10
St. Bonaventure	Atlantic 10
VCU	Atlantic 10
Saint Joseph's	Atlantic 10
George Washington	Atlantic 10
Davidson	Atlantic 10
Rhode Island	Atlantic 10
Fordham	Atlantic 10
Richmond	Atlantic 10
Duquesne	Atlantic 10
Massachusetts	Atlantic 10
George Mason	Atlantic 10
Saint Louis	Atlantic 10
La Salle	Atlantic 10
North Florida	ASUN
FGCU	ASUN
NJIT	ASUN
Jacksonville	ASUN
Lipscomb	ASUN
Kennesaw St.	ASUN
Stetson	ASUN
USC Upstate	ASUN
Kansas	Big 12
West Virginia	Big 12
Oklahoma	Big 12
Texas	Big 12
Iowa St.	Big 12
Baylor	Big 12
Texas Tech	Big 12
Kansas St.	Big 12
Oklahoma St.	Big 12
TCU	Big 12
Villanova	Big East
Xavier	Big East
Seton Hall	Big East
Providence	Big East
Butler	Big East
Creighton	Big East
Marquette	Big East
Georgetown	Big East
DePaul	Big East
St. John's (NY)	Big East
Weber St.	Big Sky
Montana	Big Sky
Idaho	Big Sky
Idaho St.	Big Sky
Eastern Wash.	Big Sky
North Dakota	Big Sky
Montana St.	Big Sky
Portland St.	Big Sky
Northern Colo.	Big Sky
Sacramento St.	Big Sky
Southern Utah	Big Sky
Northern Ariz.	Big Sky
Winthrop	Big South
High Point	Big South
UNC Asheville	Big South
Coastal Carolina	Big South
Gardner-Webb	Big South
Liberty	Big South
Radford	Big South
Campbell	Big South
Presbyterian	Big South
Longwood	Big South
Charleston So.	Big South
Indiana	Big Ten
Michigan St.	Big Ten
Maryland	Big Ten
Purdue	Big Ten
Iowa	Big Ten
Wisconsin	Big Ten
Ohio St.	Big Ten
Michigan	Big Ten
Northwestern	Big Ten
Penn St.	Big Ten
Nebraska	Big Ten
Illinois	Big Ten
Minnesota	Big Ten
Rutgers	Big Ten
Hawaii	Big West
UC Irvine	Big West
Long Beach St.	Big West
UC Santa Barbara	Big West
UC Davis	Big West
UC Riverside	Big West
CSUN	Big West
Cal Poly	Big West
Cal St. Fullerton	Big West
UNCW	CAA
Hofstra	CAA
James Madison	CAA
William & Mary	CAA
Towson	CAA
Northeastern	CAA
Col. of Charleston	CAA
Elon	CAA
Drexel	CAA
Delaware	CAA
UAB	CUSA
Middle Tenn.	CUSA
Louisiana Tech	CUSA
Old Dominion	CUSA
Marshall	CUSA
UTEP	CUSA
Charlotte	CUSA
Western Ky.	CUSA
FIU	CUSA
North Texas	CUSA
Rice	CUSA
Southern Miss.	CUSA
Fla. Atlantic	CUSA
UTSA	CUSA
Valparaiso	Horizon
Oakland	Horizon
Wright St.	Horizon
Green Bay	Horizon
Milwaukee	Horizon
Detroit Mercy	Horizon
Youngstown St.	Horizon
Northern Ky.	Horizon
Cleveland St.	Horizon
UIC	Horizon
Yale	Ivy League
Princeton	Ivy League
Columbia	Ivy League
Harvard	Ivy League
Penn	Ivy League
Dartmouth	Ivy League
Cornell	Ivy League
Brown	Ivy League
Monmouth	MAAC
Iona	MAAC
Siena	MAAC
Fairfield	MAAC
Saint Peter's	MAAC
Manhattan	MAAC
Canisius	MAAC
Rider	MAAC
Quinnipiac	MAAC
Niagara	MAAC
Marist	MAAC
Akron	MAC
Ohio	MAC
Kent St.	MAC
Buffalo	MAC
Miami (OH)	MAC
Bowling Green	MAC
Ball St.	MAC
Central Mich.	MAC
NIU	MAC
Eastern Mich.	MAC
Toledo	MAC
Western Mich.	MAC
Hampton	MEAC
South Carolina St.	MEAC
Norfolk St.	MEAC
Bethune-Cookman	MEAC
Savannah St.	MEAC
N.C. Central	MEAC
UMES	MEAC
N.C. A&T	MEAC
Howard	MEAC
Coppin St.	MEAC
Morgan St.	MEAC
Delaware St.	MEAC
Florida A&M	MEAC
Wichita St.	MVC
Evansville	MVC
Illinois St.	MVC
Southern Ill.	MVC
UNI	MVC
Indiana St.	MVC
Missouri St.	MVC
Loyola Chicago	MVC
Bradley	MVC
Drake	MVC
San Diego St.	Mountain West
Fresno St.	Mountain West
Boise St.	Mountain West
Nevada	Mountain West
New Mexico	Mountain West
UNLV	Mountain West
Colorado St.	Mountain West
Utah St.	Mountain West
Wyoming	Mountain West
Air Force	Mountain West
San Jose St.	Mountain West
Wagner	NEC
FDU	NEC
St. Francis Brooklyn	NEC
Sacred Heart	NEC
Mount St. Mary's	NEC
LIU	NEC
Saint Francis	NEC
Robert Morris	NEC
Bryant	NEC
Central Conn. St.	NEC
Belmont	OVC
Tennessee St.	OVC
Morehead St.	OVC
Tennessee Tech	OVC
Eastern Ky.	OVC
Jacksonville St.	OVC
UT Martin	OVC
Murray St.	OVC
Eastern Ill.	OVC
Austin Peay	OVC
SIUE	OVC
Southeast Mo. St.	OVC
Oregon	Pac-12
Utah	Pac-12
Arizona	Pac-12
California	Pac-12
Colorado	Pac-12
Southern California	Pac-12
Oregon St.	Pac-12
Washington	Pac-12
Stanford	Pac-12
UCLA	Pac-12
Arizona St.	Pac-12
Washington St.	Pac-12
Bucknell	Patriot
Lehigh	Patriot
Boston U.	Patriot
Army West Point	Patriot
Navy	Patriot
Colgate	Patriot
American	Patriot
Loyola Maryland	Patriot
Holy Cross	Patriot
Lafayette	Patriot
Texas A&M	SEC
Kentucky	SEC
South Carolina	SEC
LSU	SEC
Vanderbilt	SEC
Ole Miss	SEC
Georgia	SEC
Florida	SEC
Arkansas	SEC
Alabama	SEC
Mississippi St.	SEC
Tennessee	SEC
Auburn	SEC
Missouri	SEC
Chattanooga	SoCon
ETSU	SoCon
Furman	SoCon
Wofford	SoCon
Western Caro.	SoCon
UNC Greensboro	SoCon
Mercer	SoCon
Samford	SoCon
VMI	SoCon
The Citadel	SoCon
SFA	Southland
A&M-Corpus Christi	Southland
UIW	Southland
Sam Houston	Southland
Houston Christian	Southland
Southeastern La.	Southland
Abilene Christian	Southland
McNeese	Southland
LSU New Orleans	Southland
Nicholls	Southland
Central Ark.	Southland
Northwestern St.	Southland
Lamar University	Southland
South Dakota St.	Summit League
Purdue Fort Wayne	Summit League
Omaha	Summit League
IU Indy	Summit League
North Dakota St.	Summit League
Denver	Summit League
Oral Roberts	Summit League
South Dakota	Summit League
Western Ill.	Summit League
Little Rock	Sun Belt
ULM	Sun Belt
UT Arlington	Sun Belt
Louisiana	Sun Belt
Ga. Southern	Sun Belt
Georgia St.	Sun Belt
Texas St.	Sun Belt
South Alabama	Sun Belt
Arkansas St.	Sun Belt
App State	Sun Belt
Troy	Sun Belt
Texas Southern	SWAC
Alcorn	SWAC
Jackson St.	SWAC
Southern U.	SWAC
Alabama St.	SWAC
Prairie View	SWAC
Alabama A&M	SWAC
Ark.-Pine Bluff	SWAC
Mississippi Val.	SWAC
Grambling	SWAC
New Mexico St.	WAC
Grand Canyon	WAC
CSU Bakersfield	WAC
Seattle U	WAC
Utah Valley	WAC
Kansas City	WAC
UTRGV	WAC
Chicago St.	WAC
Saint Mary's (CA)	WCC
Gonzaga	WCC
BYU	WCC
Pepperdine	WCC
San Francisco	WCC
Santa Clara	WCC
LMU (CA)	WCC
Portland	WCC
Pacific	WCC
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