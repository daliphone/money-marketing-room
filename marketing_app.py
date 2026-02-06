import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- 1. 頁面設定 ---
st.set_page_config(
    page_title="馬尼行銷情報室 v2.3",
    page_icon="📢",
    layout="wide"
)

# --- 2. 讀取資料函式 ---
@st.cache_data(ttl=600)
def load_marketing_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Marketing_Schedule")
    df = df.dropna(how="all")
    return df

try:
    df_raw = load_marketing_data()
    df = df_raw.copy()
    # 確保日期與字串格式正確
    df['開始日期'] = pd.to_datetime(df['開始日期'], errors='coerce')
    df['結束日期'] = pd.to_datetime(df['結束日期'], errors='coerce')
    df['重複星期'] = df['重複星期'].astype(str)
    df['週期模式'] = df['週期模式'].astype(str)
except Exception as e:
    st.error(f"資料讀取失敗，請確認 Google Sheets 欄位結構 (v2.1標準)。錯誤訊息: {e}")
    st.stop()

# --- 3. 側邊欄導航 ---
with st.sidebar:
    st.title("📢 馬尼情報室")
    st.caption("v2.3 即時互動版")
    
    page = st.radio(
        "功能選單：", 
        ["➕ 活動輸入 (新增)", "📊 活動進程 (情報室)"], 
        index=0 
    )

# ==========================================
# 頁面 A: 活動輸入 (修正：移除 form 以支援動態選單)
# ==========================================
if page == "➕ 活動輸入 (新增)":
    st.header("📝 新增行銷活動")
    st.caption("請填寫下方資訊，完成後點擊最下方的確認按鈕。")
    
    # 改用 container，讓選擇 radio 時可以馬上刷新畫面
    with st.container(border=True):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("1. 基本資訊")
            # 類型
            new_type_raw = st.radio("活動類型", ["行銷案 (單次活動)", "常態 (週期活動)"], horizontal=True)
            new_name = st.text_input("活動/任務名稱", placeholder="例如：百倍奉還抽獎")
            new_owner = st.text_input("負責人")
            new_link = st.text_input("相關連結 (網址)", placeholder="https://...")

        with col2:
            st.subheader("2. 平台與形式")
            # 平台複選
            st.write("**刊登平台 (可複選)**")
            c1, c2, c3, c4 = st.columns(4)
            p_fb = c1.checkbox("FB")
            p_ig = c2.checkbox("IG")
            p_threads = c3.checkbox("@Threads")
            p_yt = c4.checkbox("YouTube")
            
            c5, c6, c7, c8 = st.columns(4)
            p_tiktok = c5.checkbox("TikTok")
            p_web = c6.checkbox("官網")
            p_line = c7.checkbox("LINE")
            p_other_text = st.text_input("其他平台 (自行填寫)")
            
            # 形式複選
            st.write("**呈現形式 (可複選)**")
            formats_selected = st.multiselect("請選擇素材形式", ["貼文", "限動", "影片", "短影音(Reels/Shorts)"])

        st.divider()
        
        # --- 3. 時間與週期 (互動核心區) ---
        st.subheader("3. 時間與週期")
        
        # 這裡移除 form 後，改變選項會立即觸發 Rerun，讓下方選單出現
        cycle_mode = st.radio("週期模式", ["單次", "每日", "重覆 (特定星期)"], horizontal=True)
        
        # 變數初始化
        final_weekdays = "" 
        
        if cycle_mode == "單次":
            d1, d2 = st.columns(2)
            new_start = d1.date_input("開始日期", datetime.today())
            new_end = d2.date_input("結束日期", datetime.today())
            st.caption("適用於有明確起訖日期的行銷檔期。")
            
        elif cycle_mode == "每日":
            d1, d2 = st.columns(2)
            new_start = d1.date_input("開始日期", datetime.today())
            new_end = d2.date_input("常態結束日期 (預設年底)", datetime(2026, 12, 31))
            final_weekdays = "每日"
            st.caption("適用於每天都要執行的例行公事。")
            
        elif cycle_mode == "重覆 (特定星期)":
            d1, d2 = st.columns(2)
            new_start = d1.date_input("開始日期", datetime.today())
            new_end = d2.date_input("常態結束日期", datetime(2026, 12, 31))
            
            # === 修正後，這一段現在會正常彈出來了 ===
            st.markdown("👇 **請在此指定重複的星期 (可多選)**")
            weekdays_list = st.multiselect(
                "選擇星期", 
                ["每週一", "每週二", "每週三", "每週四", "每週五", "每週六", "每週日"],
                placeholder="請選擇..."
            )
            final_weekdays = ", ".join(weekdays_list)
            if not weekdays_list:
                st.warning("⚠️ 選擇「重覆」模式時，請務必勾選至少一個星期！")

        new_note = st.text_area("文案重點/備註")
        
        st.divider()

        # --- 提交按鈕 (改用一般 button) ---
        submitted = st.button("🚀 確認新增", type="primary")

        if submitted:
            # 1. 整理平台
            platforms = []
            if p_fb: platforms.append("FB")
            if p_ig: platforms.append("IG")
            if p_threads: platforms.append("@Threads")
            if p_yt: platforms.append("YT")
            if p_tiktok: platforms.append("TikTok")
            if p_web: platforms.append("官網")
            if p_line: platforms.append("LINE")
            if p_other_text: platforms.append(p_other_text)
            
            # 2. 整理字串
            format_str = ", ".join(formats_selected)
            platform_str = ", ".join(platforms)
            type_str = "行銷案" if "行銷案" in new_type_raw else "常態"

            # 3. 檢查必填
            if not new_name:
                st.error("❌ 錯誤：請填寫活動名稱")
            elif cycle_mode == "重覆 (特定星期)" and not weekdays_list:
                st.error("❌ 錯誤：您選擇了重覆模式，但沒有指定星期幾！")
            else:
                # 4. 建立資料
                new_data = pd.DataFrame([{
                    "類型": type_str,
                    "活動名稱": new_name,
                    "刊登平台": platform_str,
                    "呈現形式": format_str,
                    "開始日期": new_start.strftime("%Y-%m-%d"),
                    "結束日期": new_end.strftime("%Y-%m-%d"),
                    "週期模式": cycle_mode,
                    "重複星期": final_weekdays,
                    "文案重點": new_note,
                    "負責人": new_owner,
                    "相關連結": new_link
                }])
                
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    updated_df = pd.concat([df_raw, new_data], ignore_index=True)
                    conn.update(worksheet="Marketing_Schedule", data=updated_df)
                    st.toast(f"✅ 已成功新增：{new_name}")
                    st.cache_data.clear()
                    # 提示用戶手動刷新以清空欄位 (因為移除了 form)
                    st.info("新增完成！若需新增下一筆，請重新整理頁面或直接修改上方內容再次送出。")
                except Exception as e:
                    st.error(f"寫入失敗：{e}")

# ==========================================
# 頁面 B: 活動進程 (維持原樣)
# ==========================================
elif page == "📊 活動進程 (情報室)":
    today = pd.Timestamp.now().normalize()
    weekday_map = {0: "每週一", 1: "每週二", 2: "每週三", 3: "每週四", 4: "每週五", 5: "每週六", 6: "每週日"}
    current_weekday_str = weekday_map[today.dayofweek]

    st.title("📊 馬尼行銷情報室")
    st.markdown(f"📅 今天是：**{today.strftime('%Y-%m-%d')} ({current_weekday_str})**")

    tab1, tab2, tab3 = st.tabs(["🔥 今日任務看板", "🗓️ 年度活動時程", "📂 完整資料庫"])

    # === Tab 1: 今日看板 ===
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("✅ 今日常態發文")
            mask_active = (df['類型'] == '常態') & (df['開始日期'] <= today) & (df['結束日期'] >= today)
            routine_df = df[mask_active].copy()
            
            if not routine_df.empty:
                routine_df['is_today'] = routine_df.apply(
                    lambda x: x['週期模式'] == '每日' or (current_weekday_str in str(x['重複星期'])), 
                    axis=1
                )
                daily_tasks = routine_df[routine_df['is_today']]
            else:
                daily_tasks = pd.DataFrame()

            if not daily_tasks.empty:
                for _, row in daily_tasks.iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{row['活動名稱']}**")
                        st.caption(f"📢 {row['刊登平台']} | 🎬 {row['呈現形式']}")
                        st.info(f"💡 {row['文案重點']}")
                        if pd.notna(row.get('相關連結')) and str(row.get('相關連結')).strip() != "":
                            st.link_button("🔗 前往素材", row['相關連結'])
                        st.caption(f"👤 {row['負責人']}")
            else:
                st.success("今日無常態任務。")

        with col2:
            st.subheader("🚀 執行中的行銷活動")
            active_campaigns = df[
                (df['類型'] == '行銷案') & (df['開始日期'] <= today) & (df['結束日期'] >= today)
            ]
            if not active_campaigns.empty:
                for _, row in active_campaigns.iterrows():
                    days_left = (row['結束日期'] - today).days
                    with st.container(border=True):
                        st.markdown(f"### {row['活動名稱']}")
                        st.progress((today - row['開始日期']) / (row['結束日期'] - row['開始日期']))
                        st.write(f"⏳ 剩餘 **{days_left} 天**")
                        st.write(f"📢 {row['刊登平台']} ({row['呈現形式']})")
                        st.warning(f"📌 {row['文案重點']}")
                        if pd.notna(row.get('相關連結')) and str(row.get('相關連結')).strip() != "":
                            st.link_button("🔗 查看企劃", row['相關連結'])
            else:
                st.info("目前無大型活動。")

    # === Tab 2: 甘特圖 ===
    with tab2:
        st.subheader("⏳ 行銷活動甘特圖")
        campaign_df = df[df['類型'] == '行銷案']
        if not campaign_df.empty:
            fig = px.timeline(
                campaign_df, x_start="開始日期", x_end="結束日期", y="活動名稱", 
                color="刊登平台", 
                hover_data=["呈現形式", "負責人"], 
                title="活動檔期"
            )
            fig.add_vline(x=today.timestamp() * 1000, line_width=2, line_dash="dash", line_color="red")
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("尚無活動資料。")

    # === Tab 3: 資料庫 ===
    with tab3:
        st.subheader("📝 所有行銷紀錄")
        st.dataframe(
            df, use_container_width=True,
            column_config={
                "相關連結": st.column_config.LinkColumn("連結", display_text="開啟"),
                "開始日期": st.column_config.DateColumn("開始", format="YYYY-MM-DD"),
                "結束日期": st.column_config.DateColumn("結束", format="YYYY-MM-DD"),
            }
        )
