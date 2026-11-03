# Servicii terțe utilizate de AI DocuSearch

> **Notă:** Aceasta este o traducere automată, în scop informativ. Versiunea în limba engleză (`THIRD_PARTY_SERVICES.md`) este cea obligatorie din punct de vedere juridic și prevalează în caz de neconcordanță.

**Ultima actualizare:** 15 septembrie 2026

AI DocuSearch se bazează pe servicii externe pentru răspunsurile modelelor lingvistice, pentru diagnosticare opțională, colectarea feedback-ului și găzduire. Serviciul utilizat într-o anumită instalare depinde de configurarea operatorului și de funcția pe care o alegi.

Nu încărca documente confidențiale, reglementate sau sensibile într-o instalare de testare, decât dacă ești autorizat să distribui conținutul furnizorilor aplicabili.

## Furnizorul de modele lingvistice

AI DocuSearch trimite întrebarea ta, metadatele documentului și fie fragmentele relevante, fie textul extras complet al documentului către furnizorul de modele lingvistice compatibil cu OpenAI, configurat. Acest lucru este necesar pentru a genera un răspuns.

Atunci când operatorul activează interpretarea imaginilor (`MULTIMODAL_ENABLED`), o imagine redusă a fiecărei pagini PDF sau a fiecărui fișier PNG/JPEG/WebP încărcat este trimisă, de asemenea, o singură dată, la încărcare, unui model capabil de viziune de la același furnizor. Metadatele imaginii, precum EXIF, sunt eliminate înainte de trimitere. Descrierile returnate sunt păstrate împreună cu textul extras al sesiunii și sunt etichetate ca generate de AI în răspunsuri.

Furnizorul poate fi OpenAI, xAI, Groq sau un alt serviciu compatibil, ales de operatorul aplicației. Se aplică propriile sale termeni privind confidențialitatea, securitatea, păstrarea datelor și transferurile internaționale. Furnizorul activ nu este în prezent afișat în interfața utilizatorului; contactează operatorul aplicației înainte de utilizare dacă ai nevoie de informații specifice despre furnizor.

## LangSmith

Atunci când operatorul aplicației activează trasarea, LangSmith poate primi întrebări, solicitări, fragmente din document sau text extras incluse în solicitări, răspunsuri generate, metadate despre timp și tokeni, erori și evaluările „Util” / „Nu a fost util” asociate unei trasări.

LangSmith este folosit pentru depanarea și evaluarea comportamentului aplicației. Utilizatorii nu pot dezactiva trasarea din interfață. Nu folosi aplicația dacă nu consimți la această prelucrare, atunci când trasarea este activată.

- Furnizor: LangChain, Inc.
- Informații despre confidențialitate: https://www.langchain.com/privacy-policy

## Google Forms

Butonul **Trimite feedback** deschide un formular Google opțional, într-un tab nou. AI DocuSearch nu trimite automat documentul, întrebările, răspunsurile sau identificatorul sesiunii către acest formular. Google primește răspunsurile pe care le introduci și poate colecta informații tehnice suplimentare, conform propriilor politici.

Nu include conținutul documentului, informații confidențiale sau date personale inutile în formular. Răspunsurile din Google Forms nu sunt incluse în exportul de date din aplicație și nu pot fi eliminate cu controlul „Șterge datele” din aplicație.

- Furnizor: Google LLC
- Informații despre confidențialitate: https://policies.google.com/privacy

## Găzduire și infrastructură

Aplicația implementată și datele temporare ale sesiunii sunt prelucrate de furnizorul de găzduire, precum Streamlit Community Cloud și furnizorii săi de infrastructură. Jurnalele de găzduire și metadatele operaționale sunt guvernate de termenii și practicile de confidențialitate ale furnizorului.

- Informații despre confidențialitate Streamlit: https://streamlit.io/privacy-policy

## Alegerile tale

- Utilizarea funcției de întrebări cu AI necesită trimiterea conținutului relevant către furnizorul de model configurat.
- Deschiderea și trimiterea formularului Google de feedback este opțională.
- Trasarea LangSmith este controlată de configurarea instalării, nu de o setare a utilizatorului din aplicație.
- Limba interfeței o alegi tu pe ecranul de start; nu este dedusă din adresa ta IP.
- Aplicația nu vinde datele tale și nu le trimite agenților de publicitate.
- Consultă Politica de confidențialitate pentru informații despre păstrare, ștergere și drepturile asupra datelor.

Întrebările despre furnizorii activi sau despre ștergerea datelor păstrate de furnizori trebuie adresate operatorului aplicației.
