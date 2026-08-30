# Piecehunt (legacy design archive)

> Historical note: this document reflects the original project concept and older architecture. It is no longer the active reference for the current application. The current project documentation is in [README.md](README.md), and the current development state is documented in [changelog.md](changelog.md).

## Korte beschrijving project

Als je een berg lego hebt en alle sets door mekaar zitten is het niet evident om alles terug te sorteren per set.  
De App heeft de focus op het compleet maken van elke lego set.  
Je kan hiermee gestrucureerd bijhouden welke steentjes je al hebt gevonden en welke nog moeten worden gevonden.  
De voortgang wordt dan opgeslagen, ook voor meedere sets tegelijkertijd.  
De vooruitgang wordt bijgehouden in de databank en kan steeds worden verdergezet.

---
---
# 1. Use Case/ App overzicht

## 1.1 Registratie / login
Bij het opstarten van de applicatie krijgt de gebruiker een beginscherm te zien (welkomscherm).
Als de gebruiker verbonden is met internet wordt er ook gecheckt en aangeboden om een database update uit te voeren.
Hierna zijn er 3 opties, login, registratie of account verwijderen.

### 1.1.1 Registratie
Als de gebruiker nog niet is geregistreerd zal hij zich eerst moeten aanmelden door op de register knop te duwen.  
Hier komt hij dan in een nieuw scherm terecht met in te vullen gegevens (username, email en paswoord + paswoord herhalen).  
Ook moet de gebruiker (GDPR gewijs) akkoord gaan met de voorwaarden om zich te kunnen registreren.  
Het akkoord + timestamp wordt opgeslagen in de database.    
Deze voorwaarden worden duidelijk weergegeven in een pop-up venster.    
Bij het submitten wordt er dan meteen nagegaan of alle gegevens zijn ingevuld en of beide paswoorden gelijk zijn.  
In de backend wordt dan nog het volgende gecontroleerd:
- Username : Minimum lengte. Bestaat de username al in de database.
- Email : Valabel email adres check met regex. Bestaat het al in de database.
- Paswoord : Minimum lengte, letters en cijfers gebruikt.

Als de gebruiker een foutieve ingave doet of de username of email al in gebruik is dan opent er een pop-up scherm met de bijhorende foutmelding.  
De gebruiker kan dan opnieuw proberen.

Als alles correct is ingevuld en de gegevens zijn opgeslagen in de database krijgt de gebruiker een pop-up scherm met de melding dat de registratie geslaagd is.  
Er wordt ook een email naar de gebruiker gestuurd ter bevestiging van registratie.  
Hierna wordt de gebruiker doorgestuurd naar de login pagina. (Als extra bevestiging dat de registratie geslaagd is)

### 1.1.2 Login
Als de gebruiker al geregistreerd is en hij heeft op de login knop gedrukt, dan komt hij in het login scherm terecht.  
Hier kan hij zijn gebruikersnaam en paswoord ingeven.  
- Backend checkt of de gebruikersnaam bestaat en het paswoord klopt.
- Klopt een van beide niet krijgt de gebruiker een pop-up scherm met de melding dat de combinatie niet geldig is
- Klopt het wel wordt de gebruiker aangemeld en doorgestuurd naar het Sets scherm.  

Ook is er een optie voorzien in geval de gebruiker zijn wachtwoord vergeten is.     
Er wordt een emailadres gevraagd welk gecheckt wordt en indien het correct is qua structuur en bestaat in de database wordt er een 6-cijferige code gestuurd naar dit emailadres.   
In een volgende popup krijgt de gebruiker dan de mogelijkheid om aan de hand van deze code een nieuw wachtwoord in te stellen.  
Achter de schermen wordt de 6-cijferige code samen met een timestamp (15min geldig) opgeslagen in de database.

### 1.1.3 Delete Account
Als de gebruiker zijn account wenst te verwijderen kan dit via deze weg.    
De gebruiker geeft zijn gebruikersnaam en wachtwoord en wordt 2 keer om bevestiging gevraagd.

---

## 1.2 Sets bijvoegen / selecteren

In het sets scherm krijgt de gebruiker een overzicht van de sets die hij al heeft toegevoegd.  
Alle info ivm de set en vooruitgang is beschikbaar in de databank.  
Elke set komt dan op het scherm met volgende info:
- Afbeelding van de set (locaal opgeslagen na aanmaak)
- Nummer van de set
- Naam van de set
- Progressie in percentage (database houdt bij welke stukjes al zijn gevonden)
- Bij hover over de settile veranderd de achtergrond en het muisicoon om duidelijk te maken dat deze klikbaar is.
- Om sorteren te straten / verder te zetten volstaat links klikken op de tegel --> Sorteer scherm
- Bij rechtermuisklik zijn er nog enkele andere mogelijkheden: Set Verwijderen, Set Compleet maken, Set Resetten, Set Opzoeken op enkele websites (lego, rebrickable, bricklink)

Steeds is er ook een knop aanwezig om een nieuwe set toe te voegen.  
Als er nog geen sets zijn zal dat ook het enige zijn dat de gebruiker initieel te zien krijgt, eventueel wel een korte boodschap dan op het scherm om de gebruiker welkom te heten / woordje uitleg te geven.  

Bij knop toeveoegen set:    
- Bestaat de set in de database en is deze nog niet toegevoegd.
- Voor alle afbeeldingen wordt er eerst nagegaan of ze al locaal zijn opgeslagen alvorens de download te initiëren.
- De afbeelding van de set wordt gedownload en locaal opgeslagen (url staat in database).  
- Alle afbeeldingen van de individuele steentjes (combo vorm + kleur) van die set worden ook gedownload en locaal opgeslagen (1ste poging via de url in de database, 2de poging via een andere website met nieuw samengestelde url, 3de poging via dezelde website als de 2de poging maar een alternatieve url)
- De steentjes worden dan met het juiste aantal in de database toegevoegd aan de usersets waar de voortgang gaat worden bijgehouden.   
- De minifigs staan apart in de database, er is wel een link met welke minifigs er in welke set zitten en hoeveel van elk.
- De afbeeldingen van de complete minifigs worden gedownload (via url in de database, geen alternatief want deze hebben geen universele nummer of omschrijving).
- De afbeeldingen van de individuele onderdelen van elke minifig worden ook nog gedownload op dezelfde wijze als de steentjes.
- De onderdelen van de minifigs worden dan ook toegevoegd met het juiste aantal aan de usersets.    
- Voor alle afbeeldingen wordt er ook meteen een kleinere afbeelding aangemaakt op maat van de gui om alles later vlotter te laten verlopen.
(de afbeeldingen verkleinen gebeurt ook met wx, dat gaf met voorsprong het beste en snelste resultaat boven packages zoals Pillow)
- Tijdens de download wordt er een statusbar weergegeven met de vooruitgang als progress bar en het aantal afgeronde tov het totaal nieuwe afbeeldingen.
- De download gebeurt in een aparte thread om de vooruitgang te kunnen blijven weergeven. 
- De downloads zelf gebeuren ook multithreaded binnen eenzelfde connection met httpx waardoor de vooruitgang supersnel is. (momenteel gelimiteerd op 5 workers om geen timeout te krijgen van de extrene server)

De locale opslag is noodzakelijk om ook offline te kunnen werken.  
Indien geen probleem met de download wordt de set toegevoegd aan het scherm.  
Indien er iets mis loopt komt er een pop-up scherm met bijhorende melding.  

- Bestaat de set niet in de database:   
Pop-up melding met de boodschap dat de set niet bestaat. 
- Is de set al toegevoegd:
Pop-up melding met de boodschap dat de set al is toegevoegd.

Bij elke set op het scherm komt de naam van de set, de afbeelding, en ook een progress bar. Deze geeft weer hoeveel procent van de set al compleet is. Bovenaan het scherm is ook een knop om de reserve stukjes al dan niet mee te rekenen in dit percentage.      
Bij hoverer over de progress bar komt ook het percentage zelf tevoorschijn. 


Er is ook een knop om enkel de nog niet voltooide sets weer te geven of alle sets die de gebruiker reeds heeft toegevoegd. (houdt ook rekening met al dan niet de reserve stukjes)  




## 1.3 Sorteer Scherm
Hier komt de gebruiker terecht om uiteindelijk aan het werk te gaan nadat hij de set heeft gekozen om aan te werken.  

Bij het selecteren van de set worden alle tegels met de individuele steentjes aangemaakt.   

Alle tegels uit die set (staat in database als userset) hebben volgende:  
- Afbeelding van het steentje
- Op de afbeelding klikken voor een grotere afbeelding
- Naam van het steentje
- Aantal nodig in de set
- Aantal reeds gevonden
- plus en min knop om gevonden steentjes toe te voegen of te verwijderen (logica ingebouwd om geen foute ingave toe te laten)

Bovenaan het scherm zijn er ook nog enkele knoppen
- Een knop om enkel de onvolledige steentjes weer te geven 
- Een reeks van knoppen met alle kleuren die in die set voorkomen om enkel een bepaalde kleur weer te geven
- Een knop om alles of niets weer te geven
- Een knop om de minifiguurtjes weer te geven die in deze set voorkomen.

## 1.4 Menu Balk
Aan het hoofdscherm wordt er een menubalk toegevoegd in de native stijl van het besturingssysteem.  
Deze menubalk blijft steeds zichtbaar en beschikbaar bij het gebruik van de applicatie.

### 1.4.1 Main
- Back to homepage (uitloggen), disabled op homepage zelf
- Close Piecehunt (app afsluiten)

### 1.4.2 Update
- Check for updates : opent venster met huidige en nieuwe versie en optie om update te straten. Zie hoofdstuk 2.1
- Backup Data : mogelijkheid om een extra backup van de huidige databank te maken (bij elke update gebeurt dit reeds automatisch)
- Restore Previous Data : databank terugzetten naar een vorige versie, de gebruiker krijgt een overzicht van alle beschikbare backups

### 1.4.3 Help
- About : kort overzicht met versienummer en mogelijkheid om support te mailen
- Credits : dankwoorden

### 1.4.4 Instructions
- Get Instructions : enkel enabled als er nog geen instructies zijn opgehaald. zie hoofdstuk 2.2
- Instructions : links naar de opgehaalde pdf bestanden
- Show Stickered Parts : Opent een custom viewer met alle pagina's waar stickers worden aangebracht     
- In de custom viewer kan de gebruiker ook vals positieven doorgeven, deze worden naar de developer gestuurd om het model beter te trainen      

### 1.4.5 Reports
- Missing Parts Report : opent een scherm waar de gebruiker zijn sets kan zijn die hij heeft opgeslagen.    
De sets worden in een tabelvorm weergegeven met naam, nummer en voortgang.      
De gebruiker kan kiezen om al dan niet de reserve stukjes mee te rekenen.   
De gebruiker kan dan de sets selecteren waar hij een overzicht van de missende stukjes wil van krijgen.     
Hier kan de gebruiker dan ofwel een pdf ofwel een excel van opvragen alsook verzenden via email.    

Met dit overzicht kan de gebruiker dan aan de slag om de missende stukjes aan te kopen om zo zijn sets te vervolledigen.
---
---

# 2. Details gebruikte methodes / technologieën

## 2.0 GUI
Ik heb beslist om wxpython te gebruiken als gui.
- Native stijl van het besturingssysteem
- Iets klassieker dan de modernere opties
- Heel pythonic
- Heel goed ondersteund en stabiel
- Veel support en ervaringen van andere gebruikers
 
## 2.1 Database
Ik gebruik postgres als database en sqlalchemy om ze aan te spreken.
### 2.1.1 Database model
Het database model is opgebouwd als sqlalchemy orm.  
De opbouw van de database is gebaseerd op de csv files die beschikbaar zijn op rebrickable.  
Hier staan alle mogelijke lego sets, steentjes, kleuren, links naar afbeeldingen enzoverder in.  
De relaties zijn ook gelegd om van elke set de benodigde steentjes te raadplegen.   
Aangezien de database regelmatige updates krijgt is het ook niet mogelijk om de structuur van de database aan te passen.   
  
Naast de lego heb ik in de database ook user informatie toegevoegd.  
De persoonlijke gegevens van de gebruiker (username, paswoord_hash, email, tijdstip van registratie, tijdstip van laatste aanmelding, gdpr akkoord, reset_paswoord_code).  
De sets die de gebruiker heeft toegevoegd worden opgeslagen en wordt er bijgehouden welke steentjes de gebruiker al gevonden heeft.

### 2.1.2 Database update
De update wordt ofwel aangeboden bij opstart van de app of aangeroepen vanuit de menubalk.
-Eerst wordt er gecontroleerd of er niewe data is. (online versie-timestamp wordt vergeleken met lokale)    
- De nieuwe csv files worden gedownload van rebrickable (zip wordt uitgepakt) en opgeslagen
- Er wordt een backup gemaakt van de huidige database.  
- De user data wordt apart opgeladen om later terug te zetten.
- De volledige databse wordt leeggemaakt en terug geïnitialiseerd met het sqlalchemy model. 
- De nieuwe data wordt licht aangepast om compatibel te zijn met de databank en in de databank geschreven.  
- De user data wordt teruggezet.    
- De vooruitgang kan tijdens het proces worden gevolgd in een popup venster

---
## 2.2 Instructies ophalen
Instructies ophalen gebeurt via de menubalk en is beschikbaar van zodra de gebruiker een set heeft geselecteerd om mee te werken.   
- De instructies worden opgehaald in pdf formaat van lego.com.
- Instructies met meerdere boekjes per set worden ook mooi opgeslagen en apart weergegeven in de menustructuur.
- Gebruikte techlogieën om instructies op te halen:  httpx en BeautifulSoup     
- tijdens het ophalen van de instructies worden ook meteen de bestickerde steentjes gedetecteerd en de bewuste afbeeldingen worden lokaal opgeslagen en kunnen via het menu worden weergegeven. Zie volgende hoofdstuk 2.3
---
---
## 2.3 Beeldherkenning

In de lego handleidingen staan er vaak steentjes waar een sticker met een bepaalde afbeelding moet worden aangebracht.  
Maar in de inventaris van de onderdelen in de boekjes staan deze steentjes zonder sticker weergegeven.  
Dit is natuurlijk lastig als je een bestickert steentje nodig hebt en dit pas te weten komt tijdens het bouwen.  
Hiervoor heb ik al een model getraind en code opgezet die de images met stickers herkent en weergeeft.  
De code is nog steeds beschikbaar om het model verder te trainen indien nodig, maar het is reeds heel betrouwbaar.  

### 2.3.1 Technologieën
- PyMuPDF (fitz) : pdf omzetten naar jpg
- Ultralitics (Yolo) : model is getrained op het herkennen van de sticker icoontjes

## 2.4 Logging
- Python standaard logging module wordt gebruikt om verschillende niveaus te loggen.    

### 2.4.1 DEBUG
- Extra info die kan worden weergegeven als de app niet reageert zoals het hoort.     
 
### 2.4.2 INFO
- Grote handelingen.   
- bv: Account aangemaakt, Ingelogd, Uitgelogd Set toegevoegd/verwijderd

### 2.4.3 WARNING
- Mislukte loginpogingen. Verkeerd wachtwoord bij account verwijderen.

### 2.4.4 ERROR
- Afbeelding ontbreekt  
- Set kan niet worden toegevoegd of geladen
- Database fout

### 2.4.5 CRITICAL
- Database connectie weg
- App crasht in main loop

### 2.4.6 Ingestelde Handlers
- Console : DEBUG indien --debug flag bij start. Anders INFO en hoger
- Logbestand : WARNING en hoger
- Mail : ERROR en hoger


## 2.6 Niet eerder benoemde technologiën
- dotenv : gebruikersvariabelen veilig opslaan en ophalen
- base64 : gebruikersvariabelen maskeren in .env 
- werkzeug.security: passwoord hash maken en controleren
- pandas: dataframe aanmaken voor update database
- git / github : Versiebeheer en takenbord      
- reportlab : aanmaken van pdf documenten
- openpyxl : aanmaken van excel documenten
- SMTP (Simple Mail Transfer Protocol) : emails versturen
- Gmail SMTP Server (SMTP over SSL) : beveiligde email via gmail
- email.mime :  MIME-based email samenstelling
- Ruff Linter : uniform code 

---
---
# 3. Projectstructuur
Het project is grotendeels opgedeeld in enkele hoofdmappen:
- Backend
- Data
- Database
- Frontend
- Assets
- Models
- Logs
- Scripts   
- Tests

## 3.1 Backend
 Deze map bevat zoals verwacht de code die in de backend wordt uitgevoerd.  
 Hier zijn eveneens enkele opdelingen:
 - Handlers : Aparte klasses die elk hun deel van de backend op zich nemen, zoals instruction_handler, set_handler, part_handler, database_update_handler,...
 - email_service : Email sender functie die overal in de code kan worden gebruikt, in de sub map staan ook alle templates
 - helper :  Code die door verschillende handlers wordt gebruikt    
 - reports : Code om pdf en excel files te maken

 ## 3.2 Data
 Deze map bevat de data die de app bijhoudt eigen aan de gebruiker. Deze map is uitgesloten van de git.  
 
 -Instructions: Pdf files met instructies en ook de gevonden bestickerde pagina's.  
 -New_lego_data: Hier worden de nieuw gedownloadde csv files opgeslagen met nieuwe data om de databank te updaten   
 -Parts/Images: Hier komen de afbeeldingen van de afzonderlijke steentjes   
 -Sets/images: Hier komen de afbeeldingen van de verschillende sets     
 -Yolo: Hier staan de vals positieven die de gebruiker rapporteert      
 -Database_data : De oude versies van de databank aangemaakt door de gebruiker zelf of automatisch tijdend de update    
 -Reports: Gegenereerde PDF en Excel files


 ## 3.3 Database
 Hier staat het database model voor sqlalchemy  
 Ook staat hier de code om een database session te starten met verwijzing naar de gebruikte database  
 Ook staat hier de code om de database te droppen en te initialiseren
 De databank erd is hier ook beschikbaar 

 ## 3.4 Frontend
 Weer niet heel verrassend staat hier alle code die de frontend weergeeft.  
 Alle code gerelateerd aan wxpython  
 Er is ook een commom map met code die verschillende panels kunnen gebruiken    
 Alle schermen (panels) krijgen hun eigen map met bijhorende files per subpanel om het overzicht te bewaren.  
 
 Het hoofdscherm staat samen met de run_app in de app.py  

 ## 3.5 Models
 Hier staat het yolo model voor de beeldherkenning

 ## 3.6 Assets
 Dit zijn de achtergrondafbeeldingen, logo's, iconen, default afbeelding.

 ## 3.7 Logs
 Hier staat de logging config file welke indien gewenst kan aangepast worden.   
 Ook de log bestanden bevinden zich hier

 ## 3.8 Scripts
Code die niet rechtstreeks in de app wordt aangeroepen maar wel gebruikt is en later nog dienst kan doen.
bv: color mapping, gif resizer, line counter, functie om sqlalchemy model te maken van bestaande database   

## 3.9 Tests
Unit tests die de backend functionaliteiten testen

---
---

# 4. Geheime feature

Knipoog naar retro-style key generators:  
Door de combinatie CTRL+SHIFT+K in te drukken binnen de applicatie krijg je een retro style key generator met bijpassende muziek.   
Deze heeft verder geen enkele functie.        

---
--- 

# 5. Toekomstige Projecten

De huidige versie is erop gebaseerd om alles lokaal te runnen, zowel de lego database als de gebruikersdatabase.    
Ook is alles erop voorzien om gebruikers zich te laten aanmelden met de nodige beveiliging.    
Dit is deels zo ontworpen met het doel te dienen als schaalbaar en stabiel eindwerk.

Hier zijn enkele uitbreidingen en/of wijzigingen die gepland zijn of in aanbouw voor een volgende versie.

## 4.1 No login
Voor lokaal gebruik zou er niet perse een login met wachtwoord en email moeten gevraagd worden.      
Ik zou een versie maken waar er geen login en registratiescherm bestaat.    
In een welkomscherm zou een gebruiker kunnen worden aangemaakt met een gebruikersnaam en pictogram.     
De bestaande gebruikers worden dan weergegeven, met enkele details (aantal sets, achievements,..)   
Mogelijkheid open houden om vrijblijvend een simpele beveiliging met pincode toe te voegen.    
Via de pincode kan dan enkel de bevoegde gebruiker inloggen en de account verwijderen.

## 4.2 Client / Server
Momenteel moet je om de code te kunnen runnen enkele stappen ondernemen die voor de meeste mensen niet vanzelfsprekend zijn.    
Je moet ervoor zorgen dat je uv, python en postgres op de device hebt staan.    
Dan moet je nog een postgress database aanmaken (weliswaar een lege, maar dan nog).     
Een .env file aanmaken, een bricklink api code aanvragen en je credentials invullen, eventueel een email met app paswoord voor logging en mailing.  

De applicatie moet ook beschikbaar worden voor mensen die enkel de app willen opstarten en klaar.   
Om dit mogelijk te maken zijn er vooral op database schaal grote wijzigingen nodig.     
De lego data en app credentials komen dan op een server te staan.   
De gebruikersdata blijft lokaal bij de gebruiker in een aparte sqlite databank.     
Deze sqlite databank zal dan naast de gevonden stukken ook het totale aantal te zoeken stukken moeten bevatten,     
dit zorgt wel voor een hele aanpassing in de code maar zo kan de gebruiker offline werken.      
Enkel bij sets toevoegen dient de gebruiker online te zijn, wat sowieso nu ook al het geval is.     

Het ultieme doel is dan om een enkel uitvoerbaar bestand te maken welk de gebruiker kan uitvoeren.  

Door de Client/Server logica kan er ook toegang verleend worden, enkel aan geregistreerde gebruikers.      
(ook offline gebruik zou kunnen beperkt worden door een extra controle tussen server en client uit te voeren bij connectie en hier een limiet in te stellen) 

## 4.3 Nieuwe GUI
In een later stadium kan er bekeken worden om naast de huidige wxpython gui, die gebaseerd is op desktop gebruik,   
ook een mobiele app te ontwikkelen die compatibel is met tablet en smartphone.

## 4.4 Bestickerde onderdelen
In de huidige app is er al een mooie oplossing om de afbeeldingen terug te vinden waar de sticker wordt aangebracht en zo het juiste onderdeel te identificeren.    
Deze unieke feature heb ik nog nergens elders gevonden. 

Het zou leuk zijn om naast de pagina uit de handleiding echt de afbeeldingen van de uniek bestickerde stukjes te kunnen weergeven in de onderdelenlijst.    
Dit blijkt vooralsnog niet meteen haalbaar aangezien de onderdelen zelf zonder sticker in de onderdelenlijst staan als zijnde een gewoon stukje als de anderen.    

Er zijn online wel afbeeldingen terug te vinden van de bestickerde stukjes maar die zijn nooit rechtstreeks verbonden aan een specifieke lego set.      
