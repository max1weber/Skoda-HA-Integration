# Škoda Connect voor Home Assistant

[🇬🇧 English](README.md) | [🇳🇱 Nederlands](README.nl.md)

Een meertalige [Home Assistant](https://www.home-assistant.io/) custom integration voor
Škoda-voertuigen, gebouwd op de officiële publieke MySkoda API
([public.api.connect.skoda-auto.cz](https://public.api.connect.skoda-auto.cz/docs)) via de
actief onderhouden [`myskoda`](https://github.com/skodaconnect/myskoda) Python-client.

> **Niet-officieel project.** Deze integratie is niet verbonden met, onderschreven door, of
> geassocieerd met Škoda Auto. Ze gebruikt dezelfde publieke API als de officiële MySkoda-app.
> Gebruik op eigen risico.

## Functies

Gebouwd volgens de huidige best practices voor Home Assistant-integraties: een config flow die
volledig via de UI werkt, een `DataUpdateCoordinator` voor efficiënte polling,
entity-descriptions, vertalingen per entiteit, een opties-flow, ondersteuning voor
opnieuw-aanmelden, en een diagnostics-download.

| Platform | Entiteiten |
|---|---|
| `sensor` | Batterijniveau, laadvermogen, laadsnelheid, resterende laadtijd, actieradius (batterij/totaal), brandstofniveau, AdBlue-bereik, kilometerstand, buiten-/doeltemperatuur, softwareversie |
| `binary_sensor` | Portieren, ramen, kofferbak, motorkap, verlichting, aan het laden, laadkabel aangesloten |
| `lock` | Centrale vergrendeling (vereist S-PIN) |
| `device_tracker` | Laatst bekende GPS-locatie van het voertuig |
| `climate` | Airconditioning op afstand (aan/uit, ventilatie, doeltemperatuur) |
| `switch` | Ruitverwarming, laden, batterijbeschermingsmodus, verminderde laadstroom |
| `button` | Claxon en knipperlichten, lichten laten knipperen, voertuig wekken |
| `number` | AC-laadlimiet (state of charge) |

Sensoren en bedieningselementen worden alleen aangemaakt voor data die jouw specifieke voertuig
ook daadwerkelijk levert. De entiteitenlijst past zich dus automatisch aan de mogelijkheden van
je auto aan (elektrisch, plug-in hybride, of verbrandingsmotor).

Er is een **alleen-lezen modus** die je in de opties van de integratie kunt inschakelen om alle
bedieningsfuncties (vergrendelen, klimaatregeling, laden, knoppen) uit te schakelen, terwijl alle
sensoren actief blijven.

## Ondersteunde talen

De integratie bevat vertalingen voor de config flow, de opties-flow en de entiteitsnamen in:

- English (`en`)
- Nederlands (`nl`)
- Deutsch (`de`)
- Français (`fr`)
- Čeština (`cs`)
- Slovenčina (`sk`)

Home Assistant kiest automatisch de vertaling die overeenkomt met de taalinstelling van je
installatie, met Engels als terugvaloptie. Bijdragen voor extra talen zijn welkom — voeg een
nieuw bestand toe onder `custom_components/skoda_connect/translations/`.

Ook deze documentatie is beschikbaar in het [Engels](README.md) en het
[Nederlands](README.nl.md).

## Installatie

### HACS (aanbevolen)

1. Ga in HACS naar **Integraties** → menu (⋮) → **Aangepaste repositories**.
2. Voeg de URL van deze repository toe
   (`https://github.com/max1weber/Skoda-HA-Integration`) met categorie **Integration**.
3. Zoek in HACS naar "Škoda Connect", klik op **Downloaden** en installeer de integratie.
4. Herstart Home Assistant.

### Handmatig

1. Download of clone deze repository.
2. Kopieer de map `custom_components/skoda_connect` naar de map
   `config/custom_components/` van je Home Assistant-installatie, zodat je uitkomt op
   `config/custom_components/skoda_connect/manifest.json`.
3. Herstart Home Assistant.

## Configuratie

1. Ga naar **Instellingen → Apparaten en diensten → Integratie toevoegen** en zoek naar
   "Škoda Connect".
2. Vul het e-mailadres en wachtwoord in dat je ook gebruikt in de MySkoda-app.
3. Vul optioneel je S-PIN in — dit is nodig om de vergrendel-entiteit te kunnen gebruiken.
4. Home Assistant controleert de inloggegevens en maakt bij succes één apparaat aan per
   voertuig op het account, met alle van toepassing zijnde entiteiten.
5. Open na het instellen het **Configureren**-dialoogvenster van de integratie om het
   vernieuwingsinterval aan te passen (1–1440 minuten, standaard 30) of de alleen-lezen modus
   in te schakelen.

Als je sessie verloopt, toont Home Assistant een melding om "opnieuw aan te melden" — klik
erop en voer je wachtwoord opnieuw in om de verbinding te herstellen zonder de geschiedenis
van je entiteiten te verliezen.

## Over de API

Deze integratie maakt bewust gebruik van het door de community onderhouden `myskoda`
PyPI-pakket, in plaats van zelf een OAuth2/REST/MQTT-client voor Škoda te bouwen. Zo profiteert
de integratie van updates en dekking van de steeds veranderende voertuigmogelijkheden van de
publieke API. Data wordt alleen ververst via polling — MQTT-pushmeldingen van de API worden
niet gebruikt, wat de integratie eenvoudig houdt en een extra faalpunt vermijdt.

## Disclaimer

Aangeboden zoals het is, zonder garantie. Škoda Auto kan zijn API op elk moment wijzigen,
waardoor deze integratie kan stoppen met werken. Gebruik van de publieke MySkoda API valt
onder de eigen gebruiksvoorwaarden van Škoda.
