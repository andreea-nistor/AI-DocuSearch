# Politica de confidențialitate pentru AI DocuSearch

> **Notă:** Aceasta este o traducere automată, în scop informativ. Versiunea în limba engleză (`PRIVACY_POLICY.md`) este cea obligatorie din punct de vedere juridic și prevalează în caz de neconcordanță.

**Ultima actualizare:** 15 septembrie 2026
**Data intrării în vigoare:** 15 septembrie 2026

## 1. Introducere

AI DocuSearch („Serviciul” sau „Aplicația”) este un proiect personal experimental, gratuit, operat de Andreea Nistor. În prezent este oferit pentru testare și evaluare, fără garanții de disponibilitate, suport sau nivel de serviciu de producție. Această Politică de confidențialitate explică modul în care sunt prelucrate informațiile atunci când testezi Aplicația.

**Te rugăm să citești cu atenție această Politică de confidențialitate.** Dacă nu ești de acord cu politicile și practicile noastre, te rugăm să nu folosești Serviciul.

---

## 2. Operatorul proiectului și operatorul de date

Pentru datele prelucrate direct de această Aplicație, operatorul de date (operatorul) este:

- **Nume:** Andreea Nistor
- **E-mail:** nistor_andreea_ii@yahoo.com
- **Proiect:** AI DocuSearch, un proiect personal oferit gratuit, pentru testare experimentală

Operatorul este o persoană fizică, nu o companie, și nu a numit un responsabil cu protecția datelor. Proiectul urmărește prelucrarea datelor personale în conformitate cu cerințele aplicabile de confidențialitate, inclusiv drepturile prevăzute de GDPR, acolo unde sunt aplicabile. Deoarece acesta este un serviciu experimental, utilizatorii nu ar trebui să încarce documente confidențiale, extrem de sensibile sau critice pentru afacere.

---

## 3. Informațiile pe care le colectăm

### 3.1 Informații pe care le furnizezi
- **Conținutul documentelor**: fișierele încărcate (PDF, DOCX, TXT și — atunci când operatorul activează interpretarea imaginilor — imagini PNG, JPEG sau WebP) pentru extragerea și analiza textului
- **Întrebări și interogări**: întrebările de căutare și solicitările pe care le trimiți
- **Feedback**: evaluări, comentarii și reacții la răspunsuri
- **Informații despre sesiune**: istoricul conversațiilor și datele de interacțiune

### 3.2 Informații colectate automat
- **Selectarea limbii**: limba aleasă de tine pe ecranul de start (engleză sau română) este păstrată în starea sesiunii, pe server, pentru sesiunea curentă. Aplicația nu deduce limba din adresa IP sau din anteturile browserului.
- **ID de sesiune**: identificator unic pentru urmărirea sesiunii tale
- **Semnal de dispozitiv**: Aplicația poate încerca să stabilească dacă browserul rulează pe mobil, atunci când este disponibil un semnal user-agent. Nu creează intenționat un profil detaliat al dispozitivului.
- **Metrici de utilizare a API-ului**: numărul de tokeni, timpii de răspuns, marcajele de timp
- **Trasee LangSmith**: jurnale de depanare pentru monitorizarea performanței modelului AI

### 3.3 Cookie-uri și urmărire
- **Conexiune de sesiune**: Streamlit folosește o conexiune din browser pentru a te asocia cu starea sesiunii de pe server, cât timp Aplicația este deschisă.
- **Fără analize terțe**: nu folosim Google Analytics sau alte instrumente similare de urmărire
- **Starea sesiunii pe server**: preferința de limbă, starea documentului încărcat și contoarele de cost sunt păstrate, în principal, în starea temporară a sesiunii de pe server, nu ca date permanente în stocarea locală a browserului. Starea sesiunii poate fi pierdută când fila se deconectează sau când serverul repornește.

---

## 4. Cum folosim informațiile tale

Folosim informațiile colectate pentru:

| Scop | Temei juridic | Păstrare |
|------|---------------|----------|
| **Procesarea interogărilor** | Furnizarea serviciului | Durata sesiunii |
| **Selectarea limbii** | Preferința utilizatorului | Doar pe durata sesiunii |
| **Îmbunătățirea acurateței AI** | Interes legitim | 30 de zile (anonimizat) |
| **Suport tehnic** | Obligație contractuală | 30 de zile |
| **Analize și depanare** | Interes legitim | Maximum 90 de zile |
| **Conformitate legală** | Obligație legală | Conform cerințelor |

---

## 5. Păstrarea și ștergerea datelor

### 5.1 Curățare automată
- **Istoricul conversațiilor**: șters automat după 30 de zile
- **Date de feedback**: stocate local până când folosești „Șterge datele” pentru sesiunea curentă sau până când operatorul serviciului rulează procesul de curățare disponibil
- **Datele sesiunii**: șterse la încheierea sesiunii
- **Fișiere temporare încărcate**: fișierele încărcate sunt copiate într-un director specific aplicației, pe sistemul gazdă, doar pentru extragerea textului, numărarea paginilor PDF și — atunci când interpretarea imaginilor este activată — randarea paginilor ca imagini pentru modelul de viziune. Aplicația șterge fiecare copie temporară imediat după ce prelucrarea reușește sau eșuează. Păstrează textul extras, descrierile de imagini generate și un index de regăsire din memorie pentru sesiunea activă, în loc să păstreze fișierul încărcat sau imaginile paginilor. La pornire, elimină și fișierele încărcate create de aplicație, mai vechi de o oră, care ar fi putut rămâne după o întrerupere a serverului.

### 5.2 Ștergerea inițiată de utilizator
Îți poți șterge oricând toate datele:
- Folosește „🗑️ Șterge datele” din secțiunea de subsol „Confidențialitate și gestionarea datelor”
- Aceasta elimină întrebările, răspunsurile, feedback-ul și starea documentului din memorie, stocate local pentru sesiunea curentă
- Copiile temporare ale fișierelor încărcate au fost deja eliminate după extragere; acest control nu garantează ștergerea datelor deja prelucrate sau păstrate de furnizorii LLM configurați, de LangSmith sau de Google Forms
- **Această acțiune este ireversibilă**

### 5.3 Portabilitatea datelor
Îți poți descărca oricând toate datele personale:
- Folosește „📥 Descarcă datele” din secțiunea de subsol „Confidențialitate și gestionarea datelor”
- Exportul include: întrebări, răspunsuri, feedback, metrici
- Format: JSON (citibil automat și portabil către alte servicii)

---

## 6. Partajarea datelor cu terțe părți

### 6.1 LangSmith (depanare și trasare)
- **Scop**: monitorizarea performanței modelului AI, depanarea problemelor și asocierea evaluărilor „Util” / „Nu a fost util” cu trasarea răspunsului, atunci când colectarea feedback-ului LangSmith este activată
- **Date partajate**: întrebări, răspunsuri, metadate de sesiune și evaluări pozitive sau negative ale răspunsurilor
- **Furnizor**: LangChain Inc.
- **Politica de confidențialitate**: https://docs.smith.langchain.com/
- **Rezidența datelor**: SUA (serverele LangSmith)
- **Controlul trasării**: trasarea este controlată de operatorul Aplicației, prin configurarea instalării. Utilizatorii nu o pot dezactiva în prezent din interfață. Nu folosi Aplicația dacă nu consimți la această prelucrare, atunci când trasarea este activată.

### 6.2 Furnizori de modele lingvistice (OpenAI, Grok, Groq etc.)
- **Scop**: prelucrarea întrebărilor tale prin modele AI; atunci când interpretarea imaginilor este activată, descrierea imaginilor, graficelor și diagramelor din document
- **Date partajate**: textul întrebării, fragmente din document (necesare pentru prelucrarea AI); atunci când interpretarea imaginilor este activată, o imagine redusă a fiecărei pagini PDF (sau a unei imagini încărcate) este trimisă o singură dată, la încărcare, unui model capabil de viziune. Metadatele imaginii (cum ar fi EXIF) sunt eliminate înainte de trimitere.
- **Furnizori**: OpenAI, xAI, Groq sau alte puncte de acces configurate
- **Politica de confidențialitate**: consultă politica furnizorului tău (de exemplu, https://groq.com/privacy-policy)
- **Rezidența datelor**: depinde de furnizor (de obicei SUA, pentru furnizorii majori)

### 6.3 Google Forms (feedback de testare)
- **Scop**: colectarea unui feedback opțional despre experiența de testare AI DocuSearch
- **Date partajate**: doar răspunsurile pe care alegi să le trimiți prin formularul extern, plus datele tehnice pe care Google le poate colecta conform propriilor politici
- **Furnizor**: Google LLC
- **Politica de confidențialitate**: https://policies.google.com/privacy
- **Control**: deschiderea și trimiterea formularului sunt opționale. Nu include conținutul documentelor încărcate, informații confidențiale sau alte date personale în răspunsurile libere.
- **Ștergere**: controlul „Șterge datele” din Aplicație nu poate șterge răspunsurile din Google Forms. Contactează operatorul Aplicației pentru un răspuns trimis.

### 6.4 Nicio altă partajare
- ❌ NU vindem datele tale
- ❌ NU le partajăm companiilor de marketing
- ❌ NU folosim datele tale pentru publicitate
- ❌ NU le partajăm platformelor de socializare

Consultă pagina din Aplicație **Servicii terțe** pentru o explicație consolidată a datelor furnizorilor, a controalelor și a linkurilor către informațiile lor de confidențialitate.

---

## 7. Securitatea datelor

### Măsuri de securitate
- **Criptare în tranzit**: HTTPS/TLS pentru toate conexiunile
- **Prelucrare temporară**: fișierele încărcate sunt păstrate într-un director temporar specific aplicației, doar pe durata extragerii și numărării paginilor, apoi sunt șterse
- **Control al accesului**: doar procesele autorizate accesează datele
- **Fără bază de date**: datele sunt stocate local, ca fișiere JSON (nu în cloud)
- **Izolarea sesiunilor**: datele fiecărui utilizator sunt izolate după ID-ul sesiunii

### Limitări
- Nicio măsură de securitate nu este 100% sigură
- Documentele sensibile trebuie verificate înainte de încărcare
- Nu încărca documente care conțin parole, chei API sau date financiare
- Folosește un VPN pentru o confidențialitate suplimentară în rețelele publice

---

## 8. Drepturile tale în temeiul GDPR

### Dreptul de acces (articolul 15)
Solicită o copie a tuturor datelor personale pe care le deținem despre tine
- Folosește butonul: „📥 Descarcă datele mele (GDPR)”
- Sau: contactează-ne (vezi Secțiunea 10)

### Dreptul la rectificare (articolul 16)
Solicită corectarea datelor inexacte
- Aplicația nu oferă în prezent o interfață pentru editarea întrebărilor sau a feedback-ului stocat
- Contactează operatorul proiectului, la adresa din Secțiunea 10, pentru asistență

### Dreptul la ștergere (articolul 17)
Solicită ștergerea definitivă a datelor tale („dreptul de a fi uitat”)
- Folosește butonul: „🗑️ Șterge toate datele mele (GDPR)”
- Sau: solicită prin datele de contact din Secțiunea 10
- Ștergere automată după 30/90 de zile pentru datele istorice

### Dreptul la portabilitatea datelor (articolul 20)
Primește datele tale într-un format structurat și portabil
- Folosește butonul: „📥 Descarcă datele mele (GDPR)”
- Format: JSON (portabil către orice serviciu)

### Dreptul la opoziție (articolul 21)
Te poți opune prelucrării bazate pe interese legitime
- Interfața actuală nu oferă o opțiune individuală de renunțare la trasare
- Încetează utilizarea Aplicației și trimite un e-mail operatorului proiectului pentru a solicita restricții suplimentare sau ștergere, acolo unde este posibil

### Dreptul la restricționarea prelucrării (articolul 18)
Solicită limitarea modului în care folosim datele tale
- Contactează-ne (Secțiunea 10) cu restricțiile specifice
- Vom accepta solicitările rezonabile

### Dreptul de a nu fi supus unor decizii automate (articolul 22)
Răspunsurile generate de AI sunt rezultate informative și nu iau decizii obligatorii despre utilizatori. Aplicația nu oferă în prezent un flux formal de verificare umană. Nu te baza pe un răspuns ca pe un sfat juridic, medical, financiar sau de altă natură profesională.

---

## 9. Drepturi CCPA (rezidenți din California)

Dacă ești rezident în California, ai:

- **Dreptul de a ști**: să soliciți ce date personale colectăm (folosește funcția de export a datelor)
- **Dreptul de a șterge**: să soliciți ștergerea datelor personale (folosește funcția de ștergere)
- **Dreptul de renunțare**: să renunți la vânzarea datelor (noi nu vindem date)
- **Dreptul la nediscriminare**: fără discriminare pentru exercitarea drepturilor tale

Rezidenții din California pot trimite solicitări contactându-ne (Secțiunea 10).

---

## 10. Contact

### Întrebări și solicitări privind confidențialitatea
**Operator**: Andreea Nistor

**E-mail**: nistor_andreea_ii@yahoo.com

**GitHub**: https://github.com/andreea-nistor/AI-DocuSearch  
**Timp de răspuns**: ne propunem să răspundem în cel mult 30 de zile

Nu a fost numit un responsabil cu protecția datelor, deoarece acesta este un proiect experimental operat individual, nu o companie. Dacă ai nelămuriri privind prelucrarea datelor, contactează mai întâi operatorul. Poți contacta și:
- **Autoritatea locală pentru protecția datelor** (DPA)
- **UE**: https://edpb.ec.europa.eu/edpb/node
- **Regatul Unit**: https://ico.org.uk/
- **SUA**: procurorul general al statului tău, pentru chestiuni de confidențialitate

---

## 11. Confidențialitatea minorilor

Serviciul nostru nu este destinat persoanelor sub 13 ani. Nu colectăm în mod intenționat date personale de la copii sub 13 ani. Dacă aflăm că am colectat date personale de la un copil sub 13 ani, le vom șterge fără întârziere.

---

## 12. Transferuri internaționale de date

Datele tale pot fi prelucrate în alte țări decât cea de reședință (în principal SUA, unde sunt sediile furnizorilor LLM). Prin utilizarea acestui Serviciu, consimți la astfel de transferuri în baza deciziilor de adecvare GDPR sau a clauzelor contractuale standard.

---

## 13. Modificări ale acestei Politici de confidențialitate

Putem actualiza periodic această Politică de confidențialitate. Data „Ultima actualizare” de mai sus indică cele mai recente modificări. Continuarea utilizării Serviciului constituie acceptarea modificărilor.

---

## 14. Rezumatul controalelor tale

| Control | Locație | Efect |
|---------|---------|-------|
| **Descarcă datele** | Subsol: „📥 Descarcă datele” | Obții un export JSON al datelor de sesiune asociate local |
| **Șterge datele** | Subsol: „🗑️ Șterge datele” | Elimină istoricul, feedback-ul și starea documentului din memorie pentru sesiunea curentă; copiile de la terți rămân supuse controalelor și politicilor de păstrare ale furnizorilor |
| **Selectarea limbii** | Ecranul de start (English / Română) | Alegi limba interfeței înainte de notificarea privind consimțământul; alegerea rămâne valabilă pe durata sesiunii |
| **Dezactivarea trasării** | Momentan indisponibil pentru utilizatori | Configurarea instalării este controlată de operatorul proiectului |
| **Șterge istoricul** | Automat după 30 de zile | Întrebările și răspunsurile sunt șterse automat |

---

## 15. Temeiul juridic al prelucrării (articolul 6 GDPR)

| Date | Temei juridic |
|------|---------------|
| Întrebări și răspunsuri | Executarea contractului (furnizarea serviciului) |
| Feedback și evaluări | Interes legitim (îmbunătățirea serviciului) |
| Date de sesiune/IP | Interes legitim (securitate, funcționalitate) |
| Trasee LangSmith | Interes legitim (depanare, performanță) |
| Selectarea limbii | Interes legitim (experiența utilizatorului) |

---

**Prin utilizarea AI DocuSearch, confirmi că ai citit și înțeles această Politică de confidențialitate.**

Pentru mai multe detalii, deschide pagina Termeni și condiții din Aplicație.
