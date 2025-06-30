import os
import csv
import json

# --- Seller Follow-up Logic ---

SELLER_COUNTRY_LANG_MAP = {
    'Italy': 'it', 'France': 'fr', 'Belgium': 'fr', 'Switzerland': 'fr',
    'Canada': 'fr', 'USA': 'en', 'United States': 'en', 'UK': 'en',
    'Germany': 'en', 'Spain': 'en',
}

EXCLUDED_COUNTRIES = {
    "australia", "belarus", "brazil", "egypt", "germany", "india", "indonesia",
    "israel", "jordan", "korea republic of", "kuwait", "mexico", "moroco", "pakistan",
    "turkey", "ukraine", "united arab emirates", "united states"
}

def load_templates(file_path):
    """Loads a template dictionary from a JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Template file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_name(email):
    if '@' not in email:
        return "Client"
    return email.split('@')[0].split('.')[0].capitalize()

def get_seller_followup_email_generator(csv_path, start_email_str=None):
    """Generator function to yield one seller follow-up email at a time."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"File not found: {csv_path}")

    seller_templates = load_templates('seller_templates.json')
    start_output = False if start_email_str else True
    
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        total_rows = len(rows)

        if start_email_str:
            start_email_str_lower = start_email_str.lower()

        for i, row in enumerate(rows):
            row_index = i + 2  # CSV row number
            email = row.get('Email address', '').strip()
            country = row.get('Country', '').strip().lower()

            if start_email_str and not start_output:
                if email.lower() == start_email_str_lower:
                    start_output = True
                else:
                    continue 

            if not start_output or not email or country in EXCLUDED_COUNTRIES:
                continue

            name = extract_name(email)
            lang = SELLER_COUNTRY_LANG_MAP.get(country.title(), 'en')
            template = seller_templates.get(lang, seller_templates['en'])
            message = template.format(name=name)
            
            yield {
                "row_index": row_index, "email": email, "country": country,
                "language": lang, "message": message, "progress_current": i + 1,
                "progress_total": total_rows
            }

# --- Lead Email (Metabase) Logic ---

LEAD_COUNTRY_LANG_MAP = {
    'Italy': 'it', 'France': 'fr', 'Belgium': 'fr', 'Switzerland': 'fr',
    'Canada': 'fr', 'USA': 'en', 'United States': 'en', 'UK': 'en',
    'Germany': 'en', 'Spain': 'en',
}

def get_lead_email_generator(csv_path, price, link, machine):
    """Generator function to yield one lead email at a time."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"File not found: {csv_path}")

    lead_templates = load_templates('lead_templates.json')

    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        total_rows = len(rows)

        for i, row in enumerate(rows):
            if not all(k in row for k in ['Lead Email', 'Lead Country']):
                continue 
                
            email = row.get('Lead Email', '').strip()
            country = row.get('Lead Country', '').strip()

            if not email or not country:
                continue

            language = LEAD_COUNTRY_LANG_MAP.get(country, 'en')
            template = lead_templates.get(language, lead_templates['en'])
            name_part = email.split('@')[0].split('.')[0]
            name = name_part.capitalize()
            filled_email = template.format(name=name, machine=machine, price=price, link=link)

            yield {
                "email": email, "country": country, "language": language,
                "message": filled_email, "progress_current": i + 1, "progress_total": total_rows
            }
