import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- KONFIGURACJA POŁĄCZENIA ---
# Upewnij się, że w .streamlit/secrets.toml masz zdefiniowane SUPABASE_URL i SUPABASE_KEY
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_connection():
    return create_client(URL, KEY)

supabase = init_connection()

# --- FUNKCJE POMOCNICZE ---
def get_categories():
    """Pobiera kategorie i zwraca słownik {nazwa: id}."""
    try:
        res = supabase.table("kategorie").select("id, nazwa").execute()
        return {item['nazwa']: item['id'] for item in res.data}
    except Exception as e:
        st.error(f"Błąd pobierania kategorii: {e}")
        return {}

def delete_product(product_id):
    """Usuwa produkt z bazy i odświeża stronę."""
    try:
        supabase.table("produkty").delete().eq("id", product_id).execute()
        st.success("Produkt został pomyślnie usunięty!")
        st.rerun()
    except Exception as e:
        st.error(f"Nie udało się usunąć produktu: {e}")

# --- INTERFEJS UŻYTKOWNIKA ---
st.set_page_config(page_title="Magazyn Supabase", layout="centered")
st.title("📦 System Zarządzania Produktami")

# --- PANEL 1: DODAWANIE KATEGORII ---
with st.expander("➕ Dodaj nową kategorię"):
    with st.form("category_form", clear_on_submit=True):
        kat_nazwa = st.text_input("Nazwa kategorii")
        kat_opis = st.text_area("Opis kategorii")
        submit_kat = st.form_submit_button("Zapisz kategorię")

        if submit_kat:
            if kat_nazwa:
                supabase.table("kategorie").insert({"nazwa": kat_nazwa, "opis": kat_opis}).execute()
                st.success(f"Dodano kategorię: {kat_nazwa}")
                st.rerun()
            else:
                st.error("Nazwa kategorii jest wymagana!")

# --- PANEL 2: DODAWANIE PRODUKTU ---
st.header("Dodaj nowy produkt")
categories_dict = get_categories()

if not categories_dict:
    st.warning("Najpierw dodaj przynajmniej jedną kategorię!")
else:
    with st.form("product_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            prod_nazwa = st.text_input("Nazwa produktu")
            prod_cena = st.number_input("Cena", min_value=0.0, format="%.2f")
        with col2:
            prod_liczba = st.number_input("Liczba (sztuki)", min_value=0, step=1)
            wybrana_kat_nazwa = st.selectbox("Wybierz kategorię", options=list(categories_dict.keys()))
        
        submit_prod = st.form_submit_button("Dodaj produkt do bazy")

        if submit_prod:
            if prod_nazwa:
                prod_data = {
                    "nazwa": prod_nazwa,
                    "liczba": prod_liczba,
                    "cena": prod_cena,
                    "kategoria_id": categories_dict[wybrana_kat_nazwa]
                }
                supabase.table("produkty").insert(prod_data).execute()
                st.success(f"Dodano produkt: {prod_nazwa}")
                st.rerun()
            else:
                st.error("Uzupełnij nazwę produktu!")

st.divider()

# --- PANEL 3: PODGLĄD I USUWANIE ---
st.header("📋 Aktualny stan magazynowy")

# Pobranie danych produktów wraz z nazwą kategorii (Join)
products_res = supabase.table("produkty").select("id, nazwa, liczba, cena, kategorie(nazwa)").execute()
products_list = products_res.data

if products_list:
    # Przygotowanie danych do tabeli
    display_data = []
    for p in products_list:
        display_data.append({
            "ID": p['id'],
            "Nazwa": p['nazwa'],
            "Sztuki": p['liczba'],
            "Cena": f"{p['cena']:.2f} zł",
            "Kategoria": p['kategorie']['nazwa'] if p['kategorie'] else "Brak"
        })
    
    df = pd.DataFrame(display_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Sekcja usuwania
    st.subheader("🗑️ Usuwanie produktów")
    delete_options = {f"{p['nazwa']} (ID: {p['id']})": p['id'] for p in products_list}
    
    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        to_delete_label = st.selectbox("Wybierz produkt do usunięcia", options=list(delete_options.keys()))
    with col_btn:
        st.write(" ") # Odstęp dla wyrównania
        st.write(" ")
        if st.button("Usuń trwale", type="primary", use_container_width=True):
            delete_product(delete_options[to_delete_label])
else:
    st.info("Baza danych jest obecnie pusta.")
