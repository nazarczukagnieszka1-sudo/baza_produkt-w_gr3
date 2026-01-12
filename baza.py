import streamlit as st
import pandas as pd

# Zakładamy, że funkcja get_products() jest już zdefiniowana w Twoim kodzie
with tab3:
    st.header("📊 Zaawansowana Analityka Magazynu")
    prods = get_products()
    
    if prods:
        # 1. PRZYGOTOWANIE DANYCH
        df = pd.json_normalize(prods)
        df['Wartość'] = df['liczba'] * df['cena']
        df = df.rename(columns={
            'nazwa': 'Produkt',
            'liczba': 'Stan',
            'cena': 'Cena_Jedn',
            'kategorie.nazwa': 'Kategoria'
        })

        # 2. WSKAŹNIKI KLUCZOWE (KPI)
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        
        total_value = df['Wartość'].sum()
        total_items = df['Stan'].sum()
        avg_price = df['Cena_Jedn'].mean()
        low_stock_count = df[df['Stan'] < 5].shape[0] # Produkty poniżej 5 sztuk

        col_kpi1.metric("Wartość Magazynu", f"{total_value:,.2f} zł")
        col_kpi2.metric("Suma Produktów", f"{int(total_items)} szt.")
        col_kpi3.metric("Średnia Cena", f"{avg_price:.2f} zł")
        col_kpi4.metric("Niski Stan (<5 szt.)", low_stock_count, delta_color="inverse")

        st.divider()

        # 3. WYKRESY PORÓWNAWCZE
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("📦 Ranking ilościowy kategorii")
            cat_qty = df.groupby('Kategoria')['Stan'].sum().sort_values(ascending=True)
            st.bar_chart(cat_qty, horizontal=True)

        with c2:
            st.subheader("💰 Podział wartościowy")
            cat_val = df.groupby('Kategoria')['Wartość'].sum()
            # Używamy area_chart dla wizualizacji rozkładu wartości
            st.area_chart(cat_val)

        st.divider()

        # 4. TABELA ANALITYCZNA Z ALERTAMI
        st.subheader("🔍 Szczegółowy wykaz produktów")
        
        # Funkcja kolorująca niskie stany magazynowe
        def highlight_low_stock(val):
            color = '#ff4b4b' if val < 5 else 'none'
            return f'background-color: {color}'

        # Wybieramy i formatujemy kolumny do raportu
        report_df = df[['Produkt', 'Kategoria', 'Stan', 'Cena_Jedn', 'Wartość']]
        
        st.dataframe(
            report_df.style.map(highlight_low_stock, subset=['Stan']),
            use_container_width=True,
            hide_index=True
        )

        # 5. DODATKOWE PODSUMOWANIE (TOP 3)
        st.subheader("🏆 Najdroższe pozycje w magazynie")
        top_expensive = df.nlargest(3, 'Wartość')[['Produkt', 'Stan', 'Wartość']]
        st.table(top_expensive)

    else:
        st.info("Brak danych do analizy. Dodaj produkty w zakładce 'Produkty'.")
