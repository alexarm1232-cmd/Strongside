import os
import json

BASE_DIR = "data/seasons/2021 full"

teams_data = """
Wichita St.	American
Houston	American
Memphis	American
SMU	American
Cincinnati	American
UCF	American
Tulsa	American
South Fla.	American
Temple	American
Tulane	American
East Carolina	American
Virginia	ACC
Florida St.	ACC
Virginia Tech	ACC
Georgia Tech	ACC
Clemson	ACC
North Carolina	ACC
Louisville	ACC
Syracuse	ACC
NC State	ACC
Duke	ACC
Notre Dame	ACC
Pittsburgh	ACC
Miami (FL)	ACC
Wake Forest	ACC
Boston College	ACC
UMBC	America East
Vermont	America East
New Hampshire	America East
Hartford	America East
UAlbany	America East
UMass Lowell	America East
Stony Brook	America East
NJIT	America East
Binghamton	America East
Maine	America East
St. Bonaventure	Atlantic 10
VCU	Atlantic 10
Davidson	Atlantic 10
Saint Louis	Atlantic 10
Massachusetts	Atlantic 10
George Mason	Atlantic 10
Dayton	Atlantic 10
Richmond	Atlantic 10
Duquesne	Atlantic 10
Rhode Island	Atlantic 10
George Washington	Atlantic 10
La Salle	Atlantic 10
Saint Joseph's	Atlantic 10
Fordham	Atlantic 10
Liberty	ASUN
Bellarmine	ASUN
Lipscomb	ASUN
North Florida	ASUN
North Ala.	ASUN
FGCU	ASUN
Stetson	ASUN
Jacksonville	ASUN
Kennesaw St.	ASUN
Baylor	Big 12
Kansas	Big 12
Texas	Big 12
West Virginia	Big 12
Oklahoma St.	Big 12
Texas Tech	Big 12
Oklahoma	Big 12
TCU	Big 12
Kansas St.	Big 12
Iowa St.	Big 12
Villanova	Big East
Creighton	Big East
UConn	Big East
St. John's (NY)	Big East
Seton Hall	Big East
Providence	Big East
Xavier	Big East
Georgetown	Big East
Marquette	Big East
Butler	Big East
DePaul	Big East
Southern Utah	Big Sky
Weber St.	Big Sky
Eastern Wash.	Big Sky
Montana St.	Big Sky
Idaho St.	Big Sky
Montana	Big Sky
Northern Colo.	Big Sky
Portland St.	Big Sky
Sacramento St.	Big Sky
Northern Ariz.	Big Sky
Idaho	Big Sky
Winthrop	Big South
Radford	Big South
Campbell	Big South
UNC Asheville	Big South
Gardner-Webb	Big South
Longwood	Big South
Hampton	Big South
High Point	Big South
USC Upstate	Big South
Presbyterian	Big South
Charleston So.	Big South
Michigan	Big Ten
Illinois	Big Ten
Iowa	Big Ten
Purdue	Big Ten
Ohio St.	Big Ten
Wisconsin	Big Ten
Rutgers	Big Ten
Maryland	Big Ten
Michigan St.	Big Ten
Indiana	Big Ten
Penn St.	Big Ten
Northwestern	Big Ten
Minnesota	Big Ten
Nebraska	Big Ten
UC Santa Barbara	Big West
UC Irvine	Big West
UC Riverside	Big West
CSU Bakersfield	Big West
UC Davis	Big West
Hawaii	Big West
CSUN	Big West
Cal St. Fullerton	Big West
Long Beach St.	Big West
UC San Diego	Big West
Cal Poly	Big West
James Madison	CAA
Northeastern	CAA
Col. of Charleston	CAA
Hofstra	CAA
Delaware	CAA
Drexel	CAA
William & Mary	CAA
Elon	CAA
Towson	CAA
UNCW	CAA
Western Ky.	CUSA
Old Dominion	CUSA
Marshall	CUSA
Fla. Atlantic	CUSA
Charlotte	CUSA
Middle Tenn.	CUSA
FIU	CUSA
Louisiana Tech	CUSA
UAB	CUSA
North Texas	CUSA
UTSA	CUSA
UTEP	CUSA
Rice	CUSA
Southern Miss.	CUSA
Wright St.	Horizon
Cleveland St.	Horizon
Detroit Mercy	Horizon
Northern Ky.	Horizon
Oakland	Horizon
Youngstown St.	Horizon
IU Indy	Horizon
Milwaukee	Horizon
Green Bay	Horizon
UIC	Horizon
Purdue Fort Wayne	Horizon
Robert Morris	Horizon
Siena	MAAC
Monmouth	MAAC
Iona	MAAC
Canisius	MAAC
Marist	MAAC
Saint Peter's	MAAC
Niagara	MAAC
Quinnipiac	MAAC
Fairfield	MAAC
Manhattan	MAAC
Rider	MAAC
Toledo	MAC
Buffalo	MAC
Akron	MAC
Kent St.	MAC
Ohio	MAC
Bowling Green	MAC
Miami (OH)	MAC
Ball St.	MAC
Western Mich.	MAC
Eastern Mich.	MAC
Central Mich.	MAC
NIU	MAC
Norfolk St.	MEAC
Coppin St.	MEAC
Morgan St.	MEAC
Delaware St.	MEAC
Howard	MEAC
N.C. A&T	MEAC
Florida A&M	MEAC
N.C. Central	MEAC
South Carolina St.	MEAC
Loyola Chicago	MVC
Drake	MVC
Missouri St.	MVC
Indiana St.	MVC
UNI	MVC
Evansville	MVC
Valparaiso	MVC
Bradley	MVC
Southern Ill.	MVC
Illinois St.	MVC
San Diego St.	Mountain West
Colorado St.	Mountain West
Utah St.	Mountain West
Boise St.	Mountain West
Nevada	Mountain West
Fresno St.	Mountain West
UNLV	Mountain West
Wyoming	Mountain West
Air Force	Mountain West
San Jose St.	Mountain West
New Mexico	Mountain West
Wagner	NEC
Bryant	NEC
Mount St. Mary's	NEC
Sacred Heart	NEC
LIU	NEC
Merrimack	NEC
St. Francis Brooklyn	NEC
FDU	NEC
Saint Francis	NEC
Central Conn. St.	NEC
Belmont	OVC
Morehead St.	OVC
Eastern Ky.	OVC
Jacksonville St.	OVC
Austin Peay	OVC
Murray St.	OVC
Southeast Mo. St.	OVC
SIUE	OVC
Eastern Ill.	OVC
UT Martin	OVC
Tennessee Tech	OVC
Tennessee St.	OVC
Oregon	Pac-12
Southern California	Pac-12
Colorado	Pac-12
UCLA	Pac-12
Arizona	Pac-12
Oregon St.	Pac-12
Stanford	Pac-12
Utah	Pac-12
Arizona St.	Pac-12
Washington St.	Pac-12
Washington	Pac-12
California	Pac-12
Lafayette	Patriot
Bucknell	Patriot
Lehigh	Patriot
Colgate	Patriot
Army West Point	Patriot
Boston U.	Patriot
Holy Cross	Patriot
Navy	Patriot
American	Patriot
Loyola Maryland	Patriot
Alabama	SEC
Arkansas	SEC
LSU	SEC
Tennessee	SEC
Florida	SEC
Ole Miss	SEC
Missouri	SEC
Kentucky	SEC
Mississippi St.	SEC
Georgia	SEC
Auburn	SEC
South Carolina	SEC
Texas A&M	SEC
Vanderbilt	SEC
UNC Greensboro	SoCon
Wofford	SoCon
Furman	SoCon
Chattanooga	SoCon
ETSU	SoCon
VMI	SoCon
Mercer	SoCon
The Citadel	SoCon
Western Caro.	SoCon
Samford	SoCon
Nicholls	Southland
Abilene Christian	Southland
SFA	Southland
Sam Houston	Southland
Northwestern St.	Southland
LSU New Orleans	Southland
Lamar University	Southland
UIW	Southland
Southeastern La.	Southland
McNeese	Southland
Houston Christian	Southland
Central Ark.	Southland
A&M-Corpus Christi	Southland
South Dakota St.	Summit League
South Dakota	Summit League
North Dakota St.	Summit League
Oral Roberts	Summit League
North Dakota	Summit League
Kansas City	Summit League
Western Ill.	Summit League
Omaha	Summit League
Denver	Summit League
Georgia St.	Sun Belt
Coastal Carolina	Sun Belt
South Alabama	Sun Belt
App State	Sun Belt
Ga. Southern	Sun Belt
Troy	Sun Belt
Texas St.	Sun Belt
Louisiana	Sun Belt
UT Arlington	Sun Belt
Arkansas St.	Sun Belt
Little Rock	Sun Belt
ULM	Sun Belt
Prairie View	SWAC
Jackson St.	SWAC
Texas Southern	SWAC
Grambling	SWAC
Southern U.	SWAC
Alcorn	SWAC
Alabama A&M	SWAC
Alabama St.	SWAC
Ark.-Pine Bluff	SWAC
Mississippi Val.	SWAC
Grand Canyon	WAC
Utah Valley	WAC
New Mexico St.	WAC
California Baptist	WAC
Chicago St.	WAC
Seattle U	WAC
Tarleton St.	WAC
Utah Tech	WAC
UTRGV	WAC
Gonzaga	WCC
BYU	WCC
LMU (CA)	WCC
Pepperdine	WCC
Pacific	WCC
Santa Clara	WCC
Saint Mary's (CA)	WCC
San Francisco	WCC
San Diego	WCC
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