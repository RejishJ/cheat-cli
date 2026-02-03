#!/usr/bin/env python3

import sys
import shutil
from pathlib import Path

import pandas as pd
from tabulate import tabulate
from importlib.resources import files

# ===============================
# Paths & Data Handling
# ===============================

def user_data_path() -> Path:
    """
    Location for user-modifiable data.
    """
    return Path.home() / ".local" / "share" / "cheat-cli" / "commands.csv"


def packaged_csv_path():
    """
    Read-only CSV shipped inside the package.
    """
    return files("cheat_cli").joinpath("data/commands.csv")


def ensure_user_csv_exists() -> Path:
    """
    Ensure user CSV exists by copying from packaged CSV on first run.
    """
    path = user_data_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        shutil.copy(packaged_csv_path(), path)

    return path


def load_df() -> pd.DataFrame:
    return pd.read_csv(ensure_user_csv_exists())


def save_df(df: pd.DataFrame):
    df.to_csv(user_data_path(), index=False)


# ===============================
# Output Helpers
# ===============================

def print_table(df: pd.DataFrame):
    if df.empty:
        print("\033[91mNo results found.\033[0m")
        return

    print(tabulate(df, headers="keys", tablefmt="fancy_grid", showindex=False))


# ===============================
# Core Features
# ===============================

def search(df: pd.DataFrame, term: str):
    term = term.lower()
    mask = (
        df["tool"].str.lower().str.contains(term) |
        df["command"].str.lower().str.contains(term) |
        df["description"].str.lower().str.contains(term) |
        df["tags"].str.lower().str.contains(term)
    )
    print_table(df[mask])


def add_interactive(df: pd.DataFrame):
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


def delete_command(df: pd.DataFrame, query: str):
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


# ===============================
# Entry Point
# ===============================

def main():
    df = load_df()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  cheat <search-term>")
        print("  cheat add")
        print("  cheat delete <query>")
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


if __name__ == "__main__":
    main()
