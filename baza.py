import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. KONFIGURACJA I POŁĄCZENIE ---
# Dane pobierane z .streamlit/secrets.toml
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    st.error("Błąd: Brak kluczy Supabase w secrets.toml!")
    st.stop()

@st.cache_resource
def init_connection():
    return create_client(URL, KEY)

supabase = init_connection()

# --- 2. FUNKCJE LOGICZNE (CRUD) ---

def get_categories():
    """Pobiera dostępne kategorie."""
    res = supabase.table("kategorie").select("id, nazwa").execute()
    return {item['nazwa']: item['id'] for item in res.data}

def add_category(name, description):
    """Dodaje nową kategorię."""
    supabase.table("kategorie").insert({"nazwa": name, "opis": description}).execute()

def add_product(name, quantity, price, cat_id):
    """Dodaje nowy produkt."""
    data = {
        "nazwa": name,
        "liczba": quantity,
        "cena": price,
        "kategoria_id": cat_id
    }
    supabase.table("produkty").insert(data).execute()

def delete_product(product_id):
    """Usuwa produkt po ID."""
    supabase.table("produkty").delete().eq("id", product_id).execute()

# --- 3. INTERFEJS UŻYTKOWNIKA (UI) ---

st.set_page_config(page_title="Magazyn v2", layout="wide")
st.title("📦 System Zarządzania Magazynem")

# Sidebar - nawigacja
menu = st.sidebar.radio("Menu", ["Podgląd i Usuwanie", "Dodaj Produkt", "Dodaj Kategorię"])

# --- SEKCJA: DODAWANIE KATEGORII ---
if menu == "Dodaj Kategorię":
    st.header("Nowa Kategoria")
    with st.form("kat_form", clear_on_submit=True):
        n = st.text_input("Nazwa kategorii")
        o = st.text_area("Opis")
        if st.form_submit_button("Zapisz"):
            if n:
                add_category(n, o)
                st.success(f"Dodano: {n}")
            else:
                st.warning("Podaj nazwę!")

# --- SEKCJA: DODAWANIE PRODUKTU ---
elif menu == "Dodaj Produkt":
    st.header("Nowy Produkt")
    kategorie = get_categories()
    
    if not kategorie:
        st.error("Najpierw dodaj kategorię w menu bocznym!")
    else:
        with st.form("prod_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                p_nazwa = st.text_input("Nazwa produktu")
                p_cena = st.number_input("Cena (PLN)", min_value=0.0, step=0.01)
            with col2:
                p_ilosc = st.number_input("Ilość", min_value=0, step=1)
                p_kat = st.selectbox("Kategoria", options=list(kategorie.keys()))
            
            if st.form_submit_button("Dodaj do bazy"):
                if p_nazwa:
                    add_product(p_nazwa, p_ilosc, p_cena, kategorie[p_kat])
                    st.success(f"Produkt {p_nazwa} został dodany.")
                else:
                    st.warning("Nazwa jest wymagana!")

# --- SEKCJA: PODGLĄD I USUWANIE ---
elif menu == "Podgląd i Usuwanie":
    st.header("Stan Magazynowy")
    
    # Pobranie danych z JOINEM (pobieramy nazwę kategorii z relacji)
    res = supabase.table("produkty").select("id, nazwa, liczba, cena, kategorie(nazwa)").execute()
    
    if res.data:
        # Formatowanie danych do tabeli
        df_data = []
        for item in res.data:
            df_data.append({
                "ID": item['id'],
                "Nazwa": item['nazwa'],
                "Ilość": item['liczba'],
                "Cena": f"{item['cena']:.2f} zł",
                "Kategoria": item['kategorie']['nazwa'] if item['kategorie'] else "Brak"
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("Usuń produkt")
        # Wybór produktu do usunięcia
        options = {f"{row['Nazwa']} (ID: {row['ID']})": row['ID'] for row in df_data}
        target = st.selectbox("Wybierz produkt", options=list(options.keys()))
        
        if st.button("Usuń zaznaczony produkt", type="primary"):
            delete_product(options[target])
            st.rerun()
    else:
        st.info("Magazyn jest pusty.")
