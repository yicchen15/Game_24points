import streamlit as st
import random
import time
import itertools
from operator import add, sub, mul, truediv

# --- 設定頁面資訊 ---
st.set_page_config(page_title="24點撲克牌大師 Pro", page_icon="♠️", layout="centered")

# ==========================================
# 核心邏輯區：尋找所有可行解
# ==========================================

def find_all_solutions(nums, target=24):
    """
    遞迴尋找所有不重複的運算式。
    使用 set 儲存以避免字串完全相同的重複解。
    """
    results = set()
    
    def backtrack(current_nums):
        if len(current_nums) == 1:
            if abs(current_nums[0]['val'] - target) < 1e-6:
                # 移除最外層不必要的括號
                expr = current_nums[0]['expr']
                if expr.startswith('(') and expr.endswith(')'):
                    expr = expr[1:-1]
                results.add(expr)
            return

        for i in range(len(current_nums)):
            for j in range(len(current_nums)):
                if i != j:
                    n1, n2 = current_nums[i], current_nums[j]
                    remaining = [current_nums[k] for k in range(len(current_nums)) if k != i and k != j]
                    
                    # 四則運算
                    ops = [(add, '+'), (sub, '-'), (mul, '*'), (truediv, '/')]
                    for op_func, op_symbol in ops:
                        if op_symbol == '/' and abs(n2['val']) < 1e-6: continue
                        
                        new_val = op_func(n1['val'], n2['val'])
                        new_expr = f"({n1['expr']} {op_symbol} {n2['expr']})"
                        backtrack(remaining + [{'val': new_val, 'expr': new_expr}])

    backtrack(nums)
    return sorted(list(results))

def deal_cards(num_cards=4):
    suits, ranks = ['♠️', '♥️', '♦️', '♣️'], ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    values = {'A': 1, 'J': 11, 'Q': 12, 'K': 13, **{str(i): i for i in range(2, 11)}}
    drawn = random.sample(list(itertools.product(suits, ranks)), num_cards)
    return [{'display': f"{s}{r}", 'value': values[r], 'rank': r} for s, r in drawn]

def parse_card_input(input_str):
    if not input_str: return None
    values = {'A': 1, '1': 1, 'J': 11, 'Q': 12, 'K': 13, **{str(i): i for i in range(2, 14)}}
    raw_items = input_str.strip().replace(',', ' ').split()
    parsed_nums = []
    for item in raw_items:
        key = item.upper()
        if key in values:
            val = float(values[key])
            parsed_nums.append({'val': val, 'expr': str(int(val))})
        else:
            try:
                val = float(item)
                parsed_nums.append({'val': val, 'expr': str(int(val) if val.is_integer() else val)})
            except: return None
    return parsed_nums

# ==========================================
# Session State 初始化
# ==========================================
init_states = {
    'game_active': False, 
    'current_cards': [], 
    'all_solutions': [], 
    'time_left': 0, 
    'reveal_answer': False,
    'difficulty_level': '普通'
}
for key, val in init_states.items():
    if key not in st.session_state: st.session_state[key] = val

# ==========================================
# 介面佈局
# ==========================================

st.title("🃏 撲克牌神算 24點 Pro")
tab1, tab2 = st.tabs(["🎮 挑戰模式", "🧮 解牌計算機"])

with tab1:
    with st.expander("⚙️ 遊戲設定", expanded=False):
        col_set1, col_set2 = st.columns(2)
        with col_set1:
            game_target = st.number_input("遊戲目標點數", value=24, step=1)
            game_cards_num = st.number_input("抽牌張數", value=4, min_value=2, max_value=5, step=1)
            diff_opt = st.selectbox("題目難度", ["容易 (15組解以上)", "普通 (10-15組解)", "困難 (4-9組解)", "SSS (3組解以內)"], index=1)
        with col_set2:
            game_time_s = st.number_input("倒數時間 (秒)", value=30, step=5)
            allow_no_sol = st.toggle("包含無解題目", value=False)
            show_hint = st.toggle("顯示牌面數字", value=True)

    def start_new_game():
        # 難度範圍定義
        diff_map = {
            "容易 (15組解以上)": (15, 999),
            "普通 (10-15組解)": (10, 14),
            "困難 (4-9組解)": (4, 9),
            "SSS (3組解以內)": (1, 3)
        }
        min_sols, max_sols = diff_map[diff_opt]
        
        attempt = 0
        while attempt < 100: # 防止無窮迴圈
            cards = deal_cards(game_cards_num)
            nums = [{'val': float(c['value']), 'expr': str(c['value'])} for c in cards]
            sols = find_all_solutions(nums, game_target)
            
            num_sols = len(sols)
            
            # 判斷邏輯：
            # 1. 如果允許無解且抽到無解
            if allow_no_sol and num_sols == 0:
                break
            # 2. 如果不允許無解，則必須符合難度區間
            if not allow_no_sol and (min_sols <= num_sols <= max_sols):
                break
            # 3. 如果允許無解但這次抽到有解，也要符合難度區間
            if allow_no_sol and num_sols > 0 and (min_sols <= num_sols <= max_sols):
                break
                
            attempt += 1

        st.session_state.current_cards = cards
        st.session_state.all_solutions = sols
        st.session_state.game_active = True
        st.session_state.time_left = game_time_s
        st.session_state.reveal_answer = False

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("發牌 / 開始", use_container_width=True, type="primary"):
            start_new_game()
            st.rerun()
    with col2:
        if st.button("👀 看解答", use_container_width=True, disabled=not st.session_state.game_active or st.session_state.reveal_answer):
            st.session_state.reveal_answer = True
            st.rerun()
    with col3:
        if st.button("跳過 / 重來", use_container_width=True):
            start_new_game()
            st.rerun()

    @st.fragment
    def game_render_loop():
        if st.session_state.game_active:
            st.divider()
            c_cols = st.columns(len(st.session_state.current_cards))
            for idx, card in enumerate(st.session_state.current_cards):
                with c_cols[idx]:
                    display_text = card['display']
                    if show_hint and card['rank'] in ['A', 'J', 'Q', 'K']:
                        display_text = f"{card['display']} <span style='font-size: 14px; color: gray;'>({card['value']})</span>"
                    st.markdown(f"""<div style="border: 2px solid #ddd; border-radius: 8px; padding: 15px; text-align: center; font-size: 20px; background: white; color: {'red' if card['display'][0] in ['♥️', '♦️'] else 'black'}; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">{display_text}</div>""", unsafe_allow_html=True)
            st.divider()

            timer_placeholder = st.empty()
            result_placeholder = st.empty()

            if st.session_state.reveal_answer or st.session_state.time_left <= 0:
                timer_placeholder.caption("🛑 狀態：已顯示解答")
                sols = st.session_state.all_solutions
                if not sols:
                    result_placeholder.warning("此局無解 😅")
                else:
                    with result_placeholder.container():
                        st.success(f"🎉 找到 {len(sols)} 組可行解答：")
                        # 使用 columns 或多行顯示所有解答
                        st.code("\n".join([f"{s} = {game_target}" for s in sols]), language="text")
                    # if st.session_state.reveal_answer: st.balloons()
            else:
                for i in range(st.session_state.time_left, -1, -1):
                    st.session_state.time_left = i
                    timer_placeholder.progress(i / game_time_s, text=f"⏳ 剩餘時間: {i}s")
                    if st.session_state.reveal_answer: break
                    time.sleep(1)
                if st.session_state.time_left == 0:
                    st.rerun()

    game_render_loop()

# ------------------------------------------
# 分頁 2: 解牌計算機
# ------------------------------------------
with tab2:
    st.markdown("### 🧮 全功能解牌器")
    st.caption("輸入牌面 (A, 2-10, J, Q, K)，系統將列出所有可能的組合")
    
    solver_target = st.number_input("目標點數", value=24, step=1, key="s_target_input")
    input_cols = st.columns(4)
    card_inputs = [input_cols[i].text_input(f"第 {i+1} 張", placeholder="A", key=f"card_{i}") for i in range(4)]

    if st.button("🚀 開始計算", type="primary", use_container_width=True):
        combined_input = " ".join([c for c in card_inputs if c.strip()])
        if not combined_input:
            st.warning("請至少輸入幾張牌！")
        else:
            parsed_cards = parse_card_input(combined_input)
            if parsed_cards is None: 
                st.error("輸入格式錯誤！")
            elif len(parsed_cards) < 2: 
                st.warning("請輸入至少兩張牌。")
            else:
                st.info(f"正在分析組合... 目標: {solver_target}")
                start_time = time.time()
                all_res = find_all_solutions(parsed_cards, solver_target)
                end_time = time.time()
                
                st.divider()
                if all_res:
                    st.success(f"### ✨ 找到 {len(all_res)} 組解答")
                    # 計算機模式不噴氣球，直接列出結果
                    st.code("\n".join([f"{r} = {solver_target}" for r in all_res]), language="text")
                else: 
                    st.error(f"### ❌ 這組牌型在目標為 {solver_target} 時無解")
                st.caption(f"計算耗時: {end_time - start_time:.4f} 秒")