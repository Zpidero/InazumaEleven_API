from app.scraper import build_players_df, save_players_csv

if __name__ == "__main__":
    print("🚀 Starting update...\n")
    df = build_players_df()
    save_players_csv(df)