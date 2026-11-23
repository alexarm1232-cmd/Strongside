import os
import json

BASE_DIR = "data/seasons/0506"

teams_data = """
Duke	ACC
North Carolina	ACC
Boston College	ACC
NC State	ACC
Florida St.	ACC
Maryland	ACC
Virginia	ACC
Miami (FL)	ACC
Clemson	ACC
Virginia Tech	ACC
Georgia Tech	ACC
Wake Forest	ACC
UAlbany	America East
Binghamton	America East
Boston U.	America East
Hartford	America East
New Hampshire	America East
Vermont	America East
Maine	America East
UMBC	America East
Stony Brook	America East
George Washington	Atlantic 10
Charlotte	Atlantic 10
La Salle	Atlantic 10
Saint Louis	Atlantic 10
Saint Joseph's	Atlantic 10
Fordham	Atlantic 10
Xavier	Atlantic 10
Temple	Atlantic 10
Rhode Island	Atlantic 10
Massachusetts	Atlantic 10
Dayton	Atlantic 10
Richmond	Atlantic 10
St. Bonaventure	Atlantic 10
Duquesne	Atlantic 10
Lipscomb	ASUN
Belmont	ASUN
Fla. Atlantic	ASUN
Gardner-Webb	ASUN
ETSU	ASUN
Stetson	ASUN
Kennesaw St.	ASUN
Campbell	ASUN
Mercer	ASUN
North Florida	ASUN
Jacksonville	ASUN
Texas	Big 12
Kansas	Big 12
Oklahoma	Big 12
Texas A&M	Big 12
Colorado	Big 12
Nebraska	Big 12
Oklahoma St.	Big 12
Texas Tech	Big 12
Kansas St.	Big 12
Iowa St.	Big 12
Missouri	Big 12
Baylor	Big 12
UConn	Big East
Villanova	Big East
West Virginia	Big East
Marquette	Big East
Georgetown	Big East
Pittsburgh	Big East
Seton Hall	Big East
Cincinnati	Big East
Syracuse	Big East
Rutgers	Big East
Louisville	Big East
Notre Dame	Big East
DePaul	Big East
Providence	Big East
St. John's (NY)	Big East
South Fla.	Big East
Northern Ariz.	Big Sky
Montana	Big Sky
Eastern Wash.	Big Sky
Montana St.	Big Sky
Sacramento St.	Big Sky
Portland St.	Big Sky
Idaho St.	Big Sky
Weber St.	Big Sky
Winthrop	Big South
Birmingham-Southern	Big South
Coastal Carolina	Big South
Radford	Big South
High Point	Big South
Charleston So.	Big South
UNC Asheville	Big South
Liberty	Big South
VMI	Big South
Ohio St.	Big Ten
Iowa	Big Ten
Illinois	Big Ten
Wisconsin	Big Ten
Indiana	Big Ten
Michigan St.	Big Ten
Michigan	Big Ten
Penn St.	Big Ten
Northwestern	Big Ten
Minnesota	Big Ten
Purdue	Big Ten
Pacific	Big West
UC Irvine	Big West
Long Beach St.	Big West
Cal Poly	Big West
UC Santa Barbara	Big West
Cal St. Fullerton	Big West
CSUN	Big West
UC Riverside	Big West
UNCW	CAA
George Mason	CAA
Hofstra	CAA
Old Dominion	CAA
Northeastern	CAA
VCU	CAA
Towson	CAA
Drexel	CAA
Delaware	CAA
Georgia St.	CAA
William & Mary	CAA
James Madison	CAA
Memphis	CUSA
UAB	CUSA
UTEP	CUSA
Houston	CUSA
UCF	CUSA
Tulsa	CUSA
Rice	CUSA
Tulane	CUSA
Marshall	CUSA
SMU	CUSA
Southern Miss.	CUSA
East Carolina	CUSA
Milwaukee	Horizon
Butler	Horizon
Green Bay	Horizon
Loyola Chicago	Horizon
Detroit Mercy	Horizon
UIC	Horizon
Wright St.	Horizon
Cleveland St.	Horizon
Youngstown St.	Horizon
A&M-Corpus Christi	Independent
North Dakota St.	Independent
Utah Valley	Independent
Purdue Fort Wayne	Independent
Longwood	Independent
South Dakota St.	Independent
UC Davis	Independent
UTRGV	Independent
Northern Colo.	Independent
Savannah St.	Independent
Penn	Ivy League
Princeton	Ivy League
Cornell	Ivy League
Yale	Ivy League
Brown	Ivy League
Harvard	Ivy League
Columbia	Ivy League
Dartmouth	Ivy League
Manhattan	MAAC
Iona	MAAC
Marist	MAAC
Siena	MAAC
Saint Peter's	MAAC
Loyola Maryland	MAAC
Niagara	MAAC
Fairfield	MAAC
Canisius	MAAC
Rider	MAAC
Kent St.	MAC
Akron	MAC
Miami (OH)	MAC
Ohio	MAC
Buffalo	MAC
Bowling Green	MAC
NIU	MAC
Western Mich.	MAC
Toledo	MAC
Ball St.	MAC
Eastern Mich.	MAC
Central Mich.	MAC
Delaware St.	MEAC
Coppin St.	MEAC
Bethune-Cookman	MEAC
South Carolina St.	MEAC
Hampton	MEAC
Florida A&M	MEAC
Norfolk St.	MEAC
N.C. A&T	MEAC
Howard	MEAC
UMES	MEAC
Morgan St.	MEAC
Oral Roberts	Summit League
IU Indy	Summit League
Kansas City	Summit League
Valparaiso	Summit League
Southern Utah	Summit League
Chicago St.	Summit League
Oakland	Summit League
Western Ill.	Summit League
Centenary (LA)	Summit League
Wichita St.	MVC
Missouri St.	MVC
Creighton	MVC
Southern Ill.	MVC
UNI	MVC
Bradley	MVC
Drake	MVC
Evansville	MVC
Indiana St.	MVC
Illinois St.	MVC
San Diego St.	Mountain West
Air Force	Mountain West
BYU	Mountain West
UNLV	Mountain West
New Mexico	Mountain West
Utah	Mountain West
Wyoming	Mountain West
Colorado St.	Mountain West
TCU	Mountain West
FDU	NEC
Central Conn. St.	NEC
Monmouth	NEC
Mount St. Mary's	NEC
Robert Morris	NEC
LIU	NEC
Sacred Heart	NEC
Quinnipiac	NEC
St. Francis Brooklyn	NEC
Wagner	NEC
Saint Francis	NEC
Murray St.	OVC
Samford	OVC
Tennessee Tech	OVC
Jacksonville St.	OVC
Eastern Ky.	OVC
Austin Peay	OVC
Tennessee St.	OVC
UT Martin	OVC
Eastern Ill.	OVC
Southeast Mo. St.	OVC
Morehead St.	OVC
UCLA	Pac-10
Washington	Pac-10
California	Pac-10
Arizona	Pac-10
Stanford	Pac-10
Southern California	Pac-10
Oregon	Pac-10
Oregon St.	Pac-10
Arizona St.	Pac-10
Washington St.	Pac-10
Bucknell	Patriot
Holy Cross	Patriot
Lehigh	Patriot
American	Patriot
Lafayette	Patriot
Colgate	Patriot
Navy	Patriot
Army West Point	Patriot
Tennessee	SEC
Florida	SEC
Kentucky	SEC
Vanderbilt	SEC
South Carolina	SEC
Georgia	SEC
LSU	SEC
Alabama	SEC
Arkansas	SEC
Mississippi St.	SEC
Auburn	SEC
Ole Miss	SEC
Elon	SoCon
Chattanooga	SoCon
Western Caro.	SoCon
App State	SoCon
UNC Greensboro	SoCon
Ga. Southern	SoCon
Davidson	SoCon
Col. of Charleston	SoCon
Furman	SoCon
Wofford	SoCon
The Citadel	SoCon
Northwestern St.	Southland
Sam Houston	Southland
Southeastern La.	Southland
SFA	Southland
Lamar University	Southland
McNeese	Southland
UT Arlington	Southland
UTSA	Southland
ULM	Southland
Nicholls	Southland
Texas St.	Southland
Western Ky.	Sun Belt
Middle Tenn.	Sun Belt
Arkansas St.	Sun Belt
Little Rock	Sun Belt
FIU	Sun Belt
South Alabama	Sun Belt
Louisiana	Sun Belt
Denver	Sun Belt
LSU New Orleans	Sun Belt
North Texas	Sun Belt
Troy	Sun Belt
Southern U.	SWAC
Grambling	SWAC
Alabama A&M	SWAC
Jackson St.	SWAC
Alabama St.	SWAC
Mississippi Val.	SWAC
Ark.-Pine Bluff	SWAC
Alcorn	SWAC
Texas Southern	SWAC
Prairie View	SWAC
Nevada	WAC
Utah St.	WAC
Louisiana Tech	WAC
Hawaii	WAC
New Mexico St.	WAC
Fresno St.	WAC
Boise St.	WAC
San Jose St.	WAC
Idaho	WAC
Gonzaga	WCC
LMU (CA)	WCC
Saint Mary's (CA)	WCC
San Francisco	WCC
San Diego	WCC
Santa Clara	WCC
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