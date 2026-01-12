import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="Magazyn Pro", layout="wide", page_icon="📊")

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

# --- 2. FUNKCJE POBIERANIA DANYCH ---
def get_categories():
    res = supabase.table("kategorie").select("*").execute()
    return res.data

def get_products():
    res = supabase.table("produkty").select("id, nazwa, liczba, cena, kategorie(nazwa)").execute()
    return res.data

# --- 3. INTERFEJS ---
st.title("🚀 System Magazynowy z Analityką")

tab1, tab2, tab3 = st.tabs(["🛍️ Produkty", "📂 Kategorie", "📈 Analityka"])

# --- TABELA PRODUKTY (Z USUWANIEM) ---
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
            df_p = df_p.rename(columns={'id': 'ID', 'nazwa': 'Nazwa', 'liczba': 'Sztuki', 'cena': 'Cena', 'kategorie.nazwa': 'Kategoria'})
            st.dataframe(df_p[['ID', 'Nazwa', 'Sztuki', 'Cena', 'Kategoria']], use_container_width=True, hide_index=True)
            
            p_del = st.selectbox("Wybierz ID do usunięcia", options=[p['id'] for p in prods])
            if st.button("Usuń produkt", type="primary"):
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
            cols = [c for c in ['id', 'nazwa', 'opis'] if c in df_kat.columns]
            st.table(df_kat[cols])

# --- TABELA ANALITYKA I WYKRESY ---
with tab3:
    st.header("📊 Raport Magazynowy")
    prods = get_products()
    
    if prods:
        df_raw = pd.json_normalize(prods)
        # Obliczanie łącznej wartości
        df_raw['Wartość'] = df_raw['liczba'] * df_raw['cena']
        
        # Statystyki ogólne
        m1, m2, m3 = st.columns(3)
        m1.metric("Suma sztuk", int(df_raw['liczba'].sum()))
        m2.metric("Łączna wartość", f"{df_raw['Wartość'].sum():,.2f} zł")
        m3.metric("Liczba produktów", len(df_raw))

        st.divider()
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("📦 Ilość towaru wg kategorii")
            # Grupowanie danych do wykresu
            chart_data = df_raw.groupby('kategorie.nazwa')['liczba'].sum()
            st.bar_chart(chart_data)

        with col_right:
            st.subheader("💰 Wartość magazynu wg kategorii")
            val_data = df_raw.groupby('kategorie.nazwa')['Wartość'].sum()
            st.area_chart(val_data)
            
        st.subheader("📄 Podsumowanie tabelaryczne")
        summary_df = df_raw.groupby('kategorie.nazwa').agg({
            'id': 'count',
            'liczba': 'sum',
            'Wartość': 'sum'
        }).rename(columns={'id': 'Ilość typów', 'liczba': 'Suma sztuk', 'Wartość': 'Suma wartość (zł)'})
        st.dataframe(summary_df, use_container_width=True)
    else:
        st.info("Dodaj produkty, aby zobaczyć statystyki.")
