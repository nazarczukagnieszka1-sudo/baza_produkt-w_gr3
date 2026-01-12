import streamlit as st
from supabase import create_client, Client

# Konfiguracja połączenia z Supabase
# W wersji produkcyjnej użyj st.secrets dla bezpieczeństwa
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_connection():
    return create_client(URL, KEY)

supabase = init_connection()

st.title("📦 System Zarządzania Produktami")

# --- PANEL KATEGORII ---
st.header("Dodaj nową kategorię")
with st.form("category_form", clear_on_submit=True):
    kat_nazwa = st.text_input("Nazwa kategorii")
    kat_opis = st.text_area("Opis kategorii")
    submit_kat = st.form_submit_button("Dodaj kategorię")

    if submit_kat:
        if kat_nazwa:
            data = {"nazwa": kat_nazwa, "opis": kat_opis}
            response = supabase.table("kategorie").insert(data).execute()
            st.success(f"Dodano kategorię: {kat_nazwa}")
        else:
            st.error("Nazwa kategorii jest wymagana!")

st.divider()

# --- PANEL PRODUKTÓW ---
st.header("Dodaj nowy produkt")

# Pobranie aktualnych kategorii do rozwijanej listy
def get_categories():
    res = supabase.table("kategorie").select("id, nazwa").execute()
    return {item['nazwa']: item['id'] for item in res.data}

categories_dict = get_categories()

with st.form("product_form", clear_on_submit=True):
    prod_nazwa = st.text_input("Nazwa produktu")
    prod_liczba = st.number_input("Liczba (sztuki)", min_value=0, step=1)
    prod_cena = st.number_input("Cena", min_value=0.0, format="%.2f")
    
    # Wybór kategorii z listy
    wybrana_kat_nazwa = st.selectbox("Wybierz kategorię", options=list(categories_dict.keys()))
    
    submit_prod = st.form_submit_button("Dodaj produkt")

    if submit_prod:
        if prod_nazwa and wybrana_kat_nazwa:
            prod_data = {
                "nazwa": prod_nazwa,
                "liczba": prod_liczba,
                "cena": prod_cena,
                "kategoria_id": categories_dict[wybrana_kat_nazwa]
            }
            supabase.table("produkty").insert(prod_data).execute()
            st.success(f"Dodano produkt: {prod_nazwa}")
        else:
            st.error("Uzupełnij nazwę produktu!")

# --- PODGLĄD DANYCH ---
if st.checkbox("Pokaż listę produktów"):
    st.subheader("Aktualne produkty w bazie")
    products_res = supabase.table("produkty").select("nazwa, liczba, cena, kategorie(nazwa)").execute()
    st.table(products_res.data)
