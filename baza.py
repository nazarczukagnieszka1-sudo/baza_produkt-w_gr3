import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Magazyn Supabase", layout="wide", page_icon="📦")

# --- POŁĄCZENIE Z SUPABASE ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        st.error("Błąd: Skonfiguruj SUPABASE_URL i SUPABASE_KEY w Secrets!")
        st.stop()

supabase = init_connection()

# --- FUNKCJE POMOCNICZE ---
def get_categories():
    res = supabase.table("kategorie").select("id, nazwa").execute()
    return res.data

def get_products():
    # Pobieramy produkty wraz z nazwą kategorii dzięki relacji klucza obcego
    res = supabase.table("produkty").select("id, nazwa, liczba, cena, kategorie(nazwa)").execute()
    return res.data

# --- INTERFEJS UŻYTKOWNIKA ---
st.title("📦 System Zarządzania Magazynem")

tab1, tab2 = st.tabs(["🛍️ Produkty", "📂 Kategorie"])

# --- TAB 1: ZARZĄDZANIE PRODUKTAMI ---
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Dodaj produkt")
        kategorie_data = get_categories()
        kat_options = {item['nazwa']: item['id'] for item in kategorie_data}
        
        with st.form("form_produkt", clear_on_submit=True):
            p_nazwa = st.text_input("Nazwa produktu")
            p_liczba = st.number_input("Ilość", min_value=0, step=1)
            p_cena = st.number_input("Cena", min_value=0.0, format="%.2f")
            p_kat = st.selectbox("Kategoria", options=list(kat_options.keys()) if kat_options else ["Brak kategorii"])
            
            if st.form_submit_button("Zapisz produkt"):
                if p_nazwa and kat_options:
                    supabase.table("produkty").insert({
                        "nazwa": p_nazwa, 
                        "liczba": p_liczba, 
                        "cena": p_cena, 
                        "kategoria_id": kat_options[p_kat]
                    }).execute()
                    st.success("Dodano produkt!")
                    st.rerun()

    with col2:
        st.subheader("Lista produktów")
        produkty = get_products()
        if produkty:
            df_prod = pd.json_normalize(produkty)
            # Zmiana nazw kolumn dla czytelności
            df_prod = df_prod.rename(columns={
                'id': 'ID', 'nazwa': 'Nazwa', 'liczba': 'Sztuki', 
                'cena': 'Cena', 'kategorie.nazwa': 'Kategoria'
            })
            st.dataframe(df_prod[['ID', 'Nazwa', 'Sztuki', 'Cena', 'Kategoria']], use_container_width=True, hide_index=True)
            
            st.divider()
            st.subheader("Usuń produkt")
            p_to_del = st.selectbox("Wybierz produkt do usunięcia", options=[p['id'] for p in produkty], format_func=lambda x: next(p['nazwa'] for p in produkty if p['id'] == x))
            if st.button("Usuń wybrany produkt", type="primary"):
                supabase.table("produkty").delete().eq("id", p_to_del).execute()
                st.success("Usunięto!")
                st.rerun()
        else:
            st.info("Brak produktów.")

# --- TAB 2: ZARZĄDZANIE KATEGORIAMI ---
with tab2:
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        st.subheader("Dodaj kategorię")
        with st.form("form_kategoria", clear_on_submit=True):
            k_nazwa = st.text_input("Nazwa kategorii")
            k_opis = st.text_area("Opis")
            if st.form_submit_button("Zapisz kategorię"):
                if k_nazwa:
                    supabase.table("kategorie").insert({"nazwa": k_nazwa, "opis": k_opis}).execute()
                    st.success("Dodano kategorię!")
                    st.rerun()

    with col_b:
        st.subheader("Lista kategorii")
        kategorie = get_categories()
        if kategorie:
            df_kat = pd.DataFrame(kategorie)
            st.table(df_kat[['id', 'nazwa', 'opis']])
            
            st.divider()
            st.subheader("Usuń kategorię")
            st.warning("Uwaga: Usunięcie kategorii może usunąć przypisane do niej produkty (zależnie od ustawień bazy SQL).")
            k_to_del = st.selectbox("Wybierz kategorię do usunięcia", options=[k['id'] for k in kategorie], format_func=lambda x: next(k['nazwa'] for k in kategorie if k['id'] == x))
            if st.button("Usuń wybraną kategorię", type="primary"):
                try:
                    supabase.table("kategorie").delete().eq("id", k_to_del).execute()
                    st.success("Usunięto kategorię!")
                    st.rerun()
                except Exception as e:
                    st.error("Nie można usunąć kategorii, która posiada produkty (błąd klucza obcego).")
        else:
            st.info("Brak kategorii.")
