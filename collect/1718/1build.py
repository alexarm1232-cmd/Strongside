import os
import json

BASE_DIR = "data/seasons/1718"

teams_data = """
Cincinnati	American
Houston	American
Wichita St.	American
Tulsa	American
Memphis	American
UCF	American
Temple	American
UConn	American
SMU	American
Tulane	American
East Carolina	American
South Fla.	American
Virginia	ACC
Duke	ACC
Clemson	ACC
North Carolina	ACC
Miami (FL)	ACC
NC State	ACC
Virginia Tech	ACC
Florida St.	ACC
Louisville	ACC
Syracuse	ACC
Notre Dame	ACC
Boston College	ACC
Georgia Tech	ACC
Wake Forest	ACC
Pittsburgh	ACC
Vermont	America East
UMBC	America East
Hartford	America East
UAlbany	America East
Stony Brook	America East
UMass Lowell	America East
New Hampshire	America East
Maine	America East
Binghamton	America East
Rhode Island	Atlantic 10
St. Bonaventure	Atlantic 10
Davidson	Atlantic 10
Saint Joseph's	Atlantic 10
VCU	Atlantic 10
Saint Louis	Atlantic 10
George Mason	Atlantic 10
Richmond	Atlantic 10
Dayton	Atlantic 10
Duquesne	Atlantic 10
George Washington	Atlantic 10
La Salle	Atlantic 10
Massachusetts	Atlantic 10
Fordham	Atlantic 10
FGCU	ASUN
Lipscomb	ASUN
Jacksonville	ASUN
NJIT	ASUN
North Florida	ASUN
Kennesaw St.	ASUN
Stetson	ASUN
USC Upstate	ASUN
Kansas	Big 12
Texas Tech	Big 12
West Virginia	Big 12
Kansas St.	Big 12
TCU	Big 12
Oklahoma St.	Big 12
Oklahoma	Big 12
Baylor	Big 12
Texas	Big 12
Iowa St.	Big 12
Xavier	Big East
Villanova	Big East
Seton Hall	Big East
Creighton	Big East
Providence	Big East
Butler	Big East
Marquette	Big East
Georgetown	Big East
St. John's (NY)	Big East
DePaul	Big East
Montana	Big Sky
Idaho	Big Sky
Weber St.	Big Sky
Eastern Wash.	Big Sky
Northern Colo.	Big Sky
Portland St.	Big Sky
Idaho St.	Big Sky
Montana St.	Big Sky
North Dakota	Big Sky
Southern Utah	Big Sky
Sacramento St.	Big Sky
Northern Ariz.	Big Sky
UNC Asheville	Big South
Radford	Big South
Winthrop	Big South
Campbell	Big South
Liberty	Big South
Charleston So.	Big South
High Point	Big South
Gardner-Webb	Big South
Presbyterian	Big South
Longwood	Big South
Michigan St.	Big Ten
Purdue	Big Ten
Ohio St.	Big Ten
Michigan	Big Ten
Nebraska	Big Ten
Penn St.	Big Ten
Indiana	Big Ten
Maryland	Big Ten
Wisconsin	Big Ten
Northwestern	Big Ten
Minnesota	Big Ten
Illinois	Big Ten
Iowa	Big Ten
Rutgers	Big Ten
UC Davis	Big West
UC Santa Barbara	Big West
UC Irvine	Big West
Cal St. Fullerton	Big West
Long Beach St.	Big West
Hawaii	Big West
Cal Poly	Big West
UC Riverside	Big West
CSUN	Big West
Col. of Charleston	CAA
Northeastern	CAA
Hofstra	CAA
William & Mary	CAA
Towson	CAA
UNCW	CAA
Elon	CAA
Delaware	CAA
Drexel	CAA
James Madison	CAA
Middle Tenn.	CUSA
Old Dominion	CUSA
Western Ky.	CUSA
Marshall	CUSA
UTSA	CUSA
UAB	CUSA
North Texas	CUSA
FIU	CUSA
Louisiana Tech	CUSA
Southern Miss.	CUSA
Fla. Atlantic	CUSA
UTEP	CUSA
Rice	CUSA
Charlotte	CUSA
Northern Ky.	Horizon
Wright St.	Horizon
UIC	Horizon
Oakland	Horizon
Milwaukee	Horizon
IU Indy	Horizon
Green Bay	Horizon
Cleveland St.	Horizon
Youngstown St.	Horizon
Detroit Mercy	Horizon
Penn	Ivy League
Harvard	Ivy League
Yale	Ivy League
Cornell	Ivy League
Princeton	Ivy League
Columbia	Ivy League
Brown	Ivy League
Dartmouth	Ivy League
Rider	MAAC
Canisius	MAAC
Niagara	MAAC
Iona	MAAC
Fairfield	MAAC
Manhattan	MAAC
Quinnipiac	MAAC
Monmouth	MAAC
Saint Peter's	MAAC
Siena	MAAC
Marist	MAAC
Buffalo	MAC
Kent St.	MAC
Miami (OH)	MAC
Bowling Green	MAC
Ohio	MAC
Akron	MAC
Toledo	MAC
Eastern Mich.	MAC
Ball St.	MAC
Western Mich.	MAC
Central Mich.	MAC
NIU	MAC
Bethune-Cookman	MEAC
Savannah St.	MEAC
Hampton	MEAC
N.C. A&T	MEAC
Norfolk St.	MEAC
N.C. Central	MEAC
Morgan St.	MEAC
Howard	MEAC
Florida A&M	MEAC
South Carolina St.	MEAC
Coppin St.	MEAC
UMES	MEAC
Delaware St.	MEAC
Loyola Chicago	MVC
Southern Ill.	MVC
Illinois St.	MVC
Drake	MVC
Bradley	MVC
Indiana St.	MVC
Missouri St.	MVC
Evansville	MVC
UNI	MVC
Valparaiso	MVC
Nevada	Mountain West
Boise St.	Mountain West
New Mexico	Mountain West
San Diego St.	Mountain West
Fresno St.	Mountain West
Wyoming	Mountain West
UNLV	Mountain West
Utah St.	Mountain West
Air Force	Mountain West
Colorado St.	Mountain West
San Jose St.	Mountain West
Wagner	NEC
Saint Francis	NEC
Mount St. Mary's	NEC
LIU	NEC
St. Francis Brooklyn	NEC
Robert Morris	NEC
FDU	NEC
Central Conn. St.	NEC
Sacred Heart	NEC
Bryant	NEC
Murray St.	OVC
Belmont	OVC
Austin Peay	OVC
Jacksonville St.	OVC
Tennessee Tech	OVC
Tennessee St.	OVC
Southeast Mo. St.	OVC
Eastern Ill.	OVC
Eastern Ky.	OVC
UT Martin	OVC
SIUE	OVC
Morehead St.	OVC
Arizona	Pac-12
Southern California	Pac-12
Utah	Pac-12
UCLA	Pac-12
Stanford	Pac-12
Oregon	Pac-12
Washington	Pac-12
Arizona St.	Pac-12
Colorado	Pac-12
Oregon St.	Pac-12
Washington St.	Pac-12
California	Pac-12
Bucknell	Patriot
Colgate	Patriot
Navy	Patriot
Lehigh	Patriot
Boston U.	Patriot
Holy Cross	Patriot
Lafayette	Patriot
Army West Point	Patriot
Loyola Maryland	Patriot
American	Patriot
Auburn	SEC
Tennessee	SEC
Florida	SEC
Kentucky	SEC
Arkansas	SEC
Missouri	SEC
Mississippi St.	SEC
Texas A&M	SEC
Alabama	SEC
LSU	SEC
Georgia	SEC
South Carolina	SEC
Vanderbilt	SEC
Ole Miss	SEC
UNC Greensboro	SoCon
ETSU	SoCon
Furman	SoCon
Wofford	SoCon
Mercer	SoCon
Western Caro.	SoCon
Samford	SoCon
The Citadel	SoCon
VMI	SoCon
Chattanooga	SoCon
Nicholls	Southland
Southeastern La.	Southland
SFA	Southland
Sam Houston	Southland
Lamar University	Southland
LSU New Orleans	Southland
Central Ark.	Southland
Abilene Christian	Southland
McNeese	Southland
A&M-Corpus Christi	Southland
UIW	Southland
Houston Christian	Southland
Northwestern St.	Southland
South Dakota St.	Summit League
South Dakota	Summit League
Denver	Summit League
Purdue Fort Wayne	Summit League
North Dakota St.	Summit League
Oral Roberts	Summit League
Omaha	Summit League
Western Ill.	Summit League
Louisiana	Sun Belt
Georgia St.	Sun Belt
Ga. Southern	Sun Belt
UT Arlington	Sun Belt
ULM	Sun Belt
Troy	Sun Belt
App State	Sun Belt
Coastal Carolina	Sun Belt
Texas St.	Sun Belt
South Alabama	Sun Belt
Arkansas St.	Sun Belt
Little Rock	Sun Belt
Grambling	SWAC
Prairie View	SWAC
Texas Southern	SWAC
Ark.-Pine Bluff	SWAC
Southern U.	SWAC
Jackson St.	SWAC
Alabama St.	SWAC
Alcorn	SWAC
Mississippi Val.	SWAC
Alabama A&M	SWAC
New Mexico St.	WAC
Utah Valley	WAC
Grand Canyon	WAC
Seattle U	WAC
UTRGV	WAC
CSU Bakersfield	WAC
Kansas City	WAC
Chicago St.	WAC
Gonzaga	WCC
Saint Mary's (CA)	WCC
BYU	WCC
San Diego	WCC
San Francisco	WCC
Pacific	WCC
Santa Clara	WCC
LMU (CA)	WCC
Portland	WCC
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