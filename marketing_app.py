import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, date

# --- 1. 頁面設定 ---
st.set_page_config(
    page_title="馬尼行銷活動進程 v4.1",
    page_icon="📢",
    layout="wide"
)

# --- 常數 ---
ADMIN_PASSWORD = "888"
SHEET_ID = "1DWKxP5UU0em42PweKet2971BamOnNCLpvDj6rAHh3Mo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"
WEEKDAY_MAP = {0:"每週一",1:"每週二",2:"每週三",3:"每週四",4:"每週五",5:"每週六",6:"每週日"}
SOP_STEPS   = ["企畫撰寫","素材製作","文案審核","排程上線","成效回報"]
STATUS_DONE = ["已核准"]
STATUS_WIP  = ["進行中","待審核","需修改"]

# --- CSS ---
st.markdown("""
<style>
.kpi-card{background:var(--background-color,#f8f9fa);border-radius:12px;padding:16px 20px;text-align:center;border:1px solid rgba(0,0,0,0.08);}
.kpi-label{font-size:12px;color:#888;margin-bottom:4px;letter-spacing:.5px;}
.kpi-number{font-size:36px;font-weight:700;line-height:1.1;}
.kpi-sub{font-size:12px;color:#aaa;margin-top:2px;}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:500;margin:2px;}
.badge-green{background:#d4f5e2;color:#1a7a44;}
.badge-amber{background:#fff3cd;color:#856404;}
.badge-red{background:#fde8e8;color:#b91c1c;}
.badge-gray{background:#e9ecef;color:#555;}
.badge-blue{background:#dbeafe;color:#1e40af;}
.campaign-card{border-radius:10px;padding:14px 16px;margin-bottom:10px;border:1px solid rgba(0,0,0,0.08);}
.card-urgent{border-left:4px solid #e74c3c;}
.card-normal{border-left:4px solid #2ecc71;}
.card-plan{border-left:4px solid #f39c12;}
.progress-wrap{background:#e9ecef;border-radius:6px;height:8px;margin:6px 0 4px 0;overflow:hidden;}
.progress-bar{height:8px;border-radius:6px;}
.sop-row{display:flex;gap:5px;flex-wrap:wrap;margin:8px 0 4px 0;}
.sop-step{flex:1;min-width:76px;text-align:center;padding:6px 4px;border-radius:8px;font-size:11px;font-weight:500;border:1px solid rgba(0,0,0,0.07);}
.sop-done{background:#d4f5e2;color:#1a7a44;}
.sop-wip{background:#dbeafe;color:#1e40af;}
.sop-block{background:#fde8e8;color:#b91c1c;}
.sop-todo{background:#f1f3f5;color:#aaa;}
.sop-owner{font-size:10px;opacity:.75;display:block;margin-top:2px;}
</style>
""", unsafe_allow_html=True)

# --- 2. 讀取資料 ---
@st.cache_data(ttl=600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)

    df = conn.read(worksheet="Marketing_Schedule")
    df = df.dropna(how="all")
    df['開始日期'] = pd.to_datetime(df['開始日期'], errors='coerce')
    df['結束日期'] = pd.to_datetime(df['結束日期'], errors='coerce')
    for col in ['重複星期','週期模式','活動狀態','類型','活動名稱','相關連結','負責人','文案重點','刊登平台','呈現形式']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().replace(['nan','NaN'], '')
    if '活動狀態' not in df.columns:
        df['活動狀態'] = "執行中"
    else:
        df['活動狀態'] = df['活動狀態'].replace('', '企畫中')

    try:
        tasks = conn.read(worksheet="Campaign_Tasks")
        tasks = tasks.dropna(how="all")
        for col in ['任務ID','活動名稱','SOP步驟','任務說明','負責人','審核狀態','備註']:
            if col in tasks.columns:
                tasks[col] = tasks[col].astype(str).str.strip().replace(['nan','NaN'], '')
        tasks['預計完成日'] = pd.to_datetime(tasks.get('預計完成日'), errors='coerce')
        tasks['實際完成日'] = pd.to_datetime(tasks.get('實際完成日'), errors='coerce')
    except Exception:
        tasks = pd.DataFrame(columns=['任務ID','活動名稱','SOP步驟','任務說明','負責人','審核狀態','預計完成日','實際完成日','備註'])

    return df, tasks

try:
    df, tasks_df = load_data()
except Exception as e:
    st.error(f"資料讀取失敗：{e}")
    st.stop()

# --- 3. SOP 輔助函式 ---
def get_sop_status(campaign_name, tasks_df):
    sub = tasks_df[tasks_df['活動名稱'] == campaign_name]
    result = {}
    for step in SOP_STEPS:
        row = sub[sub['SOP步驟'] == step]
        if not row.empty:
            result[step] = {"status": row.iloc[0]['審核狀態'], "owner": row.iloc[0]['負責人']}
        else:
            result[step] = {"status": "—", "owner": ""}
    return result

def sop_progress_pct(sop_dict):
    done = sum(1 for v in sop_dict.values() if v["status"] in STATUS_DONE)
    return int(done / len(SOP_STEPS) * 100)

def sop_bar_color(pct):
    return "#2ecc71" if pct >= 80 else "#3498db" if pct >= 40 else "#f39c12"

def sop_html(sop_dict):
    html = ""
    for step in SOP_STEPS:
        info = sop_dict.get(step, {"status":"—","owner":""})
        s, o = info["status"], info["owner"]
        if s in STATUS_DONE:        cls, icon = "sop-done",  "✓"
        elif s == "需修改":          cls, icon = "sop-block", "✗"
        elif s in STATUS_WIP:       cls, icon = "sop-wip",   "⋯"
        else:                       cls, icon = "sop-todo",  "○"
        html += f'<div class="sop-step {cls}">{icon} {step}<span class="sop-owner">{o or "—"}</span></div>'
    return f'<div class="sop-row">{html}</div>'

# --- 4. KPI 計算 ---
def compute_kpi(df, today):
    exec_df = df[df['活動狀態'].str.contains("執行中", na=False)]
    plan_df = df[df['活動狀態'].str.contains("企畫中", na=False)]
    active  = exec_df[(exec_df['開始日期']<=today) & (exec_df['結束日期']>=today)]
    in_7    = exec_df[(exec_df['結束日期']>=today) & (exec_df['結束日期']<=today+pd.Timedelta(days=7))]
    in_3    = exec_df[(exec_df['結束日期']>=today) & (exec_df['結束日期']<=today+pd.Timedelta(days=3))]
    wd      = WEEKDAY_MAP[today.dayofweek]
    mask_r  = (exec_df['類型']=='常態') & (exec_df['開始日期']<=today) & (exec_df['結束日期']>=today)
    routine = exec_df[mask_r]
    if not routine.empty:
        routine = routine[routine.apply(lambda x: x['週期模式']=='每日' or (wd in str(x['重複星期'])), axis=1)]
    return dict(active_count=len(active), expire_7=len(in_7), expire_3=len(in_3),
                today_routine=len(routine), plan_count=len(plan_df),
                in_7_df=in_7, in_3_df=in_3, active_df=active, routine_df=routine, weekday_str=wd)

# --- 5. 側邊欄 ---
with st.sidebar:
    st.title("📢 馬尼行銷活動進程")
    st.caption("v4.1 SOP 追蹤版")
    st.subheader("⚙️ 顯示設定")
    mobile_mode = st.checkbox("📱 手機版面優化", value=False)
    st.divider()
    if st.button("🔄 強制刷新資料"):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    page = st.radio("功能選單：", ["🏠 指揮中心","📋 SOP 任務追蹤","➕ 活動輸入 (新增)","📊 活動進程 (情報室)"], index=0)
    st.divider()
    st.subheader("🔐 管理員後台")
    pwd = st.text_input("輸入密碼開啟試算表", type="password", placeholder="請輸入密碼...")
    if pwd == ADMIN_PASSWORD:
        st.success("身分驗證成功！")
        st.link_button("📝 前往 Google Sheets", SHEET_URL)

# ==========================================
# 頁面：指揮中心
# ==========================================
if page == "🏠 指揮中心":
    today = pd.Timestamp.now().normalize()
    kpi   = compute_kpi(df, today)
    st.title("🏠 指揮中心")
    st.markdown(f"📅 今天是 **{today.strftime('%Y-%m-%d')} ({kpi['weekday_str']})**")

    c1,c2,c3,c4,c5 = st.columns(5)
    for col,label,val,color,sub in [
        (c1,"進行中活動",   kpi['active_count'], "#2ecc71","個執行中"),
        (c2,"7 天內到期",   kpi['expire_7'],     "#f39c12","個活動"),
        (c3,"⚠️ 3天內緊急", kpi['expire_3'],     "#e74c3c" if kpi['expire_3']>0 else "#aaa","個即將到期"),
        (c4,"今日常態任務", kpi['today_routine'],"#3498db","項待執行"),
        (c5,"企畫中草案",   kpi['plan_count'],   "#9b59b6","個待審核"),
    ]:
        col.markdown(f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
                     f'<div class="kpi-number" style="color:{color}">{val}</div>'
                     f'<div class="kpi-sub">{sub}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns(2, gap="large")

    with left:
        if not kpi["in_3_df"].empty:
            st.markdown("### 🔴 緊急！3 天內到期")
            for _, row in kpi["in_3_df"].iterrows():
                d = (row['結束日期']-today).days
                st.markdown(f'<div class="campaign-card card-urgent"><b>{row["活動名稱"]}</b>'
                            f'<span class="badge badge-red">剩 {d} 天</span><br>'
                            f'<small>📢 {row["刊登平台"]} ｜ 負責人：{row.get("負責人","—")}</small></div>',
                            unsafe_allow_html=True)
        else:
            st.success("✅ 近 3 天無到期活動")

        st.markdown("### 🟡 7 天內即將到期")
        if not kpi["in_7_df"].empty:
            for _, row in kpi["in_7_df"].iterrows():
                d   = (row['結束日期']-today).days
                bc  = "badge-red" if d<=3 else "badge-amber"
                st.markdown(f'<div class="campaign-card card-plan"><b>{row["活動名稱"]}</b>'
                            f'<span class="badge {bc}">剩 {d} 天</span><br>'
                            f'<small>結束：{row["結束日期"].strftime("%Y-%m-%d")} ｜ 負責人：{row.get("負責人","—")}</small></div>',
                            unsafe_allow_html=True)
        else:
            st.info("近 7 天沒有活動到期")

    with right:
        st.markdown("### ✅ 今日常態任務")
        if not kpi["routine_df"].empty:
            for _, row in kpi["routine_df"].iterrows():
                sop   = get_sop_status(row['活動名稱'], tasks_df)
                pct   = sop_progress_pct(sop)
                bc    = sop_bar_color(pct)
                lnk   = row.get('相關連結','')
                lhtml = f'<a href="{lnk}" target="_blank" style="font-size:12px;">🔗 前往素材</a>' if str(lnk).startswith("http") else ""
                st.markdown(
                    f'<div class="campaign-card card-normal"><b>{row["活動名稱"]}</b>'
                    f'<span class="badge badge-blue">{row["週期模式"]}</span><br>'
                    f'<small>📢 {row["刊登平台"]}</small>'
                    f'<div class="progress-wrap"><div class="progress-bar" style="width:{pct}%;background:{bc}"></div></div>'
                    f'<small style="color:#888">SOP 完成度 {pct}%</small>'
                    f'{sop_html(sop)}{lhtml}</div>', unsafe_allow_html=True)
        else:
            st.info("今日無常態任務")

        st.markdown("### 🚀 進行中行銷案")
        active_c = kpi["active_df"][kpi["active_df"]['類型']=='行銷案']
        if not active_c.empty:
            for _, row in active_c.iterrows():
                dur  = max((row['結束日期']-row['開始日期']).days,1)
                tpct = min(int((today-row['開始日期']).days/dur*100),100)
                dl   = (row['結束日期']-today).days
                sop  = get_sop_status(row['活動名稱'], tasks_df)
                spct = sop_progress_pct(sop)
                bc   = "#e74c3c" if dl<=3 else "#f39c12" if dl<=7 else "#2ecc71"
                lnk  = row.get('相關連結','')
                lhtml= f'<a href="{lnk}" target="_blank" style="font-size:12px;">🔗 查看企劃</a>' if str(lnk).startswith("http") else ""
                st.markdown(
                    f'<div class="campaign-card card-normal"><b>{row["活動名稱"]}</b>'
                    f'<span class="badge badge-red" style="float:right">剩 {dl} 天</span><br>'
                    f'<small>時程進度 {tpct}%</small>'
                    f'<div class="progress-wrap"><div class="progress-bar" style="width:{tpct}%;background:{bc}"></div></div>'
                    f'<small>📢 {row["刊登平台"]} ｜ 負責人：{row.get("負責人","—")}</small><br>'
                    f'<small style="color:#888">SOP 完成度 {spct}%</small>'
                    f'{sop_html(sop)}{lhtml}</div>', unsafe_allow_html=True)
        else:
            st.info("目前無進行中的大型行銷案")

    st.divider()
    st.markdown("### 🗂️ 全部活動狀態一覽")
    sc  = df['活動狀態'].value_counts()
    bm  = {"執行中":"badge-green","企畫中":"badge-amber","已結束":"badge-gray"}
    st.markdown("".join(f'<span class="badge {bm.get(s,"badge-blue")}">{s} ({c})</span> ' for s,c in sc.items()), unsafe_allow_html=True)
    st.dataframe(df[['活動名稱','類型','活動狀態','開始日期','結束日期','負責人','刊登平台']],
        use_container_width=True,
        column_config={"開始日期":st.column_config.DateColumn("開始",format="YYYY-MM-DD"),
                       "結束日期":st.column_config.DateColumn("結束",format="YYYY-MM-DD")},
        hide_index=True)

# ==========================================
# 頁面：SOP 任務追蹤
# ==========================================
elif page == "📋 SOP 任務追蹤":
    today = pd.Timestamp.now().normalize()
    st.title("📋 SOP 任務追蹤")
    st.caption("每個活動的子任務進度、負責人與審核狀態")

    if tasks_df.empty:
        st.warning("Campaign_Tasks 分頁尚無資料，請先執行 GAS 腳本建立分頁。")
        st.stop()

    # 篩選
    f1,f2,f3 = st.columns(3)
    sel_campaign = f1.selectbox("活動名稱", ["全部"]+sorted(tasks_df['活動名稱'].unique().tolist()))
    sel_owner    = f2.selectbox("負責人",   ["全部"]+sorted(tasks_df['負責人'].replace('','—').unique().tolist()))
    sel_status   = f3.selectbox("審核狀態", ["全部","待執行","進行中","待審核","已核准","需修改"])

    filtered = tasks_df.copy()
    if sel_campaign != "全部": filtered = filtered[filtered['活動名稱']==sel_campaign]
    if sel_owner    != "全部": filtered = filtered[filtered['負責人']   ==sel_owner]
    if sel_status   != "全部": filtered = filtered[filtered['審核狀態'] ==sel_status]

    st.divider()

    for campaign_name, group in filtered.groupby('活動名稱', sort=False):
        sop  = get_sop_status(campaign_name, tasks_df)
        pct  = sop_progress_pct(sop)
        bc   = sop_bar_color(pct)

        hc1, hc2 = st.columns([3,1])
        hc1.markdown(f"#### 📌 {campaign_name}")
        hc2.markdown(f"**SOP 完成度：{pct}%**")

        st.markdown(
            f'<div class="progress-wrap" style="height:10px;margin-bottom:6px">'
            f'<div class="progress-bar" style="width:{pct}%;background:{bc}"></div></div>'
            f'{sop_html(sop)}', unsafe_allow_html=True)

        # 明細表
        dcols = [c for c in ['SOP步驟','任務說明','負責人','審核狀態','預計完成日','實際完成日','備註'] if c in group.columns]
        sc_map = {"已核准":"background-color:#d4f5e2;color:#1a7a44",
                  "進行中":"background-color:#dbeafe;color:#1e40af",
                  "待審核":"background-color:#fff3cd;color:#856404",
                  "需修改":"background-color:#fde8e8;color:#b91c1c",
                  "待執行":"background-color:#e9ecef;color:#555"}
        st.dataframe(
            group[dcols].style.applymap(lambda v: sc_map.get(v,""), subset=['審核狀態']),
            use_container_width=True,
            column_config={"預計完成日":st.column_config.DateColumn("預計完成",format="MM-DD"),
                           "實際完成日":st.column_config.DateColumn("實際完成",format="MM-DD")},
            hide_index=True)

        # 快速更新
        with st.expander(f"✏️ 快速更新「{campaign_name}」子任務狀態"):
            st.caption("選擇步驟與新狀態後點「更新」，直接寫回 Google Sheets")
            u1,u2,u3 = st.columns(3)
            sel_step   = u1.selectbox("SOP 步驟", group['SOP步驟'].tolist(), key=f"step_{campaign_name}")
            sel_new_st = u2.selectbox("新狀態", ["待執行","進行中","待審核","已核准","需修改"], key=f"st_{campaign_name}")
            if u3.button("✅ 更新", key=f"btn_{campaign_name}"):
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    raw  = conn.read(worksheet="Campaign_Tasks", ttl=0).dropna(how="all")
                    mask = (raw['活動名稱'].astype(str).str.strip()==campaign_name) & \
                           (raw['SOP步驟'].astype(str).str.strip()==sel_step)
                    raw.loc[mask,'審核狀態'] = sel_new_st
                    conn.update(worksheet="Campaign_Tasks", data=raw)
                    st.cache_data.clear()
                    st.toast(f"✅ 已更新「{sel_step}」→ {sel_new_st}")
                    st.rerun()
                except Exception as e:
                    st.error(f"更新失敗：{e}")
        st.divider()

    # 統計摘要
    st.markdown("### 📊 狀態統計")
    sc1,sc2,sc3,sc4,sc5 = st.columns(5)
    for col,status,badge in [
        (sc1,"已核准","badge-green"),(sc2,"進行中","badge-blue"),
        (sc3,"待審核","badge-amber"),(sc4,"需修改","badge-red"),(sc5,"待執行","badge-gray")
    ]:
        cnt = len(tasks_df[tasks_df['審核狀態']==status])
        col.markdown(f'<div class="kpi-card"><div class="kpi-label"><span class="badge {badge}">{status}</span></div>'
                     f'<div class="kpi-number" style="font-size:28px">{cnt}</div>'
                     f'<div class="kpi-sub">個子任務</div></div>', unsafe_allow_html=True)

# ==========================================
# 頁面：活動輸入
# ==========================================
elif page == "➕ 活動輸入 (新增)":
    st.header("📝 新增行銷活動")
    with st.container(border=True):
        col1,col2 = st.columns(2)
        with col1:
            st.subheader("1. 基本資訊")
            new_status   = st.radio("目前狀態",["企畫中 (草案)","執行中 (正式)"],index=0,horizontal=True)
            new_type_raw = st.radio("活動類型",["行銷案 (單次活動)","常態 (週期活動)"],horizontal=True)
            new_name     = st.text_input("活動/任務名稱", placeholder="例如：百倍奉還抽獎")
            new_owner    = st.text_input("負責人")
            new_link     = st.text_input("相關連結 (網址)", placeholder="https://...")
        with col2:
            st.subheader("2. 平台與形式")
            st.write("**刊登平台 (可複選)**")
            c1,c2,c3,c4 = st.columns(4)
            p_fb=c1.checkbox("FB");p_ig=c2.checkbox("IG");p_th=c3.checkbox("@Threads");p_yt=c4.checkbox("YouTube")
            c5,c6,c7,c8 = st.columns(4)
            p_tk=c5.checkbox("TikTok");p_wb=c6.checkbox("官網");p_wa=c7.checkbox("官網文章");p_ln=c8.checkbox("LINE OA")
            c9,c10 = st.columns(2)
            p_lv=c9.checkbox("LINE VOOM"); p_ot=c10.text_input("其他平台")
            st.write("**呈現形式 (可複選)**")
            formats_selected = st.multiselect("請選擇素材形式",["貼文","限動","影片","短影音(Reels/Shorts)"])

        st.divider()
        st.subheader("3. 時間與週期")
        cycle_mode = st.radio("週期模式",["單次","每日","重覆 (特定星期)"],horizontal=True)
        final_weekdays = ""
        if cycle_mode=="單次":
            d1,d2=st.columns(2); new_start=d1.date_input("開始日期",datetime.today()); new_end=d2.date_input("結束日期",datetime.today())
        elif cycle_mode=="每日":
            d1,d2=st.columns(2); new_start=d1.date_input("開始日期",datetime.today()); new_end=d2.date_input("常態結束日期",datetime(2026,12,31)); final_weekdays="每日"
        elif cycle_mode=="重覆 (特定星期)":
            d1,d2=st.columns(2); new_start=d1.date_input("開始日期",datetime.today()); new_end=d2.date_input("常態結束日期",datetime(2026,12,31))
            st.markdown("👇 **請指定重複的星期 (可多選)**")
            weekdays_list=st.multiselect("選擇星期",["每週一","每週二","每週三","每週四","每週五","每週六","每週日"]); final_weekdays=", ".join(weekdays_list)

        new_note=st.text_area("文案重點/備註")
        st.divider()
        if st.button("🚀 確認新增", type="primary"):
            platforms=[p for f,p in [(p_fb,"FB"),(p_ig,"IG"),(p_th,"@Threads"),(p_yt,"YT"),(p_tk,"TikTok"),
                       (p_wb,"官網"),(p_wa,"官網文章"),(p_ln,"LINE OA"),(p_lv,"LINE VOOM")] if f]+([p_ot] if p_ot else [])
            type_str="行銷案" if "行銷案" in new_type_raw else "常態"
            status_clean=new_status.split(" ")[0]
            if not new_name: st.error("❌ 請填寫活動名稱")
            elif cycle_mode=="重覆 (特定星期)" and not weekdays_list: st.error("❌ 請指定重複的星期")
            else:
                new_row=pd.DataFrame([{"類型":type_str,"活動名稱":new_name,"刊登平台":", ".join(platforms),
                    "呈現形式":", ".join(formats_selected),"開始日期":new_start.strftime("%Y-%m-%d"),
                    "結束日期":new_end.strftime("%Y-%m-%d"),"週期模式":cycle_mode,"重複星期":final_weekdays,
                    "文案重點":new_note,"負責人":new_owner,"相關連結":new_link,"活動狀態":status_clean}])
                try:
                    st.info("🔄 正在同步雲端最新資料...")
                    conn=st.connection("gsheets",type=GSheetsConnection)
                    cur=conn.read(worksheet="Marketing_Schedule",ttl=0).dropna(how="all")
                    conn.update(worksheet="Marketing_Schedule",data=pd.concat([cur,new_row],ignore_index=True))
                    st.toast(f"✅ 新增成功！狀態：{status_clean}"); st.cache_data.clear(); st.success("資料已同步寫入 Google Sheets。")
                except Exception as e: st.error(f"寫入失敗：{e}")

# ==========================================
# 頁面：活動進程 (情報室)
# ==========================================
elif page == "📊 活動進程 (情報室)":
    today=pd.Timestamp.now().normalize()
    wd=WEEKDAY_MAP[today.dayofweek]
    st.title("📊 馬尼行銷活動進程")
    st.markdown(f"📅 今天是：**{today.strftime('%Y-%m-%d')} ({wd})**")

    tab1,tab2,tab3,tab4,tab5 = st.tabs(["🔥 今日任務","📅 活動行程表","⏳ 年度甘特圖","💡 企畫庫","📂 完整資料庫"])

    with tab1:
        c1,c2=st.columns(2)
        exec_df=df[df['活動狀態'].str.contains("執行中",na=False)]
        with c1:
            st.subheader("✅ 今日常態發文")
            mask=(exec_df['類型']=='常態')&(exec_df['開始日期']<=today)&(exec_df['結束日期']>=today)
            routine=exec_df[mask].copy()
            if not routine.empty:
                routine=routine[routine.apply(lambda x:x['週期模式']=='每日' or (wd in str(x['重複星期'])),axis=1)]
            if not routine.empty:
                for _,row in routine.iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{row['活動名稱']}**"); st.caption(f"📢 {row['刊登平台']} | 🎬 {row['呈現形式']}")
                        st.info(f"💡 {row['文案重點']}")
                        if str(row.get('相關連結','')).startswith("http"): st.link_button("🔗 前往素材",row['相關連結'])
            else: st.success("今日無常態任務。")
        with c2:
            st.subheader("🚀 進行中的行銷案")
            active=exec_df[(exec_df['類型']=='行銷案')&(exec_df['開始日期']<=today)&(exec_df['結束日期']>=today)]
            if not active.empty:
                for _,row in active.iterrows():
                    dl=(row['結束日期']-today).days; dur=max((row['結束日期']-row['開始日期']).days,1)
                    with st.container(border=True):
                        st.markdown(f"### {row['活動名稱']}"); st.progress(min((today-row['開始日期']).days/dur,1.0))
                        st.write(f"⏳ 剩餘 **{dl} 天** ｜ 📢 {row['刊登平台']}")
                        if str(row.get('相關連結','')).startswith("http"): st.link_button("🔗 查看企劃",row['相關連結'])
            else: st.info("目前無大型活動。")

    with tab2:
        st.subheader("🗓️ 活動行程總覽")
        cs,_=st.columns([1,2])
        with cs:
            td=date.today(); sd=td.replace(day=1); ed=(td.replace(day=28)+timedelta(days=4)).replace(day=1)-timedelta(days=1)
            dr=st.date_input("📅 請選擇顯示區間",value=(sd,ed),key="range_picker")
        if len(dr)==2:
            sts=pd.Timestamp(dr[0]); ets=pd.Timestamp(dr[1])
            fdf=df[(df['開始日期']<=ets)&(df['結束日期']>=sts)].copy()
            if not fdf.empty:
                fig=px.timeline(fdf,x_start="開始日期",x_end="結束日期",y="活動名稱",color="活動狀態",text="活動名稱",
                    hover_data={"活動名稱":False,"刊登平台":True,"文案重點":True},custom_data=["相關連結","活動名稱"])
                fig.update_traces(textposition='inside',insidetextanchor='start')
                fig.update_xaxes(range=[sts,ets],tickformat="%d",dtick="D3" if mobile_mode else "D1",
                    side="top",tickangle=0 if mobile_mode else -45,tickfont=dict(size=11))
                fig.update_yaxes(autorange="reversed")
                ls=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1) if mobile_mode else {}
                fig.update_layout(height=max(400,len(fdf)*50),showlegend=True,legend=ls)
                ev=st.plotly_chart(fig,use_container_width=True,on_select="rerun",selection_mode="points")
                if ev and ev["selection"]["points"]:
                    pt=ev["selection"]["points"][0]; st.divider(); st.info(f"👉 您選擇了：**{pt['customdata'][1]}**")
                    if str(pt['customdata'][0]).startswith("http"): st.link_button("🔗 前往連結",pt['customdata'][0],type="primary")
                    else: st.warning("此活動未設定相關連結。")
            else: st.info("所選區間內沒有活動。")

    with tab3:
        st.subheader("⏳ 年度甘特圖")
        cdf=df[df['類型']=='行銷案']
        if not cdf.empty:
            fig=px.timeline(cdf,x_start="開始日期",x_end="結束日期",y="活動名稱",
                color="活動狀態",hover_data=["刊登平台","負責人"],title="年度活動檔期")
            fig.update_xaxes(tickformat="%Y/%m/%d",dtick="M1",ticklabelmode="period")
            fig.add_vline(x=today.timestamp()*1000,line_width=2,line_dash="dash",line_color="red")
            fig.update_yaxes(autorange="reversed"); st.plotly_chart(fig,use_container_width=True)
        else: st.write("尚無資料。")

    with tab4:
        st.subheader("💡 企畫中草案")
        pdf=df[df['活動狀態'].str.contains("企畫中",na=False)]
        if not pdf.empty: st.dataframe(pdf,use_container_width=True)
        else: st.info("目前沒有企畫中的草案。")

    with tab5:
        st.subheader("📝 所有紀錄")
        st.dataframe(df,use_container_width=True,
            column_config={"相關連結":st.column_config.LinkColumn("連結",display_text="開啟"),
                "開始日期":st.column_config.DateColumn("開始",format="YYYY-MM-DD"),
                "結束日期":st.column_config.DateColumn("結束",format="YYYY-MM-DD")})
