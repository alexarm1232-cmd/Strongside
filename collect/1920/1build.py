import os
import json

BASE_DIR = "data/seasons/1920"

teams_data = """
Houston	American
Tulsa	American
Cincinnati	American
Wichita St.	American
Memphis	American
UConn	American
SMU	American
UCF	American
South Fla.	American
Temple	American
East Carolina	American
Tulane	American
Florida St.	ACC
Duke	ACC
Louisville	ACC
Virginia	ACC
Georgia Tech	ACC
NC State	ACC
Notre Dame	ACC
Syracuse	ACC
Clemson	ACC
Virginia Tech	ACC
Miami (FL)	ACC
Boston College	ACC
Pittsburgh	ACC
North Carolina	ACC
Wake Forest	ACC
Vermont	America East
Stony Brook	America East
Hartford	America East
New Hampshire	America East
UMBC	America East
UAlbany	America East
UMass Lowell	America East
Maine	America East
Binghamton	America East
Dayton	Atlantic 10
Richmond	Atlantic 10
Rhode Island	Atlantic 10
Saint Louis	Atlantic 10
Duquesne	Atlantic 10
St. Bonaventure	Atlantic 10
Davidson	Atlantic 10
VCU	Atlantic 10
Massachusetts	Atlantic 10
La Salle	Atlantic 10
George Washington	Atlantic 10
George Mason	Atlantic 10
Fordham	Atlantic 10
Saint Joseph's	Atlantic 10
Liberty	ASUN
North Florida	ASUN
Lipscomb	ASUN
Stetson	ASUN
North Ala.	ASUN
Jacksonville	ASUN
FGCU	ASUN
NJIT	ASUN
Kennesaw St.	ASUN
Kansas	Big 12
Baylor	Big 12
West Virginia	Big 12
Oklahoma	Big 12
Texas	Big 12
Texas Tech	Big 12
Oklahoma St.	Big 12
TCU	Big 12
Iowa St.	Big 12
Kansas St.	Big 12
Creighton	Big East
Villanova	Big East
Seton Hall	Big East
Providence	Big East
Butler	Big East
Marquette	Big East
Xavier	Big East
St. John's (NY)	Big East
Georgetown	Big East
DePaul	Big East
Eastern Wash.	Big Sky
Northern Colo.	Big Sky
Montana	Big Sky
Portland St.	Big Sky
Northern Ariz.	Big Sky
Montana St.	Big Sky
Southern Utah	Big Sky
Sacramento St.	Big Sky
Weber St.	Big Sky
Idaho St.	Big Sky
Idaho	Big Sky
Winthrop	Big South
Radford	Big South
Gardner-Webb	Big South
Longwood	Big South
UNC Asheville	Big South
Hampton	Big South
Charleston So.	Big South
USC Upstate	Big South
Presbyterian	Big South
Campbell	Big South
High Point	Big South
Maryland	Big Ten
Michigan St.	Big Ten
Wisconsin	Big Ten
Illinois	Big Ten
Ohio St.	Big Ten
Penn St.	Big Ten
Iowa	Big Ten
Rutgers	Big Ten
Michigan	Big Ten
Indiana	Big Ten
Purdue	Big Ten
Minnesota	Big Ten
Northwestern	Big Ten
Nebraska	Big Ten
UC Irvine	Big West
UC Santa Barbara	Big West
CSUN	Big West
Hawaii	Big West
UC Davis	Big West
UC Riverside	Big West
Cal St. Fullerton	Big West
Long Beach St.	Big West
Cal Poly	Big West
Hofstra	CAA
William & Mary	CAA
Towson	CAA
Delaware	CAA
Col. of Charleston	CAA
Northeastern	CAA
Elon	CAA
Drexel	CAA
UNCW	CAA
James Madison	CAA
North Texas	CUSA
Louisiana Tech	CUSA
Western Ky.	CUSA
Charlotte	CUSA
Marshall	CUSA
FIU	CUSA
UAB	CUSA
Old Dominion	CUSA
Fla. Atlantic	CUSA
UTEP	CUSA
Rice	CUSA
UTSA	CUSA
Southern Miss.	CUSA
Middle Tenn.	CUSA
Wright St.	Horizon
Northern Ky.	Horizon
Green Bay	Horizon
Youngstown St.	Horizon
UIC	Horizon
Oakland	Horizon
Milwaukee	Horizon
Cleveland St.	Horizon
Detroit Mercy	Horizon
IU Indy	Horizon
Yale	Ivy League
Harvard	Ivy League
Princeton	Ivy League
Penn	Ivy League
Brown	Ivy League
Dartmouth	Ivy League
Cornell	Ivy League
Columbia	Ivy League
Siena	MAAC
Saint Peter's	MAAC
Rider	MAAC
Monmouth	MAAC
Quinnipiac	MAAC
Iona	MAAC
Niagara	MAAC
Manhattan	MAAC
Fairfield	MAAC
Canisius	MAAC
Marist	MAAC
Akron	MAC
Bowling Green	MAC
Buffalo	MAC
Kent St.	MAC
Ohio	MAC
Miami (OH)	MAC
Ball St.	MAC
NIU	MAC
Toledo	MAC
Central Mich.	MAC
Eastern Mich.	MAC
Western Mich.	MAC
N.C. Central	MEAC
N.C. A&T	MEAC
Norfolk St.	MEAC
Bethune-Cookman	MEAC
Florida A&M	MEAC
Morgan St.	MEAC
Coppin St.	MEAC
South Carolina St.	MEAC
Delaware St.	MEAC
UMES	MEAC
Howard	MEAC
UNI	MVC
Loyola Chicago	MVC
Bradley	MVC
Indiana St.	MVC
Southern Ill.	MVC
Valparaiso	MVC
Missouri St.	MVC
Drake	MVC
Illinois St.	MVC
Evansville	MVC
San Diego St.	Mountain West
Utah St.	Mountain West
Nevada	Mountain West
UNLV	Mountain West
Boise St.	Mountain West
Colorado St.	Mountain West
New Mexico	Mountain West
Fresno St.	Mountain West
Air Force	Mountain West
San Jose St.	Mountain West
Wyoming	Mountain West
Merrimack	NEC
Saint Francis	NEC
Robert Morris	NEC
Sacred Heart	NEC
LIU	NEC
FDU	NEC
Bryant	NEC
St. Francis Brooklyn	NEC
Mount St. Mary's	NEC
Wagner	NEC
Central Conn. St.	NEC
Belmont	OVC
Murray St.	OVC
Austin Peay	OVC
Eastern Ky.	OVC
Tennessee St.	OVC
Eastern Ill.	OVC
Jacksonville St.	OVC
Morehead St.	OVC
Tennessee Tech	OVC
UT Martin	OVC
SIUE	OVC
Southeast Mo. St.	OVC
Oregon	Pac-12
UCLA	Pac-12
Southern California	Pac-12
Arizona St.	Pac-12
Arizona	Pac-12
Colorado	Pac-12
Stanford	Pac-12
Oregon St.	Pac-12
Utah	Pac-12
California	Pac-12
Washington St.	Pac-12
Washington	Pac-12
Colgate	Patriot
Boston U.	Patriot
American	Patriot
Lafayette	Patriot
Army West Point	Patriot
Navy	Patriot
Bucknell	Patriot
Loyola Maryland	Patriot
Lehigh	Patriot
Holy Cross	Patriot
Kentucky	SEC
Auburn	SEC
LSU	SEC
Mississippi St.	SEC
Florida	SEC
South Carolina	SEC
Texas A&M	SEC
Tennessee	SEC
Alabama	SEC
Arkansas	SEC
Missouri	SEC
Ole Miss	SEC
Georgia	SEC
Vanderbilt	SEC
ETSU	SoCon
Furman	SoCon
UNC Greensboro	SoCon
Mercer	SoCon
Western Caro.	SoCon
Chattanooga	SoCon
Wofford	SoCon
Samford	SoCon
VMI	SoCon
The Citadel	SoCon
SFA	Southland
Nicholls	Southland
Abilene Christian	Southland
Sam Houston	Southland
Northwestern St.	Southland
Lamar University	Southland
McNeese	Southland
A&M-Corpus Christi	Southland
Central Ark.	Southland
UIW	Southland
LSU New Orleans	Southland
Southeastern La.	Southland
Houston Christian	Southland
North Dakota St.	Summit League
South Dakota St.	Summit League
South Dakota	Summit League
Oral Roberts	Summit League
Omaha	Summit League
North Dakota	Summit League
Purdue Fort Wayne	Summit League
Denver	Summit League
Western Ill.	Summit League
Little Rock	Sun Belt
Texas St.	Sun Belt
South Alabama	Sun Belt
Ga. Southern	Sun Belt
Georgia St.	Sun Belt
App State	Sun Belt
UT Arlington	Sun Belt
Arkansas St.	Sun Belt
Coastal Carolina	Sun Belt
Louisiana	Sun Belt
ULM	Sun Belt
Troy	Sun Belt
Prairie View	SWAC
Southern U.	SWAC
Texas Southern	SWAC
Grambling	SWAC
Alcorn	SWAC
Jackson St.	SWAC
Alabama St.	SWAC
Alabama A&M	SWAC
Ark.-Pine Bluff	SWAC
Mississippi Val.	SWAC
New Mexico St.	WAC
California Baptist	WAC
UTRGV	WAC
Kansas City	WAC
Grand Canyon	WAC
Seattle U	WAC
CSU Bakersfield	WAC
Utah Valley	WAC
Chicago St.	WAC
Gonzaga	WCC
BYU	WCC
Saint Mary's (CA)	WCC
Pacific	WCC
San Francisco	WCC
Pepperdine	WCC
Santa Clara	WCC
LMU (CA)	WCC
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