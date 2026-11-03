# Termeni și condiții pentru AI DocuSearch

> **Notă:** Aceasta este o traducere automată, în scop informativ. Versiunea în limba engleză (`TERMS_OF_SERVICE.md`) este cea obligatorie din punct de vedere juridic și prevalează în caz de neconcordanță.

**Ultima actualizare:** 15 septembrie 2026
**Data intrării în vigoare:** 15 septembrie 2026

## 1. Statutul serviciului și operatorul

AI DocuSearch („Serviciul”) este un proiect personal experimental, gratuit, operat de Andreea Nistor. În prezent este oferit pentru testare și evaluare, fără garanții de disponibilitate, suport, nivel de serviciu de producție sau recuperare a datelor. Operatorul este o persoană fizică, nu o companie.

Contact: nistor_andreea_ii@yahoo.com

Nu folosi Serviciul pentru lucrări critice pentru afacere și nu încărca informații confidențiale, extrem de sensibile sau irecuperabile.

## 2. Acceptare și eligibilitate

Prin utilizarea Serviciului, accepți acești Termeni și Politica de confidențialitate. Dacă nu ești de acord, nu încărca un document și nu trimite o întrebare.

Trebuie să ai cel puțin 18 ani sau să folosești Serviciul cu autorizarea și supravegherea unui părinte sau a unui tutore legal, acolo unde legea aplicabilă o permite. Adultul care supraveghează este responsabil pentru utilizarea Serviciului de către minor.

## 3. Serviciul experimental

Serviciul acceptă fișiere PDF, DOCX și TXT (și imagini PNG, JPEG sau WebP, atunci când operatorul activează interpretarea imaginilor), extrage textul și folosește sisteme AI pentru a răspunde la întrebări despre acest conținut. În mod normal, încearcă mai întâi generarea augmentată prin regăsire (RAG) și poate reveni la trimiterea unei porțiuni mai mari din textul documentului către un furnizor configurat de modele lingvistice mari. Atunci când interpretarea imaginilor este activată, o imagine redusă a fiecărei pagini PDF sau a fiecărei imagini încărcate este trimisă, de asemenea, o singură dată unui model capabil de viziune, iar descrierile rezultate sunt etichetate ca generate de AI în răspunsuri.

Serviciul poate fi modificat, restricționat, suspendat, resetat sau întrerupt oricând. Funcțiile pot eșua sau se pot comporta diferit în timpul testării. Nu se oferă niciun angajament privind timpul de funcționare, timpul de răspuns, compatibilitatea sau continuarea disponibilității.

## 4. Limite de utilizare și estimări de cost

Serviciul de testare găzduit este oferit în prezent gratuit. Poate aplica un buget de utilizare sau o limită de interogări pe sesiune, pentru a controla costurile API ale terților.

- Numărul de tokeni și costurile afișate pot fi estimări.
- Calculele de cost pot folosi ipoteze de preț diferite de tarifele reale ale furnizorului configurat.
- Cererile eșuate sau simulate pot fi afișate diferit, pe măsură ce implementarea de testare evoluează.
- Atingerea unei limite de sesiune poate împiedica adresarea de întrebări suplimentare.
- Nu se oferă în prezent niciun upgrade plătit, achiziție de credite, rambursare sau cotă garantată.

Limitele și ipotezele de preț se pot modifica fără notificare pe durata testării.

## 5. Responsabilitățile utilizatorului și utilizările interzise

Poți folosi Serviciul doar pentru testare și evaluare legală. Trebuie să ai dreptul și autoritatea de a prelucra fiecare document pe care îl încarci.

Nu ai voie:

- Să încarci conținut ilegal, malițios sau care încalcă drepturile altei persoane.
- Să încarci informații confidențiale ale unor terțe persoane fără autorizare.
- Să încarci parole, chei API, date de autentificare, date de card de plată, numere de identificare guvernamentale, fișe medicale detaliate sau informații similar de sensibile.
- Să încarci programe malițioase sau să încerci să compromiți, să perturbi, să supraîncarci, să faci inginerie inversă sau să ocolești limitele Serviciului găzduit.
- Să folosești Serviciul pentru a hărțui, a înșela, a discrimina sau a face rău altei persoane.
- Să tratezi un răspuns generat de AI ca pe o afirmație verificată din documentul sursă, fără a verifica documentul original.

Serviciul găzduit este destinat evaluării personale. Utilizarea codului sursă, inclusiv utilizarea comercială, este guvernată separat de licența depozitului.

## 6. Documente încărcate și permisiunea de prelucrare

Păstrezi orice drepturi deții asupra documentelor și întrebărilor pe care le trimiți. Acorzi operatorului o permisiune limitată de a prelucra acest conținut doar în măsura necesară rezonabil pentru furnizarea și operarea Serviciului, inclusiv permisiunea de a:

- Copia și stoca temporar un fișier încărcat.
- Extrage, curăța, împărți și căuta în textul său.
- Trimite fragmente relevante, întrebări, solicitări și, în cazul revenirii la calea de rezervă, eventual textul extras complet al documentului către furnizorii de servicii configurați.
- Atunci când interpretarea imaginilor este activată, randa pagini de document sau imagini încărcate și le trimite unui furnizor de model capabil de viziune configurat.
- Genera și afișa răspunsuri.
- Produce metrici operaționale și trasee de depanare descrise în Politica de confidențialitate.

Această permisiune încetează atunci când conținutul nu mai este necesar pentru aceste scopuri, sub rezerva practicilor de păstrare ale terților descrise mai jos și în Politica de confidențialitate.

## 7. Păstrarea fișierelor

Fișierele încărcate sunt copiate într-un director temporar specific aplicației, doar pentru extragere, numărarea paginilor PDF și, atunci când interpretarea imaginilor este activată, randarea paginilor. Aplicația șterge fiecare copie temporară imediat după ce prelucrarea reușește sau eșuează. Păstrează textul extras, eventualele descrieri de imagini generate și un index de regăsire din memorie pentru sesiunea activă, în loc să păstreze fișierul încărcat sau imaginile paginilor. La pornire, elimină fișierele încărcate create de aplicație, mai vechi de o oră, care ar fi putut rămâne după o întrerupere a serverului.

Controlul „Șterge datele” din subsol elimină istoricul, feedback-ul și starea documentului din memorie, stocate local pentru sesiune. Copiile temporare ale fișierelor încărcate au fost deja eliminate după extragere. Controlul nu poate garanta ștergerea datelor deja păstrate de furnizorii terți.

Deoarece textul extras poate fi trimis furnizorilor LLM și de observabilitate configurați, nu încărca fișiere confidențiale sau sensibile decât dacă înțelegi și accepți politicile acelor furnizori.

## 8. Limitările AI și sfatul profesional

Răspunsurile generate de AI pot fi incorecte, incomplete, înșelătoare, depășite sau nesusținute de documentul încărcat. Serviciul poate:

- Interpreta greșit documente scanate sau prost formatate.
- Regăsi un fragment irelevant sau incomplet.
- Omite clauze, tabele, note de subsol sau context important.
- Produce afirmații sau citări inventate.
- Eșua din cauza erorilor OCR, a limitelor de context, a limitelor de rată, a modelelor indisponibile, a erorilor furnizorilor, a problemelor de rețea sau a constrângerilor de resurse.

Verifică întotdeauna un răspuns în raport cu documentul original. Serviciul nu oferă sfaturi juridice, medicale, financiare, fiscale, de conformitate sau de altă natură profesională și nu trebuie folosit ca unică bază pentru decizii cu consecințe.

## 9. Servicii terțe și prelucrarea internațională

Serviciul se poate baza pe un furnizor configurat de modele lingvistice, pe LangSmith pentru depanare și trasare, pe Google Forms pentru feedback opțional de testare și pe furnizori de găzduire sau infrastructură. În funcție de calea de execuție, fragmente din document sau textul extras complet, întrebări, răspunsuri și metadate tehnice pot fi transmise furnizorilor relevanți. Doar informațiile pe care le introduci în formularul extern de feedback sunt trimise intenționat către Google Forms.

Serviciile terțe funcționează sub propriii termeni, politici de confidențialitate, măsuri de securitate, locații și practici de păstrare. Operatorul proiectului nu poate garanta disponibilitatea lor și nu poate șterge independent datele pe care le păstrează, decât dacă instrumentele și politicile lor o permit. Prelucrarea poate avea loc în afara țării tale de reședință.

Consultă Politica de confidențialitate pentru detaliile actuale privind prelucrarea și divulgarea. Nu folosi Serviciul dacă nu ești de acord cu prelucrarea necesară de către terți.

## 10. Istoric, feedback, export și ștergere

- Istoricul conversațiilor este destinat să fie păstrat local până la 30 de zile.
- Păstrarea feedback-ului și curățarea automată sunt încă în testare; consultă Politica de confidențialitate pentru starea actuală.
- Răspunsurile opționale din Google Forms sunt păstrate sub controalele de păstrare ale Google și ale operatorului Aplicației și nu sunt eliminate de controlul „Șterge datele” din Aplicație.
- Controlul „Descarcă datele” din secțiunea de subsol „Confidențialitate și gestionarea datelor” exportă datele de sesiune asociate local, în format JSON.
- Controlul „Șterge datele” din acel subsol elimină înregistrările locale suportate și starea documentului din memorie pentru sesiunea curentă; copiile de la terți rămân supuse controalelor și politicilor de păstrare ale furnizorilor.

Serviciul nu garantează recuperarea datelor șterse sau pierdute.

## 11. Proprietate intelectuală

### Conținutul tău

Păstrezi drepturile asupra documentelor pe care le încarci. Ești responsabil pentru asigurarea faptului că utilizarea și prelucrarea acelor documente sunt autorizate.

### Rezultatul generat

Drepturile asupra rezultatelor generate de AI pot depinde de legea aplicabilă și de termenii furnizorului configurat. Serviciul nu garantează că rezultatul este original, neîncălcător sau eligibil pentru proprietate exclusivă.

### Codul sursă

Acești Termeni guvernează utilizarea Serviciului găzduit. Utilizarea, copierea, modificarea, distribuirea și utilizarea comercială a codului sursă al depozitului sunt guvernate de Licența MIT din depozit. Bibliotecile, serviciile și modelele AI ale terților rămân supuse propriilor licențe și termeni.

Numele proiectului și identitatea vizuală nu sunt licențiate separat, cu excepția cazului în care licența depozitului sau legea aplicabilă prevede altfel.

## 12. Feedback

Dacă trimiți voluntar feedback, permiți operatorului să îl folosească pentru a evalua și îmbunătăți proiectul. Nu include date confidențiale sau date personale sensibile în feedback. Această permisiune nu transferă proprietatea asupra altor materiale neînrudite pe care le-ai putea menționa.

## 13. Suspendare și încetare

Operatorul poate limita, suspenda sau încheia accesul, poate elimina datele stocate local sau poate întrerupe Serviciul atunci când este necesar în mod rezonabil pentru a:

- Proteja securitatea, confidențialitatea, infrastructura sau serviciile terților.
- Răspunde la abuzuri, activități ilegale sau încălcări ale acestor Termeni.
- Aplica limite de resurse sau de utilizare.
- Menține, modifica sau încheia proiectul experimental.

Deoarece Serviciul este experimental și gratuit, nu se pot garanta notificarea prealabilă și recuperarea datelor.

## 14. Declinări de răspundere

Serviciul este furnizat „în forma în care se află” și „în măsura disponibilității”. În măsura maximă permisă de legea aplicabilă, nu se oferă nicio garanție că va fi exact, sigur, neîntrerupt, fără erori, potrivit pentru un anumit scop sau compatibil cu orice document ori furnizor.

Nimic din acești Termeni nu exclude garanțiile, protecțiile consumatorului sau alte drepturi care nu pot fi excluse legal.

## 15. Limitarea răspunderii

În măsura maximă permisă de legea aplicabilă, operatorul nu răspunde pentru pierderile indirecte, incidentale, speciale, consecvente sau punitive care decurg din utilizarea Serviciului sau din imposibilitatea de a-l folosi, din încrederea acordată rezultatelor generate de AI, din pierderea datelor sau din serviciile terților.

Serviciul este gratuit și experimental. Nimic din acești Termeni nu limitează răspunderea care nu poate fi limitată legal, inclusiv răspunderea care decurge din fraudă, abatere intenționată sau orice altă categorie protejată de legea aplicabilă.

## 16. Legea aplicabilă și litigiile

Drepturile obligatorii ale consumatorului, de confidențialitate și de protecție a datelor, aplicabile, rămân în vigoare indiferent de acești Termeni. Acest proiect experimental nu stabilește o jurisdicție specifică de guvernare și nici o procedură obligatorie de arbitraj.

Înainte de a iniția un litigiu formal, te rugăm să contactezi operatorul la nistor_andreea_ii@yahoo.com și să îi oferi o șansă rezonabilă de a rezolva problema. Aceasta nu îți restricționează dreptul de a te adresa unei instanțe, unui organism de protecție a consumatorilor sau unei autorități de protecție a datelor, acolo unde este aplicabil.

## 17. Modificări ale acestor Termeni

Acești Termeni pot fi actualizați pe măsură ce Serviciul se modifică. Data efectivă actuală va fi afișată în partea de sus a acestui document. Modificările importante vor fi comunicate în Aplicație, acolo unde este practic. Dacă nu ești de acord cu Termenii actualizați, încetează utilizarea Serviciului.

## 18. Divizibilitatea

Dacă o prevedere a acestor Termeni este considerată inaplicabilă, celelalte prevederi vor continua să se aplice în măsura permisă de lege.

## 19. Contact

**Operator:** Andreea Nistor

**E-mail:** nistor_andreea_ii@yahoo.com

**GitHub:** https://github.com/andreea-nistor/AI-DocuSearch

Pentru solicitări privind confidențialitatea, consultă și Politica de confidențialitate și controalele „Confidențialitate și gestionarea datelor” din subsolul Aplicației.

---

Prin utilizarea AI DocuSearch, confirmi că ai citit și înțeles acești Termeni și Politica de confidențialitate.
