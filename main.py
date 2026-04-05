import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import random
import calendar  # Обов'язково додайте цей рядок!
from datetime import datetime, timedelta

# --- ПІДКЛЮЧЕННЯ GOOGLE SHEETS ---
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1aoIactómBabATa0SHLJCWnOBKwITy74kLkJgItQMKNc/edit"
# ... далі ваш код

# --- ПІДКЛЮЧЕННЯ GOOGLE SHEETS ---
# Це посилання обов'язково має бути в коді
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1aoIactómBabATa0SHLJCWnOBKwITy74kLkJgItQMKNc/edit"

from streamlit_gsheets import GSheetsConnection

def load_sheet(sheet_name):
    try:
        # ttl=0 гарантує, що ми бачимо свіжі дані відразу
        return conn.read(spreadsheet=SPREADSHEET_URL, worksheet=sheet_name, ttl=0)
    except:
        return pd.DataFrame()

def save_sheet(df, sheet_name):
    # З новим JSON-ключем цей рядок більше не видасть помилку
    conn.update(spreadsheet=SPREADSHEET_URL, worksheet=sheet_name, data=df)

# --- 3. КОНФІГУРАЦІЯ ---
SHOPS_CONFIG = {
    "Агора": {"open": 10, "close": 20}, "Свобода48": {"open": 9, "close": 19},
    "Соборна15": {"open": 9, "close": 19}, "Мегамол": {"open": 10, "close": 21},
    "Монблан": {"open": 10, "close": 20}, "Шепетівка": {"open": 9, "close": 18},
    "Волочиськ": {"open": 9, "close": 18}, "Полонне": {"open": 9, "close": 18},
    "Бар": {"open": 9, "close": 18}, "Літин": {"open": 8, "close": 18},
}

POSITIONS = ["Продавець", "Адміністратор", "Зам. адмін", "Стажер"]
STATUSES = {"Робочий": "✅", "Вихідний": "🅿️", "Відрядження": "🚗", "Стажування": "🐣", "Відпустка": "🌴", "Лікарняний": "🤒"}
SHIFTS = ["Не вказано", "1 зміна", "2 зміна", "3 зміна"]

FACTS = [
    "Bluetooth назвали на честь данського короля Гарольда Синьозубого.",
    "Перший сервер Google стояв у корпусі з LEGO.",
    "Перший iPhone вийшов 9 січня 2007 р.",
    "Україна — одна з перших у Європі за кількістю IT-фахівців."
]

def get_daily_fact():
    random.seed(datetime.now().strftime("%Y%m%d"))
    return random.choice(FACTS)

# --- 4. ПЕРЕВІРКА ПАРОЛЯ ---
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.markdown("<h1 style='text-align:center;color:red;'>ВХІД ЧІП CLOUD</h1>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        pwd = st.text_input("Пароль компанії", type="password")
        if st.button("Увійти", type="primary"):
            if pwd == "chiponelove":
                st.session_state["auth"] = True
                st.rerun()
            else: st.error("❌ Помилка")
    st.stop()

# --- 5. ДИЗАЙН ТА ШАПКА ---
st.markdown("""<style>
@media (max-width: 768px) { h1 { font-size: 50px !important; } }
.stDataFrame, .stDataEditor { font-size: 12px; }
</style>""", unsafe_allow_html=True)

st.markdown(f"""
<div style="text-align:center;">
    <a href="https://chip-mag.com/ua/" target="_blank" style="text-decoration:none;">
        <h1 style="color:red;font-size:90px;font-weight:900;margin:0;line-height:1;">ЧІП</h1>
    </a>
</div>
""", unsafe_allow_html=True)
st.info(f"💡 **Факт дня:** {get_daily_fact()}")

# --- 6. ЗАВАНТАЖЕННЯ ДАНИХ З ХМАРИ ---
df_sch = load_sheet("schedule")
df_workers = load_sheet("shop_workers")
df_photos = load_sheet("worker_photos")

# --- 7. ФУНКЦІЇ ---
def get_workers_list(shop_name):
    if df_workers.empty: return []
    return df_workers[df_workers['shop'] == shop_name]['worker_name'].tolist()

def sidebar_controls(shop_name, key_p):
    st.sidebar.subheader(f"📅 Редагування: {shop_name}")
    workers = get_workers_list(shop_name)
    if not workers:
        st.sidebar.warning("Додайте працівників у кабінеті.")
        return

    a_worker = st.sidebar.selectbox("Працівник", workers, key=f"{key_p}_w")
    
    with st.sidebar.expander("👤 Профіль"):
        new_photo = st.text_input("Фото URL", key=f"{key_p}_ph")
        if st.button("💾 Оновити фото", key=f"{key_p}_btn_ph"):
            updated_photos = df_photos[df_photos['worker'] != a_worker]
            updated_photos = pd.concat([updated_photos, pd.DataFrame([{"worker": a_worker, "photo_url": new_photo}])])
            save_sheet(updated_photos, "worker_photos")
            st.rerun()

    a_status = st.sidebar.selectbox("Статус", list(STATUSES.keys()), key=f"{key_p}_st")
    a_shift = st.sidebar.selectbox("Зміна", SHIFTS, key=f"{key_p}_sh")
    
    dates = []
    mode = st.sidebar.radio("Режим", ["Один день", "Період"], key=f"{key_p}_mode")
    if mode == "Один день":
        dates.append(st.sidebar.date_input("Дата", key=f"{key_p}_d"))
    else:
        d1 = st.sidebar.date_input("З", key=f"{key_p}_d1")
        d2 = st.sidebar.date_input("По", key=f"{key_p}_d2")
        temp_d = d1
        while temp_d <= d2:
            dates.append(temp_d)
            temp_d += timedelta(days=1)

    if st.button("🚀 Застосувати", type="primary", key=f"{key_p}_apply"):
        global df_sch
        status_icon = f"{STATUSES[a_status]} {a_status}"
        for d in dates:
            d_str = d.strftime("%d.%m.%Y")
            # Видаляємо старий запис для цієї дати і працівника
            df_sch = df_sch[~((df_sch['worker'] == a_worker) & (df_sch['date'] == d_str))]
            new_row = pd.DataFrame([{
                "shop": shop_name, "worker": a_worker, "date": d_str, 
                "status": status_icon, "shift_num": a_shift, "photo_url": "" 
            }])
            df_sch = pd.concat([df_sch, new_row], ignore_index=True)
        save_sheet(df_sch, "schedule")
        st.success("Хмара оновлена!")
        st.rerun()

# --- 8. ВИБІР ДАТИ ---
now = datetime.now()
cm1, cm2, cm3 = st.columns([1, 1, 2])
sel_month_name = cm1.selectbox("Місяць", list(calendar.month_name)[1:], index=now.month - 1)
sel_month = list(calendar.month_name).index(sel_month_name)
sel_year = cm2.selectbox("Рік", [2026, 2027])
search_q = cm3.text_input("🔍 Пошук працівника", "").lower()

# --- 9. НАВІГАЦІЯ ---
nav = st.sidebar.radio("Навігація", ["📊 Загальний огляд"] + [f"🏢 {s}" for s in SHOPS_CONFIG])

if nav == "📊 Загальний огляд":
    st.subheader("📊 Усі магазини (Cloud)")
    for shop in SHOPS_CONFIG:
        workers = [w for w in get_workers_list(shop) if not search_q or search_q in w.lower()]
        if not workers and search_q: continue
        
        with st.expander(f"🏢 {shop.upper()}", expanded=True):
            days_in = calendar.monthrange(sel_year, sel_month)[1]
            days_list = [f"{d:02d}.{sel_month:02d}" for d in range(1, days_in + 1)]
            
            grid = []
            for w in workers:
                w_data = df_sch[(df_sch['worker'] == w) & (df_sch['shop'] == shop)]
                ph_url = df_photos[df_photos['worker'] == w]['photo_url'].values[0] if not df_photos.empty and w in df_photos['worker'].values else ""
                row = {"Фото": ph_url, "ПІБ": w}
                for d in days_list:
                    f_date = f"{d}.{sel_year}"
                    m = w_data[w_data['date'] == f_date]
                    if not m.empty:
                        icon = m['status'].values[0].split()[0]
                        sh = m['shift_num'].values[0]
                        row[d] = f"{icon}({sh[0]})" if sh != "Не вказано" else icon
                    else: row[d] = "—"
                grid.append(row)
            
            if grid:
                st.data_editor(pd.DataFrame(grid), use_container_width=True, hide_index=True, disabled=True,
                               column_config={"Фото": st.column_config.ImageColumn("Фото", width="small")})
    
    selected_edit_shop = st.sidebar.selectbox("Магазин для редагування", list(SHOPS_CONFIG.keys()))
    sidebar_controls(selected_edit_shop, "gen")

else:
    shop_name = nav.replace("🏢 ", "")
    st.subheader(f"🏢 Кабінет: {shop_name}")
    tab1, tab2 = st.tabs(["📅 Графік", "👥 Працівники"])
    
    with tab1:
        sidebar_controls(shop_name, "shop")
        # Тут можна додати візуалізацію графіка саме для цього магазину
        
    with tab2:
        st.write("Керування персоналом")
        new_w = st.text_input("ПІБ нового працівника")
        if st.button("➕ Додати"):
            if new_w:
                new_worker_df = pd.concat([df_workers, pd.DataFrame([{"shop": shop_name, "worker_name": new_w}])], ignore_index=True)
                save_sheet(new_worker_df, "shop_workers")
                st.rerun()
            else:
                st.error("Введіть ПІБ")
        
        curr_workers = get_workers_list(shop_name)
        for w in curr_workers:
            c1, c2 = st.columns([4,1])
            c1.write(w)
            if c2.button("🗑️", key=f"del_{w}"):
                updated_workers = df_workers[~((df_workers['shop'] == shop_name) & (df_workers['worker_name'] == w))]
                save_sheet(updated_workers, "shop_workers")

                st.success(f"Працівника {new_worker_name} додано!")
                st.rerun()
