import os
import json

BASE_DIR = "data/seasons/2223"

teams_data = """
Houston	American
Memphis	American
Tulane	American
Cincinnati	American
Temple	American
Wichita St.	American
UCF	American
South Fla.	American
East Carolina	American
SMU	American
Tulsa	American
Miami (FL)	ACC
Virginia	ACC
Duke	ACC
Clemson	ACC
Pittsburgh	ACC
NC State	ACC
North Carolina	ACC
Wake Forest	ACC
Syracuse	ACC
Boston College	ACC
Virginia Tech	ACC
Florida St.	ACC
Georgia Tech	ACC
Notre Dame	ACC
Louisville	ACC
Vermont	America East
UMass Lowell	America East
New Hampshire	America East
Bryant	America East
UMBC	America East
Binghamton	America East
Maine	America East
NJIT	America East
UAlbany	America East
VCU	Atlantic 10
Fordham	Atlantic 10
Dayton	Atlantic 10
Saint Louis	Atlantic 10
George Mason	Atlantic 10
Duquesne	Atlantic 10
George Washington	Atlantic 10
Davidson	Atlantic 10
Saint Joseph's	Atlantic 10
St. Bonaventure	Atlantic 10
Richmond	Atlantic 10
La Salle	Atlantic 10
Massachusetts	Atlantic 10
Rhode Island	Atlantic 10
Loyola Chicago	Atlantic 10
Liberty	ASUN
Kennesaw St.	ASUN
Eastern Ky.	ASUN
Stetson	ASUN
Lipscomb	ASUN
North Ala.	ASUN
Bellarmine	ASUN
North Florida	ASUN
Queens (NC)	ASUN
FGCU	ASUN
Jacksonville	ASUN
Jacksonville St.	ASUN
Central Ark.	ASUN
Austin Peay	ASUN
Kansas	Big 12
Texas	Big 12
Kansas St.	Big 12
Baylor	Big 12
TCU	Big 12
Iowa St.	Big 12
Oklahoma St.	Big 12
West Virginia	Big 12
Texas Tech	Big 12
Oklahoma	Big 12
Marquette	Big East
Xavier	Big East
Creighton	Big East
UConn	Big East
Providence	Big East
Seton Hall	Big East
Villanova	Big East
St. John's (NY)	Big East
Butler	Big East
DePaul	Big East
Georgetown	Big East
Eastern Wash.	Big Sky
Montana St.	Big Sky
Weber St.	Big Sky
Montana	Big Sky
Idaho St.	Big Sky
Sacramento St.	Big Sky
Portland St.	Big Sky
Northern Colo.	Big Sky
Northern Ariz.	Big Sky
Idaho	Big Sky
UNC Asheville	Big South
Longwood	Big South
Radford	Big South
USC Upstate	Big South
Gardner-Webb	Big South
Winthrop	Big South
Campbell	Big South
High Point	Big South
Charleston So.	Big South
Presbyterian	Big South
Purdue	Big Ten
Indiana	Big Ten
Northwestern	Big Ten
Michigan St.	Big Ten
Maryland	Big Ten
Illinois	Big Ten
Iowa	Big Ten
Michigan	Big Ten
Penn St.	Big Ten
Rutgers	Big Ten
Wisconsin	Big Ten
Nebraska	Big Ten
Ohio St.	Big Ten
Minnesota	Big Ten
UC Santa Barbara	Big West
UC Irvine	Big West
UC Riverside	Big West
Cal St. Fullerton	Big West
Hawaii	Big West
UC Davis	Big West
Long Beach St.	Big West
CSU Bakersfield	Big West
UC San Diego	Big West
CSUN	Big West
Cal Poly	Big West
Col. of Charleston	CAA
Hofstra	CAA
UNCW	CAA
Towson	CAA
Drexel	CAA
Delaware	CAA
N.C. A&T	CAA
William & Mary	CAA
Northeastern	CAA
Stony Brook	CAA
Elon	CAA
Hampton	CAA
Monmouth	CAA
Fla. Atlantic	CUSA
North Texas	CUSA
UAB	CUSA
Middle Tenn.	CUSA
Charlotte	CUSA
Rice	CUSA
Western Ky.	CUSA
FIU	CUSA
Louisiana Tech	CUSA
UTEP	CUSA
UTSA	CUSA
Youngstown St.	Horizon
Milwaukee	Horizon
Northern Ky.	Horizon
Cleveland St.	Horizon
Oakland	Horizon
Wright St.	Horizon
Robert Morris	Horizon
Purdue Fort Wayne	Horizon
Detroit Mercy	Horizon
IU Indy	Horizon
Green Bay	Horizon
Chicago St.	Independent
Hartford	Independent
Princeton	Ivy League
Yale	Ivy League
Penn	Ivy League
Cornell	Ivy League
Brown	Ivy League
Dartmouth	Ivy League
Harvard	Ivy League
Columbia	Ivy League
Iona	MAAC
Rider	MAAC
Quinnipiac	MAAC
Siena	MAAC
Niagara	MAAC
Manhattan	MAAC
Fairfield	MAAC
Mount St. Mary's	MAAC
Canisius	MAAC
Saint Peter's	MAAC
Marist	MAAC
Toledo	MAC
Kent St.	MAC
Akron	MAC
Ball St.	MAC
Ohio	MAC
Buffalo	MAC
NIU	MAC
Miami (OH)	MAC
Bowling Green	MAC
Central Mich.	MAC
Eastern Mich.	MAC
Western Mich.	MAC
Howard	MEAC
N.C. Central	MEAC
Norfolk St.	MEAC
UMES	MEAC
Morgan St.	MEAC
Coppin St.	MEAC
Delaware St.	MEAC
South Carolina St.	MEAC
Bradley	MVC
Drake	MVC
Southern Ill.	MVC
Belmont	MVC
Indiana St.	MVC
Missouri St.	MVC
Murray St.	MVC
UNI	MVC
Illinois St.	MVC
Valparaiso	MVC
UIC	MVC
Evansville	MVC
San Diego St.	Mountain West
Utah St.	Mountain West
Boise St.	Mountain West
Nevada	Mountain West
San Jose St.	Mountain West
New Mexico	Mountain West
UNLV	Mountain West
Colorado St.	Mountain West
Fresno St.	Mountain West
Air Force	Mountain West
Wyoming	Mountain West
Merrimack	NEC
FDU	NEC
Stonehill	NEC
Saint Francis	NEC
Wagner	NEC
Sacred Heart	NEC
St. Francis Brooklyn	NEC
Central Conn. St.	NEC
LIU	NEC
Morehead St.	OVC
Tennessee Tech	OVC
UT Martin	OVC
Tennessee St.	OVC
Southeast Mo. St.	OVC
SIUE	OVC
Southern Ind.	OVC
Lindenwood	OVC
Little Rock	OVC
Eastern Ill.	OVC
UCLA	Pac-12
Arizona	Pac-12
Southern California	Pac-12
Oregon	Pac-12
Arizona St.	Pac-12
Washington St.	Pac-12
Utah	Pac-12
Colorado	Pac-12
Washington	Pac-12
Stanford	Pac-12
Oregon St.	Pac-12
California	Pac-12
Colgate	Patriot
Navy	Patriot
Lehigh	Patriot
Army West Point	Patriot
Boston U.	Patriot
American	Patriot
Loyola Maryland	Patriot
Lafayette	Patriot
Holy Cross	Patriot
Bucknell	Patriot
Alabama	SEC
Texas A&M	SEC
Kentucky	SEC
Missouri	SEC
Tennessee	SEC
Vanderbilt	SEC
Auburn	SEC
Florida	SEC
Mississippi St.	SEC
Arkansas	SEC
Georgia	SEC
South Carolina	SEC
Ole Miss	SEC
LSU	SEC
Furman	SoCon
Samford	SoCon
UNC Greensboro	SoCon
Western Caro.	SoCon
Wofford	SoCon
ETSU	SoCon
Chattanooga	SoCon
Mercer	SoCon
The Citadel	SoCon
VMI	SoCon
A&M-Corpus Christi	Southland
Northwestern St.	Southland
Southeastern La.	Southland
Nicholls	Southland
East Texas A&M	Southland
LSU New Orleans	Southland
Houston Christian	Southland
UIW	Southland
McNeese	Southland
Lamar University	Southland
Oral Roberts	Summit League
South Dakota St.	Summit League
North Dakota St.	Summit League
St. Thomas (MN)	Summit League
Western Ill.	Summit League
South Dakota	Summit League
Kansas City	Summit League
Denver	Summit League
North Dakota	Summit League
Omaha	Summit League
Southern Miss.	Sun Belt
Louisiana	Sun Belt
Marshall	Sun Belt
James Madison	Sun Belt
Old Dominion	Sun Belt
Troy	Sun Belt
South Alabama	Sun Belt
Ga. Southern	Sun Belt
App State	Sun Belt
ULM	Sun Belt
Texas St.	Sun Belt
Coastal Carolina	Sun Belt
Arkansas St.	Sun Belt
Georgia St.	Sun Belt
Grambling	SWAC
Alcorn	SWAC
Jackson St.	SWAC
Southern U.	SWAC
Alabama A&M	SWAC
Prairie View	SWAC
Bethune-Cookman	SWAC
Texas Southern	SWAC
Ark.-Pine Bluff	SWAC
Alabama St.	SWAC
Florida A&M	SWAC
Mississippi Val.	SWAC
Utah Valley	WAC
Sam Houston	WAC
Southern Utah	WAC
Seattle U	WAC
SFA	WAC
Grand Canyon	WAC
Tarleton St.	WAC
California Baptist	WAC
UT Arlington	WAC
Abilene Christian	WAC
UTRGV	WAC
Utah Tech	WAC
New Mexico St.	WAC
Gonzaga	WCC
Saint Mary's (CA)	WCC
Santa Clara	WCC
LMU (CA)	WCC
San Francisco	WCC
BYU	WCC
Pacific	WCC
Portland	WCC
San Diego	WCC
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