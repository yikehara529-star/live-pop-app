import streamlit as st
import sqlite3
from PIL import Image, ImageDraw, ImageFont

# --- ページ設定 ---
st.set_page_config(page_title="お笑いライブ管理＆告知ポップ作成", layout="centered")
st.title("🎙️ お笑いライブ管理＆告知ポップ")

# --- データベース接続 ---
def get_db():
    conn = sqlite3.connect('live_schedule.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        live_name TEXT NOT NULL,
        live_date TEXT NOT NULL,
        place TEXT NOT NULL
    )
    ''')
    conn.commit()
    return conn, cursor

# --- 紫基調ポップ画像の生成 ---
def make_purple_pop():
    conn, cursor = get_db()
    cursor.execute('SELECT live_name, live_date, place FROM schedule WHERE live_date >= date("now") ORDER BY live_date ASC LIMIT 4')
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None

    width, height = 1000, 1200
    img = Image.new('RGB', (width, height), color='#2E004B')
    draw = ImageDraw.Draw(img)

    font_path = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
    font_title = ImageFont.truetype(font_path, 80)
    font_item_title = ImageFont.truetype(font_path, 48)
    font_item_sub = ImageFont.truetype(font_path, 36)

    # ヘッダー背景
    top_img = Image.new('RGB', (width, 400), color='#6A0DAD')
    img.paste(top_img, (0, 0))
    draw = ImageDraw.Draw(img)

    # タイトル
    draw.text((105, 75), "LIVE SCHEDULE", font=font_title, fill='#FF69B4')
    draw.text((100, 70), "LIVE SCHEDULE", font=font_title, fill='#FFFFFF')
    draw.text((100, 170), "★ 出演情報 ★", font=font_item_title, fill='#00FFFF')

    start_y = 280
    spacing = 210
    accent_colors = ['#FF69B4', '#00FFFF', '#FFD700']

    for i, row in enumerate(rows):
        live_name, live_date, place = row
        current_y = start_y + (i * spacing)
        color = accent_colors[i % len(accent_colors)]

        # 座布団・枠線
        draw.rounded_rectangle([(70, current_y - 20), (930, current_y + 170)], radius=20, fill='#4B0082')
        draw.rectangle([(80, current_y), (95, current_y + 150)], fill=color)

        # 文字
        draw.text((123, current_y + 5), live_name, font=font_item_title, fill='#000000')
        draw.text((120, current_y), live_name, font=font_item_title, fill=color)
        draw.text((150, current_y + 65), f"日時：{live_date}", font=font_item_sub, fill='#FFFFFF')
        draw.text((150, current_y + 110), f"会場：{place}", font=font_item_sub, fill='#FFFFFF')

    # フッター
    draw.rectangle([(0, height - 120), (width, height)], fill='#FF69B4')
    footer_text = "チケット取り置きはDMまでお気軽に！"
    f_w = draw.textlength(footer_text, font=font_item_sub)
    draw.text(((width - f_w) / 2, height - 80), footer_text, font=font_item_sub, fill='#FFFFFF')

    img.save("summary_pop.png")
    return "summary_pop.png"

# --- メイン画面（タブ構成） ---
tab1, tab2, tab3 = st.tabs(["➕ 予定追加", "📋 予定一覧", "🎨 ポップ作成"])

# 【タブ1】予定追加
with tab1:
    st.subheader("新しいライブ予定を追加")
    with st.form("add_form", clear_on_submit=True):
        live_name = st.text_input("ライブ名", placeholder="例：渋谷お笑い寄席")
        date_val = st.date_input("開催日")
        time_val = st.time_input("開演時間")
        place = st.text_input("会場名", placeholder="例：渋谷CBGE")
        
        submitted = st.form_submit_button("予定を保存する", type="primary")
        if submitted:
            if live_name and place:
                datetime_str = f"{date_val} {time_val.strftime('%H:%M')}"
                conn, cursor = get_db()
                cursor.execute('INSERT INTO schedule (live_name, live_date, place) VALUES (?, ?, ?)',
                               (live_name, datetime_str, place))
                conn.commit()
                conn.close()
                st.success(f"『{live_name}』を追加しました！")
            else:
                st.error("ライブ名と会場名を入力してください。")

# 【タブ2】予定一覧＆削除
with tab2:
    st.subheader("登録済みのライブ一覧")
    conn, cursor = get_db()
    cursor.execute('SELECT id, live_name, live_date, place FROM schedule ORDER BY live_date ASC')
    rows = cursor.fetchall()
    conn.close()

    if rows:
        for row in rows:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{row[1]}**")
                st.caption(f"📅 {row[2]} | 📍 {row[3]}")
            with col2:
                if st.button("削除", key=f"del_{row[0]}"):
                    conn, cursor = get_db()
                    cursor.execute('DELETE FROM schedule WHERE id = ?', (row[0],))
                    conn.commit()
                    conn.close()
                    st.rerun()
            st.divider()
    else:
        st.info("登録されている予定はありません。")

# 【タブ3】ポップ作成
with tab3:
    st.subheader("告知用ポップ画像を生成")
    st.write("登録されている最新の予定（最大4件）を入れた画像を生成します。")
    
    if st.button("告知ポップを作成する", type="primary"):
        img_path = make_purple_pop()
        if img_path:
            st.image(img_path, caption="完成した告知ポップ", use_container_width=True)
            with open(img_path, "rb") as file:
                st.download_button(
                    label="画像をスマホに保存",
                    data=file,
                    file_name="live_schedule.png",
                    mime="image/png"
                )
        else:
            st.warning("これからの予定が登録されていません。「予定追加」タブから登録してください。")
