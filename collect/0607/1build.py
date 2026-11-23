import os
import json

BASE_DIR = "data/seasons/0607"

teams_data = """
North Carolina	ACC
Virginia	ACC
Virginia Tech	ACC
Boston College	ACC
Maryland	ACC
Georgia Tech	ACC
Duke	ACC
Clemson	ACC
Florida St.	ACC
NC State	ACC
Wake Forest	ACC
Miami (FL)	ACC
Vermont	America East
UAlbany	America East
Boston U.	America East
Maine	America East
UMBC	America East
Binghamton	America East
New Hampshire	America East
Hartford	America East
Stony Brook	America East
Xavier	Atlantic 10
Massachusetts	Atlantic 10
George Washington	Atlantic 10
Fordham	Atlantic 10
Rhode Island	Atlantic 10
Saint Joseph's	Atlantic 10
Dayton	Atlantic 10
Saint Louis	Atlantic 10
Charlotte	Atlantic 10
Temple	Atlantic 10
Duquesne	Atlantic 10
Richmond	Atlantic 10
St. Bonaventure	Atlantic 10
La Salle	Atlantic 10
ETSU	ASUN
Belmont	ASUN
Lipscomb	ASUN
Jacksonville	ASUN
Kennesaw St.	ASUN
Mercer	ASUN
Campbell	ASUN
Gardner-Webb	ASUN
Stetson	ASUN
North Florida	ASUN
Kansas	Big 12
Texas A&M	Big 12
Texas	Big 12
Kansas St.	Big 12
Texas Tech	Big 12
Missouri	Big 12
Oklahoma St.	Big 12
Iowa St.	Big 12
Oklahoma	Big 12
Nebraska	Big 12
Baylor	Big 12
Colorado	Big 12
Georgetown	Big East
Louisville	Big East
Pittsburgh	Big East
Notre Dame	Big East
Syracuse	Big East
Marquette	Big East
West Virginia	Big East
DePaul	Big East
Villanova	Big East
Providence	Big East
St. John's (NY)	Big East
UConn	Big East
Seton Hall	Big East
South Fla.	Big East
Rutgers	Big East
Cincinnati	Big East
Weber St.	Big Sky
Northern Ariz.	Big Sky
Montana	Big Sky
Portland St.	Big Sky
Eastern Wash.	Big Sky
Idaho St.	Big Sky
Montana St.	Big Sky
Sacramento St.	Big Sky
Northern Colo.	Big Sky
Winthrop	Big South
High Point	Big South
Liberty	Big South
Coastal Carolina	Big South
UNC Asheville	Big South
VMI	Big South
Radford	Big South
Charleston So.	Big South
Ohio St.	Big Ten
Wisconsin	Big Ten
Indiana	Big Ten
Iowa	Big Ten
Purdue	Big Ten
Illinois	Big Ten
Michigan St.	Big Ten
Michigan	Big Ten
Minnesota	Big Ten
Northwestern	Big Ten
Penn St.	Big Ten
Long Beach St.	Big West
Cal St. Fullerton	Big West
Cal Poly	Big West
UC Santa Barbara	Big West
UC Irvine	Big West
CSUN	Big West
Pacific	Big West
UC Riverside	Big West
VCU	CAA
Old Dominion	CAA
Hofstra	CAA
Drexel	CAA
Northeastern	CAA
George Mason	CAA
Towson	CAA
William & Mary	CAA
Georgia St.	CAA
UNCW	CAA
James Madison	CAA
Delaware	CAA
Memphis	CUSA
UCF	CUSA
Houston	CUSA
Tulsa	CUSA
Tulane	CUSA
Southern Miss.	CUSA
Rice	CUSA
Marshall	CUSA
UAB	CUSA
UTEP	CUSA
SMU	CUSA
East Carolina	CUSA
Wright St.	Horizon
Butler	Horizon
Loyola Chicago	Horizon
Green Bay	Horizon
Youngstown St.	Horizon
UIC	Horizon
Milwaukee	Horizon
Detroit Mercy	Horizon
Cleveland St.	Horizon
Utah Valley	Independent
North Dakota St.	Independent
CSU Bakersfield	Independent
UTRGV	Independent
Purdue Fort Wayne	Independent
Savannah St.	Independent
Chicago St.	Independent
Longwood	Independent
South Dakota St.	Independent
UC Davis	Independent
NJIT	Independent
Winston-Salem	Independent
Penn	Ivy League
Yale	Ivy League
Cornell	Ivy League
Columbia	Ivy League
Brown	Ivy League
Harvard	Ivy League
Dartmouth	Ivy League
Princeton	Ivy League
Marist	MAAC
Niagara	MAAC
Loyola Maryland	MAAC
Siena	MAAC
Manhattan	MAAC
Fairfield	MAAC
Rider	MAAC
Canisius	MAAC
Saint Peter's	MAAC
Iona	MAAC
Akron	MAC
Kent St.	MAC
Miami (OH)	MAC
Ohio	MAC
Buffalo	MAC
Bowling Green	MAC
Toledo	MAC
Western Mich.	MAC
Central Mich.	MAC
Eastern Mich.	MAC
Ball St.	MAC
NIU	MAC
Delaware St.	MEAC
Florida A&M	MEAC
Hampton	MEAC
N.C. A&T	MEAC
South Carolina St.	MEAC
Morgan St.	MEAC
Norfolk St.	MEAC
Coppin St.	MEAC
Bethune-Cookman	MEAC
Howard	MEAC
UMES	MEAC
Oral Roberts	Summit League
Oakland	Summit League
Valparaiso	Summit League
IU Indy	Summit League
Southern Utah	Summit League
Kansas City	Summit League
Western Ill.	Summit League
Centenary (LA)	Summit League
Southern Ill.	MVC
Creighton	MVC
Missouri St.	MVC
Bradley	MVC
UNI	MVC
Wichita St.	MVC
Drake	MVC
Illinois St.	MVC
Evansville	MVC
Indiana St.	MVC
BYU	Mountain West
UNLV	Mountain West
San Diego St.	Mountain West
Air Force	Mountain West
Wyoming	Mountain West
Colorado St.	Mountain West
Utah	Mountain West
TCU	Mountain West
New Mexico	Mountain West
Central Conn. St.	NEC
Sacred Heart	NEC
Quinnipiac	NEC
Robert Morris	NEC
Mount St. Mary's	NEC
FDU	NEC
Wagner	NEC
St. Francis Brooklyn	NEC
Monmouth	NEC
LIU	NEC
Saint Francis	NEC
Austin Peay	OVC
Eastern Ky.	OVC
Tennessee Tech	OVC
Murray St.	OVC
Samford	OVC
Southeast Mo. St.	OVC
Morehead St.	OVC
Tennessee St.	OVC
Jacksonville St.	OVC
Eastern Ill.	OVC
UT Martin	OVC
UCLA	Pac-10
Washington St.	Pac-10
Oregon	Pac-10
Southern California	Pac-10
Arizona	Pac-10
Stanford	Pac-10
Washington	Pac-10
California	Pac-10
Oregon St.	Pac-10
Arizona St.	Pac-10
Holy Cross	Patriot
Bucknell	Patriot
Lehigh	Patriot
American	Patriot
Colgate	Patriot
Army West Point	Patriot
Navy	Patriot
Lafayette	Patriot
Florida	SEC
Vanderbilt	SEC
Tennessee	SEC
Kentucky	SEC
Georgia	SEC
South Carolina	SEC
Mississippi St.	SEC
Ole Miss	SEC
Arkansas	SEC
Auburn	SEC
Alabama	SEC
LSU	SEC
App State	SoCon
UNC Greensboro	SoCon
Western Caro.	SoCon
Chattanooga	SoCon
Elon	SoCon
Davidson	SoCon
Col. of Charleston	SoCon
Furman	SoCon
Ga. Southern	SoCon
Wofford	SoCon
The Citadel	SoCon
Northwestern St.	Southland
McNeese	Southland
Southeastern La.	Southland
Lamar University	Southland
Nicholls	Southland
Central Ark.	Southland
A&M-Corpus Christi	Southland
Sam Houston	Southland
SFA	Southland
UT Arlington	Southland
Texas St.	Southland
UTSA	Southland
South Alabama	Sun Belt
Western Ky.	Sun Belt
Fla. Atlantic	Sun Belt
Troy	Sun Belt
Middle Tenn.	Sun Belt
FIU	Sun Belt
Arkansas St.	Sun Belt
ULM	Sun Belt
North Texas	Sun Belt
LSU New Orleans	Sun Belt
Little Rock	Sun Belt
Louisiana	Sun Belt
Denver	Sun Belt
Mississippi Val.	SWAC
Jackson St.	SWAC
Grambling	SWAC
Alcorn	SWAC
Texas Southern	SWAC
Ark.-Pine Bluff	SWAC
Southern U.	SWAC
Alabama St.	SWAC
Prairie View	SWAC
Alabama A&M	SWAC
Nevada	WAC
New Mexico St.	WAC
Fresno St.	WAC
Utah St.	WAC
Hawaii	WAC
Boise St.	WAC
Louisiana Tech	WAC
San Jose St.	WAC
Idaho	WAC
Gonzaga	WCC
Santa Clara	WCC
Saint Mary's (CA)	WCC
San Francisco	WCC
San Diego	WCC
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