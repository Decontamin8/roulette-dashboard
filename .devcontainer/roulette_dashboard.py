import streamlit as st
import random
import pandas as pd

# --- Configuration ---
INITIAL_BANKROLL = 0
STOP_WIN        = 100
STOP_LOSS       = -200
MAX_BET         = 320
START_BET       = 5

# --- Page setup ---
st.set_page_config(page_title="Roulette Strategy Dashboard", layout="centered")
st.title("🌀 Live Roulette Strategy Tracker")
st.markdown("Follow your optimized Martingale + Streak-Pause strategy with real-time guidance.")

# --- Initialize session state ---
if "bankroll" not in st.session_state:
    st.session_state.bankroll         = INITIAL_BANKROLL
    st.session_state.loss_chain       = []
    st.session_state.current_bet      = START_BET
    st.session_state.target_color     = random.choice(["Red", "Black"])
    st.session_state.streak_buffer    = []
    st.session_state.in_streak_pause  = False
    st.session_state.previous_chain   = []
    st.session_state.spin_count       = 0
    st.session_state.log              = []
    st.session_state.session_complete = False

# --- Display summary metrics ---
next_bet   = st.session_state.current_bet
next_color = (st.session_state.streak_buffer[-1]
              if st.session_state.in_streak_pause
              else st.session_state.target_color)

col1, col2, col3 = st.columns(3)
col1.metric("Bankroll",      f"${st.session_state.bankroll}")
col2.metric("Next Bet",      f"${next_bet}")
col3.metric("Target Color",  next_color)

if st.session_state.bankroll >= STOP_WIN:
    st.success("🌟 Profit target reached! +$100")
    st.session_state.session_complete = True
elif st.session_state.bankroll <= STOP_LOSS:
    st.error("💀 Loss cap reached! -$200")
    st.session_state.session_complete = True

# --- Main input/logic ---
if not st.session_state.session_complete:
    st.subheader("Record Next Spin")
    result = st.radio("Spin result:", ["Red", "Black", "Green"])
    if st.button("Submit Spin"):
        st.session_state.spin_count += 1

        # 1) Update streak buffer
        sb = st.session_state.streak_buffer
        sb.append(result)
        if len(sb) > 3:
            sb.pop(0)

        # 2) Check for immediate 3-in-a-row streak
        if len(sb) == 3 and sb.count(sb[0]) == 3 and not st.session_state.in_streak_pause:
            # Trigger a pause-bet next
            st.session_state.in_streak_pause = True
            st.session_state.previous_chain   = st.session_state.loss_chain.copy()
            st.session_state.streak_color     = sb[0]
            # Log the *trigger* (no bankroll change yet)
            st.session_state.log.append({
                "Spin":         st.session_state.spin_count,
                "Result":       result,
                "Outcome":      "Streak-Pause Triggered",
                "Bankroll":     st.session_state.bankroll,
                "Next Bet":     START_BET,
                "Target Color": st.session_state.streak_color,
                "Context":      "3-in-a-row"
            })

        # 3) Execute either the pause-bet or normal Martingale
        if st.session_state.in_streak_pause:
            # place $5 on the streak color
            win = (result == st.session_state.streak_color)
            change = START_BET if win else -START_BET
            st.session_state.bankroll += change
            outcome_label = "Streak Win" if win else "Streak Loss"
            # restore or reset Martingale chain
            if win:
                st.session_state.loss_chain   = []
                st.session_state.current_bet  = START_BET
                st.session_state.target_color = random.choice(["Red", "Black"])
            else:
                st.session_state.loss_chain   = st.session_state.previous_chain.copy()
                nxt = sum(st.session_state.loss_chain) + START_BET if st.session_state.loss_chain else START_BET
                st.session_state.current_bet = min(nxt, MAX_BET)
            # clear streak-pause state & buffer
            st.session_state.in_streak_pause = False
            st.session_state.streak_buffer    = []
            st.session_state.log.append({
                "Spin":         st.session_state.spin_count,
                "Result":       result,
                "Outcome":      outcome_label,
                "Bankroll":     st.session_state.bankroll,
                "Next Bet":     st.session_state.current_bet,
                "Target Color": st.session_state.target_color,
                "Context":      "Streak-Pause Bet"
            })

        else:
            # Normal Martingale bet
            win = (result == st.session_state.target_color)
            if win:
                st.session_state.bankroll += st.session_state.current_bet
                st.session_state.loss_chain   = []
                st.session_state.current_bet  = START_BET
                st.session_state.target_color = random.choice(["Red", "Black"])
                outcome_label = "Martingale Win"
            else:
                st.session_state.bankroll -= st.session_state.current_bet
                st.session_state.loss_chain.append(st.session_state.current_bet)
                nxt = sum(st.session_state.loss_chain) + START_BET
                if nxt > MAX_BET:
                    # chain busted
                    st.session_state.loss_chain   = []
                    st.session_state.current_bet  = START_BET
                    st.session_state.target_color = random.choice(["Red", "Black"])
                    outcome_label = "Chain Busted"
                else:
                    st.session_state.current_bet = nxt
                    outcome_label              = "Martingale Loss"
            st.session_state.log.append({
                "Spin":         st.session_state.spin_count,
                "Result":       result,
                "Outcome":      outcome_label,
                "Bankroll":     st.session_state.bankroll,
                "Next Bet":     st.session_state.current_bet,
                "Target Color": st.session_state.target_color,
                "Context":      "Martingale"
            })

# --- Display log & reset ---
st.subheader("Session Log")
df = pd.DataFrame(st.session_state.log)
st.dataframe(df, use_container_width=True)

csv = df.to_csv(index=False).encode("utf-8")
st.download_button("📅 Download Session Log", data=csv,
                   file_name="roulette_session_log.csv", mime="text/csv")

if st.button("🔄 Reset Session"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.experimental_rerun()
