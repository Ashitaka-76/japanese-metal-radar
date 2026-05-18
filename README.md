# Japanese Metal Radar 🎸

Monitora automaticamente le nuove uscite discografiche di artisti J-Metal / J-Rock
e le aggiunge nella playlist **Playlist Giappone** di YouTube Music.

Gira ogni giorno tramite GitHub Actions — zero manutenzione dopo il setup.

---

## Artisti monitorati

| Artista | Genere |
|---|---|
| BABYMETAL | J-Metal / Idol Metal |
| BAND-MAID | Hard Rock / Heavy Metal |
| Wagakki Band | Japanese Traditional Rock |
| Ado | J-Pop / Alternative |
| Maximum the Hormone | Nu-Metal / Punk |
| NEMOPHILA | Heavy Metal |
| Haku | J-Rock |
| HAGANE | J-Metal |

Puoi aggiungerne altri in qualsiasi momento (vedi sotto).

---

## Setup (una volta sola)

### 1. Clona il repository

```bash
git clone https://github.com/TUO-USERNAME/japanese-metal-radar.git
cd japanese-metal-radar
```

### 2. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 3. Autentica YouTube Music

```bash
python setup_auth.py
```

Questo aprirà il browser e genererà il file `oauth.json`.  
**Non committare mai `oauth.json`** — è già in `.gitignore`.

### 4. Aggiungi il secret su GitHub

1. Vai su **Settings → Secrets and variables → Actions** nel tuo repo
2. Crea un nuovo secret chiamato `YTMUSIC_OAUTH`
3. Incolla il contenuto **completo** di `oauth.json` come valore

### 5. Primo avvio — importa tutti i brani

Localmente:
```bash
python main.py --first-run
```

Oppure da GitHub Actions: vai su **Actions → Japanese Metal Radar → Run workflow**
e spunta l'opzione *"Primo avvio"*.

Questo creerà la playlist **Playlist Giappone** e importerà tutti i brani
esistenti degli artisti monitorati.

---

## Utilizzo quotidiano

GitHub Actions esegue automaticamente lo script ogni giorno alle 09:00 (ora italiana).
Non devi fare nulla — i nuovi brani appaiono in playlist da soli.

Per eseguire manualmente un aggiornamento:
```bash
python main.py
```

---

## Aggiungere un nuovo artista

```bash
python main.py --add-artist "Nome Artista"
```

Questo aggiorna `config/artists.json`. Alla prossima esecuzione (o con `--first-run`
per importare subito i brani esistenti) l'artista verrà monitorato.

---

## Struttura del progetto

```
japanese-metal-radar/
├── .github/workflows/radar.yml   # Automazione giornaliera
├── config/artists.json           # Lista artisti (modificabile)
├── data/state.json               # Stato persistente (committato)
├── src/
│   ├── radar.py                  # Logica principale
│   ├── ytmusic_client.py         # Wrapper ytmusicapi
│   └── state.py                  # Gestione stato
├── main.py                       # Entry point CLI
├── setup_auth.py                 # Setup OAuth (una volta sola)
└── requirements.txt
```

---

## Note tecniche

- Usa [`ytmusicapi`](https://ytmusicapi.readthedocs.io/) per interagire con YouTube Music
- Lo stato (album già processati, ID playlist) è salvato in `data/state.json`
  e committato automaticamente dal workflow per persistere tra le esecuzioni
- I duplicati sono gestiti lato API (`duplicates=False`) e lato stato locale
- Le chiamate API sono rallentate per evitare rate limiting

---

## Licenza

MIT
