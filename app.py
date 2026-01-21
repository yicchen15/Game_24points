import streamlit as st
import random
import time
import re
from operator import add, sub, mul, truediv
from streamlit_autorefresh import st_autorefresh

# --- 頁面設定 ---
st.set_page_config(page_title=" 24點撲克牌挑戰", page_icon="🃏", layout="centered")

# --- 核心演算法 (Solver) ---
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

# --- Session State ---
if 'start_time' not in st.session_state: st.session_state.start_time = None
if 'current_cards' not in st.session_state: st.session_state.current_cards = []
if 'formula' not in st.session_state: st.session_state.formula = []
if 'msg' not in st.session_state: st.session_state.msg = None
if 'reveal_answer' not in st.session_state: st.session_state.reveal_answer = False
if 'is_playing' not in st.session_state: st.session_state.is_playing = False
if 'is_exploded' not in st.session_state: st.session_state.is_exploded = False

# --- 側邊欄 ---
with st.sidebar:
    st.header("⚙️ 設定")
    g_num = st.number_input("🎴 抽牌張數", value=4, min_value=2, max_value=6)
    g_target = st.number_input("🎯 目標點數", value=24)
    g_time = st.number_input("⏳ 秒數", value=30, step=5)
    show_hint = st.toggle("顯示數值提示", value=True)

st.title("🃏 24點撲克牌挑戰")

if st.session_state.is_playing and not st.session_state.is_exploded:
    st_autorefresh(interval=1000, key="gametimer")

# --- 控制區 ---
c1, c2, c3 = st.columns(3)
def init_game():
    st.session_state.current_cards = deal_cards(g_num)
    st.session_state.start_time = time.time()
    st.session_state.formula = []
    st.session_state.msg = None
    st.session_state.reveal_answer = False
    st.session_state.is_playing = True
    st.session_state.is_exploded = False

if c1.button("🔥 開始", use_container_width=True, type="primary"): init_game()
if c2.button("👀 答案", use_container_width=True): 
    st.session_state.reveal_answer = True
    st.session_state.is_playing = False
if c3.button("⏭️ 跳過", use_container_width=True): init_game()

st.divider()

if st.session_state.start_time:
    # 爆炸邏輯
    elapsed = time.time() - st.session_state.start_time
    remaining = int(g_time - elapsed)
    if st.session_state.is_playing and not st.session_state.is_exploded:
        if remaining > 0:
            st.markdown(f"<h3 style='text-align: center; color: {'green' if remaining > 10 else 'red'};'>⏳ {remaining} 秒</h3>", unsafe_allow_html=True)
        else:
            st.session_state.is_playing = False
            st.session_state.is_exploded = True
            st.rerun()

    if st.session_state.is_exploded:
        st.markdown("""
            <div style='text-align: center; padding: 10px; background-color: #fff0f0; border-radius: 8px; border: 2px solid #ff4b4b; margin-bottom: 5px;'>
                <div style='font-size: 32px; line-height: 1;'>💥 BOOM!</div>
                <div style='color: #cc0000; font-weight: bold; font-size: 18px; margin: 5px 0;'>時間到！任務失敗</div>
                <div style='font-size: 13px; color: #555;'>卡片已保留，可繼續嘗試或查看解答。</div>
            </div>
        """, unsafe_allow_html=True)

    # --- 1. 撲克牌區 (強制 4 個一行) ---
    cards = st.session_state.current_cards
    for i in range(0, len(cards), 4):
        cols = st.columns(4) # 每一橫排固定 4 欄
        for j in range(4):
            idx = i + j
            if idx < len(cards):
                card = cards[idx]
                label = card['display']
                if show_hint and card['rank'] in ['A', 'J', 'Q', 'K']:
                    label += f"\n({card['value']})"
                if cols[j].button(label, key=f"c_{idx}", use_container_width=True):
                    st.session_state.formula.append(str(card['value']))
                    st.rerun()

    st.write("") # 間隔

    # --- 2. 運算符號區 (強制 4 個一行) ---
    # 分成兩組，每組四個
    op_set1 = [("➕", "+"), ("➖", "-"), ("✖️", "*"), ("➗", "/")]
    op_set2 = [("(", "("), (")", ")"), ("⌫ 退格", "back"), ("🗑️ 重置", "clear")]

    # 第一排符號
    op_cols1 = st.columns(4)
    for i, (icon, sym) in enumerate(op_set1):
        if op_cols1[i].button(icon, key=f"op1_{i}", use_container_width=True):
            st.session_state.formula.append(sym)
            st.rerun()

    # 第二排符號 (含功能鍵)
    op_cols2 = st.columns(4)
    for i, (icon, sym) in enumerate(op_set2):
        if op_cols2[i].button(icon, key=f"op2_{i}", use_container_width=True):
            if sym == "back":
                if st.session_state.formula: st.session_state.formula.pop()
            elif sym == "clear":
                st.session_state.formula = []
                st.session_state.msg = None
            else:
                st.session_state.formula.append(sym)
            st.rerun()

    # --- 3. 算式與檢查 ---
    current_f = "".join(st.session_state.formula)
    display_f = current_f.replace("*", "×").replace("/", "÷")
    st.markdown(f"<div style='background:#f8f9fa; padding:10px; border-radius:8px; text-align:center; font-size:24px; font-family:monospace; border:2px dashed #ccc;'>{display_f if display_f else '...'}</div>", unsafe_allow_html=True)

    if st.button("✅ 檢查拆彈結果", use_container_width=True, type="primary"):
        if current_f:
            try:
                used_nums = re.findall(r'\d+', current_f)
                target_nums = [str(c['value']) for c in st.session_state.current_cards]
                if sorted(used_nums) != sorted(target_nums):
                    st.session_state.msg = ("error", "需用完所有數字且不重複！")
                else:
                    res = eval(current_f)
                    if abs(res - g_target) < 1e-6:
                        st.session_state.msg = ("success", "答對了！" if not st.session_state.is_exploded else "算對了！但時間已過..")
                        if not st.session_state.is_exploded: st.balloons()
                        st.session_state.is_playing = False
                    else:
                        st.session_state.msg = ("error", f"結果是 {res} ❌")
            except: st.session_state.msg = ("error", "算式錯誤")
        st.rerun()

    if st.session_state.msg:
        tp, txt = st.session_state.msg
        if tp == "success": st.success(txt)
        elif tp == "error": st.error(txt)

    if st.session_state.reveal_answer:
        st.divider()
        nums = [{'val': float(c['value']), 'expr': str(c['value'])} for c in st.session_state.current_cards]
        ans = solve_24(nums, g_target)
        if ans: st.info(f"💡 解答：{ans.replace('*','×').replace('/','÷')}")
        else: st.warning("無解！")