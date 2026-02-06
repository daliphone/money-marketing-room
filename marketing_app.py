import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- 1. 頁面設定 (更名) ---
st.set_page_config(
    page_title="馬尼行銷活動進程 v2.4",
    page_icon="📢",
    layout="wide"
)

# --- 設定管理員密碼 (您可以在此修改) ---
ADMIN_PASSWORD = "888"  # <--- 請自行修改這組密碼

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
    
    # 資料清洗與型別轉換
    df['開始日期'] = pd.to_datetime(df['開始日期'], errors='coerce')
    df['結束日期'] = pd.to_datetime(df['結束日期'], errors='coerce')
    df['重複星期'] = df['重複星期'].astype(str)
    df['週期模式'] = df['週期模式'].astype(str)
    
    # 處理新欄位：活動狀態
    # 如果 Excel 裡還沒填，預設填入 "執行中" (避免舊資料消失)
    if '活動狀態' not in df.columns:
        df['活動狀態'] = "執行中"
    else:
        df['活動狀態'] = df['活動狀態'].fillna("企畫中") # 新增的空資料預設為企畫中
        
except Exception as e:
    st.error(f"資料讀取失敗，請確認 Google Sheets 是否已新增『活動狀態』欄位。錯誤訊息: {e}")
    st.stop()

# --- 3. 側邊欄導航 ---
with st.sidebar:
    st.title("📢 馬尼行銷活動進程")
    st.caption("v2.4 狀態管理版")
    
    # 選單順序
    page = st.radio(
        "功能選單：", 
        ["➕ 活動輸入 (新增)", "📊 活動進程 (情報室)"], 
        index=0 
    )
    
    st.divider()
    
    # === 4. 管理員專區 (密碼鎖) ===
    st.subheader("🔐 管理員後台")
    password_input = st.text_input("輸入密碼開啟試算表", type="password", placeholder="請輸入密碼...")
    
    if password_input == ADMIN_PASSWORD:
        st.success("身分驗證成功！")
        # 請將下方的 URL 換成您 Google Sheets 的真實網址
        sheet_url = "https://docs.google.com/spreadsheets/d/1DWKxP5UU0em42PweKet2971BamOnNCLpvDj6rAHh3Mo/edit" 
        st.link_button("📝 前往 Google Sheets 審核/編輯", sheet_url)
    elif password_input != "":
        st.error("密碼錯誤")

# ==========================================
# 頁面 A: 活動輸入
# ==========================================
if page == "➕ 活動輸入 (新增)":
    st.header("📝 新增行銷活動")
    st.caption("輸入新點子 (企畫中) 或 正式活動 (執行中)")
    
    with st.container(border=True):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("1. 基本資訊")
            # --- 新增：狀態選擇 ---
            new_status = st.radio("目前狀態", ["企畫中 (草案)", "執行中 (正式)"], index=0, horizontal=True)
            
            new_type_raw = st.radio("活動類型", ["行銷案 (單次活動)", "常態 (週期活動)"], horizontal=True)
            new_name = st.text_input("活動/任務名稱", placeholder="例如：百倍奉還抽獎")
            new_owner = st.text_input("負責人")
            new_link = st.text_input("相關連結 (網址)", placeholder="https://...")

        with col2:
            st.subheader("2. 平台與形式")
            st.write("**刊登平台 (可複選)**")
            c1, c2, c3, c4 = st.columns(4)
            p_fb = c1.checkbox("FB")
            p_ig = c2.checkbox("IG")
            p_threads = c3.checkbox("@Threads")
            p_yt = c4.checkbox("YouTube")
            
            c5, c6, c7, c8 = st.columns(4)
            p_tiktok = c5.checkbox("TikTok")
            p_web = c6.checkbox("官網")
            # --- 更新：加入 LINE VOOM ---
            p_line = c7.checkbox("LINE OA")
            p_line_voom = c8.checkbox("LINE VOOM")
            
            p_other_text = st.text_input("其他平台 (自行填寫)")
            
            st.write("**呈現形式 (可複選)**")
            formats_selected = st.multiselect("請選擇素材形式", ["貼文", "限動", "影片", "短影音(Reels/Shorts)"])

        st.divider()
        
        # --- 3. 時間與週期 ---
        st.subheader("3. 時間與週期")
        cycle_mode = st.radio("週期模式", ["單次", "每日", "重覆 (特定星期)"], horizontal=True)
        final_weekdays = "" 
        
        if cycle_mode == "單次":
            d1, d2 = st.columns(2)
            new_start = d1.date_input("開始日期", datetime.today())
            new_end = d2.date_input("結束日期", datetime.today())
            
        elif cycle_mode == "每日":
            d1, d2 = st.columns(2)
            new_start = d1.date_input("開始日期", datetime.today())
            new_end = d2.date_input("常態結束日期", datetime(2026, 12, 31))
            final_weekdays = "每日"
            
        elif cycle_mode == "重覆 (特定星期)":
            d1, d2 = st.columns(2)
            new_start = d1.date_input("開始日期", datetime.today())
            new_end = d2.date_input("常態結束日期", datetime(2026, 12, 31))
            st.markdown("👇 **請在此指定重複的星期 (可多選)**")
            weekdays_list = st.multiselect("選擇星期", ["每週一", "每週二", "每週三", "每週四", "每週五", "每週六", "每週日"])
            final_weekdays = ", ".join(weekdays_list)

        new_note = st.text_area("文案重點/備註")
        
        st.divider()
        submitted = st.button("🚀 確認新增", type="primary")

        if submitted:
            # 資料整理
            platforms = []
            if p_fb: platforms.append("FB")
            if p_ig: platforms.append("IG")
            if p_threads: platforms.append("@Threads")
            if p_yt: platforms.append("YT")
            if p_tiktok: platforms.append("TikTok")
            if p_web: platforms.append("官網")
            if p_line: platforms.append("LINE OA")
            if p_line_voom: platforms.append("LINE VOOM") # 新增
            if p_other_text: platforms.append(p_other_text)
            
            format_str = ", ".join(formats_selected)
            platform_str = ", ".join(platforms)
            type_str = "行銷案" if "行銷案" in new_type_raw else "常態"
            
            # 處理狀態字串 (只取前三個字，如 "企畫中")
            status_clean = new_status.split(" ")[0]

            if not new_name:
                st.error("❌ 請填寫活動名稱")
            elif cycle_mode == "重覆 (特定星期)" and not weekdays_list:
                st.error("❌ 請指定重複的星期")
            else:
                # 建立新資料 (包含活動狀態)
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
                    "相關連結": new_link,
                    "活動狀態": status_clean # 新欄位
                }])
                
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    updated_df = pd.concat([df_raw, new_data], ignore_index=True)
                    conn.update(worksheet="Marketing_Schedule", data=updated_df)
                    st.toast(f"✅ 已新增：{new_name} ({status_clean})")
                    st.cache_data.clear()
                    st.info("新增完成！若需審核或轉為執行中，請至側邊欄「管理員後台」。")
                except Exception as e:
                    st.error(f"寫入失敗：{e}")

# ==========================================
# 頁面 B: 活動進程 (情報室)
# ==========================================
elif page == "📊 活動進程 (情報室)":
    today = pd.Timestamp.now().normalize()
    weekday_map = {0: "每週一", 1: "每週二", 2: "每週三", 3: "每週四", 4: "每週五", 5: "每週六", 6: "每週日"}
    current_weekday_str = weekday_map[today.dayofweek]

    st.title("📊 馬尼行銷活動進程")
    st.markdown(f"📅 今天是：**{today.strftime('%Y-%m-%d')} ({current_weekday_str})**")

    # 分頁增加「企畫庫」
    tab1, tab2, tab3, tab4 = st.tabs(["🔥 今日任務 (執行中)", "🗓️ 活動甘特圖", "💡 企畫庫 (草案)", "📂 完整資料庫"])

    # === Tab 1: 今日任務 (只顯示執行中) ===
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        # 篩選基礎：只顯示「執行中」
        df_executing = df[df['活動狀態'] == '執行中']
        
        with col1:
            st.subheader("✅ 今日常態發文")
            mask_active = (df_executing['類型'] == '常態') & (df_executing['開始日期'] <= today) & (df_executing['結束日期'] >= today)
            routine_df = df_executing[mask_active].copy()
            
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
            st.subheader("🚀 進行中的行銷案")
            active_campaigns = df_executing[
                (df_executing['類型'] == '行銷案') & (df_executing['開始日期'] <= today) & (df_executing['結束日期'] >= today)
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

    # === Tab 2: 甘特圖 (顯示所有狀態，用顏色區分) ===
    with tab2:
        st.subheader("⏳ 年度活動時程總覽")
        st.caption("包含 執行中、企畫中、已結案 之所有活動")
        
        campaign_df = df[df['類型'] == '行銷案']
        if not campaign_df.empty:
            fig = px.timeline(
                campaign_df, x_start="開始日期", x_end="結束日期", y="活動名稱", 
                color="活動狀態", # 改用狀態來區分顏色
                hover_data=["刊登平台", "負責人"], 
                title="活動檔期 (顏色區分狀態)"
            )
            fig.add_vline(x=today.timestamp() * 1000, line_width=2, line_dash="dash", line_color="red")
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("尚無資料。")

    # === Tab 3: 企畫庫 (只顯示企畫中) ===
    with tab3:
        st.subheader("💡 企畫中草案 (Planning Pool)")
        st.caption("這些活動尚未正式執行，請管理員確認後至 Excel 轉為執行中。")
        
        planning_df = df[df['活動狀態'] == '企畫中']
        if not planning_df.empty:
            st.dataframe(
                planning_df[['類型', '活動名稱', '開始日期', '結束日期', '文案重點', '負責人']],
                use_container_width=True
            )
        else:
            st.info("目前沒有企畫中的草案。")

    # === Tab 4: 完整資料庫 ===
    with tab4:
        st.subheader("📝 所有行銷紀錄")
        st.dataframe(
            df, use_container_width=True,
            column_config={
                "相關連結": st.column_config.LinkColumn("連結", display_text="開啟"),
                "開始日期": st.column_config.DateColumn("開始", format="YYYY-MM-DD"),
                "結束日期": st.column_config.DateColumn("結束", format="YYYY-MM-DD"),
            }
        )
