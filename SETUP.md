# README di profilo in stile neofetch

Ricalca l'impianto di [Andrew6rant/Andrew6rant](https://github.com/Andrew6rant/Andrew6rant):
il `README.md` non contiene testo, solo un `<picture>` che punta a due SVG
(chiaro/scuro); gli SVG sono rigenerati ogni giorno da una GitHub Action, così
le statistiche restano aggiornate da sole.

## File

| file | a cosa serve |
|---|---|
| `README.md` | il profilo: un solo `<picture>`, niente altro |
| `dark_mode.svg` / `light_mode.svg` | generati, **non** editare a mano |
| `generate.py` | impagina gli SVG: legge `art.json` + statistiche live da GitHub |
| `art.json` | l'avatar in ASCII a colori: caratteri, palette, indici |
| `make_art.py` | rigenera `art.json` da `avatar.png` |
| `avatar.png` | sorgente dell'arte |
| `stats_cache.json` | ultime statistiche buone, usate se le API non rispondono |
| `.github/workflows/build.yaml` | ricostruisce gli SVG ogni giorno alle 04:17 UTC |

## Messa in opera

1. Crea il repository `Pinperepette/Pinperepette` (nome **identico** allo
   username: è così che GitHub lo riconosce come profilo).
2. Copia dentro questi file e fai push su `main`.
3. Vai in *Settings → Actions → General → Workflow permissions* e metti
   **Read and write permissions**, altrimenti la Action non può committare.
4. *(opzionale)* Per la riga `Commits` serve un token: crea un PAT classico con
   scope `read:user` e salvalo come secret `ACCESS_TOKEN`. Senza token la riga
   viene semplicemente omessa, il resto funziona uguale.

## Cosa modificare

Le voci non deducibili dalle API stanno tutte nel dizionario `CONFIG` in cima a
`generate.py` — sistema; ho messo valori plausibili ma **vanno controllati**:

```python
"os":           "macOS, Arch Linux, Windows",
"ide":          "Neovim, VS Code, Claude Code",
"birth":        None,     # metti "1976-04-23" per avere Uptime = la tua età
"hobbies_sw":   "Adversarial ML, malware analysis, RE",
"hobbies_hw":   "SDR, homelab, saldatore",
"hobbies_real": "Panna (il cane), il mare",
```

Finché `birth` è `None`, `Uptime` misura l'età dell'account GitHub (12 marzo
2012), non la tua.

Tutto il resto — repo, stelle, follower, linguaggi, azienda, sede, sito — viene
letto ogni volta dalle API, non serve toccarlo.

Dopo ogni modifica:

```bash
python3 generate.py     # riscrive i due SVG
```

## L'arte

È ASCII: caratteri veri, colorati uno per uno. Due scelte non ovvie, entrambe
imposte dalla sorgente.

**Rampa stretta.** Con la classica rampa a 70 caratteri la densità segue la
luminanza; siccome la pelle occupa quasi tutto il fotogramma a un tono medio
uniforme, esce rumore che copre il disegno. Qui la rampa è di cinque glifi di
peso simile — `+ * # % @` — così i caratteri fanno solo texture e la forma la
porta il colore.

**Palette costruita a mano.** Il mediancut assegna i colori in base a quanti
pixel li usano: la pelle arancione se li prende tutti e l'azzurro dell'iride
sparisce. Il pixel più azzurro dell'immagine, il bianco e il nero sono quindi
riservati d'ufficio, e il resto viene rimappato sul più vicino con pesi tarati
sulla sensibilità dell'occhio.

```bash
python3 make_art.py 80 42    # colonne, righe; poi rilancia generate.py
```

La griglia è 80×42 e non quadrata perché una cella di testo è alta circa il
doppio di quanto è larga: servono più colonne che righe per non schiacciare il
volto.

### Il pannello scuro

L'arte sta su un rettangolo scuro in **entrambi** i temi. Non è un vezzo: i
colori sono quelli veri dell'avatar, e su fondo bianco un teschio bianco non si
può disegnare. Invertire i toni non risolve — sparirebbe la benda nera — e
comprimere la gamma appiattisce il contrasto fino a rendere il volto illeggibile
(provato: viene una macchia bruna uniforme).

Col pannello, invece, l'avatar è identico nei due temi. In tema scuro il
rettangolo è `#0d1117`, cioè lo stesso fondo di GitHub, quindi non si vede; in
tema chiaro diventa una finestra di terminale. Si regola da `THEMES` in
`generate.py` con `art_bg`, più `art_floor`/`art_ceil` che tengono i toni
dell'avatar dentro una gamma leggibile.

### Un limite da conoscere

Un'ASCII **monocroma** in stile Andrew6rant da questo avatar non viene, e non è
questione di parametri. L'ASCII codifica una cosa sola, la densità, cioè il
tono. La sua sorgente è una foto: toni continui, volto illuminato su fondo nero
— tono e spazio vuoto, esattamente ciò che i caratteri sanno rendere. Qui invece
l'informazione sta nella tinta e in campiture piatte a bordi netti, e il volto
riempie il fotogramma. Togliendo la pelle per creare il vuoto si perde il
teschio dentro la benda; tenendo tutto viene poltiglia.

Se un giorno vuoi la resa monocroma, la strada non è ritoccare lo script ma
cambiare sorgente: un mezzo busto dello stesso personaggio, **fondo nero**, luce
laterale forte, spazio attorno alla testa. Con quella `make_art.py` può tornare
a una rampa lunga e a un solo colore.

Serve `pillow` solo per `make_art.py`. `generate.py` usa la sola libreria
standard.
