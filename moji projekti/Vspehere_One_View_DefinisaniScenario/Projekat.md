Procedura za patchovanje VCentar HP One View
VMvare 
skeniranje Sistema jednom dnevo I pracenje promena (razlike po danima)
- ugasene vrtualne masine
- alarmi na masinama, datastorovima, Host clusterima, Datastora clusteruma
- dnevni izvestaj
- Razlika izmedju izvestaja po danima, sedmicama, mesecni izvestaj
- Potrebno je uraditi Preseke

- HP One View skenirati konfiguraciju, 
1. Appliance (Sistemski nivo)
Pre bilo čega, proveravaš zdravlje samog OneView softvera.
Objekat: Appliance Node
Šta proveriti: Status servisa, iskorišćenost diska i verziju softvera (da li je u toku neki update).
2. Enclosures (Šasije)
Ovo je provera fizičkog "domaćina" za blejd servere.
Objekat: Enclosures
Šta proveriti: Status napajanja (Power), hlađenja (Fans) i da li su Onboard Administrator (OA) moduli ispravni.
3. Server Hardware (Fizički serveri) - 
Provera stanja svakog pojedinačnog "blejda" ili rack servera.
Objekat: Server Hardware
Šta proveriti: Status procesora, memorije, temperaturni senzori i iLO status.
4. Logical Interconnects (LI) – Aktivna mreža
Ovo je najbitnija stavka za proveru mrežne povezanosti.
Objekat: Logical Interconnects
Šta proveriti:
Uplink Ports: Da li su fizički linkovi ka core switch-u "Up".
Consistency: Da li je konfiguracija modula usklađena sa LIG-om (šablonom).
Telemetrija: Greške na portovima (CRC errors, drops).
5. Server Profiles (Identitet servera)
Provera da li serveri rade onako kako je planirano.
Objekat: Server Profiles
Šta proveriti:
Status: Da li je "Normal" ili "Warning". Firmware primenjen.
ConsistencyState: Da li profil odstupa od svog Template-a.
Connections: Da li su sve virtuelne NIC kartice u stanju "Connected".
6. Storage Systems & Volumes
Ako koristiš eksterni storage (npr. HPE Primera, 3PAR ili Alletra).
Objekat: Storage Volumes
Šta proveriti: Da li su volumeni ispravno mapirani na server profile i kakav je status putanja (Paths) do njih.
7. Logical Drive Settings (Lokalni RAID)
Objekat: Drive Enclosures / Logical Drives
Šta proveriti: Zdravlje fizičkih diskova unutar servera i status RAID polja.
8. Alerts & Events (Dnevnik grešaka)
Finalna provera svih aktivnih problema.
Objekat: Alerts
Šta proveriti: Filtriraj sve alerte koji su u stanju Active i imaju ozbiljnost Critical ili Warning.

- Napraviti izvestaj HTML.

Scenario 1

Patchovanje VMware I HP One view infrastructure
Pojedinanci Host u Host clusteru.
- Backup procedura.

Patchovanje ESXi hostova putem vCentera (koristeći
vSphere Lifecycle Manager - vLCM) je standardni proces koji osigurava stabilnost i sigurnost sistema.
Evo detaljnog vodiča kroz sve faze, od pripreme do završne verifikacije.

1. Pripremne radnje (Pre-checks)
Pre nego što uopšte pokrenete proces, morate osigurati "zdravlje" okruženja.
Backup: Osigurajte da imate aktuelan backup vCenter servera i konfiguracije hostova.
Provera resursa: Uverite se da preostali hostovi u clusteru imaju dovoljno CPU i RAM resursa da prihvate virtuelne mašine (VM) sa hosta koji ide u Maintenance Mode.
Provera vCenter verzije: vCenter uvek mora biti na istoj ili višoj verziji od ESXi verzije koju instalirate.
External Storage: Proverite da li su svi datastore-ovi dostupni i stabilni.
CD-ROM/ISO: Proverite da ni jedna VM nema "zakačen" lokalni ISO fajl (ovo može sprečiti migraciju mašina).

2. Priprema Patch-eva (Lifecycle Manager)
 Lifecycle Manager.
Sync Updates: Sync Updates da povučete najnovije definicije sa VMware portala.
Kreiranje Baseline-a (za starije verzije):
Provera Baselines.

3. Attachment i Analiza (Check Compliance)
Povezivanje i provera zakrpe sa hostom ili klasterom.
Idite na nivo Clustera ili pojedinačnog Hosta.
- Updates.
Check Compliance.
Ako je Compliant: Host već ima zakrpe.
Non-Compliant: Hostu nedostaju zakrpe (potrebna akcija).

4. Izvršavanje (Remediation)
Ovo je kritična faza gde se vrši stvarna instalacija.
Korak A: Pre-Remediation Check
Uraditi  Pre-Remediation Check. vCenter će skenirati potencijalne probleme (npr. problemi sa DRS-om, High Availability greške ili diskonektovani uređaji). Rešite sve crvene alarme pre nastavka.
Korak B: Maintenance Mode (Automatski mode) 

Automatski: Tokom procesa Remediation-a, vCenter će sam pokušati da prebaci host u ovaj mod.
Korak C: Remediation
Proveriti da li je sve uredu.

Tokom ovog procesa host će se verovatno restartovati barem jednom. Pratite napredak kroz Recent Tasks.

5. Post-patch radnje i verifikacija
Nakon što se host vrati u online stanje:
Exit Maintenance Mode:Pre izlaska iz maintanace moda proveriti da li je sve uradjeno kako treba.

Verify Compliance: Ponovo uraditi heck Compliance da potvrdite da je status sada zelen (Compliant).
Provera verzije: U tabu Summary proverite da li je "Build Number" ispravan.
Uraditi Vmotion test
vMotion test: Vratite nekoliko VM-ova na host da potvrdite da mreža i storage rade ispravno.
VMware Tools: Proverite da li je potrebno ažurirati VMware Tools na virtuelnim mašinama, jer novi ESXi često donosi i novu verziju Tools-a.

I. Faza pripreme (Pre-Check)
Pre nego što kliknete na bilo koju opciju u vCenteru, obeležite ove stavke:
vCenter Backup: Uspešno kreiran file-based backup vCenter servera (VAMI).
Kompatibilnost: Proverena verzija vCentera (mora biti ista ili viša od ESXi patch-a).
Resursi klastera: Preostali hostovi imaju bar 20-30% slobodnog RAM-a/CPU-a da prihvate VM-ove sa hosta koji se patchuje.
Hardware Compatibility (HCL): Provereno da je trenutni hardver (posebno storage kontroleri i mrežne kartice) podržan na novom ESXi build-u.
Nema zakačenih ISO fajlova: VM-ovi nemaju montirane lokalne ISO fajlove koji bi blokirali vMotion.


II. Lifecycle Manager / VUM Konfiguracija
Sync Updates: Urađen "Sync Updates" na vSphere Lifecycle Manageru (vLCM).
Baseline kreiran: Napravljen novi Patch Baseline sa konkretnim kritičnim zakrpama (ako ne koristite Cluster Image).
Baseline Attached: Baseline je povezan (Attached) na nivo klastera ili hosta.
Compliance Scan: Pokrenut "Check Compliance" i host je dobio status "Non-Compliant".


III. Neposredno pre egzekucije (Staging)
Pre-Remediation Check: Pokrenut "Pre-check" bez pronađenih kritičnih grešaka.
Staging (opciono ali preporučeno): Pokrenut "Stage" proces (kopiranje fajlova na host pre samog restarta kako bi se skratilo vreme zastoja).
Maintenance Mode: Host uspešno ušao u Maintenance Mode (svi VM-ovi evakuisani).


IV. Egzekucija (Remediation)
Pokretanje: Kliknuto na Remediate.
Monitoring: Praćenje napretka kroz Recent Tasks (očekuje se barem jedan reboot).
Reboot: Host se vratio "online" i vCenter ga vidi kao povezanog.


V. Post-patch verifikacija
Compliance Status: Ponovni "Check Compliance" pokazuje status Compliant.
Build Number: Verifikovano u Summary tabu da build broj odgovara novom patch-u.
Exit Maintenance Mode: Host izveden iz maintenance moda.
vMotion Test: Uspešno vraćeno nekoliko VM-ova na patchovani host.
VMware Tools Update: Samo Provera da li VM-ovi zahtevaju ažuriranje Tools-a nakon patchovanja hosta.

Svaka ova od akcija koja treba da se uradi, treba da bude obuhvacena try and catch logom, proverom i mogucnoscu simulacije i testiranja akcija.


Scenario 2
Uraditi dodatak kao odvejen deo gde ce se uz Vcentar update moci uradit i Update Hosta na HP one view apliancu tacnije serveru koji je tu definisan
Ova  akcija ce bti odvojena od Updeta Vcentra
Provera da li je Host na kome se radi primena u maintanance modu.
Firmware Repository: Proveri da li je željeni HPE Service Pack for ProLiant (SPP) već upload-ovan u Settings -> Firmware Bundles na OneView appliance-u.
Uvek je bolje menjati Server Profile Template (SPT) nego direktno profil, kako bi zadržao standardizaciju.
U server template-u proferiti da li je postoji firmwware
U sekciji Firmware, postaviti novi Firmware Baseline (željeni SPP).
Odaberi Update Policy:
"Firmware only" (Samo firmver).
"Firmware and OS drivers" ( HPE Smart Update Tools - SUT)
naprvaiti try and check potvrdu da li je ovaj uslov zadovljen, ako jeste onda krenuti dalje
Na Server Profile će dobiti status "Not Consistent with Template". 

Na Server Profiles i odaberi profil definisanog hosta.
Actions -> Update from Template.
Pregledaj listu promena koju OneView prikazuje (paza na to da li OneView zahteva restart servera).
Posto ova faza dosta dugo traje porebno je napraviti sistem monitorisanja kako bi se dobijao status u kom je trenutno host u kojoj je fazi.
Ako je potreban cold restart dobiti poruku o tome kako bi se proces nastavio.
Svaka od ovih akcija treba da ima try and catch logiku i log kako bi se moglo videti sta treba da se ispravi, sa jasnom porukom gde je problem nastao.
Isto tako je potrebno da se ima i report nakon zavrsene akcije.



Scenario 3

Ujediniti Scenario 1 i 2 u jednu akciju.
Sa svim definisanim stvarima i mogucnoscu Simulacije, Testiranja i Izvrsenja




Scenario 4

Bi trebalo da ima mogucnost patchovanja host by host u okviru Vmware Clustera po scenario 1 i Scenario 2 uz sve pratece definisane korake, kao jednu kompletnu celinu

Napoomena:
Svaka od kreiranih skripti, mora da ima opis, svaka akcija mora imati definisan komentar na Srpskom Jeziku, mora imati specificirane korake za izvrsenje, mora da ima svu neophodnu dokumentaciju vezanu za celu akciju, i mora da ima graficki prikaz akcije sa redosledom izvrsavanja
Ono sto bi bilo idealno - da ovo bude uradjeno u jednom folderu u vise opcija

1. Opcija je PowerShell Skripte
2. Opcija je za Ansible








