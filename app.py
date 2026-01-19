import streamlit as st
import random
import time
import itertools
from operator import add, sub, mul, truediv

# --- 設定頁面資訊 ---
st.set_page_config(page_title="24點撲克牌挑戰", page_icon="♠️")

# --- 核心邏輯：24點計算求解器 ---
def solve_24(nums, target=24):
    """
    輸入數字列表，返回一個可行解的字串，若無解返回 None。
    這是一個遞迴解法，嘗試所有排列與運算符號。
    """
    if len(nums) == 1:
        # 允許極小的浮點數誤差
        if abs(nums[0]['val'] - target) < 1e-6:
            return nums[0]['expr']
        else:
            return None

    # 從列表中任取兩個數字進行運算
    for i in range(len(nums)):
        for j in range(len(nums)):
            if i != j:
                n1 = nums[i]
                n2 = nums[j]
                
                # 剩下的數字列表
                remaining = [nums[k] for k in range(len(nums)) if k != i and k != j]
                
                # 定義四則運算
                ops = [
                    (add, '+'), 
                    (sub, '-'), 
                    (mul, '*'), 
                    (truediv, '/')
                ]
                
                for op_func, op_symbol in ops:
                    # 避免除以零
                    if op_symbol == '/' and abs(n2['val']) < 1e-6:
                        continue
                        
                    # 運算並產生新的表達式
                    # 加括號是為了保證運算順序顯示正確，雖然有時候是多餘的
                    new_val = op_func(n1['val'], n2['val'])
                    new_expr = f"({n1['expr']} {op_symbol} {n2['expr']})"
                    
                    new_item = {'val': new_val, 'expr': new_expr}
                    
                    # 遞迴呼叫
                    res = solve_24(remaining + [new_item], target)
                    if res:
                        return res
    return None

# --- 輔助函式：發牌 ---
def deal_cards(num_cards=4):
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

# --- 初始化 Session State (狀態管理) ---
if 'game_active' not in st.session_state:
    st.session_state.game_active = False
if 'current_cards' not in st.session_state:
    st.session_state.current_cards = []
if 'solution' not in st.session_state:
    st.session_state.solution = None
if 'time_left' not in st.session_state:
    st.session_state.time_left = 0

# --- 側邊欄設定 ---
with st.sidebar:
    st.header("⚙️ 遊戲設定")
    target_y = st.number_input("目標點數 (Y)", value=24, step=1)
    cards_x = st.number_input("抽牌張數 (X)", value=4, min_value=2, max_value=6, step=1)
    time_s = st.number_input("倒數時間 (秒)", value=30, step=5)
    
    st.info("規則：使用加減乘除，每張牌必須使用且只能用一次。")

# --- 主畫面 ---
st.title(f"🃏 撲克牌神算：目標 {target_y}")

col1, col2 = st.columns([1, 1])

def start_new_game():
    st.session_state.current_cards = deal_cards(cards_x)
    st.session_state.game_active = True
    st.session_state.time_left = time_s
    st.session_state.solution = None # 重置答案
    
    # 預先計算答案，避免倒數結束才算，增加流暢度
    nums = [{'val': float(c['value']), 'expr': str(c['value'])} for c in st.session_state.current_cards]
    sol = solve_24(nums, target_y)
    st.session_state.solution = sol if sol else "無解 (請按跳過)"

with col1:
    if st.button("發牌 / 開始遊戲", use_container_width=True, type="primary"):
        start_new_game()

with col2:
    if st.button("跳過 / 重新發牌", use_container_width=True):
        start_new_game()

# --- 遊戲顯示區 ---
if st.session_state.game_active:
    st.divider()
    
    # 顯示撲克牌 (使用 Streamlit 的 metric 元件或 HTML 美化)
    cols = st.columns(len(st.session_state.current_cards))
    for idx, card in enumerate(st.session_state.current_cards):
        with cols[idx]:
            # 簡單的卡片樣式
            st.markdown(
                f"""
                <div style="
                    border: 2px solid #ccc; 
                    border-radius: 10px; 
                    padding: 20px; 
                    text-align: center; 
                    font-size: 24px;
                    background-color: white;
                    color: {'red' if card['display'][0] in ['♥️', '♦️'] else 'black'};
                ">
                    {card['display']}
                </div>
                """, 
                unsafe_allow_html=True
            )
            
    st.divider()
    
    # --- 倒數計時邏輯 ---
    timer_placeholder = st.empty()
    solution_placeholder = st.empty()
    
    # 這裡使用一個 Loop 來模擬倒數
    # 注意：Streamlit 的 Loop 會阻擋其他互動，但在簡單遊戲中是可以接受的
    if st.session_state.time_left > 0:
        for i in range(st.session_state.time_left, -1, -1):
            # 顯示進度條或文字
            progress = i / time_s
            timer_placeholder.progress(progress, text=f"⏳ 剩餘時間: {i} 秒")
            time.sleep(1)
            
            if i == 0:
                st.session_state.time_left = 0
                st.rerun() # 時間到，重新執行以顯示答案
                
    else:
        # 時間到 (time_left == 0)
        timer_placeholder.error("⏰ 時間到！")
        
        if st.session_state.solution:
            if st.session_state.solution == "無解 (請按跳過)":
                 solution_placeholder.warning(f"這組牌無解：{st.session_state.solution}")
            else:
                # 美化顯示答案，把原本的運算式稍微修整（去掉最外層括號）
                display_sol = st.session_state.solution
                if display_sol.startswith('(') and display_sol.endswith(')'):
                    display_sol = display_sol[1:-1]
                    
                solution_placeholder.success(f"🎉 可行解： {display_sol} = {target_y}")
                st.balloons()