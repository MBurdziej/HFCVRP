# Vehicle Routing Problem (VRP) Solver

## Opis

Ten skrypt wykorzystuje bibliotekę OR-Tools od Google do rozwiązania problemu optymalizacji tras pojazdów (VRP). Program pobiera dane z Google Maps API, w tym macierz odległości i czasy przejazdu między lokalizacjami, a następnie przydziela pojazdy o określonej pojemności i kosztach do klientów w sposób minimalizujący całkowity koszt transportu.

## Wymagania

- Python 3.7+
- Google OR-Tools
- Google Maps API Key

## Instalacja

1. Zainstaluj wymagane biblioteki:
   ```sh
   pip install ortools googlemaps
   ```
2. Uzyskaj klucz API Google Maps i uzupełnij wartość w kodzie:
   ```python
   gmaps = googlemaps.Client(key="TWOJ_GOOGLE_MAPS_API_KEY")
   ```

## Struktura danych

- **`clients`** – lista klientów wraz z ich lokalizacją i zapotrzebowaniem.
- **`depot`** – lokalizacja magazynu.
- **`vehicle_data`** – dane o pojazdach (pojemność, zużycie paliwa, koszt paliwa, stawka godzinowa, limit czasu).

## Działanie

1. Pobierane są dane o odległościach i czasach przejazdu między lokalizacjami.
2. OR-Tools tworzy model VRP i optymalizuje trasy, uwzględniając:
   - pojemność pojazdów,
   - koszty paliwa i pracy kierowcy,
   - ograniczenia czasowe.
3. Program wypisuje zoptymalizowane trasy dla każdego pojazdu wraz ze szczegółowymi kosztami transportu.

## Uruchomienie

Wystarczy uruchomić skrypt:
```sh
python HFCVRP.py
```

## Wynik

Dla każdego pojazdu program zwraca:
- trasę przejazdu,
- całkowity koszt transportu,
- przejechany dystans,
- czas w trasie,
- zużycie paliwa,
- koszt paliwa i pracy kierowcy.

Na końcu wyświetlany jest całkowity koszt wszystkich tras.
Przykładowy wynik:

Trasa dla pojazdu 4: Katowice, Polska -> Gdańsk, Polska -> Warszawa, Polska -> Katowice, Polska

Koszt trasy: 1265.75 zł

Przejechana odległość: 1161.55 km

Czas w trasie: 11 godz 59 min

Paliwo zużyte: 139.39 l

Koszt paliwa: 906.01 zł

Koszt kierowcy: 359.74 zł

