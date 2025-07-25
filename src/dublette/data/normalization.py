"""
Data Normalization Module for Duplicate Detection POC

This module provides comprehensive data normalization functions for partner data
to improve duplicate detection accuracy. The normalization follows a structured
approach:

1. Basic text normalization (uppercase, trim, unicode)
2. Domain-specific normalization (addresses, names, cities)
3. Date normalization
4. Final cleanup (remove spaces and special characters)

The module is designed to be resource-efficient and doesn't rely on external
ML models or hardcoded mappings.
"""

import pandas as pd
import re
import unicodedata


def normalize_text_basic(text: str) -> str:
    """
    Grundlegende Textnormalisierung ohne externe Modelle.

    Schritte:
    1. In Großbuchstaben umwandeln
    2. Trimmen
    3. Unicode-Normalisierung (deutsche Umlaute)

    Args:
        text (str): Zu normalisierender Text

    Returns:
        str: Normalisierter Text
    """
    if pd.isna(text) or text is None:
        return ""

    # 1. In Großbuchstaben umwandeln
    text = str(text).upper()

    # 2. Trimmen
    text = text.strip()

    # 3. Unicode-Normalisierung für deutsche Zeichen
    text = unicodedata.normalize("NFD", text)

    # Deutsche Umlaute manuell behandeln (häufigste Fälle)
    # Das ist ressourcenschonend und deckt die wichtigsten deutschen Zeichen ab
    replacements = {
        "Ä": "AE",
        "Ö": "OE",
        "Ü": "UE",
        "ß": "SS",
        "À": "A",
        "Á": "A",
        "Â": "A",
        "Ã": "A",
        "È": "E",
        "É": "E",
        "Ê": "E",
        "Ë": "E",
        "Ì": "I",
        "Í": "I",
        "Î": "I",
        "Ï": "I",
        "Ò": "O",
        "Ó": "O",
        "Ô": "O",
        "Õ": "O",
        "Ù": "U",
        "Ú": "U",
        "Û": "U",
        "Ç": "C",
        "Ñ": "N",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def normalize_address(address: str) -> str:
    """
    Spezielle Normalisierung für Adressen.

    Behandelt häufige Variationen in deutschen Adressen:
    - STR./STRAßE -> STRASSE
    - Andere Abkürzungen (PL. -> PLATZ, etc.)

    Args:
        address (str): Adresse

    Returns:
        str: Normalisierte Adresse
    """
    if pd.isna(address) or address is None:
        return ""

    address = normalize_text_basic(address)

    # 4. STR. und STRAßE normalisieren
    address = re.sub(r"\bSTR\b\.?", "STRASSE", address)
    address = re.sub(r"\bSTRASSE\b", "STRASSE", address)

    # Weitere häufige Abkürzungen in deutschen Adressen
    address_replacements = {
        r"\bPL\b\.?": "PLATZ",
        r"\bPLZ\b\.?": "PLATZ",
        r"\bALLE\b": "ALLEE",
        r"\bDAMM\b": "DAMM",
        r"\bWEG\b": "WEG",
        r"\bGASSE\b": "GASSE",
        r"\bRING\b": "RING",
        r"\bUFER\b": "UFER",
        r"\bBRUECKE\b": "BRUECKE",
        r"\bTOR\b": "TOR",
        r"\bHOF\b": "HOF",
        r"\bNR\b\.?": "",  # Hausnummer-Kennzeichnung entfernen
        r"\bNUMMER\b": "",
    }

    for pattern, replacement in address_replacements.items():
        address = re.sub(pattern, replacement, address)

    return address


def normalize_name(name: str) -> str:
    """
    Spezielle Normalisierung für Namen (Vor- und Nachnamen).

    Verwendet phonetische Ähnlichkeitsmuster ohne externe Modelle.
    Behandelt häufige Variationen in deutschen Namen.

    Args:
        name (str): Name

    Returns:
        str: Normalisierter Name
    """
    if pd.isna(name) or name is None:
        return ""

    name = normalize_text_basic(name)

    # Häufige phonetische Variationen von Namen normalisieren
    # Basiert auf häufigen deutschen Schreibweisen und Aussprachen
    name_patterns = {
        r"\bCH\b": "K",  # Christian -> Kristian
        r"\bPH\b": "F",  # Philipp -> Filip
        r"\bTH\b": "T",  # Thomas -> Tomas
        r"\bCK\b": "K",  # Dirck -> Dirk
        r"\bQU\b": "KW",  # Quelle -> Kwelle
        r"\bX\b": "KS",  # Alexander -> Aleksander
        r"\bZ\b": "S",  # Franz -> Frans (in einigen Dialekten)
        r"\bY\b": "I",  # Yvonne -> Ivonne
        r"\bV\b": "F",  # Veit -> Feit (phonetisch)
        r"\bW\b": "V",  # Wilhelm -> Vilhelm
    }

    for pattern, replacement in name_patterns.items():
        name = re.sub(pattern, replacement, name)

    # Doppelte Konsonanten reduzieren (häufig bei Namen)
    name = re.sub(r"([BCDFGHJKLMNPQRSTVWXZ])\1+", r"\1", name)

    return name


def normalize_city(city: str) -> str:
    """
    Spezielle Normalisierung für Ortsnamen.

    Behandelt häufige Variationen in deutschen Ortsnamen.

    Args:
        city (str): Ortsname

    Returns:
        str: Normalisierter Ortsname
    """
    if pd.isna(city) or city is None:
        return ""

    city = normalize_text_basic(city)

    # Häufige Variationen in deutschen Ortsnamen
    city_patterns = {
        r"\bAM\b": "A",  # Frankfurt am Main -> Frankfurt A Main
        r"\bIM\b": "I",  # Weiden in der Oberpfalz
        r"\bBEI\b": "B",  # Neustadt bei Coburg
        r"\bAN\b": "A",  # Rothenburg an der Tauber
        r"\bAUF\b": "A",  # Roth auf der Roth
        r"\bINS\b": "I",  #
        r"\bUNTER\b": "U",  # Bad Reichenhall unter
        r"\bOBER\b": "O",  # Oberammergau
        r"\bNIEDER\b": "N",  # Niederbrechen
        r"\bGROSS\b": "G",  # Grossbottwar
        r"\bKLEIN\b": "K",  # Kleinmachnow
        r"\bSANKT\b": "ST",  # Sankt Augustin -> St Augustin
        r"\bST\b\.?": "ST",  # St. -> ST
        r"\bBAD\b": "B",  # Bad Homburg -> B Homburg
    }

    for pattern, replacement in city_patterns.items():
        city = re.sub(pattern, replacement, city)

    return city


def normalize_date(date_str: str) -> str:
    """
    Datumsnormalisierung - vereinheitlicht auf YYYY-MM-DD Format.
    Behält Sonderzeichen bei (Bindestriche).

    Args:
        date_str (str): Datum als String

    Returns:
        str: Normalisiertes Datum im Format YYYY-MM-DD
    """
    if pd.isna(date_str) or date_str is None:
        return ""

    # Nur Leerzeichen trimmen, Sonderzeichen beibehalten
    date_str = str(date_str).strip()

    # Versuche verschiedene Datumsformate zu parsen
    date_patterns = [
        r"(\d{4})-(\d{2})-(\d{2})",  # YYYY-MM-DD (bereits korrekt)
        r"(\d{2})\.(\d{2})\.(\d{4})",  # DD.MM.YYYY (deutsch)
        r"(\d{2})/(\d{2})/(\d{4})",  # DD/MM/YYYY
        r"(\d{4})(\d{2})(\d{2})",  # YYYYMMDD (ohne Trenner)
        r"(\d{1,2})\.(\d{1,2})\.(\d{4})",  # D.M.YYYY oder DD.MM.YYYY
        r"(\d{4})/(\d{2})/(\d{2})",  # YYYY/MM/DD
    ]

    for pattern in date_patterns:
        match = re.search(pattern, date_str)
        if match:
            groups = match.groups()
            if len(groups) == 3:
                # Bestimme Format basierend auf der ersten Gruppe
                if len(groups[0]) == 4:  # Jahr zuerst (YYYY-MM-DD, YYYY/MM/DD)
                    year, month, day = groups
                else:  # Tag zuerst (DD.MM.YYYY, DD/MM/YYYY)
                    day, month, year = groups

                # Validierung und Formatierung
                try:
                    day, month, year = int(day), int(month), int(year)

                    # Grundlegende Plausibilitätsprüfung
                    if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                        return f"{year:04d}-{month:02d}-{day:02d}"

                except ValueError:
                    continue

    # Fallback: Original zurückgeben wenn kein gültiges Format erkannt
    return date_str


def remove_special_chars_and_spaces(text: str, preserve_date_chars: bool = False) -> str:
    """
    Entfernt Leerzeichen und Sonderzeichen (außer bei Datumsfeldern).

    Dies ist der finale Normalisierungsschritt.

    Args:
        text (str): Text
        preserve_date_chars (bool): Ob Datums-Sonderzeichen beibehalten werden sollen

    Returns:
        str: Bereinigter Text
    """
    if pd.isna(text) or text is None:
        return ""

    text = str(text)

    if preserve_date_chars:
        # Nur Leerzeichen entfernen, Datums-Sonderzeichen (Bindestriche) behalten
        text = re.sub(r"\s+", "", text)
    else:
        # Alle Leerzeichen entfernen
        text = re.sub(r"\s+", "", text)
        # Sonderzeichen entfernen (nur Buchstaben und Zahlen behalten)
        text = re.sub(r"[^A-Z0-9]", "", text)

    return text


def normalize_partner_data(
    df: pd.DataFrame,
    normalize_for_splink: bool = True,
    enhanced_mode: bool = False,
    phonetic_names: bool = False,
    fuzzy_cities: bool = False,
    nlp_addresses: bool = False,
) -> pd.DataFrame:
    """
    Vollständige Normalisierung der Partnerdaten mit optionalen Erweiterungen.

    Führt alle Normalisierungsschritte in der korrekten Reihenfolge durch:
    1. Grundlegende Normalisierung (Groß, Trim, Unicode)
    2. Spezielle Normalisierung nach Spaltentyp (mit optionalen Erweiterungen)
    3. Datumsnormalisierung
    4. Finale Bereinigung (Leerzeichen und Sonderzeichen)

    Args:
        df (pd.DataFrame): DataFrame mit Partnerdaten
        normalize_for_splink (bool): Ob finale Bereinigung für Splink durchgeführt werden soll
        enhanced_mode (bool): Aktiviert alle erweiterten Algorithmen
        phonetic_names (bool): Phonetische Algorithmen für Namen
        fuzzy_cities (bool): Fuzzy-Matching für Ortsnamen
        nlp_addresses (bool): NLP-basierte Adresserweiterungen

    Returns:
        pd.DataFrame: Normalisiertes DataFrame
    """
    if df is None or df.empty:
        return df

    df_normalized = df.copy()

    # Enhanced mode aktiviert alle Erweiterungen
    if enhanced_mode:
        phonetic_names = True
        fuzzy_cities = True
        nlp_addresses = True

    print("Starte umfassende Datennormalisierung...")
    print(f"Anzahl Datensätze: {len(df_normalized)}")
    print(f"Spalten: {list(df_normalized.columns)}")

    if enhanced_mode:
        print("🚀 Enhanced Mode aktiviert - verwende erweiterte Algorithmen")

    # Check optional dependencies
    optional_deps = {}
    if phonetic_names or fuzzy_cities:
        try:
            import jellyfish

            optional_deps["jellyfish"] = True
            print("✓ jellyfish verfügbar für phonetische/fuzzy Algorithmen")
        except ImportError:
            optional_deps["jellyfish"] = False
            print("⚠ jellyfish nicht installiert - verwende Standard-Algorithmen")

    # Schritt 1-3: Spezielle Normalisierung nach Spaltentyp
    for column in df_normalized.columns:
        print(f"  Normalisiere Spalte: {column}")

        if column in ["NAME"]:
            if phonetic_names and optional_deps.get("jellyfish", False):
                df_normalized[column] = df_normalized[column].apply(lambda x: normalize_name_enhanced(x, use_phonetic=True))
            else:
                df_normalized[column] = df_normalized[column].apply(normalize_name)

        elif column in ["VORNAME"]:
            if phonetic_names and optional_deps.get("jellyfish", False):
                df_normalized[column] = df_normalized[column].apply(lambda x: normalize_name_enhanced(x, use_phonetic=True))
            else:
                df_normalized[column] = df_normalized[column].apply(normalize_name)

        elif column in ["ORT"]:
            if fuzzy_cities and optional_deps.get("jellyfish", False):
                df_normalized[column] = df_normalized[column].apply(lambda x: normalize_city_enhanced(x, fuzzy_matching=True))
            else:
                df_normalized[column] = df_normalized[column].apply(normalize_city)

        elif column in ["ADRESSZEILE"]:
            if nlp_addresses:
                df_normalized[column] = df_normalized[column].apply(lambda x: normalize_address_enhanced(x, use_nlp=True))
            else:
                df_normalized[column] = df_normalized[column].apply(normalize_address)

        elif column in ["GEBURTSDATUM"]:
            df_normalized[column] = df_normalized[column].apply(normalize_date)
        else:
            # Grundlegende Normalisierung für alle anderen Spalten
            df_normalized[column] = df_normalized[column].apply(normalize_text_basic)

    # Schritt 4: Finale Bereinigung für Splink (optional)
    if normalize_for_splink:
        print("  Finale Bereinigung: Entferne Leerzeichen und Sonderzeichen...")

        for column in df_normalized.columns:
            if column == "GEBURTSDATUM":
                # Bei Datum nur Leerzeichen entfernen, Bindestriche behalten
                df_normalized[column] = df_normalized[column].apply(
                    lambda x: remove_special_chars_and_spaces(x, preserve_date_chars=True)
                )
            else:
                # Bei allen anderen Spalten: Leerzeichen und Sonderzeichen entfernen
                df_normalized[column] = df_normalized[column].apply(
                    lambda x: remove_special_chars_and_spaces(x, preserve_date_chars=False)
                )

    print("Datennormalisierung erfolgreich abgeschlossen!")

    # Zeige Beispiele der Normalisierung
    if len(df_normalized) > 0:
        print("\nBeispiele der Normalisierung:")
        for column in ["NAME", "VORNAME", "ORT", "ADRESSZEILE"][:3]:
            if column in df_normalized.columns:
                original = df.iloc[0][column] if not pd.isna(df.iloc[0][column]) else "N/A"
                normalized = df_normalized.iloc[0][column] if not pd.isna(df_normalized.iloc[0][column]) else "N/A"
                print(f"  {column}: '{original}' -> '{normalized}'")

    return df_normalized


def get_normalization_statistics(df_original: pd.DataFrame, df_normalized: pd.DataFrame) -> dict:
    """
    Erstellt Statistiken über die Normalisierung.

    Args:
        df_original (pd.DataFrame): Original DataFrame
        df_normalized (pd.DataFrame): Normalisiertes DataFrame

    Returns:
        dict: Statistiken über die Normalisierung
    """
    stats = {"total_records": len(df_original), "columns_processed": len(df_original.columns), "changes_by_column": {}}

    for column in df_original.columns:
        if column in df_normalized.columns:
            original_values = df_original[column].astype(str)
            normalized_values = df_normalized[column].astype(str)

            changes = (original_values != normalized_values).sum()
            change_percentage = (changes / len(df_original)) * 100

            stats["changes_by_column"][column] = {"changes": int(changes), "change_percentage": round(change_percentage, 2)}

    return stats


# === ENHANCED HYBRID NORMALIZATION FUNCTIONS ===


def normalize_name_enhanced(name: str, use_phonetic: bool = False) -> str:
    """
    Erweiterte Namen-Normalisierung mit optionaler phonetischer Komponente.

    Kombiniert die bestehende regelbasierte Normalisierung mit optionalen
    phonetischen Algorithmen für bessere Duplikaterkennung.

    Args:
        name (str): Name
        use_phonetic (bool): Ob phonetische Algorithmen verwendet werden sollen

    Returns:
        str: Normalisierter Name
    """
    # Basis-Normalisierung (bereits vorhanden und bewährt)
    name = normalize_name(name)

    # Optional: Phonetische Erweiterung
    if use_phonetic:
        try:
            import jellyfish

            # Soundex für deutsche Namen - robuster als Metaphone
            phonetic_code = jellyfish.soundex(name)
            # Kombiniere beide für beste Ergebnisse
            return f"{name}_{phonetic_code}" if phonetic_code else name
        except ImportError:
            # Graceful fallback - keine Abhängigkeit erzwungen
            print("  Hinweis: jellyfish nicht installiert, verwende Standard-Normalisierung")

    return name


def normalize_city_enhanced(city: str, fuzzy_matching: bool = False) -> str:
    """
    Erweiterte Orts-Normalisierung mit optionalem Fuzzy-Matching.

    Erweitert die bestehende Ortsnormalisierung um Fuzzy-Matching gegen
    eine kleine Liste häufiger deutscher Städte.

    Args:
        city (str): Ortsname
        fuzzy_matching (bool): Ob Fuzzy-Matching verwendet werden soll

    Returns:
        str: Normalisierter Ortsname
    """
    # Basis-Normalisierung (bereits vorhanden)
    city = normalize_city(city)

    # Optional: Fuzzy-Matching gegen bekannte deutsche Städte
    if fuzzy_matching:
        try:
            import jellyfish

            # Kleine Liste häufiger deutscher Städte (nur Großstädte)
            # Bewusst klein gehalten für Performance und Genauigkeit
            major_cities = {
                "BERLIN",
                "HAMBURG",
                "MUENCHEN",
                "KOELN",
                "FRANKFURT",
                "STUTTGART",
                "DUESSELDORF",
                "DORTMUND",
                "ESSEN",
                "LEIPZIG",
                "BREMEN",
                "DRESDEN",
                "HANNOVER",
                "NUERNBERG",
                "DUISBURG",
            }

            best_match = None
            best_score = 0

            for ref_city in major_cities:
                score = jellyfish.jaro_winkler_similarity(city, ref_city)
                if score > best_score and score > 0.85:  # Hoher Threshold für Genauigkeit
                    best_score = score
                    best_match = ref_city

            if best_match:
                # print(f"    Fuzzy-Match: '{city}' -> '{best_match}' (Score: {best_score:.2f})")
                return best_match

        except ImportError:
            print("  Hinweis: jellyfish nicht installiert, verwende Standard-Normalisierung")
        except Exception as e:
            print(f"  Hinweis: Fuzzy-Matching fehlgeschlagen ({e}), verwende Standard-Normalisierung")

    return city


def normalize_address_enhanced(address: str, use_nlp: bool = False) -> str:
    """
    Erweiterte Adress-Normalisierung mit optionaler NLP-Komponente.

    Args:
        address (str): Adresse
        use_nlp (bool): Ob NLP-basierte Erweiterungen verwendet werden sollen

    Returns:
        str: Normalisierte Adresse
    """
    # Basis-Normalisierung (bereits vorhanden und sehr gut)
    address = normalize_address(address)

    # Optional: NLP-basierte Erweiterungen für komplexere Adressen
    if use_nlp:
        try:
            # Hier könnte spaCy oder andere NLP-Tools integriert werden
            # Für jetzt: Zusätzliche Regex-Patterns für komplexere Fälle

            # Hausnummern normalisieren
            address = re.sub(r"(\d+)\s*([A-Z])\b", r"\1\2", address)  # "123 A" -> "123A"

            # Postfächer
            address = re.sub(r"\bPOSTFACH\b", "PF", address)
            address = re.sub(r"\bPF\b\.?", "PF", address)

        except Exception as e:
            print(f"  Hinweis: Erweiterte Adressnormalisierung fehlgeschlagen ({e})")

    return address
