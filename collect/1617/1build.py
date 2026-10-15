import os
import json

BASE_DIR = "data/seasons/1617"

teams_data = """
SMU	American
Cincinnati	American
Houston	American
UCF	American
Memphis	American
UConn	American
Tulsa	American
Temple	American
East Carolina	American
Tulane	American
South Fla.	American
North Carolina	ACC
Florida St.	ACC
Louisville	ACC
Notre Dame	ACC
Duke	ACC
Virginia	ACC
Virginia Tech	ACC
Miami (FL)	ACC
Syracuse	ACC
Wake Forest	ACC
Georgia Tech	ACC
Clemson	ACC
Pittsburgh	ACC
NC State	ACC
Boston College	ACC
Vermont	America East
Stony Brook	America East
New Hampshire	America East
UAlbany	America East
UMBC	America East
UMass Lowell	America East
Hartford	America East
Binghamton	America East
Maine	America East
Dayton	Atlantic 10
VCU	Atlantic 10
Rhode Island	Atlantic 10
Richmond	Atlantic 10
St. Bonaventure	Atlantic 10
George Washington	Atlantic 10
George Mason	Atlantic 10
La Salle	Atlantic 10
Davidson	Atlantic 10
Fordham	Atlantic 10
Saint Louis	Atlantic 10
Massachusetts	Atlantic 10
Saint Joseph's	Atlantic 10
Duquesne	Atlantic 10
FGCU	ASUN
Lipscomb	ASUN
North Florida	ASUN
USC Upstate	ASUN
Kennesaw St.	ASUN
Jacksonville	ASUN
NJIT	ASUN
Stetson	ASUN
Kansas	Big 12
Baylor	Big 12
West Virginia	Big 12
Iowa St.	Big 12
Oklahoma St.	Big 12
Kansas St.	Big 12
TCU	Big 12
Texas Tech	Big 12
Oklahoma	Big 12
Texas	Big 12
Villanova	Big East
Butler	Big East
Creighton	Big East
Seton Hall	Big East
Providence	Big East
Marquette	Big East
Xavier	Big East
St. John's (NY)	Big East
Georgetown	Big East
DePaul	Big East
North Dakota	Big Sky
Eastern Wash.	Big Sky
Weber St.	Big Sky
Idaho	Big Sky
Montana	Big Sky
Montana St.	Big Sky
Sacramento St.	Big Sky
Portland St.	Big Sky
Northern Colo.	Big Sky
Northern Ariz.	Big Sky
Southern Utah	Big Sky
Idaho St.	Big Sky
Winthrop	Big South
UNC Asheville	Big South
Liberty	Big South
Gardner-Webb	Big South
High Point	Big South
Radford	Big South
Campbell	Big South
Charleston So.	Big South
Longwood	Big South
Presbyterian	Big South
Purdue	Big Ten
Wisconsin	Big Ten
Maryland	Big Ten
Minnesota	Big Ten
Michigan	Big Ten
Northwestern	Big Ten
Michigan St.	Big Ten
Iowa	Big Ten
Illinois	Big Ten
Ohio St.	Big Ten
Indiana	Big Ten
Penn St.	Big Ten
Nebraska	Big Ten
Rutgers	Big Ten
UC Irvine	Big West
UC Davis	Big West
Cal St. Fullerton	Big West
Long Beach St.	Big West
Hawaii	Big West
CSUN	Big West
Cal Poly	Big West
UC Riverside	Big West
UC Santa Barbara	Big West
UNCW	CAA
Col. of Charleston	CAA
Towson	CAA
Elon	CAA
William & Mary	CAA
Northeastern	CAA
Hofstra	CAA
James Madison	CAA
Delaware	CAA
Drexel	CAA
Middle Tenn.	CUSA
Louisiana Tech	CUSA
Old Dominion	CUSA
UTEP	CUSA
Rice	CUSA
Marshall	CUSA
UAB	CUSA
Western Ky.	CUSA
UTSA	CUSA
Charlotte	CUSA
Fla. Atlantic	CUSA
Southern Miss.	CUSA
FIU	CUSA
North Texas	CUSA
Oakland	Horizon
Valparaiso	Horizon
Northern Ky.	Horizon
Green Bay	Horizon
Wright St.	Horizon
UIC	Horizon
Detroit Mercy	Horizon
Youngstown St.	Horizon
Cleveland St.	Horizon
Milwaukee	Horizon
Princeton	Ivy League
Harvard	Ivy League
Yale	Ivy League
Penn	Ivy League
Columbia	Ivy League
Brown	Ivy League
Cornell	Ivy League
Dartmouth	Ivy League
Monmouth	MAAC
Saint Peter's	MAAC
Iona	MAAC
Siena	MAAC
Fairfield	MAAC
Rider	MAAC
Canisius	MAAC
Quinnipiac	MAAC
Niagara	MAAC
Manhattan	MAAC
Marist	MAAC
Akron	MAC
Ohio	MAC
Buffalo	MAC
Kent St.	MAC
Bowling Green	MAC
Miami (OH)	MAC
Ball St.	MAC
Western Mich.	MAC
Toledo	MAC
Eastern Mich.	MAC
NIU	MAC
Central Mich.	MAC
N.C. Central	MEAC
Norfolk St.	MEAC
Morgan St.	MEAC
Hampton	MEAC
Savannah St.	MEAC
UMES	MEAC
South Carolina St.	MEAC
Delaware St.	MEAC
Coppin St.	MEAC
Bethune-Cookman	MEAC
Howard	MEAC
Florida A&M	MEAC
N.C. A&T	MEAC
Wichita St.	MVC
Illinois St.	MVC
Southern Ill.	MVC
UNI	MVC
Loyola Chicago	MVC
Missouri St.	MVC
Bradley	MVC
Evansville	MVC
Indiana St.	MVC
Drake	MVC
Nevada	Mountain West
Colorado St.	Mountain West
Boise St.	Mountain West
Fresno St.	Mountain West
New Mexico	Mountain West
San Diego St.	Mountain West
Wyoming	Mountain West
San Jose St.	Mountain West
Utah St.	Mountain West
Air Force	Mountain West
UNLV	Mountain West
Mount St. Mary's	NEC
LIU	NEC
Wagner	NEC
Saint Francis	NEC
Robert Morris	NEC
Bryant	NEC
FDU	NEC
Sacred Heart	NEC
Central Conn. St.	NEC
St. Francis Brooklyn	NEC
Belmont	OVC
Morehead St.	OVC
Jacksonville St.	OVC
Tennessee St.	OVC
Tennessee Tech	OVC
Eastern Ky.	OVC
UT Martin	OVC
Southeast Mo. St.	OVC
Murray St.	OVC
Austin Peay	OVC
Eastern Ill.	OVC
SIUE	OVC
Arizona	Pac-12
Oregon	Pac-12
UCLA	Pac-12
Utah	Pac-12
Southern California	Pac-12
California	Pac-12
Colorado	Pac-12
Arizona St.	Pac-12
Stanford	Pac-12
Washington St.	Pac-12
Washington	Pac-12
Oregon St.	Pac-12
Bucknell	Patriot
Lehigh	Patriot
Boston U.	Patriot
Navy	Patriot
Holy Cross	Patriot
Loyola Maryland	Patriot
Colgate	Patriot
Army West Point	Patriot
Lafayette	Patriot
American	Patriot
Kentucky	SEC
Florida	SEC
Arkansas	SEC
South Carolina	SEC
Ole Miss	SEC
Alabama	SEC
Vanderbilt	SEC
Georgia	SEC
Texas A&M	SEC
Tennessee	SEC
Auburn	SEC
Mississippi St.	SEC
LSU	SEC
Missouri	SEC
ETSU	SoCon
UNC Greensboro	SoCon
Furman	SoCon
Chattanooga	SoCon
Wofford	SoCon
Mercer	SoCon
Samford	SoCon
The Citadel	SoCon
Western Caro.	SoCon
VMI	SoCon
LSU New Orleans	Southland
A&M-Corpus Christi	Southland
Houston Christian	Southland
SFA	Southland
Sam Houston	Southland
Lamar University	Southland
Southeastern La.	Southland
Nicholls	Southland
Abilene Christian	Southland
Northwestern St.	Southland
UIW	Southland
Central Ark.	Southland
McNeese	Southland
South Dakota	Summit League
North Dakota St.	Summit League
Omaha	Summit League
Purdue Fort Wayne	Summit League
Denver	Summit League
South Dakota St.	Summit League
IU Indy	Summit League
Western Ill.	Summit League
Oral Roberts	Summit League
UT Arlington	Sun Belt
Georgia St.	Sun Belt
Arkansas St.	Sun Belt
Texas St.	Sun Belt
Ga. Southern	Sun Belt
Louisiana	Sun Belt
Troy	Sun Belt
Coastal Carolina	Sun Belt
South Alabama	Sun Belt
Little Rock	Sun Belt
App State	Sun Belt
ULM	Sun Belt
Texas Southern	SWAC
Alcorn	SWAC
Grambling	SWAC
Southern U.	SWAC
Jackson St.	SWAC
Prairie View	SWAC
Mississippi Val.	SWAC
Alabama St.	SWAC
Ark.-Pine Bluff	SWAC
Alabama A&M	SWAC
CSU Bakersfield	WAC
New Mexico St.	WAC
Grand Canyon	WAC
Kansas City	WAC
Utah Valley	WAC
Seattle U	WAC
UTRGV	WAC
Chicago St.	WAC
Gonzaga	WCC
Saint Mary's (CA)	WCC
BYU	WCC
San Francisco	WCC
Santa Clara	WCC
LMU (CA)	WCC
San Diego	WCC
Pepperdine	WCC
Pacific	WCC
Portland	WCC
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