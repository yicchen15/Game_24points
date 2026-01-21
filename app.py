import streamlit as st
import random
import time
import re
from operator import add, sub, mul, truediv
from streamlit_autorefresh import st_autorefresh

# --- 頁面設定 ---
st.set_page_config(page_title="24點撲克牌挑戰", page_icon="🃏", layout="centered")

# ==========================================
# 核心演算法 (Solver)
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
if 'is_exploded' not in st.session_state: st.session_state.is_exploded = False # 新增爆炸狀態

# ==========================================
# 側邊欄設定 (Restored & Improved)
# ==========================================
with st.sidebar:
    st.header("⚙️ 遊戲參數設定")
    
    # 這裡就是你要找回來的設定
    g_num = st.number_input("🎴 抽牌張數 (X)", value=4, min_value=2, max_value=6)
    g_target = st.number_input("🎯 目標點數 (Y)", value=24)
    g_time = st.number_input("⏳ 倒數時間 (秒)", value=30, step=5)
    
    st.divider()
    show_hint = st.toggle("顯示字母數值 (J=11...)", value=True)
    st.caption("規則：利用加減乘除，使用所有卡片算出目標點數。")

# ==========================================
# 主畫面邏輯
# ==========================================
st.title("🃏 24點撲克牌挑戰 ")

# 自動刷新組件 (只在遊戲進行中且未爆炸時刷新)
if st.session_state.is_playing and not st.session_state.is_exploded:
    st_autorefresh(interval=1000, key="gametimer")

# --- 頂部控制區 ---
c1, c2, c3 = st.columns(3)

def init_game():
    st.session_state.current_cards = deal_cards(g_num)
    st.session_state.start_time = time.time()
    st.session_state.formula = []
    st.session_state.msg = None
    st.session_state.reveal_answer = False
    st.session_state.is_playing = True
    st.session_state.is_exploded = False # 重置爆炸

if c1.button("🔥 發牌 / 開始", use_container_width=True, type="primary"):
    init_game()

if c2.button("🏳️ 投降看解答", use_container_width=True):
    st.session_state.reveal_answer = True
    st.session_state.is_playing = False

if c3.button("⏭️ 跳過 / 重來", use_container_width=True):
    init_game()

st.divider()

# ==========================================
# 計時與爆炸邏輯
# ==========================================
if st.session_state.start_time:
    # 計算時間
    elapsed = time.time() - st.session_state.start_time
    remaining = int(g_time - elapsed)

    # 狀態 1: 遊戲進行中
    if st.session_state.is_playing and not st.session_state.is_exploded:
        if remaining > 0:
            # 進度條顏色與文字
            timer_color = "green" if remaining > 10 else "red"
            st.markdown(f"<h3 style='text-align: center; color: {timer_color};'>⏳ 剩餘時間: {remaining} 秒</h3>", unsafe_allow_html=True)
        else:
            # 時間到 -> 觸發爆炸
            st.session_state.is_playing = False
            st.session_state.is_exploded = True
            st.rerun() # 強制重整以顯示爆炸畫面

    # 狀態 2: 爆炸了 (Time's Up)
    if st.session_state.is_exploded:
        st.error("💥 **BOOM! 時間到，任務失敗！** (卡片已保留，可繼續挑戰)")
        # st.markdown("""
        #     <div style='
        #         text-align: center; 
        #         padding: 10px; 
        #         background-color: #fff0f0; 
        #         border-radius: 8px; 
        #         border: 2px solid #ff4b4b; 
        #         margin-bottom: 5px;
        #     '>
        #         <div style='font-size: 32px; line-height: 1;'>💥 BOOM!</div>
        #         <div style='color: #cc0000; font-weight: bold; font-size: 18px; margin: 5px 0;'>時間到！任務失敗</div>
        #         <div style='font-size: 13px; color: #555; line-height: 1.2;'>卡片已保留，可繼續嘗試或查看解答。</div>
        #     </div>
        # """, unsafe_allow_html=True)

    # ==========================================
    # 遊戲操作區 (無論是否爆炸都保留顯示)
    # ==========================================
    
    # 1. 顯示卡片 (點擊加入算式)
    card_cols = st.columns(len(st.session_state.current_cards))
    for i, card in enumerate(st.session_state.current_cards):
        with card_cols[i]:
            label = card['display']
            if show_hint and card['rank'] in ['A', 'J', 'Q', 'K']:
                label += f"\n({card['value']})"
            
            # 使用 container width 讓按鈕填滿
            if st.button(label, key=f"c_{i}", use_container_width=True):
                st.session_state.formula.append(str(card['value']))
                st.rerun() # 點擊後刷新

    # 2. 符號按鈕 (修復 + - 顯示問題)
    st.write(" ") # 空行
    op_cols = st.columns([1, 1, 1, 1, 1, 1, 1.5, 1.5])
    
    # 使用 Emoji 作為符號，確保不會被切掉
    ops = [
        ("➕", "+"), ("➖", "-"), 
        ("✖️", "*"), ("➗", "/"), 
        ("(", "("), (")", ")")
    ]
    
    for i, (display_icon, math_symbol) in enumerate(ops):
        with op_cols[i]:
            if st.button(display_icon, key=f"op_{i}", use_container_width=True):
                st.session_state.formula.append(math_symbol)
                st.rerun()

    # 功能鍵：退格與清除
    if op_cols[6].button("⌫ 退格", use_container_width=True):
        if st.session_state.formula: st.session_state.formula.pop()
        st.rerun()
        
    if op_cols[7].button("🗑️ 重置", use_container_width=True):
        st.session_state.formula = []
        st.session_state.msg = None
        st.rerun()

    # 3. 算式顯示區
    current_f = "".join(st.session_state.formula)
    # 將算式中的 * 和 / 替換為好看的符號顯示
    display_f = current_f.replace("*", "×").replace("/", "÷")
    
    st.markdown(f"""
        <div style="
            background: #f8f9fa; 
            padding: 15px; 
            border-radius: 10px; 
            text-align: center; 
            font-size: 28px; 
            font-family: monospace; 
            font-weight: bold; 
            color: #333; 
            border: 2px dashed #ccc;
            margin-top: 10px;
            min-height: 60px;
        ">
            {display_f if display_f else "<span style='color:#aaa; font-size:20px;'>點擊上方卡片組合算式...</span>"}
        </div>
    """, unsafe_allow_html=True)

    # 4. 計算結果 (即使爆炸了也可以按，為了讓使用者驗證自己是否原本能算對)
    check_btn_text = "✅ 拆彈 (送出計算)" if not st.session_state.is_exploded else "🤔 試算看看 (已爆炸)"
    
    if st.button(check_btn_text, use_container_width=True, type="primary"):
        if not current_f:
            st.session_state.msg = ("warning", "算式是空的！")
        else:
            try:
                # 檢查數字使用狀況
                used_nums = re.findall(r'\d+', current_f)
                target_nums = [str(c['value']) for c in st.session_state.current_cards]
                
                # 簡單排序比對，確保數字數量與值一致
                if sorted(used_nums) != sorted(target_nums):
                    st.session_state.msg = ("error", "必須剛好使用牌面上的數字，且不能重複！")
                else:
                    # 執行運算
                    res = eval(current_f)
                    if abs(res - g_target) < 1e-6:
                        if st.session_state.is_exploded:
                            st.session_state.msg = ("info", "算對了！可惜時間已經到了...下次手腳快點！ 🐢")
                        else:
                            st.session_state.msg = ("success", "拆彈成功！答對了！ 🎉🎉🎉")
                            st.session_state.is_playing = False # 停止計時
                            st.balloons()
                    else:
                        st.session_state.msg = ("error", f"計算結果是 {res}，不是 {g_target} 喔！❌")
            except:
                st.session_state.msg = ("error", "算式格式錯誤 (檢查括號或運算符) 😵")

    # 5. 訊息回饋區
    if st.session_state.msg:
        m_type, m_txt = st.session_state.msg
        if m_type == "success": st.success(m_txt)
        elif m_type == "error": st.error(m_txt)
        elif m_type == "warning": st.warning(m_txt)
        elif m_type == "info": st.info(m_txt)

    # 6. 解答顯示 (只有在按了解答按鈕後才出現)
    if st.session_state.reveal_answer:
        st.divider()
        nums = [{'val': float(c['value']), 'expr': str(c['value'])} for c in st.session_state.current_cards]
        ans = solve_24(nums, g_target)
        if ans:
             # 美化解答字串
            pretty_ans = ans.replace("*", "×").replace("/", "÷")
            if pretty_ans.startswith('(') and pretty_ans.endswith(')'):
                pretty_ans = pretty_ans[1:-1]
            st.info(f"💡 參考解答： **{pretty_ans} = {g_target}**")
        else:
            st.warning("電腦表示：這題無解，你是對的！ 🤖")