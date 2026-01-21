import streamlit as st
import random
import time
import itertools
import re
from operator import add, sub, mul, truediv

# --- 頁面設定 ---
st.set_page_config(page_title="24點撲克牌大師", page_icon="🃏", layout="centered")

# ==========================================
# 核心演算法與工具
# ==========================================

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
    deck = list(itertools.product(suits, ranks))
    drawn = random.sample(deck, num_cards)
    return [{'display': f"{s}{r}", 'value': values[r], 'rank': r, 'id': i} for i, (s, r) in enumerate(drawn)]

# ==========================================
# Session State 初始化
# ==========================================
if 'game_active' not in st.session_state: st.session_state.game_active = False
if 'current_cards' not in st.session_state: st.session_state.current_cards = []
if 'formula' not in st.session_state: st.session_state.formula = []
if 'time_left' not in st.session_state: st.session_state.time_left = 0
if 'reveal_answer' not in st.session_state: st.session_state.reveal_answer = False
if 'msg' not in st.session_state: st.session_state.msg = ("","") # (type, text)

# ==========================================
# 主畫面
# ==========================================
st.title("🃏 撲克牌 24 點：互動挑戰")

tab1, tab2 = st.tabs(["🎮 互動遊戲", "🧮 自動解牌"])

with tab1:
    with st.expander("⚙️ 設定"):
        g_target = st.number_input("目標點數", value=24, step=1)
        g_num = st.number_input("張數", value=4, min_value=2, max_value=6)
        g_time = st.number_input("秒數", value=30, step=5)
        show_hint = st.toggle("顯示字母數值", value=True)

    # 控制按鈕
    c1, c2, c3 = st.columns(3)
    
    def start_game():
        st.session_state.current_cards = deal_cards(g_num)
        st.session_state.game_active = True
        st.session_state.time_left = g_time
        st.session_state.formula = []
        st.session_state.reveal_answer = False
        st.session_state.msg = ("","")

    if c1.button("🃏 發牌 / 開始", use_container_width=True, type="primary"): start_game()
    if c2.button("👀 看解答", use_container_width=True, disabled=not st.session_state.game_active):
        st.session_state.reveal_answer = True
    if c3.button("⏭️ 跳過", use_container_width=True): start_game()

    if st.session_state.game_active:
        st.divider()
        
        # --- 顯示撲克牌 (可點擊) ---
        st.write("👇 點擊卡片或按鈕來組合算式：")
        card_cols = st.columns(len(st.session_state.current_cards))
        for idx, card in enumerate(st.session_state.current_cards):
            with card_cols[idx]:
                label = card['display']
                if show_hint and card['rank'] in ['A', 'J', 'Q', 'K']:
                    label += f"\n({card['value']})"
                
                # 使用按鈕模擬卡片點擊
                if st.button(label, key=f"btn_card_{idx}", use_container_width=True):
                    st.session_state.formula.append(str(card['value']))

        # --- 運算符號按鈕 ---
        st.write("")
        op_cols = st.columns(7)
        operators = [("+", "+"), ("-", "-"), ("*", "×"), ("/", "÷"), ("(", "("), (")", ")")]
        for i, (symbol, display) in enumerate(operators):
            if op_cols[i].button(display, key=f"op_{symbol}", use_container_width=True):
                st.session_state.formula.append(symbol)
        
        # 回車鍵 (刪除)
        if op_cols[6].button("⌫", use_container_width=True, help="刪除最後一個輸入"):
            if st.session_state.formula: st.session_state.formula.pop()

        # --- 算式輸入欄位 ---
        current_formula_str = "".join(st.session_state.formula)
        st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 2px dashed #bfc5d1; text-align: center; font-size: 24px; font-family: monospace;">
                {current_formula_str if current_formula_str else "請組合算式..."}
            </div>
        """, unsafe_allow_html=True)

        # --- 計算按鈕 ---
        if st.button("🧮 計算結果", type="primary", use_container_width=True):
            formula_str = "".join(st.session_state.formula)
            try:
                # 1. 安全檢查：只允許數字、括號和四則運算
                if not re.match(r'^[\d\+\-\*\/\(\)\s]+$', formula_str):
                    raise ValueError("含有非法字元")
                
                # 2. 邏輯檢查：是否使用了所有發出的數字
                input_numbers = re.findall(r'\d+', formula_str)
                required_numbers = [str(c['value']) for c in st.session_state.current_cards]
                
                if sorted(input_numbers) != sorted(required_numbers):
                    st.session_state.msg = ("error", f"必須使用且只能使用一次所有卡片數字：{', '.join(required_numbers)}")
                else:
                    # 3. 數學運算
                    result = eval(formula_str)
                    if abs(result - g_target) < 1e-6:
                        st.session_state.msg = ("success", "答對了~ 🎉")
                        st.balloons()
                    else:
                        st.session_state.msg = ("error", f"結果是 {result}，答錯囉... ❌")
            except Exception:
                st.session_state.msg = ("error", "算式語法錯誤，請檢查括號或運算符。")

        # 顯示訊息
        msg_type, msg_text = st.session_state.msg
        if msg_type == "success": st.success(msg_text)
        elif msg_type == "error": st.error(msg_text)

        st.divider()

        # --- 倒數與解答顯示 ---
        t_placeholder = st.empty()
        if st.session_state.reveal_answer:
            nums = [{'val': float(c['value']), 'expr': str(c['value'])} for c in st.session_state.current_cards]
            ans = solve_24(nums, g_target)
            st.warning(f"參考解答：{ans if ans else '此題無解'}")
        elif st.session_state.time_left > 0:
            # 簡單計時顯示 (非阻塞式建議用更複雜寫法，此處為保持程式碼簡潔)
            t_placeholder.metric("⏳ 剩餘時間", f"{st.session_state.time_left} 秒")
            # 註：在互動模式下，time.sleep 會導致輸入反應變慢。
            # 若要完美的計時器，建議拿掉 sleep 迴圈，改用時戳比對。