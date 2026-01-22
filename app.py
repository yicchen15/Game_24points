import streamlit as st
import random
import time
import itertools
from operator import add, sub, mul, truediv

# --- 設定頁面資訊 ---
st.set_page_config(page_title="24點撲克牌大師", page_icon="♠️", layout="centered")

# ==========================================
# 核心邏輯區 (演算法與工具)
# ==========================================

def solve_24(nums, target=24):
    """
    通用遞迴求解器。
    輸入: nums (list of dicts [{'val': float, 'expr': str}]), target (float)
    輸出: 解答算式字串 or None
    """
    if not nums:
        return None
        
    if len(nums) == 1:
        if abs(nums[0]['val'] - target) < 1e-6:
            return nums[0]['expr']
        else:
            return None

    # 排列組合兩兩運算
    for i in range(len(nums)):
        for j in range(len(nums)):
            if i != j:
                n1 = nums[i]
                n2 = nums[j]
                remaining = [nums[k] for k in range(len(nums)) if k != i and k != j]
                
                ops = [(add, '+'), (sub, '-'), (mul, '*'), (truediv, '/')]
                
                for op_func, op_symbol in ops:
                    # 避免除以零
                    if op_symbol == '/' and abs(n2['val']) < 1e-6:
                        continue
                        
                    new_val = op_func(n1['val'], n2['val'])
                    # 加上括號保護優先順序
                    new_expr = f"({n1['expr']} {op_symbol} {n2['expr']})"
                    new_item = {'val': new_val, 'expr': new_expr}
                    
                    res = solve_24(remaining + [new_item], target)
                    if res:
                        return res
    return None

def deal_cards(num_cards=4):
    """隨機發牌"""
    suits = ['♠️', '♥️', '♦️', '♣️']
    ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    values = {
        'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, 
        '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13
    }
    deck = list(itertools.product(suits, ranks))
    drawn = random.sample(deck, num_cards)
    
    card_data = []
    for suit, rank in drawn:
        card_data.append({
            'display': f"{suit}{rank}",
            'value': values[rank],
            'rank': rank
        })
    return card_data

def parse_card_input(input_str):
    """
    解析使用者輸入的牌型字串 (例如: 'A 5 5 10' 或 'K q 3 3')
    回傳: list of dicts [{'val': float, 'expr': str}]
    """
    if not input_str:
        return None
    
    # 定義對照表
    values = {
        'A': 1, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, 
        '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13
    }
    
    # 分割並標準化
    raw_items = input_str.strip().replace(',', ' ').split()
    parsed_nums = []
    
    for item in raw_items:
        key = item.upper()
        if key in values:
            val = values[key]
            parsed_nums.append({'val': float(val), 'expr': str(val)})
        else:
            # 嘗試是否為純數字 (例如使用者輸入 13 代表 K)
            try:
                val = float(item)
                parsed_nums.append({'val': val, 'expr': str(int(val) if val.is_integer() else val)})
            except ValueError:
                return None # 解析失敗
                
    return parsed_nums

# ==========================================
# Session State 初始化
# ==========================================
if 'game_active' not in st.session_state:
    st.session_state.game_active = False
if 'current_cards' not in st.session_state:
    st.session_state.current_cards = []
if 'solution' not in st.session_state:
    st.session_state.solution = None
if 'time_left' not in st.session_state:
    st.session_state.time_left = 0
if 'reveal_answer' not in st.session_state:
    st.session_state.reveal_answer = False

# ==========================================
# 介面佈局
# ==========================================

st.title("🃏 撲克牌神算 24點")

# 建立兩個分頁
tab1, tab2 = st.tabs(["🎮 挑戰模式", "🧮 解牌計算機"])

# ------------------------------------------
# 分頁 1: 遊戲模式 (原本的功能)
# ------------------------------------------
# --- 在「遊戲設定」區塊新增開關 ---
with tab1:
    with st.expander("⚙️ 遊戲設定 (點擊展開)", expanded=False):
        game_target = st.number_input("遊戲目標點數", value=24, step=1, key="g_target")
        game_cards_num = st.number_input("抽牌張數", value=4, min_value=2, max_value=6, step=1, key="g_num")
        game_time_s = st.number_input("倒數時間 (秒)", value=60, step=5, key="g_time")
        
        # 新增功能開關：顯示字母對應數字
        show_hint = st.toggle("當撲克牌為字母時顯示數字 (如: J → 11)", value=True)
    col1, col2, col3 = st.columns([1, 1, 1])

    def start_new_game():
        st.session_state.current_cards = deal_cards(game_cards_num)
        st.session_state.game_active = True
        st.session_state.time_left = game_time_s
        st.session_state.reveal_answer = False
        st.session_state.solution = None
        
        # 預計算
        nums = [{'val': float(c['value']), 'expr': str(c['value'])} for c in st.session_state.current_cards]
        sol = solve_24(nums, game_target)
        st.session_state.solution = sol if sol else "無解"

    with col1:
        if st.button("發牌 / 開始", use_container_width=True, type="primary"):
            start_new_game()

    with col2:
        btn_disabled = not st.session_state.game_active or st.session_state.reveal_answer
        if st.button("👀 看解答", use_container_width=True, disabled=btn_disabled):
            st.session_state.reveal_answer = True
            st.rerun()

    with col3:
        if st.button("跳過 / 重來", use_container_width=True):
            start_new_game()

    # 遊戲畫面顯示

    if st.session_state.game_active:
        st.divider()
        c_cols = st.columns(len(st.session_state.current_cards))
        for idx, card in enumerate(st.session_state.current_cards):
            with c_cols[idx]:
                # 準備顯示文字
                display_text = card['display']
                
                # 如果開啟了提示，且牌面是英文字母
                if show_hint and card['rank'] in ['A', 'J', 'Q', 'K']:
                    display_text = f"{card['display']} <span style='font-size: 14px; color: gray;'>({card['value']})</span>"
                
                # 渲染卡片
                st.markdown(
                    f"""
                    <div style="
                        border: 2px solid #ddd; border-radius: 8px; padding: 15px; 
                        text-align: center; font-size: 20px; background: white;
                        color: {'red' if card['display'][0] in ['♥️', '♦️'] else 'black'};
                        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                    ">
                        {display_text}
                    </div>
                    """, unsafe_allow_html=True
                )
        st.divider()

        timer_placeholder = st.empty()
        result_placeholder = st.empty()

        # 顯示邏輯
        if st.session_state.reveal_answer or st.session_state.time_left <= 0:
            timer_placeholder.caption("🛑 計時結束")
            sol = st.session_state.solution
            if sol == "無解":
                result_placeholder.warning("此局無解 😅")
            else:
                display_sol = sol[1:-1] if sol.startswith('(') and sol.endswith(')') else sol
                result_placeholder.success(f"🎉 解答： {display_sol} = {game_target}")
                if st.session_state.reveal_answer:
                    st.balloons()
        else:
            # 倒數計時 Loop
            for i in range(st.session_state.time_left, -1, -1):
                timer_placeholder.progress(i / game_time_s, text=f"⏳ {i}s")
                time.sleep(1)
                st.session_state.time_left = i
                if i == 0:
                    st.rerun()

# ------------------------------------------
# 分頁 2: 解牌計算機 (優化四個空格輸入)
# ------------------------------------------
with tab2:
    st.markdown("### 🧮 自定義解牌器")
    st.caption("請在下方四個空格分別輸入牌面 (A, 2-10, J, Q, K)")
    
    # 目標點數設定
    solver_target = st.number_input("目標點數", value=24, step=1, key="s_target_input")
    
    # 建立四個橫向排列的輸入框
    input_cols = st.columns(4)
    card_inputs = []
    
    for i in range(4):
        with input_cols[i]:
            val = st.text_input(f"第 {i+1} 張", placeholder="A", key=f"card_{i}")
            card_inputs.append(val)

    if st.button("🚀 開始計算", type="primary", use_container_width=True):
        # 過濾掉空白輸入並組合字串
        combined_input = " ".join([c for c in card_inputs if c.strip()])
        
        if not combined_input:
            st.warning("請至少輸入幾張牌！")
        else:
            # 解析輸入
            parsed_cards = parse_card_input(combined_input)
            
            if parsed_cards is None:
                st.error("輸入格式錯誤！請輸入數字 (1-10) 或字母 A, J, Q, K。")
            elif len(parsed_cards) < 2:
                st.warning("請輸入至少兩張牌進行運算。")
            else:
                st.info(f"正在計算組合: {[c['expr'] for c in parsed_cards]} 目標: {solver_target}")
                
                start_time = time.time()
                result = solve_24(parsed_cards, solver_target)
                end_time = time.time()
                
                st.divider()
                if result:
                    display_ans = result[1:-1] if result.startswith('(') and result.endswith(')') else result
                    st.success(f"### 🎉 找到解答了！")
                    st.code(f"{display_ans} = {solver_target}", language="text")
                    st.balloons()
                else:
                    st.error(f"### ❌ 這組牌型在目標為 {solver_target} 時無解")
                
                st.caption(f"計算耗時: {end_time - start_time:.4f} 秒")