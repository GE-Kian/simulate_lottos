# -*- coding: utf-8 -*-
"""
Created on Tue May 13 17:38:12 2025

@author: Kevin
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate

# Utility function to display DataFrames with right alignment
def display_dataframe_to_user(name: str, df: pd.DataFrame):
    print(f"\n=== {name} ===")
    colalign = ["center"] + ["right"] * (df.shape[1] - 1)
    print(tabulate(df, headers='keys', tablefmt='github', showindex=False, colalign=colalign))
    
def display_rtp_table_with_total(df, total):
    cols = df.columns.tolist()
    data = df.values.tolist()
    data.append([total[c] for c in cols])
    # col widths
    widths = [max(len(str(c)), *(len(str(row[i])) for row in data)) for i, c in enumerate(cols)]
    # header
    header = "| " + " | ".join(c.center(widths[i]) for i, c in enumerate(cols)) + " |"
    sep = "| " + " | ".join("-"*widths[i] for i in range(len(cols))) + " |"
    print(header)
    print(sep)
    for row in data[:-1]:
        line = "| " + " | ".join(str(row[i]).rjust(widths[i]) for i in range(len(cols))) + " |"
        print(line)
    print(sep)
    last = data[-1]
    print("| " + " | ".join(str(last[i]).rjust(widths[i]) for i in range(len(cols))) + " |")
    print(" ")

# === Demo Data with Two Theoretical Sets ===
tiers = ["1st", "2nd", "3rd", "4th", "5th"]
sim_probs   = [0.00000024, 	0.00004109, 	0.00180057, 	0.02721993, 	0.16841132]
theo1_probs = [0.0000001906, 0.0000411759, 0.0018014460, 0.0272218501, 0.1684351973]
theo2_probs = [0.0000001906, 0.0000411759, 0.0018014460, 0.0272218501, 0.1684351973]

sim_rtp   = [0.33245646, 	0.10272668, 	0.13504262, 	0.08165979, 	0.16841132]
theo1_rtp = [0.2859, 0.1029, 0.1351, 0.0817, 0.1684]
theo2_rtp = [0.2765, 0.1029, 0.1351, 0.0817, 0.1684]

# First Prize Analysis Demo Data
jackpot_amounts = np.array([
    32095481, 34013545, 34024011, 36094833, 36013653, 31998040, 33958257, 32030607, 
    42038281, 32024277, 31962837, 31921097, 37846265, 33944132, 37998847, 34047222, 
    36045444, 36179148, 34036904, 32015387, 32074715, 34046852, 32001836, 46180960, 
    42044656, 41956327, 32086075, 32008154, 34137163, 33978801, 33985385, 34084732, 
    32069196, 38072633, 44108366, 35978689, 33958739, 31920718

])
winners_per_round = np.array([
    1, 2, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 4, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1

])

# Simulation Parameters
params = {
    "num_rounds": 100,
    "players_range": "(190000, 210000)",
    "cards_per_player_range": "(9, 11)",
    "ticket_price": "20.0"
}

# 1. Prize Tier Probability Comparison
prob_df = pd.DataFrame({
    "Tier": tiers,
    "Simulated Probability": sim_probs,
    "Theoretical 1": theo1_probs,
    "Theoretical 2": theo2_probs
})
# Format as percentages with 8 decimal places
prob_df_pct = prob_df.copy()
for col in prob_df_pct.columns[1:]:
    prob_df_pct[col] = prob_df_pct[col].apply(lambda x: f"{x*100:.8f}%")
    
# Compute totals
total_sim = sum(sim_probs)
total_theo1 = sum(theo1_probs)
total_theo2 = sum(theo2_probs)
total_row = {
    "Tier": "total",
    "Simulated Probability": f"{total_sim*100:.8f}%",
    "Theoretical 1": f"{total_theo1*100:.8f}%",
    "Theoretical 2": f"{total_theo2*100:.8f}%"
}

print("=== Probability Comparison ===")
display_rtp_table_with_total(prob_df_pct, total_row)

# Plot probability comparison
x = np.arange(len(tiers))
width = 0.2
plt.figure(figsize=(6,4))
plt.bar(x-width, sim_probs, width=width, label="Simulated")
plt.bar(x,       theo1_probs, width=width, label="Theoretical 1")
plt.bar(x+width, theo2_probs, width=width, label="Theoretical 2")
plt.xticks(x, tiers)
plt.title("Prize Tier Probability Comparison")
plt.ylabel("Probability")
plt.legend()
plt.tight_layout()
plt.show()

# 2. RTP Comparison
rtp_df = pd.DataFrame({
    "Tier": tiers,
    "Simulated RTP": sim_rtp,
    "Theoretical 1 RTP": theo1_rtp,
    "Theoretical 2 RTP": theo2_rtp
})
# Format as percentages with 4 decimal places
rtp_df_pct = rtp_df.copy()
for col in rtp_df_pct.columns[1:]:
    rtp_df_pct[col] = rtp_df_pct[col].apply(lambda x: f"{x*100:.4f}%")
    
# Compute totals
total_sim = sum(sim_rtp)
total_theo1 = sum(theo1_rtp)
total_theo2 = sum(theo2_rtp)
total_row = {
    "Tier": "total",
    "Simulated RTP": f"{total_sim*100:.4f}%",
    "Theoretical 1 RTP": f"{total_theo1*100:.4f}%",
    "Theoretical 2 RTP": f"{total_theo2*100:.4f}%"
}

print("=== RTP Comparison ===")
display_rtp_table_with_total(rtp_df_pct, total_row)

plt.figure(figsize=(6,4))
plt.bar(x-width, sim_rtp, width=width, label="Simulated")
plt.bar(x,       theo1_rtp, width=width, label="Theoretical 1")
plt.bar(x+width, theo2_rtp, width=width, label="Theoretical 2")
plt.xticks(x, tiers)
plt.title("Prize Tier RTP Comparison")
plt.ylabel("RTP")
plt.legend()
plt.tight_layout()
plt.show()

# 3. First Prize Analysis
formatted_prize = f"{jackpot_amounts.mean():,.0f}"
formatted_winners = f"{winners_per_round.mean():.2f}"
stats_df = pd.DataFrame({
    "Metric": ["Average Jackpot Prize", "Average Winners per Round"],
    "Value": [formatted_prize, formatted_winners]
})
display_dataframe_to_user("First Prize Statistics", stats_df)

plt.figure(figsize=(6,4))
plt.hist(jackpot_amounts, bins=10)
plt.title("First Prize Amount Distribution (10 bins)")
plt.xlabel("Prize Amount")
plt.ylabel("Frequency")
plt.tight_layout()
plt.show()

plt.figure(figsize=(6,4))
plt.hist(winners_per_round, bins=range(winners_per_round.max()+2))
plt.title("Winners per Round Distribution")
plt.xlabel("Number of Winners")
plt.ylabel("Frequency")
plt.tight_layout()
plt.show()

# 4. Simulation Parameters
param_df = pd.DataFrame(params.items(), columns=["Parameter", "Value"])
display_dataframe_to_user("Simulation Parameters", param_df)

# 5. Funding Pool Shortfall per Round
# Manually input your actual shortfalls here
funding_pool_shortfalls = np.array([
   -25809038,-51621774,-47781948,-73863236,-69733926,-95686794,-91688102,-87544260,-113592092,-109414086,
   -105516954,-131520874,-157578564,-153604360,-179543146,-205447500,-201267998,-197456120,-193507992,-189430410,
   -185466584,-211418030,-237492356,-263650162,-289639982,-285829280,-281939068,-277957632,-303916546,-300069368,
   -326109160,-321984836,-318105342,-314071674,-340011836,-335977230,-362157894,-358015712,-353886342,-379783848,
   -375714204,-371528046,-397462050,-393454238,-419423464,-445274034,-471159868,-467180330,-493176658,-519011596,
   -515081968,-510923334,-507085208,-503161050,-499126308,-494975966,-490814738,-516945788,-512969930,-508955302,
   -504907198,-500781498,-496725426,-522658052,-518830176,-514962774,-511052102,-506986460,-502812772,-528640622,
   -554624314,-580537694,-576349988,-602418484,-598392386,-624295288,-620421616,-646304608,-642252152,-668113760,
   -694118254,-689931334,-685947918,-681968494,-708099698,-704130424,-700082900,-695921760,-691827882,-687725482,
   -683751762,-709743922,-705648802,-701794384,-727834042,-723876906,-750035470,-776223936,-772402072,-768448998
])


# Prepare table with thousand separators, no scientific notation
shortfall_table = pd.DataFrame({
    "Round": np.arange(1, 101),
    "Funding Pool Shortfall": [f"{v:,.0f}" for v in funding_pool_shortfalls]
})
display_dataframe_to_user("Funding Pool Shortfall per Round", shortfall_table)

# Plot shortfall chart using millions as unit, x-axis ticks every 10 rounds
shortfall_million = np.array(funding_pool_shortfalls) / 1e6
rounds = np.arange(1, 101)

plt.figure(figsize=(10, 4))
plt.bar(rounds, shortfall_million)
plt.title("Funding Pool Shortfall by Round")
plt.xlabel("Round Number")
plt.ylabel("Shortfall (Million)")
plt.xticks(np.arange(10, 101, 10))
plt.grid(axis='y', linestyle='--', linewidth=0.5, alpha=0.7)
plt.tight_layout()
plt.show()