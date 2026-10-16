import os
import json

BASE_DIR = "data/seasons/2122 full"

teams_data = """
Houston	American
SMU	American
Memphis	American
Temple	American
Tulane	American
UCF	American
Wichita St.	American
Cincinnati	American
East Carolina	American
Tulsa	American
South Fla.	American
Duke	ACC
North Carolina	ACC
Notre Dame	ACC
Miami (FL)	ACC
Wake Forest	ACC
Virginia	ACC
Virginia Tech	ACC
Florida St.	ACC
Syracuse	ACC
Clemson	ACC
Louisville	ACC
Boston College	ACC
Pittsburgh	ACC
Georgia Tech	ACC
NC State	ACC
Vermont	America East
UMBC	America East
Stony Brook	America East
New Hampshire	America East
UAlbany	America East
Hartford	America East
Binghamton	America East
UMass Lowell	America East
NJIT	America East
Maine	America East
Davidson	Atlantic 10
VCU	Atlantic 10
Dayton	Atlantic 10
St. Bonaventure	Atlantic 10
Saint Louis	Atlantic 10
Richmond	Atlantic 10
George Washington	Atlantic 10
Fordham	Atlantic 10
George Mason	Atlantic 10
Massachusetts	Atlantic 10
Rhode Island	Atlantic 10
La Salle	Atlantic 10
Saint Joseph's	Atlantic 10
Duquesne	Atlantic 10
Liberty	ASUN
Jacksonville	ASUN
FGCU	ASUN
Kennesaw St.	ASUN
North Florida	ASUN
Stetson	ASUN
Jacksonville St.	ASUN
Bellarmine	ASUN
Central Ark.	ASUN
Lipscomb	ASUN
Eastern Ky.	ASUN
North Ala.	ASUN
Kansas	Big 12
Baylor	Big 12
Texas Tech	Big 12
Texas	Big 12
TCU	Big 12
Oklahoma St.	Big 12
Iowa St.	Big 12
Oklahoma	Big 12
Kansas St.	Big 12
West Virginia	Big 12
Providence	Big East
Villanova	Big East
UConn	Big East
Creighton	Big East
Seton Hall	Big East
Marquette	Big East
Xavier	Big East
St. John's (NY)	Big East
DePaul	Big East
Butler	Big East
Georgetown	Big East
Montana St.	Big Sky
Southern Utah	Big Sky
Weber St.	Big Sky
Northern Colo.	Big Sky
Montana	Big Sky
Eastern Wash.	Big Sky
Portland St.	Big Sky
Sacramento St.	Big Sky
Idaho	Big Sky
Northern Ariz.	Big Sky
Idaho St.	Big Sky
Longwood	Big South
Campbell	Big South
High Point	Big South
Radford	Big South
N.C. A&T	Big South
Hampton	Big South
Winthrop	Big South
Gardner-Webb	Big South
USC Upstate	Big South
UNC Asheville	Big South
Presbyterian	Big South
Charleston So.	Big South
Wisconsin	Big Ten
Illinois	Big Ten
Purdue	Big Ten
Iowa	Big Ten
Ohio St.	Big Ten
Rutgers	Big Ten
Michigan St.	Big Ten
Michigan	Big Ten
Indiana	Big Ten
Northwestern	Big Ten
Maryland	Big Ten
Penn St.	Big Ten
Minnesota	Big Ten
Nebraska	Big Ten
Long Beach St.	Big West
Cal St. Fullerton	Big West
Hawaii	Big West
UC Irvine	Big West
UC Santa Barbara	Big West
UC Riverside	Big West
UC Davis	Big West
UC San Diego	Big West
Cal Poly	Big West
CSUN	Big West
CSU Bakersfield	Big West
UNCW	CAA
Towson	CAA
Hofstra	CAA
Delaware	CAA
Drexel	CAA
Col. of Charleston	CAA
Elon	CAA
James Madison	CAA
William & Mary	CAA
Northeastern	CAA
Middle Tenn.	CUSA
Western Ky.	CUSA
Fla. Atlantic	CUSA
Charlotte	CUSA
Old Dominion	CUSA
FIU	CUSA
Marshall	CUSA
North Texas	CUSA
UAB	CUSA
Louisiana Tech	CUSA
UTEP	CUSA
Rice	CUSA
UTSA	CUSA
Southern Miss.	CUSA
Cleveland St.	Horizon
Purdue Fort Wayne	Horizon
Northern Ky.	Horizon
Wright St.	Horizon
Oakland	Horizon
Detroit Mercy	Horizon
Youngstown St.	Horizon
UIC	Horizon
Milwaukee	Horizon
Robert Morris	Horizon
Green Bay	Horizon
IU Indy	Horizon
Princeton	Ivy League
Yale	Ivy League
Penn	Ivy League
Cornell	Ivy League
Dartmouth	Ivy League
Harvard	Ivy League
Brown	Ivy League
Columbia	Ivy League
Iona	MAAC
Saint Peter's	MAAC
Siena	MAAC
Monmouth	MAAC
Marist	MAAC
Niagara	MAAC
Manhattan	MAAC
Fairfield	MAAC
Rider	MAAC
Quinnipiac	MAAC
Canisius	MAAC
Toledo	MAC
Kent St.	MAC
Ohio	MAC
Akron	MAC
Ball St.	MAC
Central Mich.	MAC
Buffalo	MAC
NIU	MAC
Miami (OH)	MAC
Eastern Mich.	MAC
Bowling Green	MAC
Western Mich.	MAC
Norfolk St.	MEAC
Howard	MEAC
N.C. Central	MEAC
Morgan St.	MEAC
South Carolina St.	MEAC
UMES	MEAC
Coppin St.	MEAC
Delaware St.	MEAC
UNI	MVC
Loyola Chicago	MVC
Drake	MVC
Missouri St.	MVC
Bradley	MVC
Southern Ill.	MVC
Valparaiso	MVC
Illinois St.	MVC
Indiana St.	MVC
Evansville	MVC
Boise St.	Mountain West
Colorado St.	Mountain West
San Diego St.	Mountain West
Wyoming	Mountain West
UNLV	Mountain West
Fresno St.	Mountain West
Utah St.	Mountain West
Nevada	Mountain West
New Mexico	Mountain West
Air Force	Mountain West
San Jose St.	Mountain West
Bryant	NEC
Wagner	NEC
LIU	NEC
Mount St. Mary's	NEC
Merrimack	NEC
St. Francis Brooklyn	NEC
Sacred Heart	NEC
Saint Francis	NEC
FDU	NEC
Central Conn. St.	NEC
Murray St.	OVC
Belmont	OVC
Morehead St.	OVC
Southeast Mo. St.	OVC
Tennessee St.	OVC
Austin Peay	OVC
Tennessee Tech	OVC
SIUE	OVC
UT Martin	OVC
Eastern Ill.	OVC
Arizona	Pac-12
UCLA	Pac-12
Southern California	Pac-12
Colorado	Pac-12
Washington St.	Pac-12
Oregon	Pac-12
Washington	Pac-12
Arizona St.	Pac-12
Stanford	Pac-12
California	Pac-12
Utah	Pac-12
Oregon St.	Pac-12
Colgate	Patriot
Navy	Patriot
Boston U.	Patriot
Lehigh	Patriot
Army West Point	Patriot
Loyola Maryland	Patriot
Lafayette	Patriot
Holy Cross	Patriot
American	Patriot
Bucknell	Patriot
Auburn	SEC
Tennessee	SEC
Kentucky	SEC
Arkansas	SEC
Texas A&M	SEC
LSU	SEC
Florida	SEC
South Carolina	SEC
Alabama	SEC
Mississippi St.	SEC
Vanderbilt	SEC
Missouri	SEC
Ole Miss	SEC
Georgia	SEC
Chattanooga	SoCon
Furman	SoCon
Samford	SoCon
Wofford	SoCon
UNC Greensboro	SoCon
VMI	SoCon
Mercer	SoCon
ETSU	SoCon
The Citadel	SoCon
Western Caro.	SoCon
Nicholls	Southland
LSU New Orleans	Southland
Southeastern La.	Southland
A&M-Corpus Christi	Southland
Houston Christian	Southland
Northwestern St.	Southland
McNeese	Southland
UIW	Southland
South Dakota St.	Summit League
North Dakota St.	Summit League
Kansas City	Summit League
Oral Roberts	Summit League
South Dakota	Summit League
Western Ill.	Summit League
Denver	Summit League
St. Thomas (MN)	Summit League
Omaha	Summit League
North Dakota	Summit League
Texas St.	Sun Belt
App State	Sun Belt
Georgia St.	Sun Belt
Troy	Sun Belt
South Alabama	Sun Belt
Arkansas St.	Sun Belt
Coastal Carolina	Sun Belt
Louisiana	Sun Belt
UT Arlington	Sun Belt
Ga. Southern	Sun Belt
ULM	Sun Belt
Little Rock	Sun Belt
Alcorn	SWAC
Texas Southern	SWAC
Southern U.	SWAC
Florida A&M	SWAC
Alabama A&M	SWAC
Jackson St.	SWAC
Prairie View	SWAC
Grambling	SWAC
Alabama St.	SWAC
Bethune-Cookman	SWAC
Ark.-Pine Bluff	SWAC
Mississippi Val.	SWAC
Seattle U	WAC
SFA	WAC
New Mexico St.	WAC
Sam Houston	WAC
Grand Canyon	WAC
Abilene Christian	WAC
Utah Valley	WAC
Tarleton St.	WAC
California Baptist	WAC
Utah Tech	WAC
UTRGV	WAC
Chicago St.	WAC
Lamar University	WAC
Gonzaga	WCC
Saint Mary's (CA)	WCC
Santa Clara	WCC
San Francisco	WCC
BYU	WCC
Portland	WCC
San Diego	WCC
Pacific	WCC
LMU (CA)	WCC
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