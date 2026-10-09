import os
import pandas as pd
import streamlit as st
from streamlit_calendar import calendar
from datetime import datetime, timedelta

# ─── 🔑 【新機能】ログイン機能の設定 ───
# 大学のメンバーに教える「共通のIDとパスワード」をここで自由に決められます！
USER_ID = "agu"       # 好きなユーザーIDに変えてOK（半角英数字）
USER_PASS = "agu2026"       # 好きなパスワードに変えてOK（半角英数字）

# ログイン状態を記憶する箱を準備
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# まだログインしていない場合は、ログイン画面を強制表示
if not st.session_state["logged_in"]:
    st.set_page_config(layout="centered") # ログイン時は画面を中央にすっきり配置
    st.title("🔒 CLSM 予約システム - ログイン")
    st.write("このシステムは研究室・学内関係者専用です。認証情報を入力してください。")
    
    input_id = st.text_input("ユーザーID")
    input_pass = st.text_input("パスワード", type="password") # 入力文字が●になる安心設定
    
    if st.button("ログイン", type="primary"):
        if input_id == USER_ID and input_pass == USER_PASS:
            st.session_state["logged_in"] = True
            st.success("ログインに成功しました！画面を切り替えます...")
            st.rerun()
        else:
            st.error("❌ ユーザーIDまたはパスワードが正しくありません。")
            
    st.stop() # 💡 ログイン成功するまで、これより下のプログラム（カレンダーなど）を絶対に実行させない壁です

# ─── 🚀 ここから下は「ログイン成功後」だけが表示されるエリア ───
st.set_page_config(layout="wide") # カレンダーを広く見せるいつもの設定
st.title("⚙️ CLSM 予約システム（ログイン認証済）")

# 1. 機器の選択
selected_device = st.selectbox(
    "予約したい機器を選んでください",
    ["LSM800", "CLSM2"]
)

# 保存用ファイルの場所（デスクトップの yoyaku.csv）
file_path = os.path.expanduser("~/Desktop/yoyaku.csv")

# データの読み込みと初期化
if os.path.exists(file_path):
    try:
        df = pd.read_csv(file_path)
        df["ID"] = pd.to_numeric(df["ID"]).astype(int)
    except Exception:
        df = pd.DataFrame(columns=["ID", "名前", "機器", "日付", "開始時間", "終了時間"])
else:
    df = pd.DataFrame(columns=["ID", "名前", "機器", "日付", "開始時間", "終了時間"])

df_filtered = df[df["機器"] == selected_device]

# 2. カレンダー表示用のデータ作成
device_events = []
for _, row in df_filtered.iterrows():
    device_events.append({
        "id": str(int(row["ID"])),
        "title": f"{row['開始時間']}~{row['終了時間']} {row['名前']}様",
        "start": f"{row['日付']}T{row['開始時間']}:00",
        "end": f"{row['日付']}T{row['終了時間']}:00",
        "color": "#1f77b4" if selected_device == "3Dプリンター" else "#ff7f0e"
    })

# 3. 本格カレンダーの設定
calendar_options = {
    "initialView": "dayGridMonth",
    "selectable": False, 
    "dayMaxEvents": 3,
    "navLinks": False,
    "contentHeight": 600,
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": ""
    },
    "displayEventTime": False,
    "displayEventEnd": False
}

st.subheader(f"📅 【{selected_device}】の予約スケジュール")
st.info("💡 日付を1回クリックすると、下の新規予約パネルに連動します。")
st.info("💡 予約をクリックすると、変更・削除のポップアップが開きます。")

# 24時間30分刻みの時間リスト
time_slots = [f"{h:02d}:{m:02d}" for h in range(0, 24) for m in (0, 30)]

# ─── 🛠️ 4. 予約の変更・削除用ポップアップ（ダイアログ）機能 ───
@st.dialog("🔄 予約の変更・削除")
def show_edit_popup(event_id):
    current_df = pd.read_csv(file_path)
    current_df["ID"] = current_df["ID"].astype(int)
    
    target_rows = current_df[current_df["ID"] == int(event_id)]
    if target_rows.empty:
        st.error("該当する予約が見つかりませんでした。")
        return
        
    row_data = target_rows.iloc[0]
    st.write(f"対象機器: **{row_data['機器']}**")
    
    edit_name = st.text_input("名前の変更", value=row_data["名前"])
    current_event_date = datetime.strptime(str(row_data["日付"]), "%Y-%m-%d").date()
    edit_date = st.date_input("予約日の変更", value=current_event_date, key="edit_event_date")
    
    col3, col4 = st.columns(2)
    with col3:
        edit_start = st.selectbox("開始時間の変更", time_slots, index=time_slots.index(row_data["開始時間"]))
    with col4:
        edit_end = st.selectbox("終了時間の変更", time_slots, index=time_slots.index(row_data["終了時間"]))
        
    st.write("---")
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("変更を保存する", type="primary"):
            if edit_name == "":
                st.error("名前を入力してください。 例：名前（講座名）")
            elif edit_start >= edit_end:
                st.error("終了時間は開始時間より後の時間を選んでください。")
            else:
                current_df.loc[current_df["ID"] == int(event_id), ["名前", "日付", "開始時間", "終了時間"]] = [edit_name, str(edit_date), edit_start, edit_end]
                current_df.to_csv(file_path, index=False, encoding="utf-8-sig")
                st.success("予約内容を変更しました！")
                st.session_state["selected_date_raw"] = str(edit_date)
                st.rerun()
                
    with btn_col2:
        if st.button("❌ この予約を完全に削除する", type="secondary"):
            updated_df = current_df[current_df["ID"] != int(event_id)]
            updated_df.to_csv(file_path, index=False, encoding="utf-8-sig")
            st.success("予約を削除しました。")
            st.rerun()

# ─── 🚀 5. カレンダークリック時の判定と連動処理 ───
if "selected_date_raw" not in st.session_state:
    st.session_state["selected_date_raw"] = str(pd.Timestamp.now().date())

# CSSで「9a」の時間表示自体を物理的に非表示にします
state = calendar(
    events=device_events, 
    options=calendar_options, 
    custom_css="""
        .fc-daygrid-day { cursor: pointer !important; } 
        .fc-daygrid-day-frame { pointer-events: auto !important; }
        .fc-event { cursor: pointer !important; position: relative; z-index: 10; }
        .fc-event-time { display: none !important; }
    """, 
    key=f"perfect_cal_{selected_device}_{st.session_state['selected_date_raw']}"
)

if state:
    # 選択パターン①：予約の文字をクリックしたとき
    if "eventClick" in state and state["eventClick"]:
        event_id = state["eventClick"]["event"]["id"]
        clicked_event_row = df[df["ID"] == int(event_id)]
        if not clicked_event_row.empty:
            st.session_state["selected_date_raw"] = str(clicked_event_row.iloc[0]["日付"])
        show_edit_popup(event_id)
        
    # 選択パターン②：文字以外の白い部分をクリックしたとき
    elif "dateClick" in state and state["dateClick"]:
        if "date" in state["dateClick"]:
            raw_str = state["dateClick"]["date"]
            raw_date_str = raw_str.split("T")
            
            # 1日前の時差バグを完璧に日本時間に自動補正
            if "T" in raw_str and not raw_str.endswith("Z"):
                # 【大修正】リストの0番目（文字列）を確実に指定して型エラーを永久消滅させます
                correct_date_str = raw_date_str[0]
            else:
                dt = datetime.strptime(raw_date_str[0], "%Y-%m-%d")
                correct_date_str = (dt + timedelta(days=1)).strftime("%Y-%m-%d")
                
            if st.session_state["selected_date_raw"] != correct_date_str:
                st.session_state["selected_date_raw"] = correct_date_str
                st.rerun()

target_date_str = st.session_state["selected_date_raw"]

st.write("---")

# ─── 📝 6. 新規予約（左） と 時間割スケジュール（右） の横並び配置 ───
col_left, col_right = st.columns(2)

with col_right:
    st.subheader(f"📋 {target_date_str} の時間割スケジュール")
    df_day = df_filtered[df_filtered["日付"] == target_date_str].sort_values(by="開始時間")
    
    if df_day.empty:
        st.write("🔓 **この日の予約はありません。終日空いています！**")
    else:
        st.write("以下の時間帯に予約が入っています：")
        for _, row in df_day.iterrows():
            st.markdown(
                f"""
                <div style="background-color: #f0f2f6; padding: 10px; border-left: 5px solid #1f77b4; border-radius: 4px; margin-bottom: 8px;">
                    <span style="font-size: 15px; font-weight: bold; color: #31333F;">⏳ {row['開始時間']} 〜 {row['終了時間']}</span> 
                    <span style="font-size: 15px; margin-left: 15px; color: #31333F;">👤 {row['名前']}様</span>
                </div>
                """, 
                unsafe_allow_html=True
            )

with col_left:
    st.subheader("📝 新規予約を登録する")
    
    new_date_str = st.text_input("予約したい日（上のカレンダーをクリックすると自動で変わります）", value=target_date_str)
    new_name = st.text_input("名前を入力してください　例：名前（講座名）", key="add_name")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        start_t = st.selectbox("開始時間", time_slots, index=18, key="add_start") # 09:00
    with col_t2:
        end_t = st.selectbox("終了時間", time_slots, index=20, key="add_end")     # 10:00
        
    if st.button("この内容で予約を確定する", type="primary"):
        if new_name == "":
            st.error("名前を入力してください。")
        elif start_t >= end_t:
            st.error("終了時間は開始時間より後の時間を選んでください。")
        else:
            try:
                datetime.strptime(new_date_str, "%Y-%m-%d")
                new_id = int(df["ID"].max() + 1) if not df.empty else 1
                new_row = pd.DataFrame([[new_id, new_name, selected_device, new_date_str, start_t, end_t]], columns=df.columns)
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_csv(file_path, index=False, encoding="utf-8-sig")
                st.success(f"{new_date_str} の予約を保存しました！")
                st.session_state["selected_date_raw"] = new_date_str
                st.rerun()
            except ValueError:
                st.error("日付は「YYYY-MM-DD」の形式（例：2026-10-15）で入力してください。")
