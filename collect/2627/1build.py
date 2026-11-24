import os
import json

BASE_DIR = "data/seasons/2627"

teams_data = """
Boston College	ACC
Pittsburgh	ACC
SMU	ACC
Virginia	ACC
Virginia Tech	ACC
Notre Dame	ACC
Florida St.	ACC
Georgia Tech	ACC
Miami (FL)	ACC
NC State	ACC
North Carolina	ACC
Stanford	ACC
Wake Forest	ACC
Louisville	ACC
California	ACC
Clemson	ACC
Duke	ACC
Syracuse	ACC
UMass Lowell	America East
Binghamton	America East
New Hampshire	America East
UAlbany	America East
UMBC	America East
Vermont	America East
Bryant	America East
Maine	America East
NJIT	America East
Wichita St.	American
Fla. Atlantic	American
Memphis	American
Charlotte	American
Rice	American
Tulsa	American
UTSA	American
North Texas	American
UAB	American
South Fla.	American
East Carolina	American
Temple	American
Tulane	American
Rhode Island	Atlantic 10
Duquesne	Atlantic 10
George Mason	Atlantic 10
Saint Joseph's	Atlantic 10
St. Bonaventure	Atlantic 10
Fordham	Atlantic 10
George Washington	Atlantic 10
Davidson	Atlantic 10
Saint Louis	Atlantic 10
VCU	Atlantic 10
Loyola Chicago	Atlantic 10
Richmond	Atlantic 10
Dayton	Atlantic 10
La Salle	Atlantic 10
Lipscomb	ASUN
Queens (NC)	ASUN
North Florida	ASUN
West Florida	ASUN
Jacksonville	ASUN
Bellarmine	ASUN
FGCU	ASUN
Stetson	ASUN
Arizona St.	Big 12
BYU	Big 12
Houston	Big 12
Texas Tech	Big 12
Kansas	Big 12
Arizona	Big 12
Cincinnati	Big 12
Baylor	Big 12
TCU	Big 12
Iowa St.	Big 12
Oklahoma St.	Big 12
UCF	Big 12
West Virginia	Big 12
Kansas St.	Big 12
Utah	Big 12
Colorado	Big 12
DePaul	Big East
Georgetown	Big East
St. John's (NY)	Big East
Providence	Big East
Seton Hall	Big East
Xavier	Big East
UConn	Big East
Creighton	Big East
Marquette	Big East
Villanova	Big East
Butler	Big East
Idaho	Big Sky
Montana	Big Sky
Northern Colo.	Big Sky
Portland St.	Big Sky
Southern Utah	Big Sky
Eastern Wash.	Big Sky
Montana St.	Big Sky
Idaho St.	Big Sky
Weber St.	Big Sky
Northern Ariz.	Big Sky
Utah Tech	Big Sky
High Point	Big South
Longwood	Big South
Charleston So.	Big South
Radford	Big South
UNC Asheville	Big South
Presbyterian	Big South
Gardner-Webb	Big South
USC Upstate	Big South
Winthrop	Big South
Indiana	Big Ten
Minnesota	Big Ten
Nebraska	Big Ten
Southern California	Big Ten
UCLA	Big Ten
Illinois	Big Ten
Michigan St.	Big Ten
Penn St.	Big Ten
Washington	Big Ten
Oregon	Big Ten
Ohio St.	Big Ten
Purdue	Big Ten
Rutgers	Big Ten
Wisconsin	Big Ten
Maryland	Big Ten
Michigan	Big Ten
Northwestern	Big Ten
Iowa	Big Ten
UC Santa Barbara	Big West
Utah Valley	Big West
CSU Bakersfield	Big West
Cal St. Fullerton	Big West
UC Riverside	Big West
UC San Diego	Big West
Cal Poly	Big West
UC Irvine	Big West
California Baptist	Big West
Sacramento St.	Big West
CSUN	Big West
Long Beach St.	Big West
UNCW	CAA
Col. of Charleston	CAA
William & Mary	CAA
Drexel	CAA
N.C. A&T	CAA
Stony Brook	CAA
Elon	CAA
Towson	CAA
Hofstra	CAA
Campbell	CAA
Northeastern	CAA
Hampton	CAA
Monmouth	CAA
Missouri St.	CUSA
Kennesaw St.	CUSA
FIU	CUSA
Middle Tenn.	CUSA
Western Ky.	CUSA
Liberty	CUSA
Delaware	CUSA
Jacksonville St.	CUSA
Sam Houston	CUSA
New Mexico St.	CUSA
Wright St.	Horizon
Purdue Fort Wayne	Horizon
IU Indy	Horizon
NIU	Horizon
Cleveland St.	Horizon
Green Bay	Horizon
Northern Ky.	Horizon
Youngstown St.	Horizon
Milwaukee	Horizon
Robert Morris	Horizon
Oakland	Horizon
Detroit Mercy	Horizon
Columbia	Ivy League
Dartmouth	Ivy League
Princeton	Ivy League
Cornell	Ivy League
Penn	Ivy League
Harvard	Ivy League
Yale	Ivy League
Brown	Ivy League
Miami (OH)	MAC
Western Mich.	MAC
Eastern Mich.	MAC
Ohio	MAC
Akron	MAC
Central Mich.	MAC
Bowling Green	MAC
Massachusetts	MAC
Buffalo	MAC
Toledo	MAC
Kent St.	MAC
Ball St.	MAC
Howard	MEAC
Morgan St.	MEAC
South Carolina St.	MEAC
Delaware St.	MEAC
Norfolk St.	MEAC
N.C. Central	MEAC
UMES	MEAC
Coppin St.	MEAC
Fairfield	MAAC
Siena	MAAC
Canisius	MAAC
Marist	MAAC
Sacred Heart	MAAC
Iona	MAAC
Quinnipiac	MAAC
Rider	MAAC
Merrimack	MAAC
Mount St. Mary's	MAAC
Niagara	MAAC
Manhattan	MAAC
Saint Peter's	MAAC
Murray St.	MVC
Belmont	MVC
Drake	MVC
UIC	MVC
Valparaiso	MVC
Evansville	MVC
Bradley	MVC
Illinois St.	MVC
Indiana St.	MVC
UNI	MVC
Southern Ill.	MVC
Grand Canyon	Mountain West
Wyoming	Mountain West
UTEP	Mountain West
Nevada	Mountain West
Hawaii	Mountain West
New Mexico	Mountain West
UC Davis	Mountain West
UNLV	Mountain West
Air Force	Mountain West
San Jose St.	Mountain West
Central Conn. St.	NEC
FDU	NEC
New Haven	NEC
Le Moyne	NEC
Mercyhurst	NEC
Stonehill	NEC
Chicago St.	NEC
Wagner	NEC
LIU	NEC
UT Martin	OVC
Southeast Mo. St.	OVC
Morehead St.	OVC
SIUE	OVC
Tennessee St.	OVC
Lindenwood	OVC
Southern Ind.	OVC
Eastern Ill.	OVC
Western Ill.	OVC
Oregon St.	Pac-12
San Diego St.	Pac-12
Texas St.	Pac-12
Utah St.	Pac-12
Gonzaga	Pac-12
Colorado St.	Pac-12
Fresno St.	Pac-12
Boise St.	Pac-12
Washington St.	Pac-12
Boston U.	Patriot
American	Patriot
Lehigh	Patriot
Navy	Patriot
Lafayette	Patriot
Army West Point	Patriot
Colgate	Patriot
Bucknell	Patriot
Loyola Maryland	Patriot
Holy Cross	Patriot
Alabama	SEC
Georgia	SEC
LSU	SEC
Ole Miss	SEC
South Carolina	SEC
Tennessee	SEC
Texas	SEC
Texas A&M	SEC
Vanderbilt	SEC
Florida	SEC
Mississippi St.	SEC
Missouri	SEC
Oklahoma	SEC
Arkansas	SEC
Kentucky	SEC
Auburn	SEC
Furman	SoCon
Tennessee Tech	SoCon
The Citadel	SoCon
Samford	SoCon
UNC Greensboro	SoCon
VMI	SoCon
Wofford	SoCon
Chattanooga	SoCon
ETSU	SoCon
Mercer	SoCon
Western Caro.	SoCon
SFA	Southland
Houston Christian	Southland
UTRGV	Southland
Lamar University	Southland
LSU New Orleans	Southland
East Texas A&M	Southland
McNeese	Southland
Nicholls	Southland
A&M-Corpus Christi	Southland
Southeastern La.	Southland
UIW	Southland
Northwestern St.	Southland
South Dakota St.	Summit League
St. Thomas (MN)	Summit League
North Dakota	Summit League
Omaha	Summit League
Oral Roberts	Summit League
Kansas City	Summit League
North Dakota St.	Summit League
South Dakota	Summit League
Old Dominion	Sun Belt
App State	Sun Belt
Arkansas St.	Sun Belt
James Madison	Sun Belt
Louisiana Tech	Sun Belt
Southern Miss.	Sun Belt
South Alabama	Sun Belt
Ga. Southern	Sun Belt
Georgia St.	Sun Belt
Troy	Sun Belt
Coastal Carolina	Sun Belt
Marshall	Sun Belt
ULM	Sun Belt
Louisiana	Sun Belt
Alabama A&M	SWAC
Grambling	SWAC
Jackson St.	SWAC
Prairie View	SWAC
Alabama St.	SWAC
Bethune-Cookman	SWAC
Southern U.	SWAC
Texas Southern	SWAC
Alcorn	SWAC
Ark.-Pine Bluff	SWAC
Florida A&M	SWAC
Mississippi Val.	SWAC
UT Arlington	UAC
Eastern Ky.	UAC
North Ala.	UAC
Tarleton St.	UAC
Central Ark.	UAC
Abilene Christian	UAC
Austin Peay	UAC
Little Rock	UAC
West Ga.	UAC
Saint Mary's (CA)	WCC
San Diego	WCC
Santa Clara	WCC
Pacific	WCC
Seattle U	WCC
San Francisco	WCC
LMU (CA)	WCC
Pepperdine	WCC
Portland	WCC
Denver	WCC
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