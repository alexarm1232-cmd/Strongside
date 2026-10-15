import os
import json

BASE_DIR = "data/seasons/2425 full"

teams_data = """
Duke	ACC
Michigan	Big Ten
Arizona	Big 12
Illinois	Big Ten
Gonzaga	WCC
Purdue	Big Ten
Florida	SEC
Iowa St.	Big 12
Houston	Big 12
UConn	Big East
Nebraska	Big Ten
Michigan St.	Big Ten
Virginia	ACC
Kansas	Big 12
Texas Tech	Big 12
Louisville	ACC
Vanderbilt	SEC
Arkansas	SEC
Alabama	SEC
Tennessee	SEC
BYU	Big 12
St. John's (NY)	Big East
Utah St.	Mountain West
Saint Louis	Atlantic 10
North Carolina	ACC
Saint Mary's (CA)	WCC
Iowa	Big Ten
NC State	ACC
Kentucky	SEC
SMU	ACC
Villanova	Big East
Wisconsin	Big Ten
Georgia	SEC
Miami (FL)	ACC
Ohio St.	Big Ten
Auburn	SEC
Texas	SEC
Clemson	ACC
UCLA	Big Ten
Indiana	Big Ten
Santa Clara	WCC
Texas A&M	SEC
UCF	Big 12
New Mexico	Mountain West
TCU	Big 12
San Diego St.	Mountain West
VCU	Atlantic 10
Miami (OH)	MAC
Baylor	Big 12
Virginia Tech	ACC
Cincinnati	Big 12
South Fla.	American
Belmont	MVC
Washington	Big Ten
Seton Hall	Big East
Tulsa	American
Missouri	SEC
McNeese	Southland
California	ACC
Boise St.	Mountain West
Akron	MAC
Nevada	Mountain West
Southern California	Big Ten
Yale	Ivy League
Wake Forest	ACC
West Virginia	Big 12
LSU	SEC
Oklahoma	SEC
Northwestern	Big Ten
Minnesota	Big Ten
Colorado	Big 12
High Point	Big South
Arizona St.	Big 12
Dayton	Atlantic 10
Stanford	ACC
Grand Canyon	Mountain West
Syracuse	ACC
Butler	Big East
Providence	Big East
Oklahoma St.	Big 12
Utah Valley	WAC
Florida St.	ACC
Creighton	Big East
George Washington	Atlantic 10
UNI	MVC
Wichita St.	American
Colorado St.	Mountain West
SFA	Southland
Liberty	CUSA
Ole Miss	SEC
UNCW	CAA
Illinois St.	MVC
Hofstra	CAA
Mississippi St.	SEC
Notre Dame	ACC
Xavier	Big East
George Mason	Atlantic 10
Wyoming	Mountain West
Georgetown	Big East
Kansas St.	Big 12
Murray St.	MVC
Marquette	Big East
Sam Houston	CUSA
DePaul	Big East
Hawaii	Big West
South Carolina	SEC
Pacific	WCC
Davidson	Atlantic 10
UIC	MVC
UAB	American
Bradley	MVC
North Dakota St.	Summit League
St. Thomas (MN)	Summit League
Oregon	Big Ten
California Baptist	WAC
Memphis	American
Southern Ill.	MVC
Utah	Big 12
ETSU	SoCon
Fla. Atlantic	American
William & Mary	CAA
Pittsburgh	ACC
UC San Diego	Big West
UC Irvine	Big West
Seattle U	WAC
Winthrop	Big South
UNLV	Mountain West
Duquesne	Atlantic 10
San Francisco	WCC
Washington St.	WCC
Rhode Island	Atlantic 10
Penn St.	Big Ten
Austin Peay	ASUN
Fresno St.	Mountain West
UTRGV	Southland
UC Santa Barbara	Big West
Troy	Sun Belt
Portland St.	Big Sky
Richmond	Atlantic 10
Navy	Patriot
Kent St.	MAC
Maryland	Big Ten
Montana St.	Big Sky
Arkansas St.	Sun Belt
Marshall	Sun Belt
Valparaiso	MVC
Harvard	Ivy League
Wright St.	Horizon
Northern Colo.	Big Sky
North Texas	American
Saint Joseph's	Atlantic 10
Western Ky.	CUSA
Robert Morris	Horizon
St. Bonaventure	Atlantic 10
Col. of Charleston	CAA
Middle Tenn.	CUSA
Utah Tech	WAC
Rutgers	Big Ten
Bowling Green	MAC
UT Arlington	WAC
Penn	Ivy League
Cornell	Ivy League
Toledo	MAC
LMU (CA)	WCC
CSUN	Big West
Boston College	ACC
Oakland	Horizon
Lipscomb	ASUN
Marist	MAAC
Idaho	Big Sky
Georgia Tech	ACC
Mercer	SoCon
UC Davis	Big West
Temple	American
South Alabama	Sun Belt
Kennesaw St.	CUSA
Fordham	Atlantic 10
Central Ark.	ASUN
New Mexico St.	CUSA
Charlotte	American
App State	Sun Belt
Merrimack	MAAC
Oregon St.	WCC
Tulane	American
Towson	CAA
Columbia	Ivy League
Buffalo	MAC
Siena	MAAC
UT Martin	OVC
Furman	SoCon
FIU	CUSA
Cal St. Fullerton	Big West
Montana	Big Sky
Weber St.	Big Sky
Monmouth	CAA
Northern Ky.	Horizon
A&M-Corpus Christi	Southland
Massachusetts	Atlantic 10
Drake	MVC
LIU	NEC
Youngstown St.	Horizon
LSU New Orleans	Southland
Elon	CAA
Quinnipiac	MAAC
South Dakota St.	Summit League
Queens (NC)	ASUN
Eastern Wash.	Big Sky
James Madison	Sun Belt
Campbell	CAA
Howard	MEAC
Stony Brook	CAA
Drexel	CAA
Ohio	MAC
Samford	SoCon
Tennessee St.	OVC
Southeast Mo. St.	OVC
Colgate	Patriot
Jacksonville St.	CUSA
Missouri St.	MVC
Idaho St.	Big Sky
Green Bay	Horizon
Tarleton St.	WAC
Coastal Carolina	Sun Belt
Denver	Summit League
Vermont	America East
Indiana St.	MVC
Portland	WCC
Cal Poly	Big West
Lamar University	Southland
UNC Asheville	Big South
Southern Miss.	Sun Belt
Eastern Mich.	MAC
San Diego	WCC
Abilene Christian	WAC
Saint Peter's	MAAC
Iona	MAAC
Wofford	SoCon
UMBC	America East
La Salle	Atlantic 10
Texas St.	Sun Belt
Fairfield	MAAC
Dartmouth	Ivy League
Louisiana Tech	CUSA
Detroit Mercy	Horizon
Radford	Big South
American	Patriot
Omaha	Summit League
FGCU	ASUN
Nicholls	Southland
San Jose St.	Mountain West
Western Caro.	SoCon
Rice	American
Purdue Fort Wayne	Horizon
Old Dominion	Sun Belt
Bethune-Cookman	SWAC
Milwaukee	Horizon
Princeton	Ivy League
Charleston So.	Big South
Lindenwood	OVC
Ga. Southern	Sun Belt
N.C. A&T	CAA
UTEP	CUSA
Morehead St.	OVC
SIUE	OVC
Long Beach St.	Big West
Hampton	CAA
Sacramento St.	Big Sky
Presbyterian	Big South
Longwood	Big South
Boston U.	Patriot
East Carolina	American
Delaware	CAA
Southern U.	SWAC
Pepperdine	WCC
North Dakota	Summit League
Chattanooga	SoCon
Eastern Ky.	ASUN
UC Riverside	Big West
Central Mich.	MAC
Brown	Ivy League
Southern Utah	WAC
Mercyhurst	NEC
Northeastern	CAA
UIW	Southland
Western Mich.	MAC
Central Conn. St.	NEC
Grambling	SWAC
USC Upstate	Big South
Le Moyne	NEC
Bellarmine	ASUN
South Dakota	Summit League
Mount St. Mary's	MAAC
Northwestern St.	Southland
Georgia St.	Sun Belt
Northern Ariz.	Big Sky
Sacred Heart	MAAC
Houston Christian	Southland
Lehigh	Patriot
East Texas A&M	Southland
Southeastern La.	Southland
UNC Greensboro	SoCon
Tennessee Tech	OVC
Evansville	MVC
Norfolk St.	MEAC
Jacksonville	ASUN
Alabama A&M	SWAC
Little Rock	OVC
West Ga.	ASUN
Loyola Chicago	Atlantic 10
NJIT	America East
Louisiana	Sun Belt
Cleveland St.	Horizon
IU Indy	Horizon
Wagner	NEC
Ark.-Pine Bluff	SWAC
UMass Lowell	America East
NIU	MAC
Texas Southern	SWAC
Alabama St.	SWAC
Ball St.	MAC
UAlbany	America East
Eastern Ill.	OVC
Holy Cross	Patriot
Manhattan	MAAC
Stetson	ASUN
Loyola Maryland	Patriot
CSU Bakersfield	Big West
Prairie View	SWAC
Lafayette	Patriot
FDU	NEC
Florida A&M	SWAC
Army West Point	Patriot
Oral Roberts	Summit League
North Florida	ASUN
Bucknell	Patriot
Stonehill	NEC
North Ala.	ASUN
Maine	America East
New Hampshire	America East
Chicago St.	NEC
Southern Ind.	OVC
UTSA	American
Alcorn	SWAC
Jackson St.	SWAC
N.C. Central	MEAC
Niagara	MAAC
Canisius	MAAC
UMES	MEAC
Air Force	Mountain West
Saint Francis	NEC
The Citadel	SoCon
Morgan St.	MEAC
Bryant	America East
ULM	Sun Belt
Kansas City	Summit League
Rider	MAAC
South Carolina St.	MEAC
VMI	SoCon
Binghamton	America East
Delaware St.	MEAC
Western Ill.	OVC
Gardner-Webb	Big South
Coppin St.	MEAC
Mississippi Val.	SWAC
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