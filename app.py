import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time
import json
import os
import streamlit.components.v1 as components 
import html as html_lib 

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except ImportError:
    HAS_AUTOREFRESH = False

# ==========================================
# 1. 初期設定とセッションステート
# ==========================================
st.set_page_config(page_title="自動振り分けシステム", layout="wide")

if "selected_user" not in st.session_state:
    st.session_state.selected_user = "柿木田" 

WORK_LOG_FILE = "work_logs.json"

def get_user_work_data(username):
    if os.path.exists(WORK_LOG_FILE):
        try:
            with open(WORK_LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                user_data = data.get(username)
                if user_data:
                    st_time_str = user_data.get("other_work_start_time")
                    start_time = pd.to_datetime(st_time_str) if st_time_str else None
                    
                    b_time_str = user_data.get("break_start_time")
                    b_start_time = pd.to_datetime(b_time_str) if b_time_str else None
                    
                    return {
                        "current_status": user_data.get("current_status", "出社"),
                        "other_work_logs": user_data.get("other_work_logs", []),
                        "other_work_total_min": user_data.get("other_work_total_min", 0),
                        "other_work_start_time": start_time,
                        "cancel_logs": user_data.get("cancel_logs", []),
                        "cancel_total_min": user_data.get("cancel_total_min", 0),
                        "cancel_count": user_data.get("cancel_count", 0),
                        "break_logs": user_data.get("break_logs", []),
                        "break_total_min": user_data.get("break_total_min", 0),
                        "break_start_time": b_start_time
                    }
        except Exception:
            pass
    return {
        "current_status": "出社",
        "other_work_logs": [],
        "other_work_total_min": 0,
        "other_work_start_time": None,
        "cancel_logs": [],
        "cancel_total_min": 0,
        "cancel_count": 0,
        "break_logs": [],
        "break_total_min": 0,
        "break_start_time": None
    }

def save_user_work_data(username, status, logs, total_min, start_time, **kwargs):
    data = {}
    if os.path.exists(WORK_LOG_FILE):
        try:
            with open(WORK_LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
    
    st_time_str = start_time.isoformat() if start_time else None
    user_data = data.get(username, {})
    
    c_logs = kwargs.get("cancel_logs", user_data.get("cancel_logs", []))
    c_total_min = kwargs.get("cancel_total_min", user_data.get("cancel_total_min", 0))
    c_count = kwargs.get("cancel_count", user_data.get("cancel_count", 0))
    
    b_logs = kwargs.get("break_logs", user_data.get("break_logs", []))
    b_total_min = kwargs.get("break_total_min", user_data.get("break_total_min", 0))
    
    if "break_start_time" in kwargs:
        b_time_val = kwargs["break_start_time"]
        b_time_str = b_time_val.isoformat() if b_time_val else None
    else:
        b_time_str = user_data.get("break_start_time")
    
    data[username] = {
        "current_status": status,
        "other_work_logs": logs,
        "other_work_total_min": total_min,
        "other_work_start_time": st_time_str,
        "cancel_logs": c_logs,
        "cancel_total_min": c_total_min,
        "cancel_count": c_count,
        "break_logs": b_logs,
        "break_total_min": b_total_min,
        "break_start_time": b_time_str
    }
    
    try:
        with open(WORK_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def clear_all_work_data():
    if os.path.exists(WORK_LOG_FILE):
        try:
            os.remove(WORK_LOG_FILE)
        except Exception:
            pass

SYSTEM_SETTINGS_FILE = "system_settings.json"

def get_system_settings():
    if os.path.exists(SYSTEM_SETTINGS_FILE):
        try:
            with open(SYSTEM_SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_system_settings(key, value):
    data = get_system_settings()
    data[key] = value
    try:
        with open(SYSTEM_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

TASK_TIME_FILE = "task_times.json"

def get_task_times():
    if os.path.exists(TASK_TIME_FILE):
        try:
            with open(TASK_TIME_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_task_time(anken_id, time_str):
    data = get_task_times()
    data[anken_id] = time_str
    try:
        with open(TASK_TIME_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

ACTION_LOG_FILE = "action_logs.json"

def add_action_log(username, action, details=""):
    logs = []
    if os.path.exists(ACTION_LOG_FILE):
        try:
            with open(ACTION_LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            pass
    
    now = pd.Timestamp.now(tz='Asia/Tokyo')
    one_hour_ago = now - pd.Timedelta(hours=1)
    
    valid_logs = []
    for log in logs:
        try:
            log_time = pd.to_datetime(log["timestamp"])
            if log_time >= one_hour_ago:
                valid_logs.append(log)
        except:
            pass
            
    valid_logs.append({
        "timestamp": now.isoformat(),
        "user": username,
        "action": action,
        "details": details
    })
    
    try:
        with open(ACTION_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(valid_logs, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def get_action_logs():
    if os.path.exists(ACTION_LOG_FILE):
        try:
            with open(ACTION_LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
                
                now = pd.Timestamp.now(tz='Asia/Tokyo')
                one_hour_ago = now - pd.Timedelta(hours=1)
                
                valid_logs = []
                for log in logs:
                    try:
                        log_time = pd.to_datetime(log["timestamp"])
                        if log_time >= one_hour_ago:
                            valid_logs.append(log)
                    except:
                        pass
                
                valid_logs.sort(key=lambda x: x["timestamp"], reverse=True)
                return valid_logs
        except Exception:
            pass
    return []

# ※※※ GASのURL（Phase 2のもの）に書き換えてください ※※※
GAS_URL = "https://script.google.com/macros/s/AKfycbx3s90ow-zvsGQdlg-MGnKlITd14NOlZJN0Lp05oOU01QsQfkmr5Gnu-PoIoNgbP9NK/exec"

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
    
    div[data-testid="stVerticalBlock"]:has(#sticky-header-anchor):not(:has(div[data-testid="stVerticalBlock"]:has(#sticky-header-anchor))) {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        width: 100% !important;
        z-index: 9999 !important;
        background-color: rgba(244, 247, 249, 0.95) !important;
        backdrop-filter: blur(5px) !important;
        padding: 2.5rem 3rem 1rem 3rem !important; 
        border-bottom: 1px solid #e2e8f0 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
    }
    
    .block-container { 
        padding-top: 130px !important; 
        padding-bottom: 2rem; 
    }
    
    div[data-testid="stCodeBlock"] {
        margin-bottom: 0.5rem !important;
    }
    div[data-testid="stCodeBlock"] pre {
        padding: 0.6rem !important;
        font-size: 0.9em !important;
        white-space: pre-wrap !important; 
        word-break: break-word !important; 
    }
    
    .stNumberInput input { padding: 4px; font-size: 0.9em; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. バックエンド通信ロジック (リトライ機能搭載)
# ==========================================
def safe_api_post(payload, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(GAS_URL, json=payload, timeout=40)
            if response.status_code == 200:
                try:
                    result = response.json()
                except Exception:
                    raise Exception("サーバーから無効な応答が返りました。GASが最新バージョンにデプロイされているか確認してください。")
                
                if result.get("status") == "success":
                    return result
                elif "混み合っています" in result.get("message", ""):
                    time.sleep(2)
                    continue
                else:
                    raise Exception(result.get("message", "不明なエラーが発生しました"))
            else:
                time.sleep(2)
                continue
        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(f"通信エラーが発生しました。詳細: {e}")
            time.sleep(2)
            continue
            
    raise Exception("システムが非常に混み合っています。数秒待ってから再度ボタンを押してください。")

@st.cache_data(ttl=60) 
def fetch_data():
    try:
        response = requests.get(GAS_URL, timeout=30)
        fetch_time = pd.Timestamp.now(tz='Asia/Tokyo').strftime("%H:%M:%S")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                df = pd.DataFrame(data.get("data", []))
                if not df.empty:
                    df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_convert('Asia/Tokyo')
                
                members = data.get("members", [])
                api_settings = data.get("settings", {"past_days": 7, "future_days": 30})
                members_data = data.get("membersData", [])
                api_manual_data = data.get("manualData", [])
                api_fastpass_ids = data.get("fastpassIds", [])
                
                return df, members, api_settings, members_data, api_manual_data, api_fastpass_ids, fetch_time
        return pd.DataFrame(), [], {"past_days": 7, "future_days": 30}, [], [], [], fetch_time
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return pd.DataFrame(), [], {"past_days": 7, "future_days": 30}, [], [], [], pd.Timestamp.now(tz='Asia/Tokyo').strftime("%H:%M:%S")

def update_status(anken_id, new_status, fukkatsu_min=""):
    with st.spinner('ステータスを更新し、裏側で再計算しています...'):
        if new_status == "着手":
            now_str = pd.Timestamp.now(tz='Asia/Tokyo').strftime("%H:%M")
            save_task_time(anken_id, now_str)
        
        payload = {
            "action": "update_status",
            "anken_id": anken_id,
            "status": new_status,
            "fukkatsu_min": fukkatsu_min
        }
        try:
            safe_api_post(payload) 
            add_action_log(st.session_state.selected_user, "タスク状態変更", f"ID:{str(anken_id).replace('_fukkatsu', '')} を「{new_status}」に変更")
            fetch_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"更新に失敗しました: {e}")

def update_assign(anken_id, assigned):
    with st.spinner('担当者を更新し、裏側で再計算しています...'):
        payload = {
            "action": "update_assign",
            "anken_id": anken_id,
            "assigned": assigned
        }
        try:
            safe_api_post(payload)
            add_action_log(st.session_state.selected_user, "担当者手動変更", f"ID:{str(anken_id).replace('_fukkatsu', '')} を「{assigned if assigned else '未割当'}」に変更")
            fetch_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"更新に失敗しました: {e}")

def update_settings(past_days, future_days):
    with st.spinner('設定を保存中...'):
        payload = {
            "action": "update_settings",
            "past_days": past_days,
            "future_days": future_days
        }
        try:
            safe_api_post(payload)
            add_action_log(st.session_state.selected_user, "カレンダー設定変更", f"過去{past_days}日 / 未来{future_days}日 に変更")
            fetch_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"更新に失敗しました: {e}")

def update_skills(name, status, shift, itsuzai, agent, shukyaku, jiei):
    with st.spinner(f'{name}さんの設定を保存中...'):
        payload = {
            "action": "update_skills",
            "name": name,
            "status": status,
            "shift": shift,
            "itsuzai": itsuzai,
            "agent": agent,
            "shukyaku": shukyaku,
            "jiei": jiei
        }
        try:
            safe_api_post(payload)
            add_action_log(st.session_state.selected_user, "メンバー設定変更", f"{name} さんのスキル/ステータスを更新")
            fetch_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"更新に失敗しました: {e}")

def reset_system():
    with st.spinner('システムを全リセットし、再振り分けを行っています... (時間がかかります)'):
        payload = {
            "action": "reset_system"
        }
        try:
            safe_api_post(payload)
            add_action_log(st.session_state.selected_user, "システム全リセット", "全データを初期化し再振り分けを実行")
            clear_all_work_data()
            fetch_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"リセットに失敗しました: {e}")

def update_all_overtime(minutes):
    with st.spinner(f'全メンバーの残業時間を {minutes} 分に設定し、再計算中...'):
        payload = {
            "action": "update_all_overtime",
            "minutes": minutes
        }
        try:
            safe_api_post(payload)
            add_action_log(st.session_state.selected_user, "残業時間一括設定", f"全メンバーの残業時間を {minutes} 分に設定")
            fetch_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"更新に失敗しました: {e}")

# ▼▼▼ 修正: 通信エラーを見逃さず、成功した時だけTrueを返すように改良 ▼▼▼
def update_user_status_api(name, status):
    with st.spinner(f'システム側も「{status}」に更新し、タスクを再計算中...'):
        payload = {
            "action": "update_member_status",
            "name": name,
            "status": status
        }
        try:
            safe_api_post(payload)
            add_action_log(st.session_state.selected_user, "ステータス連動", f"{name} さんが「{status}」に変更")
            fetch_data.clear() 
            return True
        except Exception as e:
            st.error(f"⚠️ GASとの通信に失敗しました。\nGAS側で『新しいバージョンとしてデプロイ』が実行されていない可能性が高いです。\n詳細: {e}")
            return False
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

# ==========================================
# 4. ヘッダー
# ==========================================
def handle_refresh():
    fetch_data.clear()

header_container = st.container()
df, api_members, api_settings, api_members_data, api_manual_data, api_fastpass_ids, fetch_time = fetch_data()

min_unassigned_date = None
if not df.empty:
    unassigned_df = df[df['status'] == '未対応']
    if not unassigned_df.empty:
        min_unassigned_date = unassigned_df['datetime'].dt.date.min()

if not df.empty:
    if 'fukkatsu_min' in df.columns:
        f_min_num = pd.to_numeric(df['fukkatsu_min'], errors='coerce').fillna(0)
        df.loc[f_min_num > 0, 'fukkatsu'] = True
    elif 'fukkatsu' not in df.columns:
        df['fukkatsu'] = False

with header_container:
    st.markdown('<div id="sticky-header-anchor"></div>', unsafe_allow_html=True)

    col_title, col_controls = st.columns([1.5, 1])

    with col_title:
        st.markdown(f"""
            <div style='display: flex; align-items: baseline; gap: 12px;'>
                <h3 style='margin: 0; color: #2c5282; font-weight: bold;'>⚡ 自動振り分けシステム</h3>
                <span style='color: #718096; font-size: 0.85rem; font-weight: normal;'>最終更新: {fetch_time}</span>
            </div>
        """, unsafe_allow_html=True)

    with col_controls:
        ctrl_col0, ctrl_col1, ctrl_col2 = st.columns([0.4, 1.2, 1.5])
        with ctrl_col0:
            st.button("🔄", help="最新データを取得", on_click=handle_refresh)
            
        with ctrl_col1:
            users = api_members if api_members else ["柿木田", "中林", "今村"] 
            url_user = st.query_params.get("user")
            
            if url_user and url_user in users and st.session_state.selected_user != url_user:
                st.session_state.selected_user = url_user
                
            default_index = users.index(st.session_state.selected_user) if st.session_state.selected_user in users else 0
            
            def on_user_change():
                st.query_params["user"] = st.session_state.selected_user
                
            if not url_user:
                 st.query_params["user"] = st.session_state.selected_user

            st.selectbox(
                "担当者", 
                users, 
                index=default_index, 
                key="selected_user", 
                on_change=on_user_change,
                label_visibility="collapsed"
            )
            
        with ctrl_col2:
            url_tab = st.query_params.get("tab")
            tab_options = ["👤 ユーザー", "⚙️ 管理者", "📖 監査マニュアル"]
            
            default_tab_index = 0
            if url_tab == "admin":
                default_tab_index = 1
            elif url_tab == "manual":
                default_tab_index = 2
            
            def on_tab_change():
                if st.session_state.current_tab == "⚙️ 管理者":
                    st.query_params["tab"] = "admin"
                elif st.session_state.current_tab == "📖 監査マニュアル":
                    st.query_params["tab"] = "manual"
                else:
                    st.query_params["tab"] = "user"
                    
            if not url_tab:
                 st.query_params["tab"] = "user"

            current_tab = st.radio(
                "画面", 
                tab_options, 
                index=default_tab_index,
                horizontal=True, 
                label_visibility="collapsed", 
                key="current_tab",
                on_change=on_tab_change
            )

st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

# ==========================================
# 5. メイン画面（ユーザータブ）
# ==========================================
today_str = pd.Timestamp.now(tz='Asia/Tokyo').strftime("%Y-%m-%d")

if current_tab == "👤 ユーザー":
    st.info(f"💡 **ヒント:** 右上の担当者を選んだ状態でこの画面（URL）をブックマークすると、次回から直接 **{st.session_state.selected_user}** さんのページが開きます。")
    
    my_tasks = pd.DataFrame()
    if not df.empty:
        my_tasks = df[df['assigned'] == st.session_state.selected_user].copy()
    
    comp_count_normal = 0
    comp_min_normal = 0
    comp_count_fukkatsu = 0
    comp_min_fukkatsu = 0
    
    if not my_tasks.empty:
        completed_df = my_tasks[my_tasks['status'] == '完了']
        normal_df = completed_df[completed_df['fukkatsu'] == False]
        comp_count_normal = len(normal_df)
        comp_min_normal = pd.to_numeric(normal_df['duration'], errors='coerce').fillna(0).sum()
        
        fukkatsu_df = completed_df[completed_df['fukkatsu'] == True]
        comp_count_fukkatsu = len(fukkatsu_df)
        comp_min_fukkatsu = pd.to_numeric(fukkatsu_df['fukkatsu_min'], errors='coerce').fillna(0).sum()
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        user_data = get_user_work_data(st.session_state.selected_user)
        current_status = user_data["current_status"]
        other_work_logs = user_data["other_work_logs"]
        other_work_total_min = user_data["other_work_total_min"]
        other_work_start_time = user_data["other_work_start_time"]
        
        break_logs = user_data["break_logs"]
        break_total_min = user_data["break_total_min"]
        break_start_time = user_data["break_start_time"]
        
        st.markdown(f"""
        <div class="custom-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div style="font-weight: bold; color: #2d3748;">📅 {today_str}</div>
                <div>ステータス: <span style="font-weight: bold; color: {'#3182ce' if current_status=='出社' else '#dd6b20'};">{current_status}</span></div>
            </div>
        """, unsafe_allow_html=True)
        
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if current_status == "休憩中":
                if st.button("▶️ 休憩から戻る", use_container_width=True):
                    # ▼ 修正: GAS通信が成功した時だけステータスを変更し画面をリロードする
                    if update_user_status_api(st.session_state.selected_user, "出社"):
                        now = pd.Timestamp.now(tz='Asia/Tokyo')
                        break_logs.append(f"終了: {now.strftime('%H:%M')}")
                        
                        if break_start_time:
                            diff = now - break_start_time
                            minutes = int(diff.total_seconds() / 60)
                            break_total_min += minutes
                            break_start_time = None
                            
                        save_user_work_data(
                            st.session_state.selected_user, "出社", other_work_logs, other_work_total_min, other_work_start_time,
                            break_logs=break_logs, break_total_min=break_total_min, break_start_time=break_start_time
                        )
                        st.rerun()
            else:
                if st.button("⏸️ 休憩に入る", use_container_width=True, disabled=(current_status == "別業務中")):
                    # ▼ 修正: GAS通信が成功した時だけステータスを変更し画面をリロードする
                    if update_user_status_api(st.session_state.selected_user, "休憩中"):
                        now = pd.Timestamp.now(tz='Asia/Tokyo')
                        break_start_time = now
                        break_logs.append(f"開始: {now.strftime('%H:%M')}")
                        
                        save_user_work_data(
                            st.session_state.selected_user, "休憩中", other_work_logs, other_work_total_min, other_work_start_time,
                            break_logs=break_logs, break_total_min=break_total_min, break_start_time=break_start_time
                        )
                        st.rerun()
                    
        with btn_c2:
            if current_status == "別業務中":
                if st.button("▶️ 別業務から戻る", use_container_width=True):
                    # ▼ 修正: GAS通信が成功した時だけステータスを変更し画面をリロードする
                    if update_user_status_api(st.session_state.selected_user, "出社"):
                        now = pd.Timestamp.now(tz='Asia/Tokyo')
                        other_work_logs.append(f"終了: {now.strftime('%H:%M')}")
                        
                        if other_work_start_time:
                            diff = now - other_work_start_time
                            minutes = int(diff.total_seconds() / 60)
                            other_work_total_min += minutes
                            other_work_start_time = None
                            
                        save_user_work_data(st.session_state.selected_user, "出社", other_work_logs, other_work_total_min, other_work_start_time)
                        st.rerun()
            else:
                if st.button("🔄 別業務に入る", use_container_width=True, disabled=(current_status == "休憩中")):
                    # ▼ 修正: GAS通信が成功した時だけステータスを変更し画面をリロードする
                    if update_user_status_api(st.session_state.selected_user, "別業務中"):
                        now = pd.Timestamp.now(tz='Asia/Tokyo')
                        other_work_start_time = now 
                        other_work_logs.append(f"開始: {now.strftime('%H:%M')}")
                        save_user_work_data(st.session_state.selected_user, "別業務中", other_work_logs, other_work_total_min, other_work_start_time)
                        st.rerun()
                    
        b_logs_html = "".join([f"<li style='margin-bottom: 2px;'>{log}</li>" for log in break_logs[-3:]])
        o_logs_html = "".join([f"<li style='margin-bottom: 2px;'>{log}</li>" for log in other_work_logs[-3:]])
        
        st.markdown(f"""
            <div style="margin-top: 15px; font-size: 0.85em; display: flex; gap: 15px;">
                <div style="flex: 1; border-right: 1px dashed #e2e8f0; padding-right: 10px;">
                    <div style="color: #4a5568; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: flex-end;">
                        <strong>☕ 休憩ログ</strong>
                        <span style="color: #2d3748; font-weight: bold; font-size: 1.1em;">{break_total_min} <span style="font-size: 0.8em; font-weight: normal;">分</span></span>
                    </div>
                    <ul class="log-list" style="margin: 0; padding-left: 20px; color: #718096;">
                        {b_logs_html if b_logs_html else "<li style='color:#a0aec0;'>記録なし</li>"}
                    </ul>
                </div>
                <div style="flex: 1; padding-left: 5px;">
                    <div style="color: #4a5568; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: flex-end;">
                        <strong>🔄 別業務ログ</strong>
                        <span style="color: #2d3748; font-weight: bold; font-size: 1.1em;">{other_work_total_min} <span style="font-size: 0.8em; font-weight: normal;">分</span></span>
                    </div>
                    <ul class="log-list" style="margin: 0; padding-left: 20px; color: #718096;">
                        {o_logs_html if o_logs_html else "<li style='color:#a0aec0;'>記録なし</li>"}
                    </ul>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown(f"""
        <div class="custom-card" style="border-left-color: #38b2ac; margin-bottom: 8px;">
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

        cancel_logs = user_data["cancel_logs"]
        cancel_total_min = user_data["cancel_total_min"]
        cancel_count = user_data["cancel_count"]
        c_logs_html = "".join([f"<li style='margin-bottom: 2px;'>{log}</li>" for log in cancel_logs[-3:]])
        
        with st.container(border=True):
            st.markdown(f"""
            <div style="border-left: 4px solid #ed8936; padding-left: 12px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between;">
                    <div style="width: 50%;">
                        <div style="color:#dd6b20; font-weight: bold; margin-bottom: 5px;">🚫 代筆中キャンセル</div>
                        <div>
                            <span style="font-size: 1.6em; font-weight: bold; color: #2d3748;">{cancel_count}</span> <span style="font-size:0.8em; color: #4a5568;">件</span>
                            <span style="margin: 0 8px; color: #cbd5e0;">|</span>
                            <span style="font-size: 1.6em; font-weight: bold; color: #2d3748;">{cancel_total_min}</span> <span style="font-size:0.8em; color: #4a5568;">分</span>
                        </div>
                    </div>
                    <div style="width: 50%; text-align: right;">
                        <strong style="color: #4a5568; font-size: 0.8em;">追加履歴:</strong>
                        <ul style="margin: 0; padding-left: 0; list-style-type: none; font-size: 0.8em; color: #718096;">
                            {c_logs_html if c_logs_html else "<li style='color:#a0aec0;'>記録なし</li>"}
                        </ul>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            c_col1, c_col2, c_col3 = st.columns([1.5, 2, 1])
            with c_col1:
                st.markdown("<div style='font-size: 0.8em; color: #718096; margin-bottom: 2px;'>分数</div>", unsafe_allow_html=True)
                input_c_min = st.number_input("分数", min_value=1, max_value=180, value=10, key="input_c_min", label_visibility="collapsed")
            with c_col2:
                st.markdown("<div style='font-size: 0.8em; color: #718096; margin-bottom: 2px;'>メモ(任意)</div>", unsafe_allow_html=True)
                input_c_memo = st.text_input("メモ", placeholder="案件IDなど", key="input_c_memo", label_visibility="collapsed")
            with c_col3:
                st.markdown("<div style='font-size: 0.8em; color: #718096; margin-bottom: 2px;'>&nbsp;</div>", unsafe_allow_html=True)
                if st.button("追加", key="add_cancel_btn", use_container_width=True):
                    now_time = pd.Timestamp.now(tz='Asia/Tokyo').strftime('%H:%M')
                    memo_str = f" ({input_c_memo})" if input_c_memo else ""
                    new_log = f"{now_time} - {input_c_min}分{memo_str}"
                    
                    new_logs = cancel_logs.copy()
                    new_logs.append(new_log)
                    new_count = cancel_count + 1
                    new_total_min = cancel_total_min + input_c_min
                    
                    save_user_work_data(
                        st.session_state.selected_user, 
                        current_status, 
                        other_work_logs, 
                        other_work_total_min, 
                        other_work_start_time,
                        cancel_logs=new_logs,
                        cancel_total_min=new_total_min,
                        cancel_count=new_count
                    )
                    add_action_log(st.session_state.selected_user, "代筆中キャンセル追加", f"{input_c_min}分 {memo_str}")
                    st.rerun()

            st.markdown("""
            <div style='margin-top: 8px; padding-top: 8px; border-top: 1px dashed #e2e8f0; text-align: right;'>
                <a href='https://231707ee.form.kintoneapp.com/public/surrender' target='_blank' rel='noopener noreferrer' style='color: #2b6cb0; text-decoration: none; font-size: 0.85em; font-weight: bold;'>
                    📝 代筆中キャンセル登録フォーム
                </a>
            </div>
            """, unsafe_allow_html=True)
        
        now = pd.Timestamp.now(tz='Asia/Tokyo')
        today_date = now.date()
        
        sys_settings = get_system_settings()
        saved_target_date = sys_settings.get("target_date")
        
        if saved_target_date:
            target_end_date = pd.to_datetime(saved_target_date).date()
        else:
            target_end_date = today_date + pd.Timedelta(days=1)
        
        my_active_tasks = my_tasks[my_tasks['status'].isin(['着手', '中断', '未対応'])]
        
        # ▼▼▼ 修正: 日ごとに判定し、自分のタスクがない日の他/未割当タスクを日別に表示 ▼▼▼
        current_date = today_date
        has_any_displayed = False
        
        while current_date <= target_end_date:
            # その日の自分のアクティブタスクを取得
            my_active_for_date = my_active_tasks[my_active_tasks['datetime'].dt.date == current_date]
            
            # 自分のタスクがない場合のみ、その日の他の未対応タスクを探して表示
            if my_active_for_date.empty:
                other_target_tasks = pd.DataFrame()
                if not df.empty:
                    other_target_tasks = df[
                        (df['datetime'].dt.date == current_date) & 
                        (df['status'] == '未対応') &  
                        (df['assigned'].fillna('未割当') != st.session_state.selected_user) &
                        (df['product'] != 'JOBYmini')
                    ].sort_values('datetime')
                    
                if not other_target_tasks.empty:
                    has_any_displayed = True
                    date_str = current_date.strftime('%m/%d')
                    if current_date == today_date:
                        header_text = f"📅 今日 ({date_str}) の待機タスク (他/未割当)"
                    else:
                        header_text = f"📅 {date_str} の待機タスク (他/未割当)"
                        
                    st.markdown(f"<div style='margin-bottom: 2px; color: #d69e2e; font-weight: bold; font-size: 0.85em;'>{header_text}</div>", unsafe_allow_html=True)
                    task_list_html = "<div class='custom-card' style='padding: 6px 12px; border-left-color: #ecc94b; max-height: 90px; overflow-y: auto; font-size: 0.85em; margin-bottom: 8px;'>"
                    for _, t in other_target_tasks.iterrows():
                        t_time = t['datetime'].strftime('%H:%M')
                        disp_id = str(t['anken_id']).replace('_fukkatsu', '')
                        task_list_html += f"<div style='padding: 2px 0; border-bottom: 1px dashed #edf2f7; color: #4a5568;'>🕒 {t_time} <span style='color: #cbd5e0; margin: 0 5px;'>|</span> 🆔 {disp_id}</div>"
                    task_list_html += "</div>"
                    st.markdown(task_list_html, unsafe_allow_html=True)
            
            current_date += pd.Timedelta(days=1) # 翌日へ進める
            
        if not has_any_displayed:
            st.markdown(f"<div style='margin-bottom: 2px; color: #a0aec0; font-weight: bold; font-size: 0.85em;'>📅 今日〜{target_end_date.strftime('%m/%d')} の待機タスクはありません</div>", unsafe_allow_html=True)
        # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

    # --- 中段: 現在着手中の案件 ---
    st.markdown("<div style='margin-bottom: 4px; color: #4a5568; font-weight: bold;'>🏃 現在着手中</div>", unsafe_allow_html=True)
    
    active_tasks = my_tasks[my_tasks['status'] == '着手'] if not my_tasks.empty else pd.DataFrame()
    
    if not active_tasks.empty:
        task = active_tasks.iloc[0]
        task_date = task['datetime'].strftime('%m/%d')
        start_t = task['datetime'].strftime('%H:%M')
        duration_m = int(task['duration'])
        
        with st.container(border=True):
            st.markdown(f"""
            <div style="border-left: 4px solid #e53e3e; padding-left: 12px; margin-bottom: 8px;">
                <div style="font-size: 1.1em; font-weight: bold; color: #2d3748; margin-bottom: 4px;">
                    {task['method']}商談 ({task['product']})
                </div>
                <div style="color: #4a5568; font-size: 0.95em; margin-bottom: 6px;">
                    📝 {task['title']}
                </div>
                <div style="color: #718096; font-size: 0.9em;">
                    🕒 {task_date} {start_t} &nbsp;&nbsp;⏳ {duration_m} 分
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            phone_str = str(task['phone']).strip() if pd.notna(task['phone']) and str(task['phone']).strip() != "" else ""
            
            col_id, col_phone = st.columns(2)
            with col_id:
                st.markdown("<div style='font-size: 0.85em; color: #718096; margin-bottom: 2px;'>🆔 案件ID</div>", unsafe_allow_html=True)
                disp_id = str(task['anken_id']).replace('_fukkatsu', '')
                st.code(disp_id, language="text")
                
            with col_phone:
                if phone_str:
                    phone_str = phone_str.replace(",", " ")
                    st.markdown("<div style='font-size: 0.85em; color: #718096; margin-bottom: 2px;'>📞 連絡先電話番号</div>", unsafe_allow_html=True)
                    st.code(phone_str, language="text")
            
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
                    update_status(task['anken_id'], "未対応")
    else:
        st.info("現在着手中のタスクはありません。下の待機リストから「着手する」を押してください。")

    # --- 中段: 中断中のタスクリスト ---
    paused_tasks = my_tasks[my_tasks['status'] == '中断'].sort_values('datetime') if not my_tasks.empty else pd.DataFrame()
    
    if not paused_tasks.empty:
        st.markdown("<div style='margin-bottom: 4px; margin-top: 15px; color: #dd6b20; font-weight: bold;'>⏸️ 中断中のタスク</div>", unsafe_allow_html=True)
        
        for idx, task in paused_tasks.iterrows():
            task_date = task['datetime'].strftime('%m/%d')
            start_t = task['datetime'].strftime('%H:%M')
            duration_m = int(task['duration'])
            f_icon = "🔊 復活音源 " if task['fukkatsu'] else ""
            
            with st.container(border=True):
                st.markdown(f"""
                <div style="border-left: 4px solid #ed8936; padding-left: 12px; margin-bottom: 8px;">
                    <div style="font-weight: bold; color: #2d3748; margin-bottom: 2px;">
                        <span style="color:#805ad5;">{f_icon}</span>{task['method']}商談 ({task['product']})
                    </div>
                    <div style="color: #4a5568; font-size: 0.85em; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                        📝 {task['title']}
                    </div>
                    <div style="color: #718096; font-size: 0.85em;">
                        🕒 {task_date} {start_t} &nbsp;&nbsp;⏳ {duration_m} 分 &nbsp;&nbsp;|&nbsp;&nbsp; <span style="color: #dd6b20; font-weight: bold;">⏸️ 中断中</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                phone_str = str(task['phone']).strip() if pd.notna(task['phone']) and str(task['phone']).strip() != "" else ""
                
                col_id, col_phone = st.columns(2)
                with col_id:
                    st.markdown("<div style='font-size: 0.85em; color: #718096; margin-bottom: 2px;'>🆔 案件ID</div>", unsafe_allow_html=True)
                    disp_id = str(task['anken_id']).replace('_fukkatsu', '')
                    st.code(disp_id, language="text")
                with col_phone:
                    if phone_str:
                        phone_str = phone_str.replace(",", " ")
                        st.markdown("<div style='font-size: 0.85em; color: #718096; margin-bottom: 2px;'>📞 連絡先電話番号</div>", unsafe_allow_html=True)
                        st.code(phone_str, language="text")
                
                b_col1, b_col2 = st.columns([4, 1])
                with b_col2:
                    is_disabled = not active_tasks.empty
                    if st.button("▶ 再開する", key=f"resume_{task['anken_id']}", disabled=is_disabled, use_container_width=True):
                        update_status(task['anken_id'], "着手")

    # --- 下段: 待機中のタスクリスト ---
    st.markdown("<div style='margin-bottom: 4px; margin-top: 15px; color: #4a5568; font-weight: bold;'>📋 待機中のタスク</div>", unsafe_allow_html=True)
    
    waiting_tasks = my_tasks[my_tasks['status'] == '未対応'].copy() if not my_tasks.empty else pd.DataFrame()
    
    if waiting_tasks.empty:
        st.success("待機中のタスクはすべて完了しました！🎉")
    else:
        waiting_tasks['is_fp'] = waiting_tasks.apply(lambda r: str(r['anken_id']).replace('_fukkatsu', '') in api_fastpass_ids and (min_unassigned_date is None or r['datetime'].date() <= min_unassigned_date), axis=1)
        waiting_tasks = waiting_tasks.sort_values(by=['is_fp', 'datetime'], ascending=[False, True])
        
        for idx, task in waiting_tasks.iterrows():
            task_date = task['datetime'].strftime('%m/%d')
            start_t = task['datetime'].strftime('%H:%M')
            duration_m = int(task['duration'])
            f_icon = "🔊 復活音源 " if task['fukkatsu'] else ""
            
            is_fp = task.get('is_fp', False)
            border_color = "#e53e3e" if is_fp else "#a0aec0"
            fp_badge = "<span style='background-color: #e53e3e; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; margin-right: 8px;'>🔥 優先</span>" if is_fp else ""
            
            with st.container(border=True):
                st.markdown(f"""
                <div style="border-left: 4px solid {border_color}; padding-left: 12px; margin-bottom: 8px;">
                    <div style="font-weight: bold; color: #2d3748; margin-bottom: 2px;">
                        {fp_badge}<span style="color:#805ad5;">{f_icon}</span>{task['method']}商談 ({task['product']})
                    </div>
                    <div style="color: #4a5568; font-size: 0.85em; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                        📝 {task['title']}
                    </div>
                    <div style="color: #718096; font-size: 0.85em;">
                        🕒 {task_date} {start_t} &nbsp;&nbsp;⏳ {duration_m} 分 &nbsp;&nbsp;|&nbsp;&nbsp; 🏷️ 未対応
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                phone_str = str(task['phone']).strip() if pd.notna(task['phone']) and str(task['phone']).strip() != "" else ""
                
                col_id, col_phone = st.columns(2)
                with col_id:
                    st.markdown("<div style='font-size: 0.85em; color: #718096; margin-bottom: 2px;'>🆔 案件ID</div>", unsafe_allow_html=True)
                    disp_id = str(task['anken_id']).replace('_fukkatsu', '')
                    st.code(disp_id, language="text")
                with col_phone:
                    if phone_str:
                        phone_str = phone_str.replace(",", " ")
                        st.markdown("<div style='font-size: 0.85em; color: #718096; margin-bottom: 2px;'>📞 連絡先電話番号</div>", unsafe_allow_html=True)
                        st.code(phone_str, language="text")
                
                b_col1, b_col2 = st.columns([4, 1])
                with b_col2:
                    is_disabled = not active_tasks.empty
                    if st.button("▶ 着手する", key=f"start_{task['anken_id']}", disabled=is_disabled, use_container_width=True):
                        update_status(task['anken_id'], "着手")

    # --- 最下段: 完了済みのタスクリスト ---
    st.markdown("<div style='margin-bottom: 4px; margin-top: 25px; color: #4a5568; font-weight: bold;'>✅ 本日の完了タスク</div>", unsafe_allow_html=True)
    
    if not my_tasks.empty:
        completed_df = my_tasks[my_tasks['status'] == '完了']
        if completed_df.empty:
            st.info("本日完了したタスクはまだありません。")
        else:
            for idx, task in completed_df.sort_values('datetime', ascending=False).iterrows():
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
                
                with st.container(border=True):
                    st.markdown(f"""
                    <div style="border-left: 4px solid #48bb78; padding-left: 12px; background-color: #f0fff4; opacity: 0.8; padding-top: 5px; padding-bottom: 5px; border-radius: 4px;">
                        <div style="font-weight: bold; color: #4a5568; margin-bottom: 2px;">
                            <span style="color:#805ad5;">{f_icon}</span>{task['method']}商談 ({task['product']})
                        </div>
                        <div style="color: #718096; font-size: 0.85em; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-decoration: line-through;">
                            📝 {task['title']}
                        </div>
                        <div style="color: #718096; font-size: 0.85em;">
                            🕒 {task_date} {start_t} &nbsp;&nbsp;⏳ {duration_m} 分 &nbsp;&nbsp;|&nbsp;&nbsp; <span style="color: #2f855a; font-weight: bold;">✅ 完了 {f_min_text}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    phone_str = str(task['phone']).strip() if pd.notna(task['phone']) and str(task['phone']).strip() != "" else ""
                    
                    st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
                    col_id, col_phone = st.columns(2)
                    with col_id:
                        st.markdown("<div style='font-size: 0.8em; color: #718096; margin-bottom: 2px;'>🆔 案件ID</div>", unsafe_allow_html=True)
                        disp_id = str(task['anken_id']).replace('_fukkatsu', '')
                        st.code(disp_id, language="text")
                    with col_phone:
                        if phone_str:
                            phone_str = phone_str.replace(",", " ")
                            st.markdown("<div style='font-size: 0.8em; color: #718096; margin-bottom: 2px;'>📞 連絡先電話番号</div>", unsafe_allow_html=True)
                            st.code(phone_str, language="text")

# ==========================================
# 6. 管理者タブ
# ==========================================
elif current_tab == "⚙️ 管理者":
    st.markdown("<h2 style='color: #2c5282; margin-bottom: 20px;'>⚙️ 管理者コントロールパネル</h2>", unsafe_allow_html=True)

    if HAS_AUTOREFRESH:
        st_autorefresh(interval=60000, key="admin_autorefresh")
    else:
        st.warning("💡 **管理者用の自動更新機能を有効にするには:** Pythonの実行環境（ターミナル）で `pip install streamlit-autorefresh` を実行して再起動してください。")

    if df.empty:
        st.warning("現在表示できるデータがありません。（GASからデータを取得できていません）")
    else:
        col_admin_l, col_admin_r = st.columns([1, 1.4])
        
        with col_admin_l:
            st.markdown("<h4 style='color: #4a5568;'>🕒 指定日時までのタスク抽出</h4>", unsafe_allow_html=True)
            
            sys_settings = get_system_settings()
            saved_target_date_str = sys_settings.get("target_date")
            default_target_date = pd.to_datetime(saved_target_date_str).date() if saved_target_date_str else pd.Timestamp.now(tz='Asia/Tokyo').date()

            col_d, col_t = st.columns(2)
            with col_d:
                target_date = st.date_input("対象日付", default_target_date)
                if str(target_date) != saved_target_date_str:
                    save_system_settings("target_date", str(target_date))
            with col_t:
                target_time = st.time_input("対象時間 (まで)", datetime.strptime("15:00", "%H:%M").time())
                
            target_datetime = datetime.combine(target_date, target_time)
            target_dt_tz = pd.to_datetime(target_datetime).tz_localize('Asia/Tokyo')
            
            filtered_df = df[(df['datetime'] <= target_dt_tz) & (df['product'] != 'JOBYmini') & (~df['status'].isin(['完了', '取り消し']))].copy()
            
            if filtered_df.empty:
                st.info(f"{target_date.strftime('%m/%d')} {target_time.strftime('%H:%M')} までのタスクなし")
            else:
                filtered_df = filtered_df.sort_values('datetime')
                st.markdown(f"<div style='margin-bottom: 5px; font-weight: bold; color: #2d3748;'>該当タスク: <span style='color: #e53e3e; font-size: 1.2em;'>{len(filtered_df)}</span> 件</div>", unsafe_allow_html=True)
                
                display_df = filtered_df[['datetime', 'anken_id']].copy()
                display_df['datetime'] = display_df['datetime'].dt.strftime('%m/%d %H:%M')
                display_df['anken_id'] = display_df['anken_id'].astype(str).str.replace('_fukkatsu', '')
                display_df.columns = ['日時', '案件ID']
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )

            st.markdown("<hr style='margin: 25px 0 15px 0;'>", unsafe_allow_html=True)
            st.markdown("<h5 style='color: #4a5568;'>⚙️ カレンダー取得範囲設定</h5>", unsafe_allow_html=True)
            
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                past_days = st.number_input("開始(過去〇日)", min_value=0, max_value=365, value=api_settings.get("past_days", 7))
            with col_s2:
                future_days = st.number_input("終了(未来〇日)", min_value=0, max_value=365, value=api_settings.get("future_days", 30))
            
            if st.button("💾 設定を保存して再取得", type="primary", use_container_width=True):
                update_settings(past_days, future_days)

            st.markdown("<hr style='margin: 25px 0 15px 0;'>", unsafe_allow_html=True)
            
            header_col1, header_col2 = st.columns([1.5, 1])
            with header_col1:
                st.markdown("<h5 style='color: #4a5568; padding-top: 25px;'>📅 直近1週間の残りタスク数</h5>", unsafe_allow_html=True)
            with header_col2:
                boundary_time = st.time_input("AM/PM 分割時間 (指定時間までがAM)", datetime.strptime("13:00", "%H:%M").time())
            
            if not df.empty:
                target_tasks = df[(df['status'].isin(['着手', '中断', '未対応'])) & (df['product'] != 'JOBYmini')].copy()
                task_counts = {}
                if not target_tasks.empty:
                    target_tasks['date'] = target_tasks['datetime'].dt.date
                    target_tasks['time'] = target_tasks['datetime'].dt.time
                    target_tasks['is_jiei'] = target_tasks['title'].astype(str).str.contains('自営', na=False)
                    target_tasks['is_am'] = target_tasks['time'] <= boundary_time
                    
                    def categorize(row):
                        if row['is_jiei']:
                            return '自営'
                        elif row['is_am']:
                            return '他営AM'
                        else:
                            return '他営PM'
                            
                    target_tasks['category'] = target_tasks.apply(categorize, axis=1)
                    
                    for _, row in target_tasks.iterrows():
                        d = row['date']
                        cat = row['category']
                        if d not in task_counts:
                            task_counts[d] = {'他営AM': 0, '他営PM': 0, '自営': 0}
                        task_counts[d][cat] += 1
            else:
                task_counts = {}

            now = pd.Timestamp.now(tz='Asia/Tokyo')
            today_date = now.date()
            youbi_list = ['月', '火', '水', '木', '金', '土', '日']
            
            upcoming_data = []
            for i in range(7):
                target_d = today_date + pd.Timedelta(days=i)
                counts = task_counts.get(target_d, {'他営AM': 0, '他営PM': 0, '自営': 0})
                
                am_c = counts['他営AM']
                pm_c = counts['他営PM']
                jiei_c = counts['自営']
                total_c = am_c + pm_c + jiei_c
                
                date_str = f"{target_d.month}/{target_d.day}（{youbi_list[target_d.weekday()]}）"
                
                upcoming_data.append({
                    "日付（曜日）": date_str,
                    "他営AM": am_c,
                    "他営PM": pm_c,
                    "自営": jiei_c,
                    "合計": total_c
                })
                
            upcoming_df = pd.DataFrame(upcoming_data)
            
            st.dataframe(
                upcoming_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "日付（曜日）": st.column_config.Column("日付（曜日）", width="small"),
                    "他営AM": st.column_config.NumberColumn("他営AM", format="%d 件", width="small"),
                    "他営PM": st.column_config.NumberColumn("他営PM", format="%d 件", width="small"),
                    "自営": st.column_config.NumberColumn("自営", format="%d 件", width="small"),
                    "合計": st.column_config.NumberColumn("合計", format="%d 件", width="small")
                }
            )

            st.markdown("<hr style='margin: 25px 0 15px 0;'>", unsafe_allow_html=True)
            st.markdown("<h5 style='color: #4a5568;'>⏰ 全メンバー一括 残業設定</h5>", unsafe_allow_html=True)
            st.markdown("<p style='font-size: 0.85em; color: #718096; margin-bottom: 10px;'>※この設定は「早番」の退勤リミット（17:00）を延長し、夕方以降のタスクも割り当てられるようにします。</p>", unsafe_allow_html=True)
            
            current_ot = 0
            if api_members_data and len(api_members_data) > 0:
                current_ot = int(api_members_data[0].get("overtime", 0))
                
            col_ot1, col_ot2 = st.columns([2, 1], vertical_alignment="bottom")
            with col_ot1:
                new_overtime = st.number_input("残業時間 (分)", min_value=0, max_value=300, step=30, value=current_ot)
            with col_ot2:
                if st.button("💾 適用して再計算", type="primary", use_container_width=True, key="btn_update_ot"):
                    update_all_overtime(new_overtime)

        with col_admin_r:
            st.markdown("<h4 style='color: #4a5568;'>👥 メンバー稼働ステータス</h4>", unsafe_allow_html=True)
            
            task_times = get_task_times()
            
            active_df = df[df['status'] == '着手'] if not df.empty else pd.DataFrame()
            active_dict = {}
            for _, row in active_df.iterrows():
                disp_id = str(row['anken_id']).replace('_fukkatsu', '')
                active_dict[row['assigned']] = disp_id
                
            summary_data = []
            
            raw_users_list = api_members if api_members else df['assigned'].fillna('未割当').unique().tolist()
            if "未割当" not in raw_users_list:
                raw_users_list = list(raw_users_list) + ["未割当"]
            
            clean_users = []
            for u in raw_users_list:
                if pd.isna(u): continue
                u_str = str(u).strip().replace("　", "") 
                if u_str == "": continue
                if u == "未割当" and (df.empty or len(df[df['assigned'].fillna('未割当') == '未割当']) == 0): continue
                if u not in clean_users: clean_users.append(u)
            
            for user in clean_users:
                user_df = df[df['assigned'].fillna('未割当') == user] if not df.empty else pd.DataFrame()
                
                mitaiou_count = len(user_df[user_df['status'] == '未対応']) if not user_df.empty else 0
                
                completed_df = user_df[user_df['status'] == '完了'] if not user_df.empty else pd.DataFrame()
                
                normal_df = completed_df[completed_df['fukkatsu'] == False] if not completed_df.empty else pd.DataFrame()
                comp_count = len(normal_df)
                comp_min = pd.to_numeric(normal_df['duration'], errors='coerce').fillna(0).sum() if not normal_df.empty else 0
                
                fukkatsu_df = completed_df[completed_df['fukkatsu'] == True] if not completed_df.empty else pd.DataFrame()
                fukkatsu_count = len(fukkatsu_df)
                
                user_work_data = get_user_work_data(user)
                other_work_min = user_work_data["other_work_total_min"]
                break_min = user_work_data["break_total_min"] 
                user_status = user_work_data["current_status"]
                
                current_action = active_dict.get(user)
                if current_action:
                    display_action = f"対応: {current_action}"
                elif user_status != "出社":
                    display_action = f"[{user_status}]"
                else:
                    display_action = "待機中"
                
                summary_data.append({
                    "担当者": user,
                    "未対応": mitaiou_count,
                    "完了": comp_count,
                    "完了分数": int(comp_min),
                    "復活音源件数": fukkatsu_count,
                    "別業務時間": other_work_min,
                    "休憩時間": break_min, 
                    "現在の作業": display_action
                })
                
            if summary_data:
                sum_df = pd.DataFrame(summary_data)
                calc_height = len(sum_df) * 30 + 38 
                
                st.dataframe(
                    sum_df,
                    use_container_width=True,
                    hide_index=True,
                    height=calc_height,
                    column_config={
                        "担当者": st.column_config.Column("担当者", width="small"),
                        "未対応": st.column_config.NumberColumn("未対応", format="%d", width="small"),
                        "完了": st.column_config.NumberColumn("完了", format="%d", width="small"),
                        "完了分数": st.column_config.NumberColumn("完了分数", format="%d 分", width="small"),
                        "復活音源件数": st.column_config.NumberColumn("復活音源", format="%d", width="small"),
                        "別業務時間": st.column_config.NumberColumn("別業務", format="%d 分", width="small"),
                        "休憩時間": st.column_config.NumberColumn("休憩", format="%d 分", width="small"), 
                        "現在の作業": st.column_config.Column("現在の作業", width="medium"),
                    }
                )
            else:
                st.info("現在稼働中のメンバーデータがありません。")

            st.markdown("<hr style='margin: 25px 0 15px 0;'>", unsafe_allow_html=True)
            
            with st.expander("🛠️ メンバースキル＆勤怠設定 (自動振り分け条件) を開く / 閉じる", expanded=False):
                if api_members_data:
                    mem_df = pd.DataFrame(api_members_data)
                    clean_mem_data = []
                    for _, row in mem_df.iterrows():
                        u = row['name']
                        if pd.isna(u): continue
                        u_str = str(u).strip().replace("　", "")
                        if u_str == "": continue
                        clean_mem_data.append(row)
                    
                    if clean_mem_data:
                        clean_mem_df = pd.DataFrame(clean_mem_data)
                        if 'shift' not in clean_mem_df.columns:
                            clean_mem_df['shift'] = '早番'
                        
                        display_mem_df = clean_mem_df[['name', 'status', 'shift', 'itsuzai', 'agent', 'shukyaku', 'jiei']].copy()
                        display_mem_df.columns = ['担当者', 'ステータス', 'シフト', 'ｲﾂｻﾞｲ', 'ｴｰｼﾞｪﾝﾄ', '集客', '自営(/自)']
                        
                        calc_skill_height = len(display_mem_df) * 30 + 38
                        
                        edited_mem_df = st.data_editor(
                            display_mem_df,
                            use_container_width=True,
                            hide_index=True,
                            height=calc_skill_height,
                            disabled=['担当者'],
                            column_config={
                                "担当者": st.column_config.Column("担当者", width="small"),
                                "ステータス": st.column_config.SelectboxColumn("ステータス ✏️", options=["出社", "退勤", "欠勤", "休憩中", "別業務中"], width="small"),
                                "シフト": st.column_config.SelectboxColumn("シフト ✏️", options=["早番", "中番"], width="small"),
                                "ｲﾂｻﾞｲ": st.column_config.CheckboxColumn("ｲﾂｻﾞｲ", default=False),
                                "ｴｰｼﾞｪﾝﾄ": st.column_config.CheckboxColumn("ｴｰｼﾞｪﾝﾄ", default=False),
                                "集客": st.column_config.CheckboxColumn("集客", default=False),
                                "自営(/自)": st.column_config.CheckboxColumn("自営(/自)", default=False),
                            },
                            key="admin_skills_editor"
                        )
                        
                        if not edited_mem_df.equals(display_mem_df):
                            for idx in display_mem_df.index:
                                old_row = display_mem_df.loc[idx]
                                new_row = edited_mem_df.loc[idx]
                                if not old_row.equals(new_row):
                                    update_skills(
                                        new_row['担当者'], new_row['ステータス'], new_row['シフト'],
                                        bool(new_row['ｲﾂｻﾞｲ']), bool(new_row['ｴｰｼﾞｪﾝﾄ']), bool(new_row['集客']), bool(new_row['自営(/自)'])
                                    )
                                    break
                    else:
                        st.info("有効なメンバー設定データがありません。")
                else:
                    st.info("メンバー設定データがありません。")

        st.markdown("<hr style='margin: 30px 0;'>", unsafe_allow_html=True)
        
        all_display_df = df[['assigned', 'status', 'datetime', 'anken_id', 'title', 'duration', 'product', 'method']].copy()
        
        all_display_df['is_fp'] = all_display_df.apply(lambda r: str(r['anken_id']).replace('_fukkatsu', '') in api_fastpass_ids and (min_unassigned_date is None or r['datetime'].date() <= min_unassigned_date), axis=1)
        
        all_display_df['datetime'] = all_display_df['datetime'].dt.strftime('%m/%d %H:%M')
        all_display_df.columns = ['担当者', 'ステータス', '日時', '案件ID', 'タイトル', '分数', '商材', '商談方法', 'is_fp']
        all_display_df['担当者'] = all_display_df['担当者'].fillna('')
        all_display_df['表示用案件ID'] = all_display_df['案件ID'].astype(str).str.replace('_fukkatsu', '')
        
        unique_products = all_display_df['商材'].dropna().unique().tolist()
        default_products = [p for p in unique_products if p != "JOBYmini"]
        
        selected_products = st.multiselect(
            "🏷️ 表示する商材を選択 (JOBYminiはデフォルトで除外されています)",
            options=unique_products,
            default=default_products
        )
        
        filtered_all_df = all_display_df[all_display_df['商材'].isin(selected_products)].copy()
        
        completed_cases_df = filtered_all_df[filtered_all_df['ステータス'] == '完了'].copy()
        completed_cases_df = completed_cases_df.sort_values('日時', ascending=False).reset_index(drop=True)
        
        in_progress_cases_df = filtered_all_df[filtered_all_df['ステータス'].isin(['着手', '中断'])].copy()
        status_priority_prog = {'着手': 1, '中断': 2}
        in_progress_cases_df['優先度'] = in_progress_cases_df['ステータス'].map(status_priority_prog).fillna(3)
        in_progress_cases_df = in_progress_cases_df.sort_values(['優先度', '日時']).drop('優先度', axis=1).reset_index(drop=True)
        
        task_times = get_task_times()
        in_progress_cases_df['開始時間'] = in_progress_cases_df['案件ID'].astype(str).map(task_times).fillna('')
        
        in_progress_cols = ['担当者', 'ステータス', '開始時間', '日時', '案件ID', '表示用案件ID', 'タイトル', '分数', '商材', '商談方法']
        in_progress_cases_df = in_progress_cases_df[in_progress_cols]
        
        waiting_cases_df = filtered_all_df[~filtered_all_df['ステータス'].isin(['完了', '着手', '中断'])].copy()
        status_priority_wait = {'未対応': 1, '取り消し': 2}
        waiting_cases_df['優先度'] = waiting_cases_df['ステータス'].map(status_priority_wait).fillna(3)
        waiting_cases_df = waiting_cases_df.sort_values(['優先度', '日時']).drop('優先度', axis=1).reset_index(drop=True)
        
        assign_options = [""] + users
        
        col_w_title, col_w_search = st.columns([3, 1], vertical_alignment="bottom")
        with col_w_title:
            st.markdown("<h4 style='color: #4a5568; margin-top: 15px;'>📋 現在の案件リスト (未対応 / 担当者変更可)</h4>", unsafe_allow_html=True)
        with col_w_search:
            search_query = st.text_input("検索", placeholder="🔍 案件IDで検索...", label_visibility="collapsed", key="search_waiting")
            
        if search_query:
            waiting_cases_display_df = waiting_cases_df[waiting_cases_df['案件ID'].astype(str).str.contains(search_query, case=False, na=False)].reset_index(drop=True)
        else:
            waiting_cases_display_df = waiting_cases_df
        
        fp_waiting_df = waiting_cases_display_df[waiting_cases_display_df['is_fp'] == True].reset_index(drop=True)
        normal_waiting_df = waiting_cases_display_df[waiting_cases_display_df['is_fp'] == False].reset_index(drop=True)
        
        if fp_waiting_df.empty and normal_waiting_df.empty:
            if search_query: st.info(f"「{search_query}」に一致する待機中案件はありません。")
            else: st.success("現在待機中の案件はありません。")
        else:
            if not fp_waiting_df.empty:
                st.markdown("<div style='margin-bottom: 5px; color: #e53e3e; font-weight: bold;'>🔥 優先タスク (ファストパス)</div>", unsafe_allow_html=True)
                edited_fp_df = st.data_editor(
                    fp_waiting_df,
                    use_container_width=True,
                    hide_index=True,
                    disabled=['ステータス', '日時', '案件ID', '表示用案件ID', 'タイトル', '分数', '商材', '商談方法', 'is_fp'],
                    column_order=['担当者', 'ステータス', '日時', '表示用案件ID', 'タイトル', '分数', '商材', '商談方法'],
                    column_config={
                        "タイトル": st.column_config.Column("タイトル", width="large"),
                        "担当者": st.column_config.SelectboxColumn("担当者 ✏️", width="small", options=assign_options),
                        "ステータス": st.column_config.Column("ステータス", width="small"),
                        "表示用案件ID": st.column_config.Column("案件ID", width="small"),
                        "案件ID": None, 
                        "is_fp": None,
                    },
                    key="admin_fp_waiting_data_editor"
                )
                if not edited_fp_df.equals(fp_waiting_df):
                    for idx in fp_waiting_df.index:
                        if fp_waiting_df.loc[idx, '担当者'] != edited_fp_df.loc[idx, '担当者']:
                            update_assign(edited_fp_df.loc[idx, '案件ID'], edited_fp_df.loc[idx, '担当者'])
                            break

            if not normal_waiting_df.empty:
                if not fp_waiting_df.empty:
                    st.markdown("<div style='margin-top: 15px; margin-bottom: 5px; color: #4a5568; font-weight: bold;'>🔹 通常タスク</div>", unsafe_allow_html=True)
                edited_normal_df = st.data_editor(
                    normal_waiting_df,
                    use_container_width=True,
                    hide_index=True,
                    disabled=['ステータス', '日時', '案件ID', '表示用案件ID', 'タイトル', '分数', '商材', '商談方法', 'is_fp'],
                    column_order=['担当者', 'ステータス', '日時', '表示用案件ID', 'タイトル', '分数', '商材', '商談方法'],
                    column_config={
                        "タイトル": st.column_config.Column("タイトル", width="large"),
                        "担当者": st.column_config.SelectboxColumn("担当者 ✏️", width="small", options=assign_options),
                        "ステータス": st.column_config.Column("ステータス", width="small"),
                        "表示用案件ID": st.column_config.Column("案件ID", width="small"),
                        "案件ID": None, 
                        "is_fp": None,
                    },
                    key="admin_normal_waiting_data_editor"
                )
                if not edited_normal_df.equals(normal_waiting_df):
                    for idx in normal_waiting_df.index:
                        if normal_waiting_df.loc[idx, '担当者'] != edited_normal_df.loc[idx, '担当者']:
                            update_assign(edited_normal_df.loc[idx, '案件ID'], edited_normal_df.loc[idx, '担当者'])
                            break
                        
        st.markdown("<hr style='margin: 30px 0 15px 0; border-top: dashed 2px #cbd5e0;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #4a5568;'>🏃 着手中・中断中の案件リスト (担当者変更可)</h4>", unsafe_allow_html=True)
        
        if in_progress_cases_df.empty:
            st.info("現在着手中・中断中の案件はありません。")
        else:
            edited_inprogress_df = st.data_editor(
                in_progress_cases_df,
                use_container_width=True,
                hide_index=True,
                disabled=['ステータス', '開始時間', '日時', '案件ID', '表示用案件ID', 'タイトル', '分数', '商材', '商談方法'],
                column_order=['担当者', 'ステータス', '開始時間', '日時', '表示用案件ID', 'タイトル', '分数', '商材', '商談方法'],
                column_config={
                    "タイトル": st.column_config.Column("タイトル", width="large"),
                    "担当者": st.column_config.SelectboxColumn("担当者 ✏️", width="small", options=assign_options),
                    "ステータス": st.column_config.Column("ステータス", width="small"),
                    "開始時間": st.column_config.Column("開始時間", width="small"),
                    "表示用案件ID": st.column_config.Column("案件ID", width="small"),
                    "案件ID": None, 
                },
                key="admin_inprogress_data_editor"
            )
            
            if not edited_inprogress_df.equals(in_progress_cases_df):
                for idx in in_progress_cases_df.index:
                    if in_progress_cases_df.loc[idx, '担当者'] != edited_inprogress_df.loc[idx, '担当者']:
                        update_assign(edited_inprogress_df.loc[idx, '案件ID'], edited_inprogress_df.loc[idx, '担当者'])
                        break

        st.markdown("<hr style='margin: 30px 0 15px 0; border-top: dashed 2px #cbd5e0;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #4a5568;'>✅ 完了済みの案件リスト</h4>", unsafe_allow_html=True)
        
        if completed_cases_df.empty:
            st.info("完了済みの案件はまだありません。")
        else:
            st.dataframe(
                completed_cases_df,
                use_container_width=True,
                hide_index=True,
                column_order=['担当者', 'ステータス', '日時', '表示用案件ID', 'タイトル', '分数', '商材', '商談方法'],
                column_config={
                    "タイトル": st.column_config.Column("タイトル", width="large"),
                    "担当者": st.column_config.Column("担当者", width="small"),
                    "ステータス": st.column_config.Column("ステータス", width="small"),
                    "表示用案件ID": st.column_config.Column("案件ID", width="small"),
                    "案件ID": None, 
                    "is_fp": None,
                }
            )

        st.markdown("<hr style='margin: 40px 0 20px 0; border-top: solid 2px #e53e3e;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #e53e3e;'>🚨 危険エリア (システム全リセット)</h4>", unsafe_allow_html=True)
        
        with st.expander("⚠️ 全データを白紙に戻し、カレンダーから再取得＆再振り分けを実行する", expanded=False):
            st.warning("**【注意】** この操作を行うと、本日の担当者の振り分け状況、完了ステータス、手 manualで変更した担当者情報などが**すべて白紙に戻ります**。\n1日の業務がすべて終了した後の「翌日に向けたリセット」や、システムに大きなズレが生じた場合の「緊急復旧」の時のみ使用してください。")
            if st.checkbox("上記を理解した上で、全リセットを実行します。"):
                if st.button("🔥 実行する (元に戻せません)", type="primary"):
                    reset_system()

        st.markdown("<hr style='margin: 40px 0 20px 0; border-top: dashed 2px #cbd5e0;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #4a5568;'>📜 過去1時間のシステム動作ログ</h4>", unsafe_allow_html=True)
        
        action_logs = get_action_logs()
        if not action_logs:
            st.info("過去1時間の間に記録された動作ログはありません。")
        else:
            log_data = []
            for log in action_logs:
                ts = pd.to_datetime(log["timestamp"]).strftime('%H:%M:%S')
                log_data.append({
                    "時間": ts,
                    "操作ユーザー": log["user"],
                    "アクション": log["action"],
                    "詳細": log["details"]
                })
            
            log_df = pd.DataFrame(log_data)
            st.dataframe(
                log_df,
                use_container_width=True,
                hide_index=True,
                height=300,
                column_config={
                    "時間": st.column_config.Column("時間", width="small"),
                    "操作ユーザー": st.column_config.Column("操作ユーザー", width="small"),
                    "アクション": st.column_config.Column("アクション", width="medium"),
                    "詳細": st.column_config.Column("詳細", width="large"),
                }
            )

# ==========================================
# 7. 監査マニュアルタブ
# ==========================================
elif current_tab == "📖 監査マニュアル":
    st.markdown("<h2 style='color: #2c5282; margin-bottom: 20px;'>📖 監査マニュアル</h2>", unsafe_allow_html=True)
    
    if not api_manual_data:
        st.warning("現在表示できるデータがありません。（GASからデータを取得できていないか、スプレッドシートが空です）")
        st.info("※GASのdoGet関数を最新のものに更新しているか確認してください。")
    else:
        st.info("💡 **一括コピー機能:** 以下のカードの**どこでもクリックするだけ**で、中身のテキストがクリップボードに一発でコピーされます！")
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: sans-serif; margin: 0; padding: 10px; background-color: #f4f7f9; }
                .grid-container {
                    display: grid;
                    grid-template-columns: repeat(6, 1fr);
                    gap: 10px;
                }
                .header-card {
                    background-color: #2c5282;
                    color: white;
                    font-weight: bold;
                    text-align: center;
                    padding: 10px;
                    border-radius: 6px;
                    font-size: 14px;
                    position: sticky;
                    top: 0;
                    z-index: 10;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .cell-card {
                    background-color: white;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    padding: 12px;
                    font-size: 13px;
                    color: #4a5568;
                    cursor: pointer;
                    position: relative;
                    transition: all 0.2s ease;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                    min-height: 80px;
                }
                .cell-card:hover {
                    border-color: #4299e1;
                    box-shadow: 0 4px 6px rgba(66, 153, 225, 0.2);
                    transform: translateY(-2px);
                }
                .cell-card:active {
                    background-color: #ebf8ff;
                    transform: translateY(0);
                }
                .text-content {
                    white-space: pre-wrap;
                    word-break: break-word;
                    margin-bottom: 10px;
                    pointer-events: none; 
                }
                .copied-badge {
                    position: absolute;
                    bottom: 8px;
                    right: 8px;
                    background-color: #48bb78;
                    color: white;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 3px 8px;
                    border-radius: 12px;
                    opacity: 0;
                    transition: opacity 0.3s ease;
                    pointer-events: none;
                }
                .empty-cell {
                    background-color: transparent;
                    border: 1px dashed #cbd5e0;
                    color: #a0aec0;
                    text-align: center;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: default;
                }
                .empty-cell:hover { transform: none; box-shadow: none; border-color: #cbd5e0; }
            </style>
        </head>
        <body>
            <div class="grid-container">
                <div class="header-card">level⑥</div>
                <div class="header-card">level⑤</div>
                <div class="header-card">level④</div>
                <div class="header-card">level③</div>
                <div class="header-card">level②</div>
                <div class="header-card">level①</div>
        """
        
        for row in api_manual_data:
            for key in ["level6", "level5", "level4", "level3", "level2", "level1"]:
                val = row.get(key, "").strip()
                if val:
                    display_val = html_lib.escape(val)
                    html_content += f"""
                    <div class="cell-card" onclick="copyToClipboard(this)">
                        <div class="text-content">{display_val}</div>
                        <span class="copied-badge">Copied!</span>
                    </div>
                    """
                else:
                    html_content += f'<div class="cell-card empty-cell">-</div>'
                    
        html_content += """
            </div>
            
            <script>
            function copyToClipboard(element) {
                const text = element.querySelector('.text-content').innerText;
                
                const fallbackCopy = (str) => {
                    const textArea = document.createElement("textarea");
                    textArea.value = str;
                    document.body.appendChild(textArea);
                    textArea.select();
                    try { document.execCommand('copy'); } catch (err) {}
                    document.body.removeChild(textArea);
                };
                
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(text).catch(() => fallbackCopy(text));
                } else {
                    fallbackCopy(text);
                }
                
                const badge = element.querySelector('.copied-badge');
                if (badge) {
                    badge.style.opacity = '1';
                    setTimeout(() => {
                        badge.style.opacity = '0';
                    }, 1500);
                }
            }
            </script>
        </body>
        </html>
        """
        
        components.html(html_content, height=800, scrolling=True)
