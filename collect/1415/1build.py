import os
import json

BASE_DIR = "data/seasons/1415"

teams_data = """
SMU	American
Tulsa	American
Temple	American
Cincinnati	American
UConn	American
Memphis	American
Tulane	American
East Carolina	American
UCF	American
Houston	American
South Fla.	American
Virginia	ACC
Duke	ACC
Notre Dame	ACC
Louisville	ACC
North Carolina	ACC
Miami (FL)	ACC
NC State	ACC
Syracuse	ACC
Pittsburgh	ACC
Clemson	ACC
Florida St.	ACC
Wake Forest	ACC
Boston College	ACC
Georgia Tech	ACC
Virginia Tech	ACC
UAlbany	America East
Stony Brook	America East
Vermont	America East
New Hampshire	America East
Hartford	America East
UMass Lowell	America East
Binghamton	America East
UMBC	America East
Maine	America East
Davidson	Atlantic 10
Dayton	Atlantic 10
Rhode Island	Atlantic 10
VCU	Atlantic 10
Richmond	Atlantic 10
George Washington	Atlantic 10
St. Bonaventure	Atlantic 10
Massachusetts	Atlantic 10
La Salle	Atlantic 10
Saint Joseph's	Atlantic 10
Duquesne	Atlantic 10
Fordham	Atlantic 10
George Mason	Atlantic 10
Saint Louis	Atlantic 10
North Florida	ASUN
FGCU	ASUN
USC Upstate	ASUN
Lipscomb	ASUN
Northern Ky.	ASUN
Jacksonville	ASUN
Kennesaw St.	ASUN
Stetson	ASUN
Kansas	Big 12
Iowa St.	Big 12
Oklahoma	Big 12
West Virginia	Big 12
Baylor	Big 12
Texas	Big 12
Oklahoma St.	Big 12
Kansas St.	Big 12
TCU	Big 12
Texas Tech	Big 12
Villanova	Big East
Butler	Big East
Georgetown	Big East
Providence	Big East
St. John's (NY)	Big East
Xavier	Big East
Seton Hall	Big East
DePaul	Big East
Creighton	Big East
Marquette	Big East
Eastern Wash.	Big Sky
Montana	Big Sky
Sacramento St.	Big Sky
Northern Ariz.	Big Sky
Northern Colo.	Big Sky
Portland St.	Big Sky
Idaho	Big Sky
Weber St.	Big Sky
Southern Utah	Big Sky
North Dakota	Big Sky
Idaho St.	Big Sky
Montana St.	Big Sky
High Point	Big South
Charleston So.	Big South
Coastal Carolina	Big South
Radford	Big South
Winthrop	Big South
Gardner-Webb	Big South
UNC Asheville	Big South
Presbyterian	Big South
Longwood	Big South
Campbell	Big South
Liberty	Big South
Wisconsin	Big Ten
Maryland	Big Ten
Michigan St.	Big Ten
Iowa	Big Ten
Purdue	Big Ten
Ohio St.	Big Ten
Indiana	Big Ten
Illinois	Big Ten
Michigan	Big Ten
Minnesota	Big Ten
Northwestern	Big Ten
Nebraska	Big Ten
Penn St.	Big Ten
Rutgers	Big Ten
UC Davis	Big West
UC Irvine	Big West
UC Santa Barbara	Big West
Long Beach St.	Big West
Hawaii	Big West
UC Riverside	Big West
Cal Poly	Big West
CSUN	Big West
Cal St. Fullerton	Big West
Northeastern	CAA
William & Mary	CAA
James Madison	CAA
UNCW	CAA
Hofstra	CAA
Drexel	CAA
Delaware	CAA
Elon	CAA
Towson	CAA
Col. of Charleston	CAA
Louisiana Tech	CUSA
Old Dominion	CUSA
UTEP	CUSA
Western Ky.	CUSA
UAB	CUSA
Middle Tenn.	CUSA
FIU	CUSA
UTSA	CUSA
North Texas	CUSA
Rice	CUSA
Charlotte	CUSA
Marshall	CUSA
Southern Miss.	CUSA
Fla. Atlantic	CUSA
Valparaiso	Horizon
Green Bay	Horizon
Cleveland St.	Horizon
Oakland	Horizon
Milwaukee	Horizon
Detroit Mercy	Horizon
UIC	Horizon
Wright St.	Horizon
Youngstown St.	Horizon
NJIT	Independent
Harvard	Ivy League
Yale	Ivy League
Princeton	Ivy League
Dartmouth	Ivy League
Columbia	Ivy League
Cornell	Ivy League
Brown	Ivy League
Penn	Ivy League
Iona	MAAC
Rider	MAAC
Manhattan	MAAC
Monmouth	MAAC
Canisius	MAAC
Quinnipiac	MAAC
Saint Peter's	MAAC
Siena	MAAC
Niagara	MAAC
Fairfield	MAAC
Marist	MAAC
Buffalo	MAC
Kent St.	MAC
Bowling Green	MAC
Akron	MAC
Miami (OH)	MAC
Ohio	MAC
Central Mich.	MAC
Toledo	MAC
Western Mich.	MAC
Eastern Mich.	MAC
NIU	MAC
Ball St.	MAC
N.C. Central	MEAC
Norfolk St.	MEAC
UMES	MEAC
Howard	MEAC
Delaware St.	MEAC
Hampton	MEAC
Bethune-Cookman	MEAC
South Carolina St.	MEAC
N.C. A&T	MEAC
Coppin St.	MEAC
Savannah St.	MEAC
Morgan St.	MEAC
Florida A&M	MEAC
Wichita St.	MVC
UNI	MVC
Illinois St.	MVC
Indiana St.	MVC
Evansville	MVC
Loyola Chicago	MVC
Drake	MVC
Missouri St.	MVC
Southern Ill.	MVC
Bradley	MVC
San Diego St.	Mountain West
Boise St.	Mountain West
Colorado St.	Mountain West
Wyoming	Mountain West
Utah St.	Mountain West
Fresno St.	Mountain West
UNLV	Mountain West
New Mexico	Mountain West
Air Force	Mountain West
Nevada	Mountain West
San Jose St.	Mountain West
St. Francis Brooklyn	NEC
Robert Morris	NEC
Bryant	NEC
Mount St. Mary's	NEC
Saint Francis	NEC
Sacred Heart	NEC
LIU	NEC
Wagner	NEC
FDU	NEC
Central Conn. St.	NEC
Belmont	OVC
Eastern Ky.	OVC
Morehead St.	OVC
Jacksonville St.	OVC
Tennessee Tech	OVC
Tennessee St.	OVC
Murray St.	OVC
UT Martin	OVC
Eastern Ill.	OVC
SIUE	OVC
Southeast Mo. St.	OVC
Austin Peay	OVC
Arizona	Pac-12
Utah	Pac-12
Oregon	Pac-12
UCLA	Pac-12
Stanford	Pac-12
Arizona St.	Pac-12
Oregon St.	Pac-12
California	Pac-12
Colorado	Pac-12
Washington St.	Pac-12
Washington	Pac-12
Southern California	Pac-12
Bucknell	Patriot
Colgate	Patriot
Lehigh	Patriot
Lafayette	Patriot
Boston U.	Patriot
American	Patriot
Holy Cross	Patriot
Navy	Patriot
Loyola Maryland	Patriot
Army West Point	Patriot
Kentucky	SEC
Arkansas	SEC
LSU	SEC
Georgia	SEC
Texas A&M	SEC
Ole Miss	SEC
Vanderbilt	SEC
Alabama	SEC
Florida	SEC
Tennessee	SEC
South Carolina	SEC
Mississippi St.	SEC
Auburn	SEC
Missouri	SEC
Wofford	SoCon
Chattanooga	SoCon
Mercer	SoCon
Western Caro.	SoCon
ETSU	SoCon
VMI	SoCon
Samford	SoCon
The Citadel	SoCon
UNC Greensboro	SoCon
Furman	SoCon
SFA	Southland
Sam Houston	Southland
Northwestern St.	Southland
A&M-Corpus Christi	Southland
UIW	Southland
Lamar University	Southland
McNeese	Southland
Houston Christian	Southland
Nicholls	Southland
LSU New Orleans	Southland
Southeastern La.	Southland
Abilene Christian	Southland
Central Ark.	Southland
North Dakota St.	Summit League
South Dakota St.	Summit League
Oral Roberts	Summit League
Purdue Fort Wayne	Summit League
South Dakota	Summit League
Denver	Summit League
IU Indy	Summit League
Omaha	Summit League
Western Ill.	Summit League
Georgia St.	Sun Belt
Ga. Southern	Sun Belt
ULM	Sun Belt
Louisiana	Sun Belt
UT Arlington	Sun Belt
App State	Sun Belt
South Alabama	Sun Belt
Little Rock	Sun Belt
Texas St.	Sun Belt
Arkansas St.	Sun Belt
Troy	Sun Belt
Texas Southern	SWAC
Alabama St.	SWAC
Southern U.	SWAC
Prairie View	SWAC
Ark.-Pine Bluff	SWAC
Jackson St.	SWAC
Alabama A&M	SWAC
Mississippi Val.	SWAC
Alcorn	SWAC
Grambling	SWAC
New Mexico St.	WAC
Grand Canyon	WAC
Kansas City	WAC
Seattle U	WAC
CSU Bakersfield	WAC
Utah Valley	WAC
UTRGV	WAC
Chicago St.	WAC
Gonzaga	WCC
BYU	WCC
Saint Mary's (CA)	WCC
Pepperdine	WCC
San Diego	WCC
Portland	WCC
San Francisco	WCC
Santa Clara	WCC
Pacific	WCC
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