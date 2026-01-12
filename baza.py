import streamlit as st
import pandas as pd

# Sekcja Analityki (Tab 3)
with tab3:
    st.header("📊 Analityka i Raporty Magazynowe")
    prods = get_products()
    
    if prods:
        # --- 1. PRZYGOTOWANIE I CZYSZCZENIE DANYCH ---
        df = pd.json_normalize(prods)
        df['Wartość'] = df['liczba'] * df['cena']
        
        # Zmiana nazw na bardziej przyjazne
        df = df.rename(columns={
            'nazwa': 'Produkt',
            'liczba': 'Stan',
            'cena': 'Cena_Jedn',
            'kategorie.nazwa': 'Kategoria'
        })

        # --- 2. KLUCZOWE WSKAŹNIKI (KPI) ---
        # Wyglądają jak kafelki na dashboardzie
        m1, m2, m3, m4 = st.columns(4)
        
        total_value = df['Wartość'].sum()
        total_items = df['Stan'].sum()
        low_stock_threshold = 5
        low_stock_df = df[df['Stan'] <= low_stock_threshold]

        m1.metric("Wartość Magazynu", f"{total_value:,.2f} zł")
        m2.metric("Łączna Ilość", f"{int(total_items)} szt.")
        m3.metric("Liczba Kategorii", len(df['Kategoria'].unique()))
        m4.metric("Niski Stan (≤5)", len(low_stock_df), delta="- Uwaga!", delta_color="inverse")

        st.divider()

        # --- 3. WIZUALIZACJA DANYCH ---
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("📦 Struktura zapasów wg kategorii")
            # Wykres horyzontalny jest czytelniejszy przy długich nazwach kategorii
            cat_qty = df.groupby('Kategoria')['Stan'].sum().sort_values(ascending=True)
            st.bar_chart(cat_qty, horizontal=True, color="#29b5e8")

        with col_right:
            st.subheader("💰 Wartość towaru w kategoriach")
            cat_val = df.groupby('Kategoria')['Wartość'].sum().sort_values(ascending=False)
            st.area_chart(cat_val, color="#ff4b4b")

        st.divider()

        # --- 4. INTERAKTYWNA TABELA Z ALERTAMI ---
        st.subheader("🔍 Szczegółowy wykaz z alertami")
        st.info("💡 Produkty podświetlone na czerwono wymagają pilnego uzupełnienia (stan ≤ 5).")

        # Funkcja formatująca kolory
        def style_low_stock(row):
            return ['background-color: #ffcccc' if row.Stan <= low_stock_threshold else '' for _ in row]

        # Wyświetlanie sformatowanej tabeli
        st.dataframe(
            df[['Produkt', 'Kategoria', 'Stan', 'Cena_Jedn', 'Wartość']]
            .style.apply(style_low_stock, axis=1)
            .format({'Cena_Jedn': '{:.2f} zł', 'Wartość': '{:.2f} zł'}),
            use_container_width=True,
            hide_index=True
        )

        # --- 5. TOP 5 NAJDROŻSZYCH ZASOBÓW ---
        with st.expander("🏆 Zobacz TOP 5 najbardziej wartościowych produktów"):
            top_5 = df.nlargest(5, 'Wartość')[['Produkt', 'Kategoria', 'Wartość']]
            st.table(top_5)

    else:
        st.warning("Brak danych do wygenerowania analizy. Dodaj produkty w pierwszej zakładce.")
