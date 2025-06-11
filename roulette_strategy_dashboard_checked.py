
import streamlit as st
import random
import pandas as pd

st.set_page_config(page_title="Roulette Strategy Dashboard", layout="centered")
st.title("🎰 Live Roulette Strategy Tracker")
st.markdown("Follow your optimized Martingale strategy with real-time guidance.")

# Initialize state
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 0
    st.session_state.loss_chain = []
    st.session_state.current_bet = 5
    st.session_state.target_color = random.choice(["Red", "Black"])
    st.session_state.spin_history = []
    st.session_state.spin_count = 0
    st.session_state.log = []
    st.session_state.in_streak_pause = False
    st.session_state.streak_color = None
    st.session_state.session_complete = False
    st.session_state.busted_chains = 0
    st.session_state.total_wins = 0
    st.session_state.total_losses = 0
    st.session_state.strategy_context = "Normal"

next_bet = 5 if not st.session_state.loss_chain else sum(st.session_state.loss_chain) + 5
next_color = st.session_state.target_color

# Session metrics
st.subheader("Session Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Bankroll", f"${st.session_state.bankroll}")
col2.metric("Next Bet", f"${next_bet} ({'Fresh' if not st.session_state.loss_chain else 'Recovery'})")
col3.metric("Target Color", next_color)

if st.session_state.bankroll >= 100:
    st.success("🎯 Profit target reached! +$100")
    st.session_state.session_complete = True
elif st.session_state.bankroll <= -200:
    st.error("💀 Loss cap reached! -$200")
    st.session_state.session_complete = True

if not st.session_state.session_complete:
    st.subheader("Enter Spin Result")
    result = st.radio("What was the result of the spin?", ["Red", "Black", "Green"])
    outcome = st.radio("Did you win or lose this spin?", ["Win", "Loss"])

    if st.button("Submit Spin"):
        st.session_state.spin_count += 1
        st.session_state.spin_history.append(result)
        if len(st.session_state.spin_history) > 3:
            st.session_state.spin_history.pop(0)

        if st.session_state.in_streak_pause:
            if result == st.session_state.streak_color:
                st.session_state.bankroll += 5
            else:
                st.session_state.bankroll -= 5
            st.session_state.in_streak_pause = False
            st.session_state.loss_chain = []
            st.session_state.current_bet = 5
            st.session_state.target_color = random.choice(["Red", "Black"])
        else:
            if len(st.session_state.spin_history) == 3 and all(x == st.session_state.spin_history[0] for x in st.session_state.spin_history):
                st.session_state.in_streak_pause = True
                st.session_state.streak_color = st.session_state.spin_history[0]
            else:
                if outcome == "Win":
                    st.session_state.bankroll += st.session_state.current_bet
                    st.session_state.loss_chain = []
                    st.session_state.current_bet = 5
                    st.session_state.target_color = random.choice(["Red", "Black"])
                elif outcome == "Loss":
                    st.session_state.bankroll -= st.session_state.current_bet
                    st.session_state.loss_chain.append(st.session_state.current_bet)
                    next_bet = sum(st.session_state.loss_chain) + 5
                    if next_bet > 320:
                        st.session_state.busted_chains += 1
                        st.session_state.loss_chain = []
                        st.session_state.current_bet = 5
                        st.session_state.target_color = random.choice(["Red", "Black"])
                    else:
                        st.session_state.current_bet = next_bet

        st.session_state.log.append({
            "Spin": st.session_state.spin_count,
            "Result": result,
            "Outcome": outcome,
            "Bankroll": st.session_state.bankroll,
            "Next Bet": st.session_state.current_bet,
            "Target Color": st.session_state.target_color
        })

st.subheader("Spin History")
df_log = pd.DataFrame(st.session_state.log)
st.dataframe(df_log, use_container_width=True)
