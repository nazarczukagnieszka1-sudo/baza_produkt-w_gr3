import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- KONFIGURACJA ---
st.set_page_config(page_title="Magazyn Supabase", layout="wide")

@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        st.error("Błąd: Brak kluczy w Secrets!")
        st.stop()

supabase = init_connection()

# --- FUNKCJE ---
def get_categories():
    res = supabase.table("kategorie").select("*").execute()
    return res.data

def get_products():
    # Pobieramy produkty z nazwą kategorii
    res = supabase.table("produkty").select("id, nazwa, liczba, cena, kategorie(nazwa)").execute()
    return res.data

# --- UI ---
st.title("📦 System Zarządzania Magazynem")
tab1, tab2 = st.tabs(["🛍️ Produkty", "📂 Kategorie"])

# --- TABELA PRODUKTY ---
with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Dodaj produkt")
        kat_data = get_categories()
        kat_dict = {item['nazwa']: item['id'] for item in kat_data}
        
        with st.form("f_prod", clear_on_submit=True):
            n = st.text_input("Nazwa")
            l = st.number_input("Ilość", min_value=0)
            c = st.number_input("Cena", min_value=0.0)
            k = st.selectbox("Kategoria", options=list(kat_dict.keys()) if kat_dict else ["Brak"])
            if st.form_submit_button("Zapisz"):
                if n and kat_dict:
                    supabase.table("produkty").insert({"nazwa": n, "liczba": l, "cena": c, "kategoria_id": kat_dict[k]}).execute()
                    st.rerun()

    with col2:
        st.subheader("Lista produktów")
        prods = get_products()
        if prods:
            df_p = pd.json_normalize(prods)
            # Mapowanie nazw kolumn (obsługa kropek z json_normalize)
            rename_map = {'id': 'ID', 'nazwa': 'Nazwa', 'liczba': 'Sztuki', 'cena': 'Cena', 'kategorie.nazwa': 'Kategoria'}
            df_p = df_p.rename(columns=rename_map)
            # Wyświetlamy tylko te kolumny, które faktycznie istnieją w DataFrame
            cols_to_show = [c for c in rename_map.values() if c in df_p.columns]
            st.dataframe(df_p[cols_to_show], use_container_width=True, hide_index=True)
            
            # USUWANIE PRODUKTU
            st.divider()
            p_del = st.selectbox("Usuń produkt (ID)", options=[p['id'] for p in prods])
            if st.button("Usuń produkt"):
                supabase.table("produkty").delete().eq("id", p_del).execute()
                st.rerun()

# --- TABELA KATEGORIE ---
with tab2:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Dodaj kategorię")
        with st.form("f_kat", clear_on_submit=True):
            kn = st.text_input("Nazwa kategorii")
            ko = st.text_area("Opis")
            if st.form_submit_button("Zapisz"):
                if kn:
                    supabase.table("kategorie").insert({"nazwa": kn, "opis": ko}).execute()
                    st.rerun()

    with c2:
        st.subheader("Lista kategorii")
        kats = get_categories()
        if kats:
            df_kat = pd.DataFrame(kats)
            
            # --- ROZWIĄZANIE BŁĘDU KeyError ---
            # Sprawdzamy, które kolumny z listy ['id', 'nazwa', 'opis'] faktycznie są w df_kat
            wymagane_kolumny = ['id', 'nazwa', 'opis']
            istniejace_kolumny = [col for col in wymagane_kolumny if col in df_kat.columns]
            
            st.table(df_kat[istniejace_kolumny])
            
            # USUWANIE KATEGORII
            st.divider()
            k_del = st.selectbox("Usuń kategorię (ID)", options=[k['id'] for k in kats])
            if st.button("Usuń kategorię"):
                try:
                    supabase.table("kategorie").delete().eq("id", k_del).execute()
                    st.rerun()
                except:
                    st.error("Nie można usunąć kategorii, która ma przypisane produkty!")
        else:
            st.info("Brak kategorii.")
