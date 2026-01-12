import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="System Magazynowy", layout="wide", page_icon="📦")

# --- POŁĄCZENIE Z SUPABASE ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Nie znaleziono konfiguracji w st.secrets!")
        st.stop()

supabase = init_connection()

# --- FUNKCJE LOGICZNE ---
def get_categories():
    res = supabase.table("kategorie").select("id, nazwa").execute()
    return {item['nazwa']: item['id'] for item in res.data}

def get_products():
    # Join z tabelą kategorie, aby pobrać nazwę zamiast ID
    res = supabase.table("produkty").select("id, nazwa, liczba, cena, kategorie(nazwa)").execute()
    return res.data

# --- INTERFEJS ---
st.title("📦 System Zarządzania Produktami")

tabs = st.tabs(["📊 Podgląd i Usuwanie", "➕ Dodaj Produkt", "📂 Kategorie"])

# --- TAB 1: PODGLĄD I USUWANIE ---
with tabs[0]:
    st.header("Aktualny stan magazynowy")
    products = get_products()
    
    if products:
        # Przygotowanie danych do tabeli
        data_for_df = []
        for p in products:
            data_for_df.append({
                "ID": p['id'],
                "Nazwa": p['nazwa'],
                "Ilość": p['liczba'],
                "Cena (PLN)": f"{p['cena']:.2f}",
                "Kategoria": p['kategorie']['nazwa'] if p['kategorie'] else "Brak"
            })
        
        df = pd.DataFrame(data_for_df)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("🗑️ Usuń produkt")
        
        # Selectbox do wyboru produktu do usunięcia
        product_to_del_label = st.selectbox(
            "Wybierz produkt do usunięcia", 
            options=[f"{p['nazwa']} (ID: {p['id']})" for p in products]
        )
        
        if st.button("Potwierdź usunięcie", type="primary"):
            # Wyciąganie ID z etykiety (tekst przed pierwszym nawiasem)
            prod_id = next(p['id'] for p in products if f"{p['nazwa']} (ID: {p['id']})" == product_to_del_label)
            
            try:
                supabase.table("produkty").delete().eq("id", prod_id).execute()
                st.success("Produkt został usunięty!")
                st.rerun()
            except Exception as e:
                st.error(f"Błąd podczas usuwania: {e}")
    else:
        st.info("Magazyn jest pusty.")

# --- TAB 2: DODAJ PRODUKT ---
with tabs[1]:
    st.header("Dodaj nowy produkt")
    categories = get_categories()
    
    if not categories:
        st.warning("Najpierw dodaj kategorię w zakładce 'Kategorie'!")
    else:
        with st.form("add_product_form", clear_on_submit=True):
            name = st.text_input("Nazwa produktu")
            col1, col2 = st.columns(2)
            qty = col1.number_input("Ilość", min_value=0, step=1)
            price = col2.number_input("Cena", min_value=0.0, format="%.2f")
            category_name = st.selectbox("Kategoria", options=list(categories.keys()))
            
            if st.form_submit_button("Dodaj produkt"):
                if name:
                    new_prod = {
                        "nazwa": name,
                        "liczba": qty,
                        "cena": price,
                        "kategoria_id": categories[category_name]
                    }
                    supabase.table("produkty").insert(new_prod).execute()
                    st.success(f"Dodano produkt: {name}")
                    st.rerun()
                else:
                    st.error("Nazwa produktu nie może być pusta!")

# --- TAB 3: KATEGORIE ---
with tabs[2]:
    st.header("Zarządzaj kategoriami")
    with st.form("add_cat_form", clear_on_submit=True):
        cat_name = st.text_input("Nazwa nowej kategorii")
        cat_desc = st.text_area("Opis (opcjonalnie)")
        if st.form_submit_button("Dodaj kategorię"):
            if cat_name:
                supabase.table("kategorie").insert({"nazwa": cat_name, "opis": cat_desc}).execute()
                st.success(f"Dodano kategorię: {cat_name}")
                st.rerun()
            else:
                st.error("Podaj nazwę kategorii!")
