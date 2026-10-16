import os
import json

BASE_DIR = "data/seasons/1819 full"

teams_data = """
Houston	American
Cincinnati	American
UCF	American
Temple	American
Memphis	American
Wichita St.	American
South Fla.	American
Tulsa	American
UConn	American
SMU	American
East Carolina	American
Tulane	American
Virginia	ACC
North Carolina	ACC
Duke	ACC
Florida St.	ACC
Virginia Tech	ACC
Louisville	ACC
Syracuse	ACC
NC State	ACC
Clemson	ACC
Georgia Tech	ACC
Boston College	ACC
Miami (FL)	ACC
Wake Forest	ACC
Notre Dame	ACC
Pittsburgh	ACC
Vermont	America East
Stony Brook	America East
UMBC	America East
Hartford	America East
UMass Lowell	America East
UAlbany	America East
Binghamton	America East
New Hampshire	America East
Maine	America East
VCU	Atlantic 10
Davidson	Atlantic 10
Dayton	Atlantic 10
St. Bonaventure	Atlantic 10
George Mason	Atlantic 10
Saint Louis	Atlantic 10
Duquesne	Atlantic 10
Rhode Island	Atlantic 10
La Salle	Atlantic 10
Saint Joseph's	Atlantic 10
Richmond	Atlantic 10
Massachusetts	Atlantic 10
George Washington	Atlantic 10
Fordham	Atlantic 10
Liberty	ASUN
Lipscomb	ASUN
North Florida	ASUN
FGCU	ASUN
NJIT	ASUN
North Ala.	ASUN
Jacksonville	ASUN
Stetson	ASUN
Kennesaw St.	ASUN
Texas Tech	Big 12
Kansas St.	Big 12
Kansas	Big 12
Baylor	Big 12
Iowa St.	Big 12
Texas	Big 12
TCU	Big 12
Oklahoma	Big 12
Oklahoma St.	Big 12
West Virginia	Big 12
Villanova	Big East
Marquette	Big East
Seton Hall	Big East
Georgetown	Big East
Creighton	Big East
Xavier	Big East
St. John's (NY)	Big East
Providence	Big East
DePaul	Big East
Butler	Big East
Montana	Big Sky
Northern Colo.	Big Sky
Eastern Wash.	Big Sky
Weber St.	Big Sky
Portland St.	Big Sky
Montana St.	Big Sky
Southern Utah	Big Sky
Sacramento St.	Big Sky
Northern Ariz.	Big Sky
Idaho St.	Big Sky
Idaho	Big Sky
Radford	Big South
Campbell	Big South
Gardner-Webb	Big South
Winthrop	Big South
Presbyterian	Big South
Charleston So.	Big South
High Point	Big South
Hampton	Big South
Longwood	Big South
UNC Asheville	Big South
USC Upstate	Big South
Michigan St.	Big Ten
Purdue	Big Ten
Michigan	Big Ten
Wisconsin	Big Ten
Maryland	Big Ten
Iowa	Big Ten
Minnesota	Big Ten
Ohio St.	Big Ten
Indiana	Big Ten
Rutgers	Big Ten
Penn St.	Big Ten
Illinois	Big Ten
Nebraska	Big Ten
Northwestern	Big Ten
UC Irvine	Big West
UC Santa Barbara	Big West
Cal St. Fullerton	Big West
Hawaii	Big West
Long Beach St.	Big West
CSUN	Big West
UC Davis	Big West
UC Riverside	Big West
Cal Poly	Big West
Hofstra	CAA
Northeastern	CAA
Col. of Charleston	CAA
William & Mary	CAA
Delaware	CAA
Drexel	CAA
Elon	CAA
James Madison	CAA
Towson	CAA
UNCW	CAA
Old Dominion	CUSA
Marshall	CUSA
Southern Miss.	CUSA
Western Ky.	CUSA
UTSA	CUSA
FIU	CUSA
UAB	CUSA
Louisiana Tech	CUSA
North Texas	CUSA
Fla. Atlantic	CUSA
Rice	CUSA
Middle Tenn.	CUSA
Charlotte	CUSA
UTEP	CUSA
Northern Ky.	Horizon
Wright St.	Horizon
Oakland	Horizon
Green Bay	Horizon
UIC	Horizon
IU Indy	Horizon
Youngstown St.	Horizon
Detroit Mercy	Horizon
Cleveland St.	Horizon
Milwaukee	Horizon
Yale	Ivy League
Harvard	Ivy League
Princeton	Ivy League
Brown	Ivy League
Penn	Ivy League
Cornell	Ivy League
Columbia	Ivy League
Dartmouth	Ivy League
Iona	MAAC
Quinnipiac	MAAC
Rider	MAAC
Siena	MAAC
Canisius	MAAC
Monmouth	MAAC
Manhattan	MAAC
Marist	MAAC
Niagara	MAAC
Saint Peter's	MAAC
Fairfield	MAAC
Buffalo	MAC
Bowling Green	MAC
Kent St.	MAC
Akron	MAC
Miami (OH)	MAC
Ohio	MAC
Toledo	MAC
Central Mich.	MAC
Eastern Mich.	MAC
NIU	MAC
Ball St.	MAC
Western Mich.	MAC
Norfolk St.	MEAC
N.C. A&T	MEAC
N.C. Central	MEAC
Howard	MEAC
Bethune-Cookman	MEAC
Florida A&M	MEAC
Savannah St.	MEAC
Coppin St.	MEAC
South Carolina St.	MEAC
UMES	MEAC
Morgan St.	MEAC
Delaware St.	MEAC
Drake	MVC
Loyola Chicago	MVC
Southern Ill.	MVC
Missouri St.	MVC
Bradley	MVC
Illinois St.	MVC
UNI	MVC
Indiana St.	MVC
Valparaiso	MVC
Evansville	MVC
Nevada	Mountain West
Utah St.	Mountain West
Fresno St.	Mountain West
San Diego St.	Mountain West
UNLV	Mountain West
Air Force	Mountain West
New Mexico	Mountain West
Boise St.	Mountain West
Colorado St.	Mountain West
Wyoming	Mountain West
San Jose St.	Mountain West
FDU	NEC
Saint Francis	NEC
Robert Morris	NEC
Sacred Heart	NEC
St. Francis Brooklyn	NEC
LIU	NEC
Wagner	NEC
Bryant	NEC
Mount St. Mary's	NEC
Central Conn. St.	NEC
Murray St.	OVC
Belmont	OVC
Jacksonville St.	OVC
Austin Peay	OVC
Morehead St.	OVC
Eastern Ill.	OVC
Eastern Ky.	OVC
UT Martin	OVC
SIUE	OVC
Tennessee St.	OVC
Southeast Mo. St.	OVC
Tennessee Tech	OVC
Washington	Pac-12
Arizona St.	Pac-12
Utah	Pac-12
Oregon	Pac-12
Colorado	Pac-12
Oregon St.	Pac-12
UCLA	Pac-12
Arizona	Pac-12
Southern California	Pac-12
Stanford	Pac-12
Washington St.	Pac-12
California	Pac-12
Colgate	Patriot
Bucknell	Patriot
Lehigh	Patriot
American	Patriot
Army West Point	Patriot
Navy	Patriot
Boston U.	Patriot
Loyola Maryland	Patriot
Lafayette	Patriot
Holy Cross	Patriot
LSU	SEC
Tennessee	SEC
Kentucky	SEC
Auburn	SEC
South Carolina	SEC
Mississippi St.	SEC
Ole Miss	SEC
Florida	SEC
Alabama	SEC
Arkansas	SEC
Texas A&M	SEC
Missouri	SEC
Georgia	SEC
Vanderbilt	SEC
Wofford	SoCon
UNC Greensboro	SoCon
Furman	SoCon
ETSU	SoCon
Chattanooga	SoCon
Samford	SoCon
Mercer	SoCon
The Citadel	SoCon
VMI	SoCon
Western Caro.	SoCon
Sam Houston	Southland
Abilene Christian	Southland
Lamar University	Southland
LSU New Orleans	Southland
Southeastern La.	Southland
A&M-Corpus Christi	Southland
Central Ark.	Southland
Houston Christian	Southland
SFA	Southland
Nicholls	Southland
Northwestern St.	Southland
McNeese	Southland
UIW	Southland
South Dakota St.	Summit League
Omaha	Summit League
Purdue Fort Wayne	Summit League
North Dakota St.	Summit League
South Dakota	Summit League
Oral Roberts	Summit League
North Dakota	Summit League
Western Ill.	Summit League
Denver	Summit League
Georgia St.	Sun Belt
Texas St.	Sun Belt
Ga. Southern	Sun Belt
UT Arlington	Sun Belt
Louisiana	Sun Belt
ULM	Sun Belt
Coastal Carolina	Sun Belt
South Alabama	Sun Belt
Arkansas St.	Sun Belt
App State	Sun Belt
Troy	Sun Belt
Little Rock	Sun Belt
Prairie View	SWAC
Texas Southern	SWAC
Grambling	SWAC
Ark.-Pine Bluff	SWAC
Jackson St.	SWAC
Alabama St.	SWAC
Alcorn	SWAC
Southern U.	SWAC
Mississippi Val.	SWAC
Alabama A&M	SWAC
New Mexico St.	WAC
Utah Valley	WAC
Grand Canyon	WAC
UTRGV	WAC
CSU Bakersfield	WAC
California Baptist	WAC
Seattle U	WAC
Kansas City	WAC
Chicago St.	WAC
Gonzaga	WCC
Saint Mary's (CA)	WCC
BYU	WCC
San Francisco	WCC
LMU (CA)	WCC
Santa Clara	WCC
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