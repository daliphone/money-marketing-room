import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, date

# --- 1. 頁面設定 ---
st.set_page_config(
    page_title="馬尼行銷活動進程 v3.4",
    page_icon="📢",
    layout="wide"
)

# --- 設定管理員密碼 ---
ADMIN_PASSWORD = "888"
SHEET_ID = "1DWKxP5UU0em42PweKet2971BamOnNCLpvDj6rAHh3Mo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

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
    
    # === 資料清洗 ===
    df['開始日期'] = pd.to_datetime(df['開始日期'], errors='coerce')
    df['結束日期'] = pd.to_datetime(df['結束日期'], errors='coerce')
    
    # v3.4 修正：移除 case=False，改用列表取代，解決報錯問題
    for col in ['重複星期', '週期模式', '活動狀態', '類型', '活動名稱', '相關連結', '負責人', '文案重點']:
        if col in df.columns:
            # 1. 轉字串
            df[col] = df[col].astype(str)
            # 2. 去除前後空白
            df[col] = df[col].str.strip()
            # 3. 將 'nan' 或 'NaN' 字串替換為真正的空字串
            df[col] = df[col].replace(['nan', 'NaN'], '')

    if '活動狀態' not in df.columns:
        df['活動狀態'] = "執行中"
    else:
        # 如果狀態是空的，補上 "企畫中"
        df['活動狀態'] = df['活動狀態'].replace('', '企畫中')
        
except Exception as e:
    st.error(f"資料讀取失敗，請確認 Google Sheets 連線與權限。錯誤訊息: {e}")
    st.stop()

# --- 3. 側邊欄導航 ---
with st.sidebar:
    st.title("📢 馬尼行銷活動進程")
    st.caption("v3.4 穩定修復版")
    
    if st.button("🔄 強制刷新資料"):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()

    page = st.radio(
        "功能選單：", 
        ["➕ 活動輸入 (新增)", "📊 活動進程 (情報室)"], 
        index=0 
    )
    
    st.divider()
    
    # === 管理員後台 ===
    st.subheader("🔐 管理員後台")
    password_input = st.text_input("輸入密碼開啟試算表", type="password", placeholder="請輸入密碼...")
    
    if password_input == ADMIN_PASSWORD:
        st.success("身分驗證成功！")
        st.link_button("📝 前往 Google Sheets", SHEET_URL)

# ==========================================
# 頁面 A: 活動輸入
# ==========================================
if page == "➕ 活動輸入 (新增)":
    st.header("📝 新增行銷活動")
    
    with st.container(border=True):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("1. 基本資訊")
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
            p_web_article = c7.checkbox("官網文章")
            p_line = c8.checkbox("LINE OA")
            
            c9, c10 = st.columns(2)
            p_line_voom = c9.checkbox("LINE VOOM")
            p_other_text = c10.text_input("其他平台 (自行填寫)")
            
            st.write("**呈現形式 (可複選)**")
            formats_selected = st.multiselect("請選擇素材形式", ["貼文", "限動", "影片", "短影音(Reels/Shorts)"])

        st.divider()
        
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
            platforms = []
            if p_fb: platforms.append("FB")
            if p_ig: platforms.append("IG")
            if p_threads: platforms.append("@Threads")
            if p_yt: platforms.append("YT")
            if p_tiktok: platforms.append("TikTok")
            if p_web: platforms.append("官網")
            if p_web_article: platforms.append("官網文章")
            if p_line: platforms.append("LINE OA")
            if p_line_voom: platforms.append("LINE VOOM")
            if p_other_text: platforms.append(p_other_text)
            
            format_str = ", ".join(formats_selected)
            platform_str = ", ".join(platforms)
            type_str = "行銷案" if "行銷案" in new_type_raw else "常態"
            status_clean = new_status.split(" ")[0]

            if not new_name:
                st.error("❌ 請填寫活動名稱")
            elif cycle_mode == "重覆 (特定星期)" and not weekdays_list:
                st.error("❌ 請指定重複的星期")
            else:
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
                    "活動狀態": status_clean
                }])
                
                try:
                    st.info("🔄 正在同步雲端最新資料...")
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    current_df = conn.read(worksheet="Marketing_Schedule", ttl=0)
                    current_df = current_df.dropna(how="all")
                    updated_df = pd.concat([current_df, new_data], ignore_index=True)
                    conn.update(worksheet="Marketing_Schedule", data=updated_df)
                    st.toast(f"✅ 新增成功！狀態：{status_clean}")
                    st.cache_data.clear()
                    st.success("資料已同步寫入 Google Sheets。")
                    
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

    # 分頁
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔥 今日任務", 
        "📅 活動行程表",
        "⏳ 年度甘特圖", 
        "💡 企畫庫", 
        "📂 完整資料庫"
    ])

    # === Tab 1: 今日任務 ===
    with tab1:
        col1, col2 = st.columns([1, 1])
        df_executing = df[df['活動狀態'].str.contains("執行中")]
        
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
                        
                        # 按鈕顯示邏輯 (有連結才顯示)
                        link = row.get('相關連結')
                        if link and str(link).strip() != "" and str(link).startswith("http"):
                            st.link_button("🔗 前往素材", link)
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
                        st.write(f"📢 {row['刊登平台']}")
                        
                        # 按鈕顯示邏輯 (有連結才顯示)
                        link = row.get('相關連結')
                        if link and str(link).strip() != "" and str(link).startswith("http"):
                             st.link_button("🔗 查看企劃", link)
            else:
                st.info("目前無大型活動。")

    # === Tab 2: 活動行程總覽 ===
    with tab2:
        st.subheader("🗓️ 活動行程總覽")
        
        col_sel1, col_sel2 = st.columns([1, 2])
        with col_sel1:
            today_date = date.today()
            start_default = today_date.replace(day=1)
            next_month = today_date.replace(day=28) + timedelta(days=4)
            end_default = next_month.replace(day=1) - timedelta(days=1)
            
            date_range = st.date_input(
                "📅 請選擇顯示區間", 
                value=(start_default, end_default),
                key="range_picker"
            )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            start_ts = pd.Timestamp(start_date)
            end_ts = pd.Timestamp(end_date)
            
            mask_range = (df['開始日期'] <= end_ts) & (df['結束日期'] >= start_ts)
            filtered_df = df[mask_range].copy()
            
            if not filtered_df.empty:
                fig = px.timeline(
                    filtered_df, 
                    x_start="開始日期", 
                    x_end="結束日期", 
                    y="活動名稱", 
                    color="活動狀態",
                    text="活動名稱",
                    hover_data={"活動名稱": False, "刊登平台": True, "文案重點": True, "相關連結": True}, 
                    custom_data=["相關連結", "活動名稱"]
                )
                
                fig.update_traces(textposition='inside', insidetextanchor='start')
                
                fig.update_xaxes(
                    range=[start_ts, end_ts],
                    tickformat="%m/%d",
                    dtick="D1",
                    side="top"
                )
                fig.update_yaxes(autorange="reversed")
                
                chart_height = max(400, len(filtered_df) * 50)
                fig.update_layout(height=chart_height, showlegend=True)
                
                event = st.plotly_chart(
                    fig, 
                    use_container_width=True, 
                    on_select="rerun",     
                    selection_mode="points"
                )
                
                if event and event["selection"]["points"]:
                    point = event["selection"]["points"][0]
                    clicked_url = point["customdata"][0]
                    clicked_name = point["customdata"][1]
                    
                    st.divider()
                    st.info(f"👉 您選擇了：**{clicked_name}**")
                    
                    if clicked_url and str(clicked_url).startswith("http"):
                        st.link_button(f"🔗 前往：{clicked_name} 連結", clicked_url, type="primary")
                    else:
                        st.warning("此活動未設定相關連結。")
                        
            else:
                st.info("所選區間內沒有活動。")
        else:
            st.warning("請選擇完整的起始與結束日期。")

    # === Tab 3: 甘特圖 ===
    with tab3:
        st.subheader("⏳ 年度甘特圖")
        campaign_df = df[df['類型'] == '行銷案']
        if not campaign_df.empty:
            fig = px.timeline(
                campaign_df, x_start="開始日期", x_end="結束日期", y="活動名稱", 
                color="活動狀態", 
                hover_data=["刊登平台", "負責人"], 
                title="年度活動檔期"
            )
            fig.update_xaxes(tickformat="%Y/%m/%d", dtick="M1", ticklabelmode="period")
            fig.add_vline(x=today.timestamp() * 1000, line_width=2, line_dash="dash", line_color="red")
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("尚無資料。")

    # === Tab 4: 企畫庫 ===
    with tab4:
        st.subheader("💡 企畫中草案")
        planning_df = df[df['活動狀態'].str.contains("企畫中")]
        if not planning_df.empty:
            st.dataframe(planning_df, use_container_width=True)
        else:
            st.info("目前沒有企畫中的草案。")

    # === Tab 5: 完整資料庫 ===
    with tab5:
        st.subheader("📝 所有紀錄")
        st.dataframe(
            df, use_container_width=True,
            column_config={
                "相關連結": st.column_config.LinkColumn("連結", display_text="開啟"),
                "開始日期": st.column_config.DateColumn("開始", format="YYYY-MM-DD"),
                "結束日期": st.column_config.DateColumn("結束", format="YYYY-MM-DD"),
            }
        )
