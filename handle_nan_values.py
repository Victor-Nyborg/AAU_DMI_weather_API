# -*- coding: utf-8 -*-
"""
Created on Fri Oct 16 09:15:40 2026

@author: AC03LH
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# =============================================================================
# INPUTS
# =============================================================================
# filepath to dmi_file
file = r"Data_to_show\\test_data.csv"


### How to handle missing data
# 1: Interpolate
# 2: Fill with 0
# 3: Fill with specific number
missing_data = 1
fill_missing_data_value = 10 # only relevant if missing_data = 3

# =============================================================================
# The script - PLEASE DO NOT TOUCH
# =============================================================================
def CSV(file):
    df = pd.read_csv(file)
    return df

def EXCEL(file):
    df = pd.read_excel(file)
    return df


# Load data
filename = file.split("\\")[-1]
ftype = file[file.find("."):]
print("Loaded file:", filename)
print("Loaded fileformat:", ftype)
if ftype == ".csv":
    df = CSV(file)
elif ftype == ".xlsx":
    df = EXCEL(file)


# Reformat data
df["timestamp"] = (
    pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S%z", utc=True)
    .dt.tz_convert("europe/copenhagen")
    )
df.set_index("timestamp", inplace=True)


### Check data quality
# Check data
cols = df.columns.tolist()
fig, axes = plt.subplots(nrows=len(df.columns), sharex=True, figsize=(16,10),
                         gridspec_kw={"right": 0.98,
                                      "left": 0.1,
                                      "top": 0.95,
                                      "bottom": 0.07})
for i, col in enumerate(cols):
    axes[i].scatter(df.index, df[col], s=4)
    axes[i].set_ylabel(col, rotation=0, labelpad=20, ha="right")
    axes[i].grid(True, alpha=0.3)
fig.suptitle("Raw data")


# Check amount of missing data
fig, ax = plt.subplots(gridspec_kw={"right": 0.98,
                                    "left": 0.13,
                                    "top": 0.93,
                                    "bottom": 0.3}
                       )
ax.bar(np.arange(len(cols)), df.isna().sum()/len(df))
ax.set_xticks(np.arange(len(cols)))
ax.set_xticklabels(cols, rotation=35, ha="right")
ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1.0))
ax.grid(True, alpha=0.3, axis="y")
fig.suptitle('Amount of missing data')

if missing_data == 1:
    final = df.interpolate(limit_direction="both")
elif missing_data == 2:
    final = df.fillna(0)
elif missing_data == 3:
    final = df.fillna(fill_missing_data_value)

# Check final data
fig, axes = plt.subplots(nrows=len(final.columns), sharex=True, figsize=(16,10),
                         gridspec_kw={"right": 0.98,
                                      "left": 0.1,
                                      "top": 0.95,
                                      "bottom": 0.07})
for i, col in enumerate(cols):
    axes[i].scatter(final.index, final[col], s=4)
    axes[i].set_ylabel(col, rotation=0, labelpad=20, ha="right")
    axes[i].grid(True, alpha=0.3)
fig.suptitle("Treated data")

# Check amount of missing data
fig, ax = plt.subplots(gridspec_kw={"right": 0.98,
                                    "left": 0.13,
                                    "top": 0.93,
                                    "bottom": 0.3}
                       )
ax.bar(np.arange(len(cols)), final.isna().sum()/len(final))
ax.set_xticks(np.arange(len(cols)))
ax.set_xticklabels(cols, rotation=35, ha="right")
ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1.0))
ax.grid(True, alpha=0.3, axis="y")
fig.suptitle('Amount of missing data in final data')

path = "\\".join(file.split("\\")[:-1]) + "final_data.xlsx"
final.index = final.index.strftime("%Y-%m-%d %H:%M:%S")
final.to_excel(path)