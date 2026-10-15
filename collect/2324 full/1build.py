import os
import json

BASE_DIR = "data/seasons/2324 full"

teams_data = """
South Fla.	American
Fla. Atlantic	American
Charlotte	American
UAB	American
Memphis	American
SMU	American
North Texas	American
Tulsa	American
East Carolina	American
Tulane	American
Temple	American
Wichita St.	American
Rice	American
UTSA	American
North Carolina	ACC
Duke	ACC
Virginia	ACC
Pittsburgh	ACC
Clemson	ACC
Syracuse	ACC
Wake Forest	ACC
Virginia Tech	ACC
Florida St.	ACC
NC State	ACC
Boston College	ACC
Georgia Tech	ACC
Notre Dame	ACC
Miami (FL)	ACC
Louisville	ACC
Vermont	America East
UMass Lowell	America East
Bryant	America East
New Hampshire	America East
Binghamton	America East
Maine	America East
UMBC	America East
UAlbany	America East
NJIT	America East
Loyola Chicago	Atlantic 10
Richmond	Atlantic 10
Dayton	Atlantic 10
Massachusetts	Atlantic 10
VCU	Atlantic 10
Duquesne	Atlantic 10
George Mason	Atlantic 10
St. Bonaventure	Atlantic 10
Saint Joseph's	Atlantic 10
La Salle	Atlantic 10
Fordham	Atlantic 10
Rhode Island	Atlantic 10
Davidson	Atlantic 10
Saint Louis	Atlantic 10
George Washington	Atlantic 10
Eastern Ky.	ASUN
Stetson	ASUN
Lipscomb	ASUN
Austin Peay	ASUN
North Florida	ASUN
North Ala.	ASUN
FGCU	ASUN
Queens (NC)	ASUN
Kennesaw St.	ASUN
Jacksonville	ASUN
Central Ark.	ASUN
Bellarmine	ASUN
Houston	Big 12
Iowa St.	Big 12
Baylor	Big 12
Texas Tech	Big 12
BYU	Big 12
Kansas	Big 12
Texas	Big 12
TCU	Big 12
Oklahoma	Big 12
Kansas St.	Big 12
Cincinnati	Big 12
UCF	Big 12
Oklahoma St.	Big 12
West Virginia	Big 12
UConn	Big East
Marquette	Big East
Creighton	Big East
Seton Hall	Big East
St. John's (NY)	Big East
Providence	Big East
Villanova	Big East
Butler	Big East
Xavier	Big East
Georgetown	Big East
DePaul	Big East
Eastern Wash.	Big Sky
Montana	Big Sky
Northern Colo.	Big Sky
Weber St.	Big Sky
Montana St.	Big Sky
Portland St.	Big Sky
Northern Ariz.	Big Sky
Idaho St.	Big Sky
Idaho	Big Sky
Sacramento St.	Big Sky
High Point	Big South
UNC Asheville	Big South
Gardner-Webb	Big South
Winthrop	Big South
Longwood	Big South
Presbyterian	Big South
Charleston So.	Big South
Radford	Big South
USC Upstate	Big South
Purdue	Big Ten
Illinois	Big Ten
Nebraska	Big Ten
Northwestern	Big Ten
Wisconsin	Big Ten
Indiana	Big Ten
Michigan St.	Big Ten
Iowa	Big Ten
Ohio St.	Big Ten
Minnesota	Big Ten
Penn St.	Big Ten
Maryland	Big Ten
Rutgers	Big Ten
Michigan	Big Ten
UC Irvine	Big West
UC San Diego	Big West
UC Davis	Big West
Hawaii	Big West
Long Beach St.	Big West
UC Riverside	Big West
CSUN	Big West
UC Santa Barbara	Big West
CSU Bakersfield	Big West
Cal St. Fullerton	Big West
Cal Poly	Big West
Col. of Charleston	CAA
Drexel	CAA
UNCW	CAA
Hofstra	CAA
Towson	CAA
Delaware	CAA
Stony Brook	CAA
Monmouth	CAA
Campbell	CAA
Northeastern	CAA
Elon	CAA
N.C. A&T	CAA
William & Mary	CAA
Hampton	CAA
Sam Houston	CUSA
Louisiana Tech	CUSA
Western Ky.	CUSA
Liberty	CUSA
UTEP	CUSA
Middle Tenn.	CUSA
New Mexico St.	CUSA
Jacksonville St.	CUSA
FIU	CUSA
Oakland	Horizon
Youngstown St.	Horizon
Green Bay	Horizon
Wright St.	Horizon
Milwaukee	Horizon
Northern Ky.	Horizon
Purdue Fort Wayne	Horizon
Cleveland St.	Horizon
Robert Morris	Horizon
IU Indy	Horizon
Detroit Mercy	Horizon
Chicago St.	Independent
Princeton	Ivy League
Cornell	Ivy League
Yale	Ivy League
Brown	Ivy League
Harvard	Ivy League
Columbia	Ivy League
Penn	Ivy League
Dartmouth	Ivy League
Quinnipiac	MAAC
Fairfield	MAAC
Marist	MAAC
Saint Peter's	MAAC
Rider	MAAC
Niagara	MAAC
Iona	MAAC
Mount St. Mary's	MAAC
Canisius	MAAC
Manhattan	MAAC
Siena	MAAC
Toledo	MAC
Akron	MAC
Ohio	MAC
Central Mich.	MAC
Bowling Green	MAC
Miami (OH)	MAC
Western Mich.	MAC
Kent St.	MAC
Ball St.	MAC
Eastern Mich.	MAC
NIU	MAC
Buffalo	MAC
Norfolk St.	MEAC
N.C. Central	MEAC
Howard	MEAC
South Carolina St.	MEAC
Morgan St.	MEAC
Delaware St.	MEAC
UMES	MEAC
Coppin St.	MEAC
Indiana St.	MVC
Drake	MVC
Bradley	MVC
Belmont	MVC
UNI	MVC
Southern Ill.	MVC
Illinois St.	MVC
Murray St.	MVC
Missouri St.	MVC
Evansville	MVC
UIC	MVC
Valparaiso	MVC
Utah St.	Mountain West
Nevada	Mountain West
Boise St.	Mountain West
UNLV	Mountain West
San Diego St.	Mountain West
New Mexico	Mountain West
Colorado St.	Mountain West
Wyoming	Mountain West
Fresno St.	Mountain West
Air Force	Mountain West
San Jose St.	Mountain West
Central Conn. St.	NEC
Merrimack	NEC
Sacred Heart	NEC
FDU	NEC
Le Moyne	NEC
Wagner	NEC
LIU	NEC
Saint Francis	NEC
Stonehill	NEC
Morehead St.	OVC
UT Martin	OVC
Little Rock	OVC
Western Ill.	OVC
Tennessee St.	OVC
SIUE	OVC
Eastern Ill.	OVC
Tennessee Tech	OVC
Southern Ind.	OVC
Southeast Mo. St.	OVC
Lindenwood	OVC
Arizona	Pac-12
Washington St.	Pac-12
Colorado	Pac-12
Oregon	Pac-12
UCLA	Pac-12
Utah	Pac-12
Washington	Pac-12
California	Pac-12
Southern California	Pac-12
Arizona St.	Pac-12
Stanford	Pac-12
Oregon St.	Pac-12
Colgate	Patriot
American	Patriot
Boston U.	Patriot
Bucknell	Patriot
Lafayette	Patriot
Lehigh	Patriot
Navy	Patriot
Army West Point	Patriot
Holy Cross	Patriot
Loyola Maryland	Patriot
Tennessee	SEC
Auburn	SEC
South Carolina	SEC
Kentucky	SEC
Alabama	SEC
Florida	SEC
Texas A&M	SEC
LSU	SEC
Mississippi St.	SEC
Ole Miss	SEC
Georgia	SEC
Arkansas	SEC
Vanderbilt	SEC
Missouri	SEC
Samford	SoCon
UNC Greensboro	SoCon
Chattanooga	SoCon
Western Caro.	SoCon
Wofford	SoCon
Furman	SoCon
ETSU	SoCon
Mercer	SoCon
The Citadel	SoCon
VMI	SoCon
McNeese	Southland
A&M-Corpus Christi	Southland
Nicholls	Southland
Lamar University	Southland
Southeastern La.	Southland
Northwestern St.	Southland
East Texas A&M	Southland
LSU New Orleans	Southland
Houston Christian	Southland
UIW	Southland
South Dakota St.	Summit League
North Dakota	Summit League
Kansas City	Summit League
St. Thomas (MN)	Summit League
North Dakota St.	Summit League
Omaha	Summit League
Denver	Summit League
Oral Roberts	Summit League
South Dakota	Summit League
App State	Sun Belt
James Madison	Sun Belt
Troy	Sun Belt
Arkansas St.	Sun Belt
Louisiana	Sun Belt
Southern Miss.	Sun Belt
South Alabama	Sun Belt
Georgia St.	Sun Belt
Ga. Southern	Sun Belt
Texas St.	Sun Belt
Marshall	Sun Belt
ULM	Sun Belt
Coastal Carolina	Sun Belt
Old Dominion	Sun Belt
Grambling	SWAC
Alcorn	SWAC
Southern U.	SWAC
Texas Southern	SWAC
Bethune-Cookman	SWAC
Jackson St.	SWAC
Alabama A&M	SWAC
Ark.-Pine Bluff	SWAC
Alabama St.	SWAC
Prairie View	SWAC
Florida A&M	SWAC
Mississippi Val.	SWAC
Grand Canyon	WAC
Tarleton St.	WAC
UT Arlington	WAC
Seattle U	WAC
Utah Valley	WAC
SFA	WAC
Abilene Christian	WAC
California Baptist	WAC
Utah Tech	WAC
Southern Utah	WAC
UTRGV	WAC
Saint Mary's (CA)	WCC
Gonzaga	WCC
San Francisco	WCC
Santa Clara	WCC
San Diego	WCC
Pepperdine	WCC
LMU (CA)	WCC
Portland	WCC
Pacific	WCC
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