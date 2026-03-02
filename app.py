import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ==========================================
# 1. 初期設定とセッションステート
# ==========================================
st.set_page_config(page_title="自動振り分けシステム", layout="wide")

if "selected_user" not in st.session_state:
    st.session_state.selected_user = "柿木田" # テストデータに存在する名前に初期化
if "current_status" not in st.session_state:
    st.session_state.current_status = "出社"
if "other_work_logs" not in st.session_state:
    st.session_state.other_work_logs = []
if "other_work_total_min" not in st.session_state:
    st.session_state.other_work_total_min = 0

# ※※※ GASのURL（Phase 2のもの）に書き換えてください ※※※
GAS_URL = "https://script.google.com/macros/s/AKfycbzQjtNpDuDaJtHesJPFsV666R7czHHkUL7r7JcpjWRexe7vQhG4sKOAZQjLDzGni23S/exec"

# ==========================================
# 2. デザインテーマ（カスタムCSS）
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #f4f7f9; }
    html, body, [class*="st-"] { font-size: 0.9rem; }
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .custom-card {
        background-color: white; padding: 12px 18px; border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); margin-bottom: 12px;
        border-left: 4px solid #4299e1;
    }
    .active-card {
        border-left: 4px solid #e53e3e; background-color: #fffaf0;
    }
    .log-list {
        font-size: 0.85em; color: #4a5568; max-height: 60px;
        overflow-y: auto; margin-top: 5px; padding-left: 20px;
    }
    
    /* ▼▼▼ 修正: 画面全体が固まるのを防ぐ！ヘッダー「だけ」を狙い撃ちする超精密CSS ▼▼▼ */
    /* 目印を持つ「最も内側の」ブロックだけを絶対固定する */
    div[data-testid="stVerticalBlock"]:has(#sticky-header-anchor):not(:has(div[data-testid="stVerticalBlock"]:has(#sticky-header-anchor))) {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        width: 100% !important;
        z-index: 9999 !important;
        background-color: rgba(244, 247, 249, 0.95) !important;
        backdrop-filter: blur(5px) !important;
        padding: 2.5rem 3rem 1rem 3rem !important; /* 左右の余白を調整 */
        border-bottom: 1px solid #e2e8f0 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
    }
    
    /* Fixedで浮いたヘッダーの分、下のコンテンツが隠れないように押し下げる */
    .block-container { 
        padding-top: 130px !important; 
        padding-bottom: 2rem; 
    }
    /* ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲ */
    
    /* 復活音源用の入力欄を小さくする */
    .stNumberInput input { padding: 4px; font-size: 0.9em; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. バックエンド通信ロジック
# ==========================================
@st.cache_data(ttl=60) # 60秒間キャッシュ（ボタン操作で強制クリア）
def fetch_data():
    try:
        response = requests.get(GAS_URL)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                df = pd.DataFrame(data.get("data", []))
                if not df.empty:
                    # UTCの日時文字列をJST（日本時間）に変換してフォーマット
                    df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_convert('Asia/Tokyo')
                
                # ▼ 追加: GASから送られてきたメンバー一覧を取得
                members = data.get("members", [])
                
                # ▼ 追加: 設定値とメンバー詳細データを取得
                api_settings = data.get("settings", {"past_days": 7, "future_days": 30})
                members_data = data.get("membersData", [])
                
                return df, members, api_settings, members_data
        return pd.DataFrame(), [], {"past_days": 7, "future_days": 30}, []
    except Exception as e:
        st.error(f"通信エラー: {e}")
        return pd.DataFrame(), [], {"past_days": 7, "future_days": 30}, []

def update_status(anken_id, new_status, fukkatsu_min=""):
    with st.spinner('ステータスを更新中...'):
        payload = {
            "action": "update_status",
            "anken_id": anken_id,
            "status": new_status,
            "fukkatsu_min": fukkatsu_min
        }
        try:
            requests.post(GAS_URL, json=payload)
            fetch_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"更新エラー: {e}")

# ▼▼▼ おそらくここが丸ごと抜けてしまっています。追加してください ▼▼▼
def update_assign(anken_id, assigned):
    with st.spinner('担当者を更新中...'):
        payload = {
            "action": "update_assign",
            "anken_id": anken_id,
            "assigned": assigned
        }
        try:
            requests.post(GAS_URL, json=payload)
            fetch_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"更新エラー: {e}")

# ▼▼▼ 途切れて消えてしまっていた関数を復元 ▼▼▼
def update_settings(past_days, future_days):
    with st.spinner('設定を保存中...'):
        payload = {
            "action": "update_settings",
            "past_days": past_days,
            "future_days": future_days
        }
        try:
            requests.post(GAS_URL, json=payload)
            fetch_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"更新エラー: {e}")

def update_skills(name, status, itsuzai, agent, shukyaku, jiei):
    with st.spinner(f'{name}さんの設定を保存中...'):
        payload = {
            "action": "update_skills",
            "name": name,
            "status": status,
            "itsuzai": itsuzai,
            "agent": agent,
            "shukyaku": shukyaku,
            "jiei": jiei
        }
        try:
            requests.post(GAS_URL, json=payload)
            fetch_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"更新エラー: {e}")
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

# ▼▼▼ 修正: システム全リセット用関数 ▼▼▼
def reset_system():
    with st.spinner('システムを全リセットし、再振り分けを行っています... (数十秒かかります)'):
        payload = {
            "action": "reset_system"
        }
        try:
            requests.post(GAS_URL, json=payload)
            
            # ▼ 追加: 操作しているブラウザのローカルステータス（別業務など）も強制的に出社へリセット ▼
            st.session_state.current_status = "出社"
            if "other_work_logs" in st.session_state:
                st.session_state.other_work_logs = []
            if "other_work_total_min" in st.session_state:
                st.session_state.other_work_total_min = 0
            # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
            
            fetch_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"リセットエラー: {e}")
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

# ==========================================
# 4. ヘッダー
# ==========================================
# ヘッダー全体を1つのコンテナにまとめて固定化
header_container = st.container()

# データとメンバー一覧を取得
df, api_members, api_settings, api_members_data = fetch_data()

with header_container:
    # CSSにこのコンテナを「固定する場所」と教えるための目印（アンカー）
    st.markdown('<div id="sticky-header-anchor"></div>', unsafe_allow_html=True)

    col_title, col_controls = st.columns([1.5, 1])

    with col_title:
        st.markdown("<h3 style='margin: 0; color: #2c5282; font-weight: bold;'>⚡ 自動振り分けシステム</h3>", unsafe_allow_html=True)

    with col_controls:
        ctrl_col0, ctrl_col1, ctrl_col2 = st.columns([0.5, 1.2, 1.2])
        with ctrl_col0:
            if st.button("🔄", help="最新データを取得"):
                fetch_data.clear()
                st.rerun()
        with ctrl_col1:
            users = api_members if api_members else ["柿木田", "中林", "今村"] 
            if not df.empty:
                existing_users = df['assigned'].dropna().unique().tolist()
                users = list(dict.fromkeys(existing_users + users)) # 重複削除
            
            # ▼ 修正: URLパラメータからデフォルトユーザーを取得し固定化するロジック ▼
            url_user = st.query_params.get("user")
            
            default_index = 0
            if url_user and url_user in users:
                default_index = users.index(url_user) # URLの指定を最優先
            elif "selected_user" in st.session_state and st.session_state.selected_user in users:
                default_index = users.index(st.session_state.selected_user) # セッションの記憶を次に優先
                
            st.selectbox("担当者", users, index=default_index, key="selected_user", label_visibility="collapsed")
            # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
            
        with ctrl_col2:
            # ▼ 修正: key="current_tab" を追加してタブの状態を更新後も維持する ▼
            current_tab = st.radio("画面", ["👤 ユーザー", "⚙️ 管理者"], horizontal=True, label_visibility="collapsed", key="current_tab")

st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

# ==========================================
# 5. メイン画面（ユーザータブ）
# ==========================================
today_str = datetime.now().strftime("%Y-%m-%d")

if current_tab == "👤 ユーザー":
    
    # 自分のタスクだけをフィルタリング
    my_tasks = pd.DataFrame()
    if not df.empty:
        my_tasks = df[df['assigned'] == st.session_state.selected_user].copy()
    
    # --- 実績計算 ---
    comp_count_normal = 0
    comp_min_normal = 0
    comp_count_fukkatsu = 0
    comp_min_fukkatsu = 0
    
    if not my_tasks.empty:
        # 完了タスクの抽出
        completed_df = my_tasks[my_tasks['status'] == '完了']
        
        # 通常（代筆完了）
        normal_df = completed_df[completed_df['fukkatsu'] == False]
        comp_count_normal = len(normal_df)
        comp_min_normal = pd.to_numeric(normal_df['duration'], errors='coerce').fillna(0).sum()
        
        # 復活音源
        fukkatsu_df = completed_df[completed_df['fukkatsu'] == True]
        comp_count_fukkatsu = len(fukkatsu_df)
        # 復活音源は入力された fukkatsu_min を合計する
        comp_min_fukkatsu = pd.to_numeric(fukkatsu_df['fukkatsu_min'], errors='coerce').fillna(0).sum()
    
    # --- 上段: 勤怠管理 ＆ 実績サマリー ---
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.markdown(f"""
        <div class="custom-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div style="font-weight: bold; color: #2d3748;">📅 {today_str}</div>
                <div>ステータス: <span style="font-weight: bold; color: {'#3182ce' if st.session_state.current_status=='出社' else '#dd6b20'};">{st.session_state.current_status}</span></div>
            </div>
        """, unsafe_allow_html=True)
        
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.session_state.current_status == "休憩中":
                if st.button("▶️ 休憩から戻る", use_container_width=True):
                    st.session_state.current_status = "出社"; st.rerun()
            else:
                if st.button("⏸️ 休憩に入る", use_container_width=True, disabled=(st.session_state.current_status == "別業務中")):
                    st.session_state.current_status = "休憩中"; st.rerun()
        with btn_c2:
            if st.session_state.current_status == "別業務中":
                if st.button("▶️ 別業務から戻る", use_container_width=True):
                    st.session_state.current_status = "出社"
                    st.session_state.other_work_logs.append(f"終了: {datetime.now().strftime('%H:%M')}")
                    st.session_state.other_work_total_min += 30 # ダミー加算
                    st.rerun()
            else:
                if st.button("🔄 別業務に入る", use_container_width=True, disabled=(st.session_state.current_status == "休憩中")):
                    st.session_state.current_status = "別業務中"
                    st.session_state.other_work_logs.append(f"開始: {datetime.now().strftime('%H:%M')}")
                    st.rerun()
                    
        logs_html = "".join([f"<li>{log}</li>" for log in st.session_state.other_work_logs[-3:]])
        st.markdown(f"""
            <div style="margin-top: 10px; font-size: 0.9em; display: flex; justify-content: space-between; align-items: flex-end;">
                <div style="width: 60%;">
                    <strong style="color: #4a5568;">別業務ログ:</strong>
                    <ul class="log-list" style="margin: 0; padding-left: 20px;">
                        {logs_html if logs_html else "<li style='color:#a0aec0;'>記録なし</li>"}
                    </ul>
                </div>
                <div style="width: 35%; text-align: right; color: #4a5568;">
                    <strong>別業務合計:</strong><br>
                    <span style="font-size: 1.4em; font-weight: bold; color: #2d3748;">{st.session_state.other_work_total_min}</span> mm
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown(f"""
        <div class="custom-card" style="border-left-color: #38b2ac; height: 93%;">
            <div style="display: flex; justify-content: space-between; padding-top: 5px;">
                <div style="width: 48%;">
                    <div style="color:#2c5282; font-weight: bold; margin-bottom: 5px;">📈 今日の実績 (代筆完了)</div>
                    <div style="margin-top: 8px;">
                        <span style="font-size: 1.6em; font-weight: bold; color: #2d3748;">{comp_count_normal}</span> <span style="font-size:0.8em; color: #4a5568;">件</span>
                        <span style="margin: 0 8px; color: #cbd5e0;">|</span>
                        <span style="font-size: 1.6em; font-weight: bold; color: #2d3748;">{int(comp_min_normal)}</span> <span style="font-size:0.8em; color: #4a5568;">分</span>
                    </div>
                </div>
                <div style="width: 48%;">
                    <div style="color:#553c9a; font-weight: bold; margin-bottom: 5px;">🔊 復活音源実績</div>
                    <div style="margin-top: 8px;">
                        <span style="font-size: 1.6em; font-weight: bold; color: #2d3748;">{comp_count_fukkatsu}</span> <span style="font-size:0.8em; color: #4a5568;">件</span>
                        <span style="margin: 0 8px; color: #cbd5e0;">|</span>
                        <span style="font-size: 1.6em; font-weight: bold; color: #2d3748;">{int(comp_min_fukkatsu)}</span> <span style="font-size:0.8em; color: #4a5568;">分</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- 中段: 現在着手中の案件 ---
    st.markdown("<div style='margin-bottom: 4px; color: #4a5568; font-weight: bold;'>🏃 現在着手中</div>", unsafe_allow_html=True)
    
    active_tasks = my_tasks[my_tasks['status'] == '着手'] if not my_tasks.empty else pd.DataFrame()
    
    if not active_tasks.empty:
        task = active_tasks.iloc[0]
        # ▼ 修正: カレンダーの本来の日付を取得し、終了時間を消して分数を取得
        task_date = task['datetime'].strftime('%m/%d')
        start_t = task['datetime'].strftime('%H:%M')
        duration_m = int(task['duration'])
        
        with st.container():
            st.markdown(f"""
            <div class="custom-card active-card" style="padding-bottom: 8px;">
                <div style="font-size: 1.1em; font-weight: bold; color: #2d3748; margin-bottom: 4px;">
                    {task['method']}商談 ({task['product']}) <span style="color: #cbd5e0; margin: 0 10px;">|</span> <span style="color: #2b6cb0;">{task['anken_id']}</span>
                </div>
                <div style="color: #4a5568; font-size: 0.95em; margin-bottom: 6px;">
                    📝 {task['title']}
                </div>
                <div style="color: #718096; font-size: 0.9em; margin-bottom: 12px;">
                    🕒 {task_date} {start_t} &nbsp;&nbsp;⏳ {duration_m} 分
                </div>
            """, unsafe_allow_html=True)
            
            fukkatsu_input = ""
            if task['fukkatsu'] == True:
                fukkatsu_input = st.number_input("🔊 復活音源の確認分数 (分)", min_value=0, max_value=120, value=0, key="fukkatsu_input")
            
            act_col1, act_col2, act_col3 = st.columns([1, 1, 1])
            with act_col1:
                if st.button("✅ 完了", key=f"comp_{task['anken_id']}", type="primary", use_container_width=True):
                    update_status(task['anken_id'], "完了", fukkatsu_input)
            with act_col2:
                if st.button("⏸️ 中断", key=f"pause_{task['anken_id']}", use_container_width=True):
                    update_status(task['anken_id'], "中断")
            with act_col3:
                if st.button("❌ 取消", key=f"cancel_{task['anken_id']}", use_container_width=True):
                    update_status(task['anken_id'], "取り消し")
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("現在着手中のタスクはありません。下の待機リストから「着手する」を押してください。")

    # --- 下段: 待機中のタスクリスト ---
    st.markdown("<div style='margin-bottom: 4px; margin-top: 15px; color: #4a5568; font-weight: bold;'>📋 待機中のタスク</div>", unsafe_allow_html=True)
    
    waiting_tasks = my_tasks[my_tasks['status'] == '未対応'].sort_values('datetime') if not my_tasks.empty else pd.DataFrame()
    
    if waiting_tasks.empty:
        st.success("待機中のタスクはすべて完了しました！🎉")
    else:
        for idx, task in waiting_tasks.iterrows():
            # ▼ 修正: カレンダーの本来の日付を取得し、終了時間を消して分数を取得
            task_date = task['datetime'].strftime('%m/%d')
            start_t = task['datetime'].strftime('%H:%M')
            duration_m = int(task['duration'])
            f_icon = "🔊 復活音源 " if task['fukkatsu'] else ""
            
            st.markdown(f"""
            <div class="custom-card" style="padding: 10px 15px; border-left-color: #a0aec0; margin-bottom: 5px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="width: 100%; padding-right: 15px;">
                        <div style="font-weight: bold; color: #2d3748; margin-bottom: 2px;">
                            <span style="color:#805ad5;">{f_icon}</span>{task['method']}商談 ({task['product']}) <span style="color: #cbd5e0; margin: 0 10px;">|</span> <span style="color: #4a5568;">{task['anken_id']}</span>
                        </div>
                        <div style="color: #4a5568; font-size: 0.85em; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            📝 {task['title']}
                        </div>
                        <div style="color: #718096; font-size: 0.85em;">
                            🕒 {task_date} {start_t} &nbsp;&nbsp;⏳ {duration_m} 分 &nbsp;&nbsp;|&nbsp;&nbsp; 🏷️ 未対応
                        </div>
                    </div>
            """, unsafe_allow_html=True)
            
            b_col1, b_col2 = st.columns([4, 1])
            with b_col2:
                is_disabled = not active_tasks.empty
                if st.button("▶ 着手する", key=f"start_{task['anken_id']}", disabled=is_disabled, use_container_width=True):
                    update_status(task['anken_id'], "着手")
            
            st.markdown("</div></div>", unsafe_allow_html=True)

    # --- 最下段: 完了済みのタスクリスト ---
    st.markdown("<div style='margin-bottom: 4px; margin-top: 25px; color: #4a5568; font-weight: bold;'>✅ 本日の完了タスク</div>", unsafe_allow_html=True)
    
    if not my_tasks.empty:
        completed_df = my_tasks[my_tasks['status'] == '完了']
        if completed_df.empty:
            st.info("本日完了したタスクはまだありません。")
        else:
            for idx, task in completed_df.sort_values('datetime', ascending=False).iterrows():
                # ▼ 修正: カレンダーの本来の日付を取得し、終了時間を消して分数を取得
                task_date = task['datetime'].strftime('%m/%d')
                start_t = task['datetime'].strftime('%H:%M')
                duration_m = int(task['duration'])
                f_icon = "🔊 復活音源 " if task['fukkatsu'] else ""
                
                f_min_text = ""
                if task['fukkatsu'] and pd.notna(task['fukkatsu_min']) and str(task['fukkatsu_min']).strip() != "":
                    try:
                        f_min_text = f"(確認: {int(float(task['fukkatsu_min']))}分)"
                    except:
                        pass
                
                st.markdown(f"""
                <div class="custom-card" style="padding: 10px 15px; border-left-color: #48bb78; background-color: #f0fff4; opacity: 0.75; margin-bottom: 5px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="width: 100%; padding-right: 15px;">
                            <div style="font-weight: bold; color: #4a5568; margin-bottom: 2px;">
                                <span style="color:#805ad5;">{f_icon}</span>{task['method']}商談 ({task['product']}) <span style="color: #cbd5e0; margin: 0 10px;">|</span> <span style="color: #718096;">{task['anken_id']}</span>
                            </div>
                            <div style="color: #718096; font-size: 0.85em; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-decoration: line-through;">
                                📝 {task['title']}
                            </div>
                            <div style="color: #718096; font-size: 0.85em;">
                                🕒 {task_date} {start_t} &nbsp;&nbsp;⏳ {duration_m} 分 &nbsp;&nbsp;|&nbsp;&nbsp; <span style="color: #2f855a; font-weight: bold;">✅ 完了 {f_min_text}</span>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# ==========================================
# 6. 管理者タブ
# ==========================================
elif current_tab == "⚙️ 管理者":
    st.markdown("<h2 style='color: #2c5282; margin-bottom: 20px;'>⚙️ 管理者コントロールパネル</h2>", unsafe_allow_html=True)
    
    if df.empty:
        st.warning("現在表示できるデータがありません。（GASからデータを取得できていません）")
    else:
        # 上部を左右に分割（左: 抽出, 右: ステータス）
        col_admin_l, col_admin_r = st.columns([1, 1.4])
        
        with col_admin_l:
            # --- セクション1 (左): 指定日時までのタスク抽出 ---
            st.markdown("<h4 style='color: #4a5568;'>🕒 指定日時までのタスク抽出</h4>", unsafe_allow_html=True)
            
            col_d, col_t = st.columns(2)
            with col_d:
                target_date = st.date_input("対象日付", datetime.now().date())
            with col_t:
                target_time = st.time_input("対象時間 (まで)", datetime.strptime("15:00", "%H:%M").time())
                
            target_datetime = datetime.combine(target_date, target_time)
            target_dt_tz = pd.to_datetime(target_datetime).tz_localize('Asia/Tokyo')
            
            filtered_df = df[df['datetime'] <= target_dt_tz].copy()
            
            if filtered_df.empty:
                st.info(f"{target_date.strftime('%m/%d')} {target_time.strftime('%H:%M')} までのタスクなし")
            else:
                filtered_df = filtered_df.sort_values('datetime')
                st.markdown(f"<div style='margin-bottom: 5px; font-weight: bold; color: #2d3748;'>該当タスク: <span style='color: #e53e3e; font-size: 1.2em;'>{len(filtered_df)}</span> 件</div>", unsafe_allow_html=True)
                
                display_df = filtered_df[['datetime', 'anken_id']].copy()
                display_df['datetime'] = display_df['datetime'].dt.strftime('%m/%d %H:%M')
                display_df.columns = ['日時', '案件ID']
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )

            # ▼▼▼ 修正: カレンダー設定を左カラムのタスク抽出の下へ移動 ▼▼▼
            st.markdown("<hr style='margin: 25px 0 15px 0;'>", unsafe_allow_html=True)
            st.markdown("<h5 style='color: #4a5568;'>⚙️ カレンダー取得範囲設定</h5>", unsafe_allow_html=True)
            
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                past_days = st.number_input("開始(過去〇日)", min_value=0, max_value=365, value=api_settings.get("past_days", 7))
            with col_s2:
                future_days = st.number_input("終了(未来〇日)", min_value=0, max_value=365, value=api_settings.get("future_days", 30))
            if st.button("💾 設定を保存して再取得", type="primary", use_container_width=True):
                update_settings(past_days, future_days)
            # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

        with col_admin_r:
            # --- セクション2 (右): メンバー稼働ステータス ---
            st.markdown("<h4 style='color: #4a5568;'>👥 メンバー稼働ステータス</h4>", unsafe_allow_html=True)
            
            # 着手中のタスクを抽出して辞書化
            active_df = df[df['status'] == '着手'] if not df.empty else pd.DataFrame()
            active_dict = {}
            for _, row in active_df.iterrows():
                active_dict[row['assigned']] = f"{row['method']} ({row['product']})"
                
            # 担当者ごとの状態を集計
            summary_data = []
            
            # メンバー管理シートの全員をデフォルトで表示対象にする
            raw_users_list = api_members if api_members else df['assigned'].fillna('未割当').unique().tolist()
            if "未割当" not in raw_users_list:
                raw_users_list = list(raw_users_list) + ["未割当"]
            
            clean_users = []
            for u in raw_users_list:
                if pd.isna(u):
                    continue
                # 前後の空白と全角スペースを完全に除去
                u_str = str(u).strip().replace("　", "") 
                if u_str == "":
                    continue # 空白や見えない文字だけの行は完全にスキップ
                if u == "未割当" and (df.empty or len(df[df['assigned'].fillna('未割当') == '未割当']) == 0):
                    continue # 該当なしの未割当はスキップ
                if u not in clean_users:
                    clean_users.append(u)
            
            for user in clean_users:
                user_df = df[df['assigned'].fillna('未割当') == user] if not df.empty else pd.DataFrame()
                
                mitaiou_count = len(user_df[user_df['status'] == '未対応']) if not user_df.empty else 0
                
                # 完了タスクの抽出
                completed_df = user_df[user_df['status'] == '完了'] if not user_df.empty else pd.DataFrame()
                
                # 通常（代筆完了）
                normal_df = completed_df[completed_df['fukkatsu'] == False] if not completed_df.empty else pd.DataFrame()
                comp_count = len(normal_df)
                comp_min = pd.to_numeric(normal_df['duration'], errors='coerce').fillna(0).sum() if not normal_df.empty else 0
                
                # 復活音源完了
                fukkatsu_df = completed_df[completed_df['fukkatsu'] == True] if not completed_df.empty else pd.DataFrame()
                fukkatsu_count = len(fukkatsu_df)
                
                # 別業務時間の取得
                other_work_min = st.session_state.other_work_total_min if user == st.session_state.selected_user else 0
                
                summary_data.append({
                    "担当者": user,
                    "未対応": mitaiou_count,
                    "完了": comp_count,
                    "完了分数": int(comp_min),
                    "復活音源件数": fukkatsu_count,
                    "別業務時間": other_work_min,
                    "現在の作業": active_dict.get(user, "待機中")
                })
                
            if summary_data:
                sum_df = pd.DataFrame(summary_data)
                
                # ▼ 修正: 文字サイズ0.9remに完全に合わせた高さジャスト計算（1行約30px） ▼
                calc_height = len(sum_df) * 30 + 38 
                # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
                
                st.dataframe(
                    sum_df,
                    use_container_width=True,
                    hide_index=True,
                    height=calc_height,  # ジャストサイズを指定
                    column_config={
                        "担当者": st.column_config.Column("担当者", width="small"),
                        "未対応": st.column_config.NumberColumn("未対応", format="%d", width="small"),
                        "完了": st.column_config.NumberColumn("完了", format="%d", width="small"),
                        "完了分数": st.column_config.NumberColumn("完了分数", format="%d 分", width="small"),
                        "復活音源件数": st.column_config.NumberColumn("復活音源", format="%d", width="small"),
                        "別業務時間": st.column_config.NumberColumn("別業務", format="%d 分", width="small"),
                        "現在の作業": st.column_config.Column("現在の作業", width="medium"),
                    }
                )
            else:
                st.info("現在稼働中のメンバーデータがありません。")

            # ▼▼▼ 修正: スキル＆勤怠設定パネルの表示とプルダウン追加 ▼▼▼
            st.markdown("<hr style='margin: 25px 0 15px 0;'>", unsafe_allow_html=True)
            
            # st.expander を使って折りたたみ（アコーディオン）にする
            with st.expander("🛠️ メンバースキル＆勤怠設定 (自動振り分け条件) を開く / 閉じる", expanded=False):
                if api_members_data:
                    mem_df = pd.DataFrame(api_members_data)
                    
                    # 空白行や全角スペースの無効データを徹底的にクレンジング
                    clean_mem_data = []
                    for _, row in mem_df.iterrows():
                        u = row['name']
                        if pd.isna(u): continue
                        u_str = str(u).strip().replace("　", "")
                        if u_str == "": continue
                        clean_mem_data.append(row)
                    
                    if clean_mem_data:
                        clean_mem_df = pd.DataFrame(clean_mem_data)
                        
                        # ▼ 修正: status（勤怠ステータス）の列も表示データに含める
                        display_mem_df = clean_mem_df[['name', 'status', 'itsuzai', 'agent', 'shukyaku', 'jiei']].copy()
                        display_mem_df.columns = ['担当者', 'ステータス', 'ｲﾂｻﾞｲ', 'ｴｰｼﾞｪﾝﾄ', '集客', '自営(/自)']
                        
                        # 文字サイズ(0.9rem)に合わせたジャストサイズ計算（1行約30px）
                        calc_skill_height = len(display_mem_df) * 30 + 38
                        
                        edited_mem_df = st.data_editor(
                            display_mem_df,
                            use_container_width=True,
                            hide_index=True,
                            height=calc_skill_height, # ジャストサイズを適用
                            disabled=['担当者'],
                            column_config={
                                "担当者": st.column_config.Column("担当者", width="small"),
                                # ▼ 新規追加: 勤怠ステータスのプルダウン列
                                "ステータス": st.column_config.SelectboxColumn(
                                    "ステータス ✏️",
                                    options=["出社", "退勤", "欠勤", "休憩中", "別業務中"],
                                    width="small",
                                    help="クリックして勤怠を変更できます"
                                ),
                                "ｲﾂｻﾞｲ": st.column_config.CheckboxColumn("ｲﾂｻﾞｲ", default=False),
                                "ｴｰｼﾞｪﾝﾄ": st.column_config.CheckboxColumn("ｴｰｼﾞｪﾝﾄ", default=False),
                                "集客": st.column_config.CheckboxColumn("集客", default=False),
                                "自営(/自)": st.column_config.CheckboxColumn("自営(/自)", default=False),
                            },
                            key="admin_skills_editor"
                        )
                        
                        # 変更検知ロジック
                        if not edited_mem_df.equals(display_mem_df):
                            for idx in display_mem_df.index:
                                old_row = display_mem_df.loc[idx]
                                new_row = edited_mem_df.loc[idx]
                                if not old_row.equals(new_row):
                                    # ▼ 修正: 引数にステータスを追加して送信
                                    update_skills(
                                        new_row['担当者'],
                                        new_row['ステータス'],
                                        bool(new_row['ｲﾂｻﾞｲ']),
                                        bool(new_row['ｴｰｼﾞｪﾝﾄ']),
                                        bool(new_row['集客']),
                                        bool(new_row['自営(/自)'])
                                    )
                                    break
                    else:
                        st.info("有効なメンバー設定データがありません。")
                else:
                    st.info("メンバー設定データがありません。")
            # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

        # --- セクション3 (下部): 全案件リスト（未完了と完了を分割） ---
        st.markdown("<hr style='margin: 30px 0;'>", unsafe_allow_html=True)
        
        # データの整形
        all_display_df = df[['assigned', 'status', 'datetime', 'anken_id', 'title', 'duration', 'product', 'method']].copy()
        all_display_df['datetime'] = all_display_df['datetime'].dt.strftime('%m/%d %H:%M')
        all_display_df.columns = ['担当者', 'ステータス', '日時', '案件ID', 'タイトル', '分数', '商材', '商談方法']
        all_display_df['担当者'] = all_display_df['担当者'].fillna('')
        
        # 商材フィルター
        unique_products = all_display_df['商材'].dropna().unique().tolist()
        default_products = [p for p in unique_products if p != "JOBYmini"]
        
        selected_products = st.multiselect(
            "🏷️ 表示する商材を選択 (JOBYminiはデフォルトで除外されています)",
            options=unique_products,
            default=default_products
        )
        
        # 選択された商材のみにフィルタリング
        filtered_all_df = all_display_df[all_display_df['商材'].isin(selected_products)].copy()
        
        # ▼▼▼ 修正: 完了とそれ以外に分割し、優先度順にソート ▼▼▼
        # 1. 完了した案件
        completed_cases_df = filtered_all_df[filtered_all_df['ステータス'] == '完了'].copy()
        completed_cases_df = completed_cases_df.sort_values('日時', ascending=False).reset_index(drop=True)
        
        # 2. 未完了の案件（着手・中断・未対応・取り消し）
        active_cases_df = filtered_all_df[filtered_all_df['ステータス'] != '完了'].copy()
        
        # ソート優先度の設定（着手=1, 中断=2, 未対応=3, 取り消し=4）
        status_priority = {'着手': 1, '中断': 2, '未対応': 3, '取り消し': 4}
        active_cases_df['優先度'] = active_cases_df['ステータス'].map(status_priority).fillna(5)
        
        # 優先度順、その中で古い日時順にソート
        active_cases_df = active_cases_df.sort_values(['優先度', '日時']).drop('優先度', axis=1).reset_index(drop=True)
        # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
        
        # 担当者のプルダウン用選択肢
        assign_options = [""] + users
        
        # --- 3-1: 未完了案件リスト (編集可) ---
        st.markdown("<h4 style='color: #4a5568; margin-top: 15px;'>📋 現在の案件リスト (未完了 / 担当者変更可)</h4>", unsafe_allow_html=True)
        
        if active_cases_df.empty:
            st.success("現在対応が必要な案件はありません。")
        else:
            edited_df = st.data_editor(
                active_cases_df,
                use_container_width=True,
                hide_index=True,
                disabled=['ステータス', '日時', '案件ID', 'タイトル', '分数', '商材', '商談方法'], # 担当者以外は編集ロック
                column_config={
                    "タイトル": st.column_config.Column("タイトル", width="large"),
                    "担当者": st.column_config.SelectboxColumn(
                        "担当者 ✏️",
                        help="クリックして担当者を変更できます",
                        width="small",
                        options=assign_options
                    ),
                    "ステータス": st.column_config.Column("ステータス", width="small"),
                },
                key="admin_active_data_editor"
            )
            
            # 変更検知ロジック
            if not edited_df.equals(active_cases_df):
                for idx in active_cases_df.index:
                    old_val = active_cases_df.loc[idx, '担当者']
                    new_val = edited_df.loc[idx, '担当者']
                    if old_val != new_val:
                        target_id = edited_df.loc[idx, '案件ID']
                        update_assign(target_id, new_val)
                        break

        # --- 3-2: 完了済み案件リスト (表示のみ) ---
        st.markdown("<hr style='margin: 30px 0 15px 0; border-top: dashed 2px #cbd5e0;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #4a5568;'>✅ 完了済みの案件リスト</h4>", unsafe_allow_html=True)
        
        if completed_cases_df.empty:
            st.info("完了済みの案件はまだありません。")
        else:
            st.dataframe(
                completed_cases_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "タイトル": st.column_config.Column("タイトル", width="large"),
                    "担当者": st.column_config.Column("担当者", width="small"),
                    "ステータス": st.column_config.Column("ステータス", width="small"),
                }
            )

        # ▼▼▼ 新規追加: セクション4: システム全リセット ▼▼▼
        st.markdown("<hr style='margin: 40px 0 20px 0; border-top: solid 2px #e53e3e;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #e53e3e;'>🚨 危険エリア (システム全リセット)</h4>", unsafe_allow_html=True)
        
        with st.expander("⚠️ 全データを白紙に戻し、カレンダーから再取得＆再振り分けを実行する", expanded=False):
            st.warning("""
            **【注意】** この操作を行うと、本日の担当者の振り分け状況、完了ステータス、手動で変更した担当者情報などが**すべて白紙に戻ります**。
            1日の業務がすべて終了した後の「翌日に向けたリセット」や、システムに大きなズレが生じた場合の「緊急復旧」の時のみ使用してください。
            """)
            
            # 誤操作防止のチェックボックス
            confirm_reset = st.checkbox("上記を理解した上で、全リセットを実行します。")
            if confirm_reset:
                if st.button("🔥 実行する (元に戻せません)", type="primary"):
                    reset_system()
        # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
