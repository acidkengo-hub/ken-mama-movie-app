import streamlit as st
import requests
from bs4 import BeautifulSoup
import time

# --- すべての映画館のデータを一括で取得する関数 ---
# 🔥 v4に進化！今度こそ日付と時間を確実に結びつけます
@st.cache_data(ttl=3600)
def get_all_movie_schedules_v4():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    cinemas_urls = {
        "シアタス調布": "https://eiga.com/theater/13/130811/3275/",
        "TOHOシネマズ府中": "https://eiga.com/theater/13/130803/3104/",
        "シネマシティ": "https://eiga.com/theater/13/130802/3101/",
        "TOHOシネマズ立川立飛": "https://eiga.com/theater/13/130802/3309/",
        "吉祥寺オデヲン": "https://eiga.com/theater/13/130809/3109/",
        "アップリンク吉祥寺": "https://eiga.com/theater/13/130809/3285/"
    }
    
    all_data = {}
    ignore_list = [
        "イオンシネマ シアタス調布", "TOHOシネマズ府中", "シネマシティ", 
        "TOHOシネマズ立川立飛", "吉祥寺オデヲン", "アップリンク吉祥寺",
        "映画.com注目特集", "国内映画ランキング", "おすすめ情報", "特別企画", "注目作品ランキング", ""
    ]
    
    for cinema_name, url in cinemas_urls.items():
        try:
            response = requests.get(url, headers=headers)
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, 'html.parser')
            
            headings = soup.find_all('h2')
            cinema_schedule = {}
            
            for heading in headings:
                title = heading.text.strip()
                if title in ignore_list:
                    continue
                    
                schedule_table = heading.find_next('table')
                if schedule_table:
                    if "住所" in schedule_table.text or "電話番号" in schedule_table.text:
                        continue
                    
                    # 👇👇👇 【完全修正版】表の読み取りロジック 👇👇👇
                    dates = schedule_table.find_all('th')
                    times = schedule_table.find_all('td')
                    
                    formatted_schedule = ""
                    
                    # 日付(th)と時間(td)の数が対応しているかチェック
                    if len(dates) > 0 and len(times) >= len(dates):
                        for i in range(len(dates)):
                            date_text = dates[i].text.strip()
                            
                            # .stripped_stringsで、HTMLの改行コードなどを無視して時間だけをリストで取り出す！
                            time_elements = list(times[i].stripped_strings)
                            
                            if time_elements:
                                # ⏰をつけて太字の箇条書きに！
                                times_str = "\n".join([f"- **⏰ {t}**" for t in time_elements])
                                formatted_schedule += f"📅 {date_text}\n{times_str}\n\n"
                            else:
                                formatted_schedule += f"📅 {date_text}\n- 上映なし\n\n"
                    
                    # 綺麗にしたスケジュールを保存！
                    if formatted_schedule:
                        cinema_schedule[title] = formatted_schedule.strip()
                    else:
                        cinema_schedule[title] = schedule_table.text.strip().replace('\n', '  ')
                    # 👆👆👆 ここまで 👆👆👆
                        
            all_data[cinema_name] = cinema_schedule
        except Exception as e:
            print(f"エラー発生 ({cinema_name}): {e}")
            
        time.sleep(1) 
        
    return all_data

# --- 表側の画面：Streamlitの表示 ---
st.title("👩‍🦳 けんまま専用！映画スケジュール検索アプリ")

with st.spinner('すべての映画館の最新データを集めています...（約10秒お待ちください）'):
    # 🔥 関数を v4 に変更！
    all_schedules = get_all_movie_schedules_v4()

tab1, tab2 = st.tabs(["映画館から探す", "作品から探す"])

# --- タブ1：映画館から探す ---
with tab1:
    st.subheader("📍 エリアと映画館を選んでね")
    
    area = st.selectbox("エリア", ["調布", "府中", "立川", "吉祥寺"], key="area_tab1")
    
    cinemas_map = {
        "調布": ["シアタス調布"],
        "府中": ["TOHOシネマズ府中"],
        "立川": ["シネマシティ", "TOHOシネマズ立川立飛"],
        "吉祥寺": ["吉祥寺オデヲン", "アップリンク吉祥寺"]
    }
    
    selected_cinema_name = st.selectbox("映画館", cinemas_map[area], key="cinema_tab1")
    
    st.write(f"**{selected_cinema_name}** のスケジュール")
    
    cinema_data = all_schedules.get(selected_cinema_name, {})
    
    if cinema_data:
        for title, times in cinema_data.items():
            with st.expander(f"🍿 {title}"):
                # 🌟 変更前：st.markdown(times)
                # 🌟 変更後👇（### と半角スペースをつけます！）
                st.markdown(f"### {times}")
    else:
        st.warning("スケジュールの取得に失敗しました。時間をおいて再度お試しください。")

# --- タブ2：作品から探す ---
with tab2:
    st.subheader("🍿 観たい映画を選んでね")
    
    all_movie_titles = set()
    for cinema, schedule in all_schedules.items():
        for title in schedule.keys():
            all_movie_titles.add(title)
    
    sorted_movie_titles = sorted(list(all_movie_titles))
    
    if sorted_movie_titles:
        selected_movie = st.selectbox("① 作品を選択してください", sorted_movie_titles)
        
        playing_cinemas = []
        for cinema, schedule in all_schedules.items():
            if selected_movie in schedule:
                playing_cinemas.append(cinema)
        
        if playing_cinemas:
            st.write(f"**{selected_movie}** を上映している映画館")
            selected_cinema_for_movie = st.selectbox("② 映画館を選択してください", playing_cinemas, key="cinema_tab2")
            
            st.info(f"📍 **{selected_cinema_for_movie}** のスケジュール")
            movie_schedule = all_schedules[selected_cinema_for_movie][selected_movie]
            
            # 🌟 変更前：st.markdown(movie_schedule)
            # 🌟 変更後👇（こちらも ### と半角スペースをつけます！）
            st.markdown(f"### {movie_schedule}")
        else:
            st.warning("現在上映している映画館が見つかりません。")
    else:
        st.warning("作品リストが取得できませんでした。映画館のデータが空の可能性があります。")