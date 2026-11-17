"""One-off ingest helper for the H2 official NFL Game Book capture.

Transcribes the tokens read verbatim from each official Game Book PDF into the
raw capture files under raw/gamebooks/. The PDF -> markdown conversion used by
the page-fetch tool is column-lossy for a few blocks, so every string below was
copied by hand from the fetched chunk and is re-checked by
tools/verify_gamebooks.py against the committed canonical tables.

Format per team: "role:unit:pos jersey name; pos jersey name; ..."
role in starter|sub|dnp|inactive ; unit in Offense|Defense|"" (blank = the Game
Book does not label the unit for that block).
"""
import csv, os, sys

ROSTERS = {
"WASNYG": {
 "info": dict(date="2026-11-12", away="WAS", home="NYG", ap=24, hp=21,
   stadium="MetLife Stadium", city="East Rutherford, NJ", roof="Open Stadium",
   surface="Field Turf", weather="Light Rain Fog/Mist", temp=48, hum=89,
   wind_dir="NE", wind_mph=9, chill="", att=80450,
   gc="https://www.nfl.com/games/commanders-at-giants-2026-reg-10",
   pdf="https://static.www.nfl.com/image/upload/v1794570519/gamecenter/ab5828d9-4feb-11f1-abca-2c54536568a9.pdf"),
 "WAS": {
  "starter:Offense":"WR 14 A.Williams; TE 87 J.Bates; LT 74 B.Coleman; LG 75 C.Paul; C 67 N.Allegretti; RG 76 S.Cosmi; RT 72 J.Conerly; TE 82 B.Sinnott; WR 13 T.Burks; QB 5 J.Daniels; RB 1 R.White",
  "starter:Defense":"OLB 98 O.Oweh; DT 97 T.Settle; DT 96 S.Tuttle; OLB 45 K.Chaisson; LB 52 S.Styles; LB 4 F.Luvu; CB 23 T.Amos; CB 2 A.Robertson; S 39 J.Reaves; S 25 N.Cross; S 20 Q.Martin",
  "sub:":"CB 0 M.Sainristil; WR 3 S.Diggs; P 10 T.Way; WR 11 L.McCaffrey; WR 12 V.Jefferson; S 18 T.Owens; K 19 D.Stevens; CB 24 F.Moreau; CB 29 R.Douglas; RB 30 A.Ekeler; RB 34 R.Henry; S 35 P.Butler; OL B 48 J.Josephs; LB 51 A.Kaho; LB 56 K.Medrano; LB 58 J.Magee; LS 69 T.Ott; T/G 71 A.Wylie; TE 85 C.Okonkwo; DE 90 C.Omenihu; DE 91 D.Wise; OL B 92 D.Armstrong; DT 95 J.Newton",
  "dnp:":"QB 8 M.Mariota; C/G 61 J.Good-Jones; C 66 M.Gulbin",
  "inactive:":"3QB 16 A.Kaliakmanis; CB 37 I.Yiadom; DT 50 R.Barber; G 62 T.Togiai; G 63 L.Patrick; TE 80 C.Yankoff"},
 "NYG": {
  "starter:Offense":"WR 17 D.Mooney; TE 84 T.Johnson; LT 78 A.Thomas; LG 76 J.Runyan; C 60 B.Hudson; RG 65 F.Mauigoa; RT 72 J.Eluemunor; WR 1 M.Nabers; TE 9 I.Likely; QB 18 J.McCarthy; RB 44 C.Skattebo",
  "starter:Defense":"OLB 5 K.Thibodeaux; DL 93 S.Harris; DL 97 B.Jamison-Travis; DL 98 D.Reader; OLB 3 A.Carter; LB 41 M.McFadden; LB 52 A.Reese; CB 20 G.Newsome; CB 2 D.Banks; S 8 J.Holland; S 24 A.Washington",
  "sub:":"CB 12 C.Hood; P 15 J.Stout; QB 19 J.Winston; CB 22 A.Phillips; S 25 J.Pinnock; RB 26 D.Singletary; S 27 T.Nubin; DB 28 E.Campbell; RB 30 G.Desrosiers; CB 31 N.Jones; K 34 D.Zvada; FB 45 P.Ricard; LB 46 Z.Barnes; OL 48 T.Ford; LB 51 J.Kelly; LB 55 C.Martin; LS 58 B.Mann; OL 64 A.Stinnie; OL 71 M.Mbow; WR 81 J.Hyatt; TE 85 C.Manhertz; WR 88 M.Fields; WR 89 C.Jones; DL 91 D.Alexander; OL B 96 D.Smoot",
  "dnp:":"C 61 J.Schmitz",
  "inactive:":"CB 21 P.Adebo; CB 35 N.Reed; LB 54 M.Harrison; OL 67 J.Sills; OL 74 J.Davis; TE 86 T.Fidone; DL 99 B.Okoye"}},
"NEDET": {
 "info": dict(date="2026-11-15", away="NE", home="DET", ap=10, hp=35,
   stadium="Allianz Arena", city="Munich, Germany", roof="Open Stadium",
   surface="Natural Grass", weather="Cloudy", temp=52, hum=51,
   wind_dir="SE", wind_mph=3, chill="", att=70225,
   gc="https://www.nfl.com/games/patriots-at-lions-2026-reg-10",
   pdf="https://static.www.nfl.com/image/upload/v1794829721/gamecenter/ab582c2f-4feb-11f1-abca-2c54536568a9.pdf"),
 "NE": {
  "starter:Offense":"LT 66 W.Campbell; LG 70 G.Van Roten; C 55 J.Wilson; RG 65 M.Pryor; RT 76 M.Moses; TE 85 H.Henry; TE 82 E.Raridon; QB 10 D.Maye; RB 38 R.Stevenson; WR 1 A.Brown; WR 13 M.Hollins",
  "starter:Defense":"OLB 5 Dr.Jones; DT 97 M.Williams; DT 94 C.Durden; OLB 91 E.Ponder; LB 14 R.Spillane; LB 53 C.Elliss; CB 0 C.Gonzalez; CB 25 M.Jones; CB 22 C.Woods; S 4 C.Woodson; S 31 K.Byard",
  "sub:":"WR 3 D.Douglas; K 8 A.Borregales; RB 9 C.Kiner; QB 16 T.DeVito; WR 18 K.Williams; P 19 M.Wishnowsky; CB 21 K.Prunty; S 23 J.Reed; CB 29 C.Canada; S 33 M.Brown; RB 34 L.Larison; TE 36 C.Latu; FB 44 R.Gilliam; LS 47 J.Ashby; LB 48 N.Obiazor; LB 49 E.Hunter; LB 50 G.Jacas; T 52 M.Bryant; LB 54 D.Muasau; G 67 A.Rupcich; T 74 C.Lomu; WR 86 E.Chism; DT 90 C.Barmore; DT 92 J.Farmer; DL 93 L.Taylor; DT 99 Da.Jones",
  "dnp:":"",
  "inactive:":"CB 7 C.Davis; 3QB 15 B.Morton; S 41 B.Schooler; T 68 D.Crownover; OL 72 W.Rouse; C 77 B.Brown"},
 "DET": {
  "starter:Offense":"WR 18 I.TeSlaa; TE 87 S.LaPorta; LT 58 P.Sewell; LG 73 C.Mahogany; C 70 J.Scruggs; RG 69 T.Ratledge; RT 76 B.Miller; WR 1 J.Williams; WR 14 A.St. Brown; QB 16 J.Goff; RB 0 J.Gibbs",
  "starter:Defense":"DE 97 A.Hutchinson; DL 54 A.McNeill; DL 91 T.Williams; DL 93 T.Lacy; LB 53 T.Nowaske; LB 44 M.Rodriguez; LB 55 D.Barnes; DB 32 B.Branch; CB 23 R.Ya-Sin; CB 21 R.McCreary; S 36 C.Clark",
  "sub:":"CB 2 E.Rakestraw; P 3 J.Fox; DB 5 C.Izien; DE 8 D.Moore; QB 11 J.Dobbs; WR 17 T.Martin; RB 25 J.Saylors; S 28 A.Cisco; CB 30 K.Dorsey; RB 33 S.Vaki; LB 35 J.Bachie; CB 38 N.Whiteside; K 39 J.Bates; LB 40 K.Britt; LS 49 H.Hatten; DL 50 S.Gill-Howard; LB 51 O.Pappoe; C 65 S.McLaughlin; DE 66 E.O'Neill; OL 71 M.Frazier; OL 79 L.Borom; TE 83 T.Conklin; WR 86 D.Carter; TE 89 B.Wright; DL 95 L.Onwuzurike; DE 98 D.Wonnum",
  "dnp:":"",
  "inactive:":"CB 4 D.Reed; CB 6 K.Abney; LB 57 A.Ogbongbemiga; C 64 C.Mays; DL 94 M.Wingo; DE 99 A.Hassanein"}},
"KCATL": {
 "info": dict(date="2026-11-15", away="KC", home="ATL", ap=35, hp=13,
   stadium="Mercedes-Benz Stadium", city="Atlanta, GA", roof="Retractable Roof - Closed",
   surface="Field Turf", weather="", temp="", hum="",
   wind_dir="", wind_mph="", chill="", att=72045,
   gc="https://www.nfl.com/games/chiefs-at-falcons-2026-reg-10",
   pdf="https://static.www.nfl.com/image/upload/v1794829722/gamecenter/ab582f5b-4feb-11f1-abca-2c54536568a9.pdf"),
 "KC": {
  "starter:Offense":"WR 1 X.Worthy; TE 87 T.Kelce; LT 70 K.Benson; LG 76 K.Suamataia; C 52 C.Humphrey; RG 65 Tr.Smith; RT 73 J.Ezeudu; TE 83 N.Gray; WR 4 R.Rice; RB 10 E.Johnson; QB 15 P.Mahomes",
  "starter:Defense":"DE 56 G.Karlaftis; NT 92 K.Tonga; DT 95 C.Jones; DE 91 F.Anudike-Uzomah; LB 43 J.Cochrane; LB 23 D.Tranquill; LB 32 N.Bolton; DB 27 C.Conner; DB 20 N.Williams; CB 5 M.Delane; S 17 A.Gilman",
  "sub:":"QB 6 J.Fields; K 7 H.Butker; CB 8 K.Fulton; WR 11 J.Royals; WR 12 J.Downs; WR 13 C.Allen; P 14 M.Araiza; DB 21 J.Hicks; DB 22 J.Canady; S 29 X.Nwankpa; CB 30 C.Roland-Wallace; LB 31 J.Bassa; RB 35 N.Carter; LS 41 J.Winchester; LB 44 C.McDonald; DE 51 R.Thomas; T 61 D.Pounds; OL 64 H.Nourzad; OL 66 M.Caliendo; WR 82 J.De Jesus; WR 85 A.Armstrong; TE 88 J.Briningstool; TE 89 J.Wiley; DT 94 B.Eason; DT 96 M.Harris; DE 97 A.Gillotte",
  "dnp:":"RB 9 K.Walker; 3QB 19 G.Nussmeier; RB 34 J.Ott; CB 39 M.Smith; FB 47 B.VanSumeren; OL 77 J.Moore; DL 99 P.Woods",
  "inactive:":"ILB 0 D.Deablo; CB 12 Av.Terrell; 3QB 13 A.Dalton; WR 17 Z.Branch; QB 18 J.Strand; CB 37 R.Longerbeam; T 73 C.Williams"},
 "ATL": {
  "starter:Offense":"WR 4 J.Dotson; TE 8 K.Pitts; LT 70 J.Matthews; LG 65 M.Bergeron; C 62 C.Levin; RG 63 C.Lindstrom; RT 71 J.Taylor; TE 89 C.Woerner; WR 5 D.London; QB 9 M.Penix; RB 7 B.Robinson",
  "starter:Defense":"DL 54 B.Dorlus; DL 92 M.Smith; DT 95 G.Dexter; DE 99 C.Thomas; LB 53 K.Daniels; LB 42 J.Woods; DB 29 S.Brown; CB 24 A.Terrell; CB 26 C.Henderson; S 23 D.Hellams; S 31 X.Watts",
  "sub:":"WR 14 O.Zaccheaus; P 16 J.Bailey; WR 19 C.Blair; CB 21 M.Hughes; LB 22 Y.Abdullah; RB 25 K.Herbert; DE 27 J.Pearce; CB 28 M.Ford; CB 33 B.Bowman; S 34 J.Robinson; K 39 J.Moody; LB 43 T.Quinn; LB 45 C.Harris; DE 47 C.Snowden; LS 49 L.McCullough; DE 55 Z.Smith; LB 56 H.Perkins; OL 68 K.Hinton; G 74 A.Vorhees; T 75 E.Onianwa; TE 81 A.Hooper; TE 87 N.Muse; WR 88 B.Collins; DL 94 L.London; DL 96 Z.Harrison",
  "dnp:":"QB 1 T.Tagovailoa",
  "inactive:":""}},
"HOUCL": {
 "info": dict(date="2026-11-15", away="HOU", home="CLE", ap=24, hp=27,
   stadium="Huntington Bank Field", city="Cleveland, OH", roof="Open Stadium",
   surface="Natural Grass", weather="Cloudy", temp=46, hum=75,
   wind_dir="NW", wind_mph=15, chill="", att=58342,
   gc="https://www.nfl.com/games/texans-at-browns-2026-reg-10",
   pdf="https://static.www.nfl.com/image/upload/v1794829724/gamecenter/ab583279-4feb-11f1-abca-2c54536568a9.pdf"),
 "HOU": {
  "starter:Offense":"WR 12 N.Collins; LT 79 A.Ersery; LG 64 F.Nwaiwu; C 63 E.Brown; RG 69 E.Ingram; RT 77 T.Brown; TE 86 D.Schultz; WR 14 K.Boutte; WR 19 X.Hutchinson; QB 7 C.Stroud; RB 4 W.Marks",
  "starter:Defense":"DE 90 J.Clowney; DT 72 T.Togiai; DT 98 S.Rankins; DE 51 W.Anderson; CB 24 D.Stingley; CB 3 K.Lassiter; LB 35 J.Hansen; LB 39 H.To'oTo'o; S 2 C.Bullock; S 5 J.Pitre; S 29 M.Stewart",
  "sub:":"WR 1 T.Dell; S 6 R.Blankenship; TE 8 C.Stover; CB 11 T.Smith; K 15 K.Fairbairn; S 20 J.Ingram; RB 21 E.Demercado; RB 23 D.Ogunbowale; S 27 K.Ramsey; LB 30 W.Woodaz; LB 33 J.Hummel; P 38 K.Kroeger; LS 40 A.Brinkman; LB 49 C.Muma; T 57 B.Fisher; C 60 J.Andrews; T 78 N.Thomas; TE 83 M.Klein; TE 87 F.Moreau; WR 88 N.Remigio; DT 91 N.Jones; DT 93 K.McDonald; DE 94 D.Robinson; DT 96 L.Hall",
  "dnp:":"QB 10 D.Mills; T 71 B.Smith",
  "inactive:":"LB 0 A.Al-Shaair; TE 9 B.Jordan; WR 18 M.Harrison; RB 32 D.Montgomery; DE 55 D.Hunter; C/G 66 K.Rutledge; G 75 W.Teller"},
 "CLE": {
  "starter:Offense":"TE 44 H.Fannin; LT 55 S.Fano; LG 77 Z.Johnson; C 74 E.Jenkins; RG 58 A.Barber; RT 71 T.Howard; TE 86 B.Whiteheart; WR 1 K.Concepcion; WR 12 D.Boston; QB 4 D.Watson; RB 10 Q.Judkins",
  "starter:Defense":"DE 8 J.Verse; DT 94 M.Graham; DT 96 M.Collins; DE 57 I.McGuire; LB 5 Q.Williams; LB 49 C.Schwesinger; CB 26 M.Harden; CB 21 D.Ward; CB 7 T.Campbell; S 28 E.McNeil-Warren; S 9 G.Delpit",
  "sub:":"WR 0 I.Bond; WR 3 J.Jeudy; WR 11 M.Corley; P 13 C.Bojorquez; WR 16 T.Wallace; RB 22 D.Sampson; S 24 D.Thomas; K 25 A.Szmyt; CB 29 M.Blackmon; S 31 D.McMillon; CB 35 T.Pride; RB 38 J.McLaughlin; LB 42 E.Mascarenas-Arnold; TE 48 C.Ryan; LS 50 R.Sunahara; DT 51 M.Hall; DE 54 S.Williams; C 56 L.Wypler; LB 59 W.Reid; G 70 Z.Zinter; T 79 D.Jones; TE 80 Z.Mitchell-Paden; DT 92 S.Kamara; DE 97 D.Barnett; DT 98 A.Huntington",
  "dnp:":"QB 2 S.Sanders",
  "inactive:":"3QB 6 D.Gabriel; QB 15 T.Green; LB 17 J.Jefferson; CB 20 N.Igbinoghene; S 33 R.Hickman; C 52 P.Brailsford"}},
"MINGB": {
 "info": dict(date="2026-11-15", away="MIN", home="GB", ap=30, hp=10,
   stadium="Lambeau Field", city="Green Bay, WI", roof="Open Stadium",
   surface="Natural Grass", weather="Sunny", temp=45, hum=51,
   wind_dir="NW", wind_mph=5, chill=42, att=78332,
   gc="https://www.nfl.com/games/vikings-at-packers-2026-reg-10",
   pdf="https://static.www.nfl.com/image/upload/v1794829721/gamecenter/ab788967-4feb-11f1-abca-2c54536568a9.pdf"),
 "MIN": {
  "starter:Offense":"TE 85 B.Yurosek; LT 71 C.Darrisaw; LG 60 J.Huber; C 64 B.Brandel; RG 76 W.Fries; RT 75 B.O'Neill; WR 18 J.Jefferson; WR 13 T.Felton; QB 8 K.Cousins; RB 33 A.Jones; FB 45 M.Bredeson",
  "starter:Defense":"OLB 15 D.Turner; DL 95 C.Banks; DL 50 L.Rodriguez; DL 61 J.Redmond; OLB 43 A.Van Ginkel; LB 0 I.Pace; LB 55 E.Wilson; CB 2 I.Rodgers; CB 7 B.Murphy; S 26 J.Jackson; S 44 J.Metellus",
  "sub:":"WR 4 M.Price; CB 5 Z.Vaughn; S 6 Jak.Thomas; K 16 W.Reichard; OLB 17 K.Van Noy; P 19 B.Thorson; CB 20 C.Demmings; S 22 H.Smith; CB 23 J.Pierre; S 24 J.Ward; RB 27 J.Mason; S 29 Jac.Thomas; RB 31 D.Dallas; OLB 32 C.Chambliss; LB 41 J.Golday; LS 42 A.DePaola; TE 48 D.Culp; C 65 M.Jurgens; T 72 R.Van Demark; T 78 C.Tiernan; WR 82 J.Jones; TE 86 G.Bartholomew; DL 97 D.Orange; OLB 98 B.Richter; DL 99 E.Williams",
  "dnp:":"QB 11 C.Wentz",
  "inactive:":"QB 1 K.Murray; WR 3 J.Addison; 3QB 12 M.Broser; WR 14 J.Jennings; LB 51 B.Cashman; TE 87 T.Hockenson; DL 90 T.Ingram-Dawkins"},
 "GB": {
  "starter:Offense":"WR 0 M.Golden; LT 77 J.Morgan; LG 72 L.Tomlinson; C 73 J.Williams; RG 79 T.Glover; RT 71 A.Belton; TE 85 T.Kraft; WR 9 C.Watson; TE 86 M.Redman; QB 10 J.Love; RB 30 C.Brooks",
  "starter:Defense":"EDGE 90 L.Van Ness; DT 94 K.Brooks; DT 95 D.Wyatt; DT 55 C.McClellan; EDGE 99 B.Sorrell; LB 58 I.McDuffie; LB 59 T.Hopper; CB 2 B.Cisse; CB 25 K.Nixon; S 29 X.McKinney; S 33 E.Williams",
  "sub:":"QB 6 T.Taylor; S 7 J.Bullard; WR 16 B.Melton; TE 18 J.Smith; P 19 D.Whelan; CB 21 B.St-Juste; WR 23 S.Moore; CB 24 C.Valentine; RB 26 K.Johnson; S 27 K.Oladapo; K 28 T.Smack; LB 31 N.Niemann; RB 32 M.Lloyd; CB 36 K.Hadden; LS 42 M.Orzech; TE 49 D.Dabney; DE 51 D.Dennis-Sutton; LB 54 K.Welch; DE J.Sturdivant; DT 93 A.Campbell; DT 97 J.Riley",
  "dnp:":"C/G 52 J.Burton",
  "inactive:":"RB 8 J.Jacobs; RB 22 P.Strong; LB 44 Z.Franklin; G/T 67 D.Jennings; G 70 K.Zeitler; C/G 75 S.Rhyan"}},
"MIAIND": {
 "info": dict(date="2026-11-15", away="MIA", home="IND", ap=22, hp=24,
   stadium="Lucas Oil Stadium", city="Indianapolis, IN", roof="Retractable Roof - Closed",
   surface="Field Turf", weather="Cloudy", temp=48, hum=61,
   wind_dir="N", wind_mph=6, chill=45, att=64235,
   gc="https://www.nfl.com/games/dolphins-at-colts-2026-reg-10",
   pdf="https://static.www.nfl.com/image/upload/v1794829723/gamecenter/ab789365-4feb-11f1-abca-2c54536568a9.pdf"),
 "MIA": {
  "starter:Offense":"WR 7 C.Douglas; LT 52 P.Paul; LG 74 K.Proctor; C 60 A.Meyer; RG 71 J.Savaiinaea; RT 73 A.Jackson; TE 85 G.Dulcich; FB 34 D.Herman; WR 6 M.Washington; QB 14 K.McCord; RB 0 O.Gordon",
  "starter:Defense":"DE 9 J.Uche; DL 94 J.Phillips; DL 78 K.Grant; DE 44 C.Robinson; ILB 10 J.Rodriguez; ILB 20 J.Brooks; CB 3 C.Johnson; CB 8 J.Brents; S 16 M.Taaffe; S 11 D.Trader; S 19 K.Louis",
  "sub:":"WR 1 J.Tolbert; CB 4 J.Marshall; RB 5 J.Wright; WR 21 K.Coleman; S 23 Z.Anderson; S 25 J.Wood; RB 30 K.Allen; K 31 Z.Gonzalez; CB 32 J.Simpson; ILB 40 W.Gay; ILB 42 J.Woodard; LB 45 S.Heyward; LS 46 T.Addington; P 48 B.Pinion; DE 58 J.Kromah; DE 59 R.McGraw; G/T 62 J.Kingston; T 79 C.Godrick; TE 83 S.Traore; WR 88 J.Reagor; TE 89 W.Kacmarek; DE 90 M.Herring; DL 93 Z.Biggers; DL 97 K.Cooper",
  "dnp:":"QB 15 B.Cook; G 64 C.Haynes",
  "inactive:":"WR 18 C.Bell; CB 24 M.Dial; C 55 A.Brewer; G/T 77 C.Wallace; TE 80 J.Joly; WR 86 J.Wayne"},
 "IND": {
  "starter:Offense":"WR 80 D.Burks; WR 13 L.Treadwell; TE 84 T.Warren; LT 79 B.Raimann; LG 62 J.Farmer; C 60 T.Bortolini; RG 68 D.Tucker; RT 71 M.Goncalves; WR 6 A.Gould; QB 17 D.Jones; RB 28 J.Taylor",
  "starter:Defense":"DE 98 A.Key; DT 74 K.Givens; DT 90 G.Stewart; DT 95 A.Adebawore; DE 97 L.Latu; LB 50 B.Boettcher; LB 53 C.Allen; CB 1 A.Gardner; CB 7 C.Ward; S 25 A.Haulcy; S 0 C.Bynum",
  "sub:":"K 3 S.Shrader; P 8 R.Sanchez; WR 12 N.Westbrook-Ikhine; WR 16 A.Dulin; RB 20 S.McGowan; RB 21 D.Giddens; CB 27 J.Walley; S 30 H.Wohler; CB 33 K.Harris; CB 34 K.Gushiken; S 38 J.Owens; LB 44 T.Chambers; LB 47 W.Weeks; LS 48 J.Bobenmoyer; TE 49 P.Brown; DE 52 G.Gumbs; DE 55 C.Curry; LB 58 A.Ajiake; C 63 S.Van Pran-Granger; T 67 L.Tenuta; TE 85 A.Ogletree; DE 91 J.Tuimoloau; DT 93 T.Smith",
  "dnp:":"QB 5 A.Richardson; WR 9 Q.Watkins; T 73 C.Heck",
  "inactive:":"3QB 15 R.Leonard; LS 46 L.Rhodes; LB 57 J.Carlies; T 75 J.Travis; TE 86 W.Mallory; DT 94 J.Tillery"}},
}
PART2 = {
"BUFNYJ": {
 "info": dict(date="2026-11-15", away="BUF", home="NYJ", ap=31, hp=12,
   stadium="MetLife Stadium", city="East Rutherford, NJ", roof="Open Stadium",
   surface="Field Turf", weather="Sunny, Cool, with Crisp Autumn Wind", temp=49, hum=54,
   wind_dir="NW", wind_mph=11, chill=44, att=82953,
   gc="https://www.nfl.com/games/bills-at-jets-2026-reg-10",
   pdf="https://static.www.nfl.com/image/upload/v1794829722/gamecenter/ab789ac9-4feb-11f1-abca-2c54536568a9.pdf"),
 "BUF": {
  "starter:Offense":"TE 88 D.Knox; LT 73 D.Dawkins; LG 70 A.Anderson; C 66 C.McGovern; RG 64 O.Torrence; RT 79 S.Brown; WR 0 K.Coleman; TE 86 D.Kincaid; WR 2 D.Moore; QB 17 J.Allen; RB 4 J.Cook",
  "starter:Defense":"OLB 15 G.Rousseau; DL 91 E.Oliver; DL 96 D.Walker; DL 94 L.Jackson; OLB 9 B.Chubb; ILB 8 T.Bernard; CB 23 D.Alford; CB 21 D.Igbinosun; CB 47 C.Benford; S 24 C.Bishop; S 22 A.Hooker",
  "sub:":"CB 1 M.Hairston; S 3 D.Hamlin; RB 7 R.Davis; WR 10 K.Shakir; QB 11 K.Allen; WR 13 S.Bell; K 16 T.Bass; WR 19 G.Dortch; RB 26 T.Johnson; DB 28 S.Franklin; DB 37 J.Hancock; P 39 T.Doman; ILB 42 D.Williams; ILB 44 J.Andreessen; LB 52 K.Elarms-Orr; C 53 L.Cushenberry; OLB 55 M.Hoecht; OLB 56 J.Solomon; G/C 63 A.Corbett; T/G 68 T.Grable; LS 69 R.Ferguson; TE 83 K.Latu; TE 85 J.Hawes; DL 90 D.Carter; DL 98 T.Sanders; OLB 99 T.Parker",
  "dnp:":"T 76 B.Freeland",
  "inactive:":"QB 6 S.Buechele; S 29 J.Kilgore; OLB 51 M.Danna; G 60 A.Reed-Adams; T/G 74 J.Bowry; DL 97 G.Gaines"},
 "NYJ": {
  "starter:Offense":"WR 5 G.Wilson; LT 74 O.Fashanu; LG 64 D.Parham; C 71 J.Myers; RG 66 J.Tippmann; RT 70 A.Membou; TE 85 M.Taylor; WR 11 O.Cooper; TE 16 K.Sadiq; QB 7 G.Smith; RB 20 B.Hall",
  "starter:Defense":"DE 52 K.Enagbare; DL 91 J.Briggs; DL 95 D.Jackson; DL 97 H.Phillips; DE 31 D.Bailey; LB 44 J.Sherwood; LB 56 D.Davis; CB 21 B.Stephens; CB 1 A.Thomas; S 6 D.Belton; S 29 M.Fitzpatrick",
  "sub:":"RB 0 B.Allen; RB 3 K.Nwangwu; DE 9 W.McDonald; QB 10 C.Klubnik; P 14 A.McNamara; WR 15 A.Mitchell; WR 18 I.Williams; K 19 J.Sanders; CB 23 D.Ponds; DB 26 N.Wright; DB 27 M.Moore; RB 32 I.Davis; S 34 V.Payne; CB 37 Q.Stiggers; LS 42 T.Hennessy; DE 46 J.Ossai; FB 47 A.Beck; LB 48 J.Keller; LB 50 T.Reeder; OL 67 J.Meredith; OL 79 C.Okorafor; WR 84 M.McClain; TE 89 J.Ruckert; DL 96 J.Heflin; DL 98 P.Page",
  "inactive:":"DB 2 J.Brownlee; WR 17 T.Patrick; LB 49 T.Wallace; TE 86 J.Woods; DE 92 N.Lynn",
  "dnp:":""}},
"JAXTEN": {
 "info": dict(date="2026-11-15", away="JAX", home="TEN", ap=40, hp=23,
   stadium="Nissan Stadium", city="Nashville, TN", roof="Open Stadium",
   surface="Field Turf", weather="Sunny", temp=50, hum=39,
   wind_dir="NE", wind_mph=4, chill=49, att=61239,
   gc="https://www.nfl.com/games/jaguars-at-titans-2026-reg-10",
   pdf="https://static.www.nfl.com/image/upload/v1794829722/gamecenter/ab789e15-4feb-11f1-abca-2c54536568a9.pdf"),
 "JAX": {
  "starter:Offense":"WR 3 J.Meyers; TE 85 B.Strange; LT 72 W.Little; LG 75 E.Pregnon; C 73 R.Hainsey; RG 76 E.Cleveland; RT 70 C.Van Lanen; WR 11 P.Washington; WR 7 Bri.Thomas; QB 16 T.Lawrence; RB 33 B.Tuten",
  "starter:Defense":"DE 41 J.Hines-Allen; DT 91 A.Armstead; DT 93 M.Dickerson; DE 44 T.Walker; LB 23 F.Oluokun; LB 51 V.Miller; CB 12 T.Hunter; CB 1 M.Brown; S 26 K.Merriweather; S 6 A.Johnson; S 25 R.Lane",
  "sub:":"CB 2 J.Lewis; CB 4 Jar.Jones; RB 5 L.Allen; P 9 L.Cooke; WR 19 J.Cameron; RB 20 A.Abdullah; S 22 J.Huskey; RB 24 C.Rodriguez; LB 31 J.Tavai; LB 35 J.Mcleod; CB 36 Jay.Jones; K 39 C.Little; LS 46 R.Matiscik; LB 47 D.Gardeck; LB 50 B.Combs; DE 57 Bry.Thomas; OL 60 J.Monheim; OL 64 W.Milum; OL 68 D.Faalele; TE 80 Q.Morris; TE 87 N.Boerkircher; TE 88 T.Koziol; DE 92 D.Striggow; DT 94 D.Godchaux; DT 99 R.Orhorhoro",
  "dnp:":"QB 10 Q.Ewers",
  "inactive:":"S 0 J.Bates; WR 18 C.Williams; DT 90 J.Davis; DE 97 W.Williams; DT 98 A.Regis"},
 "TEN": {
  "starter:Offense":"TE 82 D.Bellinger; TE 84 G.Helm; WR 17 C.Dike; LT 75 D.Moore; LG 76 C.Zavala; C 51 A.Schlottmann; RG 70 A.Mafi; RT 55 J.Latham; WR 5 E.Ayomanor; QB 1 C.Ward; RB 20 T.Pollard",
  "starter:Defense":"DE 57 J.Martin; DL 91 J.Franklin-Myers; DT 90 S.Thomas; DE 11 J.Johnson; LB 33 C.Gray; LB 54 D.Mausi; CB 25 Jo.Williams; CB 24 A.Taylor; CB 18 C.Flott; S 29 T.Adams; S 23 K.Winston",
  "sub:":"WR 0 C.Ridley; RB 2 T.Spears; WR 4 W.Robinson; K 6 J.Slye; DE 7 O.Oladejo; P 13 T.Morstead; DE 15 K.Faulk; CB 21 M.Robinson; CB 26 M.Harris; S 28 I.Oliver; RB 36 J.Chestnut; S 38 T.Burgess; LB 40 D.Hampton; LB 44 M.Diabate; LS 46 M.Cox; DE 56 T.Jones; T 59 J.Hudson; G 71 G.Dellinger; C 79 P.Coogan; TE 86 K.Granson; WR 87 X.Restrepo; TE 88 D.Martin-Robinson; DT 93 N.Stackhouse; DT 94 T.Horne; DT 99 J.Laulu",
  "dnp:":"QB 10 M.Trubisky",
  "inactive:":"WR 14 C.Tate; RB 32 N.Singleton; CB 42 J.Jones; LB 50 C.Barton; LB 53 A.Hill; T 78 B.Crenshaw-Dickson; DT 96 J.Marshall"}},
"PITCIN": {
 "info": dict(date="2026-11-15", away="PIT", home="CIN", ap=18, hp=38,
   stadium="Paycor Stadium", city="Cincinnati, OH", roof="Open Stadium",
   surface="Field Turf", weather="Partly Cloudy", temp=42, hum=78,
   wind_dir="NE", wind_mph=2, chill="", att=66860,
   gc="https://www.nfl.com/games/steelers-at-bengals-2026-reg-10",
   pdf="https://static.www.nfl.com/image/upload/v1794829727/gamecenter/ab78aa48-4feb-11f1-abca-2c54536568a9.pdf"),
 "PIT": {
  "starter:Offense":"WR 4 D.Metcalf; LT 76 T.Fautanu; LG 66 M.McCormick; C 54 Z.Frazier; RG 67 B.Hoffman; RT 71 M.Iheanachor; TE 80 D.Washington; TE 88 P.Freiermuth; WR 17 G.Bernard; QB 8 A.Rodgers; RB 30 J.Warren",
  "starter:Defense":"LB 56 A.Highsmith; DT 97 C.He yard; DT 95 K.Benton; LB 90 T.Watt; LB 41 P.Wilson; LB 6 P.Queen; CB 35 J.Dean; CB 22 A.Samuel; CB 5 J.Ramsey; S 28 R.Spears-Jennings; S 3 J.Brisker",
  "sub:":"QB 2 M.Rudolph; K 9 C.Boswell; WR 10 K.Wetjen; RB 13 R.Dowdle; WR 15 B.Skowronek; P 19 C.Johnston; RB 21 T.Homer; CB 23 D.Everette; CB 26 B.Echols; RB 31 L.Nichols; LB 33 J.Sawyer; FB 37 R.Nowakowski; DB 40 D.Slaughter; LB 44 C.Bruener; LS 46 C.Kuntz; LB 51 N.Herbig; LB 55 C.Holcomb; T 60 D.Cook; C 62 R.McCollum; OL 74 S.Anderson; TE 85 R.Tonyan; WR 87 B.Smith; DL 92 K.Jobity; DL 94 Y.Black; DE 96 G.Rubio; DT 99 D.Harmon",
  "dnp:":"",
  "inactive:":"QB 16 D.Allar; 3QB 18 W.Howard; S 25 D.Elliott; CB 27 S.Murphy-Bunting; RB/WR 29 E.Heidenreich"},
 "CIN": {
  "starter:Offense":"WR 1 J.Chase; LOT 75 O.Brown; LG 63 D.Fairchild; C 64 T.Karras; RG 66 D.Risner; ROT 71 A.Mims; TE 88 M.Gesicki; WR 81 D.Meyers; WR 5 T.Higgins; QB 9 J.Burrow; HB 30 C.Brown",
  "starter:Defense":"LDE 99 M.Murphy; DT 93 J.Allen; NT 97 D.Lawrence; DT 92 B.Hill; RDE 53 B.Mafe; LB 49 B.Carter; LB 44 D.Knight; CB 23 D.Hill; CB 0 D.Turner; S 6 B.Cook; S 27 J.Battle",
  "sub:":"K 2 E.McPherson; P 8 R.Rehkow; QB 16 J.Flacco; CB 20 T.Davis; S 22 R.Yeast; HB 25 T.Brooks; CB 28 J.Newton; HB 34 S.Perine; S 37 P.Jules; CB 38 D.Ivey; LB 42 O.Burks; LB 43 J.Giles-Harris; LB 45 J.Kiser; LS 46 W.Wagner; DE 52 C.Johnson; G 69 J.Bayer; T 73 J.Foster; G 74 J.Rivers; WR 82 M.Tinsley; TE 84 J.Endries; TE 85 C.Grandy; WR 86 C.Young; TE 89 D.Sample; DT 90 K.Jenkins; DE 94 S.Stewart; DT 98 T.Slaton",
  "dnp:":"",
  "inactive:":"S 29 K.Dugger; C 65 C.Lew; T 77 M.Hinton; DT 96 L.Robinson"}},
"SFDAL": {
 "info": dict(date="2026-11-15", away="SF", home="DAL", ap=46, hp=40,
   stadium="AT&T Stadium", city="Arlington, TX", roof="Retractable Roof - Closed",
   surface="Field Turf", weather="Rainy", temp=49, hum=86,
   wind_dir="NE", wind_mph=3, chill=49, att=90763,
   gc="https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10",
   pdf="https://static.www.nfl.com/image/upload/v1794829724/gamecenter/ab78a748-4feb-11f1-abca-2c54536568a9.pdf"),
 "SF": {
  "starter:Offense":"WR 19 D.Samuel; FB 44 K.Juszczyk; TE 85 G.Kittle; LT 71 T.Williams; LG 75 C.Colby; C 64 J.Brendel; RG 77 D.Puni; RT 68 C.McKivitz; WR 17 J.Watkins; QB 13 B.Purdy; RB 23 C.McCaffrey",
  "starter:Defense":"DL 97 N.Bosa; DL 99 D.Buckner; DL 92 O.Odighizuwa; DL 56 K.White; LB 57 D.Greenlaw; LB 54 F.Warner; DB 2 D.Lenoir; CB 20 U.Stout; CB 0 R.Green; S 27 J.Brown; S 6 M.Mustapha",
  "sub:":"WR 3 K.Allen; WR 4 J.Cowing; TE 9 B.Willis; WR 11 D.Robinson; P 15 C.Waitman; K 18 E.Pineiro; S 24 A.Davis; RB 26 K.Black; CB 28 E.Prysock; RB 29 J.James; DB 33 S.Neal; S 36 M.Sigle; LS 46 J.Weeks; DL 47 K.Kareem; LB 49 G.Wallow; LB 51 L.Gifford; LB 53 J.Dugger; DL 55 S.Valdez; OL 58 J.Patterson; OL 74 C.Willis; OL 76 V.Lowe; TE 89 L.Farrell; DL 94 R.Height; DL 96 J.Thompson; DL 98 M.Williams",
  "dnp:":"QB 10 M.Jones",
  "inactive:":"WR 5 M.Evans; 3QB 14 K.Rourke; LB 48 T.Bethune; OL 69 E.Cruz; WR 84 B.Cooks"},
 "DAL": {
  "starter:Offense":"WR 88 C.Lamb; WR 19 R.Flournoy; LT 60 T.Guyton; LG 73 T.Smith; C 56 C.Beebe; RG 52 T.Booker; RT 78 T.Steele; TE 89 B.Spann-Ford; WR 3 G.Pickens; QB 4 D.Prescott; RB 33 J.Williams",
  "starter:Defense":"OLB 40 ; DT 92 ; DT 97 ; OLB 7 ; LB 53 ; LB 50 ; DB 13 ; CB 25 ; CB 26 ; S 14 ; S 24 ",
  "sub:":"LB 0 D.Overshown; CB 2 C.Durant; P 5 B.Anger; WR 9 K.Turpin; S 11 A.Clark; K 17 B.Aubrey; CB 23 A.Speed; CB 28 S.Revel; FB 30 H.Luepke; OL B 35 J.Barron; LB 55 J.Barham; G 66 T.Bass; T 67 D.Shelton; T 77 B.Jones; WR 80 C.Brown; TE 84 J.Mitchell; TE 86 L.Schoonmaker; DT 90 J.Bullard; DT 91 O.Ogbonna; DT 93 E.Garcia; DT 99 L.Overton",
  "dnp:":"QB 16 S.Howell",
  "inactive:":"S 1 P.Locke; OL B 6 D.Ezeiruaku; CB 15 D.Kendrick; WR 18 J.Mingo; S 43 J.Thomas; T 65 A.Cornelius; TE 87 J.Ferguson"}},
}

PART3 = {
"CARNO": {
 "info": dict(date="2026-11-15", away="CAR", home="NO", ap=20, hp=17,
   stadium="Caesars Superdome", city="New Orleans, LA", roof="Closed Stadium",
   surface="Field Turf", weather="", temp="", hum="",
   wind_dir="", wind_mph="", chill="", att=70019,
   gc="https://www.nfl.com/games/panthers-at-saints-2026-reg-10",
   pdf="https://static.www.nfl.com/image/upload/v1794829721/gamecenter/ab789769-4feb-11f1-abca-2c54536568a9.pdf"),
 "CAR": {
  "starter:Offense":"TE 88 D.Waller; LT 63 R.Walker; LG 68 D.Lewis; C 77 L.Fortner; RG 50 R.Hunt; RT 57 M.Freeling; TE 82 T.Tremble; WR 18 J.Coker; WR 4 T.McMillan; QB 9 B.Young; RB 30 C.Hubbard",
  "starter:Defense":"OLB 91 P.Jones; DT 98 T.Wharton; DT 95 D.Brown; OLB 5 J.Phillips; LB 33 T.Dodson; LB 55 D.Lloyd; CB 26 C.Smith-Wade; CB 35 M.Wilson; S 20 Z.Wheatley; S 7 T.Moehrig; S 21 N.Scott",
  "sub:":"OLB 3 P.Umanmielen; P 6 S.Martin; K 10 R.Fitzgerald; WR 13 J.Metchie; WR 17 X.Legette; S 22 L.Ransom; RB 23 T.Etienne; S 27 I.Simmons; CB 31 C.Thornton; RB 34 A.Tyus; CB 36 M.DeWalt; OLB 39 N.Hampton; LS 44 J.Jansen; LB 46 J.Kuwatch; OLB 52 T.Gipson; LB 54 B.Martin-Scott; G 65 T.Simpkins; T 67 C.Bullock; T 73 S.Forsythe; TE 81 F.Franks; TE 84 M.Evans; WR 87 B.Tremayne; DT 92 L.Hunter; DT 94 A.Hall; DT 97 B.Brown",
  "inactive:":"TE 0 J.Sanders; 3QB 16 H.King; CB 24 W.Lee; RB 28 A.Dillon; LB 58 B.Okereke; C 75 S.Hecht; DT 93 T.Edwards"},
 "NO": {
  "starter:Offense":"TE 83 J.Johnson; TE 87 N.Fant; LT 71 K.Banks; LG 76 D.Edwards; C 51 C.Ruiz; RG 65 J.Wright; RT 72 A.Richards; WR 14 D.Vele; WR 12 C.Olave; QB 6 T.Though; RB 3 T.Etienne",
  "starter:Defense":"DE 99 C.Young; DL 93 N.Shepherd; DL 91 V.Broughton; DE 96 C.Granderson; LB 55 K.Elliss; LB 20 P.Werner; CB 22 M.Emerson; CB 1 K.McKinstry; S 23 J.Blackmon; S 21 J.Reid; S 7 J.Sanker",
  "sub:":"WR 0 J.Tyson; TE 4 O.Delp; P 17 R.Wright; WR 18 B.Lance; WR/RS 19 B.Brown; CB 25 D.Richardson; LB 28 D.Stutsman; CB 29 Q.Riley; RB 30 A.Estime; DB 31 J.Howden; DE 33 A.Jennings; DB 36 L.Styles; K 39 C.Smyth; RB 41 A.Kamara; LB 44 I.Stalbird; LS 49 Z.Wood; DL 50 C.Wooden; LB 58 C.Rumph; G 66 W.Sherman; T 73 E.Kilty; T 74 M.Murphy; DE 94 C.Jordan; DL 95 J.Ridgeway; DL 97 K.Boyd; DE 98 T.Wilson",
  "inactive:":"3QB 11 Z.Wilson; S 42 M.Reid; RB 43 C.Donaldson; LB 53 J.Ford; T 75 T.Fuaga; C 78 E.McCoy"}},
"LARARI": {
 "info": dict(date="2026-11-15", away="LAR", home="ARI", ap=34, hp=6,
   stadium="State Farm Stadium", city="Glendale, AZ", roof="Retractable Roof - Open",
   surface="Natural Grass", weather="Sunny", temp=75, hum=44,
   wind_dir="E", wind_mph=3, chill="", att=60926,
   gc="https://www.nfl.com/games/rams-at-cardinals-2026-reg-10",
   pdf="https://static.www.nfl.com/image/upload/v1794854921/gamecenter/ab78a133-4feb-11f1-abca-2c54536568a9.pdf"),
 "LAR": {
  "starter:Offense":"WR 4 K.Mumpfield; LT 77 A.Jackson; LG 50 B.Limmer; C 65 C.Shelton; RG 69 K.Dotson; RT 71 W.McClendon; WR 14 X.Smith; WR 6 C.Daniels; QB 9 M.Stafford; RB 24 B.Corum; RB 23 K.Williams",
  "starter:Defense":"OLB 95 M.Garrett; DE 99 A.Donald; DE 90 T.Davis; DE 55 B.Fiske; OLB 0 B.Young; ILB 48 O.Speights; ILB 53 N.Landman; CB 30 J.Wallace; CB 22 T.McDuffie; S 37 Q.Lake; S 3 K.Curl",
  "sub:":"CB 1 E.Forbes; S 2 J.McCollough; S 5 K.Kinchens; WR 8 T.Atwell; OLB 10 J.Stewart; K 16 J.Karty; K 19 B.McManus; RB 20 R.Rivers; CB 21 C.Lampkin; CB 26 D.Williams; P 42 E.Evans; LS 43 J.McQuade; ILB 44 G.Stuard; OLB 47 W.Bailey; DE 52 L.Murchison; ILB 56 S.Dolac; NT 57 T.Hamilton; OL 63 D.McMahon; OL 66 B.Murray; OL 68 D.Quessenberry; WR 81 B.Presley; TE 84 C.Parkinson; TE 86 M.Klare; TE 87 D.Allen; TE 89 T.Higbee",
  "dnp:":"QB 13 S.Bennett",
  "inactive:":"3QB 15 T.Simpson; S 36 M.Pulley; LS 49 J.Cardona; OLB 59 D.Peterson; OL 73 S.Avila; OL 79 K.Trost; OLB 94 D.Johnson"},
 "ARI": {
  "starter:Offense":"WR 80 S.Fehoko; TE 84 E.Higgins; TE 89 H.Long; LT 78 J.Fryar; LG 73 I.Seumalo; C 58 H.Conner; RG 74 I.Adams; RT 65 E.Wilkinson; TE 85 T.McBride; QB 19 C.Beck; RB 22 T.Allgeier",
  "starter:Defense":"OLB 10 J.Sweat; DT 97 W.Nolen; DT 55 D.Stills; OLB 25 Z.Collins; ILB 50 J.Gibbons; ILB 1 Ma.Wilson; CB 35 K.King; CB 29 D.Burke; CB 13 K.Clark; S 28 A.Wingard; S 3 B.Baker",
  "sub:":"ILB 0 C.Simon; OLB 5 B.Browning; WR 7 Z.Jones; P 12 B.Gillikin; CB 16 M.Melton; RB 20 Z.Knight; CB 21 G.Williams; RB 26 E.Hull; S 36 K.Crawford; K 38 C.Ryland; S 42 D.Taylor-Demerson; ILB 43 K.Sharar; TE 47 T.Quitoriano; DL 51 R.Lopez; OLB 52 J.Burch; DL 56 D.Robinson; LS 59 C.Kreiter; OL 64 K.Eguakun; OL 79 J.Wills; WR 81 D.Duvernay; WR 82 R.Virgil; WR 83 H.Wallace; DL 91 L.Collier; DL 95 A.Billings",
  "dnp:":"QB 9 J.Johnson; OL 76 A.Reese",
  "inactive:":"3QB 18 J.Aguilar; CB 24 S.Thomas; OLB 54 E.Leota; OL 66 J.Williams; OL 71 J.Gaines; OL 72 H.Froholdt"}},
"SEALV": {
 "info": dict(date="2026-11-15", away="SEA", home="LV", ap=21, hp=13,
   stadium="Allegiant Stadium", city="Las Vegas, NV", roof="Closed Stadium",
   surface="Natural Grass", weather="Cloudy", temp=65, hum=40,
   wind_dir="NE", wind_mph=6, chill="", att=62624,
   gc="https://www.nfl.com/games/seahawks-at-raiders-2026-reg-10",
   pdf="https://static.www.nfl.com/image/upload/v1794829726/gamecenter/ab78a43c-4feb-11f1-abca-2c54536568a9.pdf"),
 "SEA": {
  "starter:Offense":"WR 11 J.Smith-Njigba; WR 10 C.Kupp; TE 81 E.Saubert; LT 74 J.Jones; LG 76 G.Zabel; C 61 J.Sundell; RG 75 A.Bradford; RT 72 A.Lucas; TE 88 A.Barner; QB 2 D.Lock; RB 26 Z.Charbonnet",
  "starter:Defense":"DE 91 B.Murphy; DE 90 J.Reed; LB 0 D.Lawrence; LB 58 D.Hall; LB 32 D.Thomas; LB 13 E.Jones; CB 21 D.Witherspoon; CB 29 J.Jobe; S 3 N.Emmanwori; S 39 T.Okada; S 20 J.Love",
  "sub:":"",
  "dnp:":"QB 6 J.Milroe; C 55 O.Oluwatimi",
  "inactive:":"QB 14 S.Darnold; RB 23 E.Wilson; CB 27 A.Smith; G 53 Q.Nelson; T 67 C.Cross; NT 97 D.Eastern; DT 99 L.Williams"},
 "LV": {
  "starter:Offense":"TE 89 B.Bowers; LT 74 K.Miller; LG 70 S.Burford; C 65 T.Linderbaum; RG 66 T.Zuhn; RT 71 D.Glaze; TE 87 M.Mayer; WR 1 T.Tucker; QB 15 F.Mendoza; FB 34 C.Heyward; RB 2 A.Jeanty",
  "starter:Defense":"DE 95 K.Paye; DT 94 F.Fatukasi; DT 69 A.Butler; DE 98 M.Crosby; LB 17 N.Dean; LB 7 Q.Walker; CB 35 H.Masses; CB 3 T.Johnson; CB 5 E.Stokes; S 11 J.Chinn; S 31 T.Stukes",
  "sub:":"",
  "dnp:":"QB 12 A.O'Connell",
  "inactive:":"WR 10 D.Thornton; WR 19 M.Benson; S 27 T.McCollum; S 43 D.Johnson; G 77 B.Cabeldue; DT 99 T.Booker"}},
}
ROSTERS.update(PART2); ROSTERS.update(PART3)
