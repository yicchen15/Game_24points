import streamlit as st
import random
import time
import re
from operator import add, sub, mul, truediv
from streamlit_autorefresh import st_autorefresh # 引入自動刷新組件

# --- 頁面設定 ---
st.set_page_config(page_title="24點撲克牌互動版", page_icon="🃏", layout="centered")

# --- 核心演算法 (24點求解) ---
def solve_24(nums, target=24):
    if not nums: return None
    if len(nums) == 1:
        return nums[0]['expr'] if abs(nums[0]['val'] - target) < 1e-6 else None
    for i in range(len(nums)):
        for j in range(len(nums)):
            if i != j:
                n1, n2 = nums[i], nums[j]
                remaining = [nums[k] for k in range(len(nums)) if k != i and k != j]
                for op_func, op_symbol in [(add, '+'), (sub, '-'), (mul, '*'), (truediv, '/')]:
                    if op_symbol == '/' and abs(n2['val']) < 1e-6: continue
                    res = solve_24(remaining + [{'val': op_func(n1['val'], n2['val']), 'expr': f"({n1['expr']}{op_symbol}{n2['expr']})"}], target)
                    if res: return res
    return None

def deal_cards(num_cards=4):
    suits = ['♠️', '♥️', '♦️', '♣️']
    ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    values = {'A':1,'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'10':10,'J':11,'Q':12,'K':13}
    deck = [(s, r) for s in suits for r in ranks]
    drawn = random.sample(deck, num_cards)
    return [{'display': f"{s}{r}", 'value': values[r], 'rank': r} for s, r in drawn]

# ==========================================
# Session State 初始化
# ==========================================
if 'start_time' not in st.session_state: st.session_state.start_time = None
if 'current_cards' not in st.session_state: st.session_state.current_cards = []
if 'formula' not in st.session_state: st.session_state.formula = []
if 'msg' not in st.session_state: st.session_state.msg = None
if 'reveal_answer' not in st.session_state: st.session_state.reveal_answer = False
if 'is_playing' not in st.session_state: st.session_state.is_playing = False

# ==========================================
# 主畫面 UI
# ==========================================
st.title("🃏 撲克牌 24 點 (自動計時版)")

# --- 自動刷新組件 ---
# 只有在遊戲進行中才啟動每 1000 毫秒 (1秒) 刷新一次
if st.session_state.is_playing and not st.session_state.reveal_answer:
    st_autorefresh(interval=1000, key="gametimer")

# 設定區
with st.sidebar:
    st.header("⚙️ 遊戲設定")
    g_target = st.number_input("目標點數", value=24)
    g_time = st.number_input("限時 (秒)", value=30)
    show_hint = st.toggle("顯示英文字母數值", value=True)

# 功能按鈕
c1, c2, c3 = st.columns(3)

def init_game():
    st.session_state.current_cards = deal_cards(4)
    st.session_state.start_time = time.time()
    st.session_state.formula = []
    st.session_state.msg = None
    st.session_state.reveal_answer = False
    st.session_state.is_playing = True

if c1.button("🆕 發牌開始", use_container_width=True, type="primary"):
    init_game()

if c2.button("👀 公布答案", use_container_width=True):
    st.session_state.reveal_answer = True
    st.session_state.is_playing = False

if c3.button("⏭️ 跳過重來", use_container_width=True):
    init_game()

# --- 遊戲主體 ---
if st.session_state.is_playing:
    # 1. 計算剩餘時間
    elapsed = time.time() - st.session_state.start_time
    remaining = int(g_time - elapsed)

    if remaining > 0 and not st.session_state.reveal_answer:
        st.subheader(f"⏳ 剩餘時間: {remaining} 秒")
        # 根據剩餘時間變色
        if remaining <= 10:
            st.warning("⏱️ 快沒時間了！")
    elif remaining <= 0:
        st.error("⏰ 時間到！")
        st.session_state.reveal_answer = True
        st.session_state.is_playing = False
    
    st.divider()

    # 2. 顯示卡片
    card_cols = st.columns(len(st.session_state.current_cards))
    for i, card in enumerate(st.session_state.current_cards):
        label = card['display']
        if show_hint and card['rank'] in ['A', 'J', 'Q', 'K']:
            label += f"\n({card['value']})"
        if card_cols[i].button(label, key=f"c_{i}", use_container_width=True):
            st.session_state.formula.append(str(card['value']))
            st.rerun()

    # 3. 符號按鈕區
    st.write("🔧 運算符號")
    op_cols = st.columns([1,1,1,1,1,1,1.5,1.5])
    ops = [("+","+"), ("-","-"), ("*","×"), ("/","÷"), ("(","("), (")",")")]
    
    for i, (sym, icon) in enumerate(ops):
        if op_cols[i].button(icon, key=f"op_{sym}", use_container_width=True):
            st.session_state.formula.append(sym)
            st.rerun()
            
    if op_cols[6].button("⌫ 退格", use_container_width=True):
        if st.session_state.formula: st.session_state.formula.pop()
        st.rerun()
    if op_cols[7].button("🗑️ 清除", use_container_width=True):
        st.session_state.formula = []
        st.session_state.msg = None
        st.rerun()

    # 4. 算式顯示
    current_f = "".join(st.session_state.formula)
    st.markdown(f"""
        <div style="background:#f0f2f6; padding:20px; border-radius:10px; text-align:center; font-size:32px; font-weight:bold; color:#1f1f1f; border: 2px solid #ddd;">
            {current_f if current_f else "請組合算式"}
        </div>
    """, unsafe_allow_html=True)

    # 5. 檢查結果
    if st.button("✅ 檢查結果", use_container_width=True, type="primary"):
        if not current_f:
            st.session_state.msg = ("warning", "算式是空的喔！")
        else:
            try:
                # 安全校驗：是否使用了所有數字
                used_nums = re.findall(r'\d+', current_f)
                target_nums = [str(c['value']) for c in st.session_state.current_cards]
                if sorted(used_nums) != sorted(target_nums):
                    st.session_state.msg = ("error", "必須剛好使用這四張牌的數字喔！")
                else:
                    res = eval(current_f)
                    if abs(res - g_target) < 1e-6:
                        st.session_state.msg = ("success", "答對了~ 太強了！ 🎉")
                        st.session_state.is_playing = False # 答對就停止計時
                        st.balloons()
                    else:
                        st.session_state.msg = ("error", f"結果是 {res}，再接再厲！ ❌")
            except:
                st.session_state.msg = ("error", "算式格式不正確！")
        st.rerun()

    if st.session_state.msg:
        m_type, m_txt = st.session_state.msg
        if m_type == "success": st.success(m_txt)
        elif m_type == "error": st.error(m_txt)
        elif m_type == "warning": st.warning(m_txt)

# 6. 公布解答 (獨立於 is_playing 之外，確保時間到也能看答案)
if st.session_state.reveal_answer:
    st.divider()
    nums = [{'val': float(c['value']), 'expr': str(c['value'])} for c in st.session_state.current_cards]
    ans = solve_24(nums, g_target)
    st.info(f"💡 參考解答：{ans if ans else '這題真的無解...'}")