#!/usr/bin/env python3

import sys
import pandas as pd
from tabulate import tabulate
from importlib.resources import files

# ---------- Helpers ----------

def get_csv_path():
    return files("cheat_cli").joinpath("data/commands.csv")

def csv_path():
    return files("cheat_cli").joinpath("data/commands.csv")

def load_df():
    return pd.read_csv(csv_path())

def save_df(df):
    df.to_csv(csv_path(), index=False)

def print_table(df):
    if df.empty:
        print("\033[91mNo results found.\033[0m")
        return
    print(tabulate(df, headers="keys", tablefmt="fancy_grid", showindex=False))

# ---------- Core Features ----------

def search(df, term):
    term = term.lower()
    mask = (
        df["tool"].str.lower().str.contains(term) |
        df["command"].str.lower().str.contains(term) |
        df["description"].str.lower().str.contains(term) |
        df["tags"].str.lower().str.contains(term)
    )
    print_table(df[mask])

def add_interactive(df):
    print("\033[94mInteractive add mode\033[0m")
    tool = input("Tool: ").strip()
    command = input("Command: ").strip()
    description = input("Description: ").strip()
    tags = input("Tags: ").strip()

    if not df[df["command"] == command].empty:
        print("\033[91m❌ Command already exists.\033[0m")
        return

    df.loc[len(df)] = [tool, command, description, tags]
    save_df(df)
    print("\033[92m✅ Command added.\033[0m")

def delete_command(df, query):
    matches = df[df["command"].str.contains(query, case=False)]
    if matches.empty:
        print("\033[91mNo match found.\033[0m")
        return

    print_table(matches)
    confirm = input("Delete these entries? (yes/no): ").lower()
    if confirm != "yes":
        print("Cancelled.")
        return

    df.drop(matches.index, inplace=True)
    save_df(df)
    print("\033[92m✅ Deleted.\033[0m")

# ---------- Entry Point ----------

def main():
    df = load_df()

    if len(sys.argv) < 2:
        print("Usage: cheat <search> | cheat add | cheat delete <query>")
        return

    cmd = sys.argv[1]

    if cmd == "add":
        add_interactive(df)
    elif cmd == "delete":
        if len(sys.argv) < 3:
            print("Usage: cheat delete <query>")
            return
        delete_command(df, sys.argv[2])
    else:
        search(df, cmd)