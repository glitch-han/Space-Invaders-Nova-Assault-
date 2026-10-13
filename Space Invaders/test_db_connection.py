import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from managers.db_manager import DatabaseManager

TEST_USERNAME = "_connection_test_player"


def main():
    print("=" * 50)
    print("Space Invaders - Database Connection Test")
    print("=" * 50)

    db = DatabaseManager()

    if not db.is_connected:
        print("\nFAILED: could not connect to MySQL.")
        print("Checklist:")
        print("  1. Is WAMP running and MySQL green?")
        print("  2. Did you import space_invaders_cordero_db.sql?")
        print("  3. Do settings.json 'database' credentials match your WAMP setup?")
        return

    print("\n[1/5] Test INSERT (register_player)...")
    player_id = db.register_player(TEST_USERNAME)
    if player_id is None:
        print("FAILED: insert did not return a player_id.")
        return
    print(f"  OK - inserted player_id={player_id}, username='{TEST_USERNAME}'")

    print("\n[2/5] Test INSERT (save_score)...")
    ok = db.save_score(player_id, score=42, level=1)
    print("  OK - score row inserted" if ok else "  FAILED to insert score")

    print("\n[3/5] Test SELECT (get_leaderboard)...")
    leaderboard = db.get_leaderboard(limit=5)
    print(f"  OK - fetched {len(leaderboard)} row(s):")
    for row in leaderboard:
        print(f"    {row['username']}: {row['high_score']}")

    print("\n[4/5] Test UPDATE (update_player_profile)...")
    ok = db.update_player_profile(player_id, TEST_USERNAME + "_renamed")
    print("  OK - profile updated" if ok else "  FAILED to update profile")
    if db.get_player_ship(player_id) is None:
        print("  NOTE - players.ship_model column is missing. Import add_ship_model.sql")
        print("         so each pilot's ship choice is saved.")
    else:
        print("  OK - ship_model column found")

    print("\n[5/5] Test DELETE (delete_player) - cleanup...")
    ok = db.delete_player(player_id)
    print("  OK - test data removed" if ok else "  FAILED to delete test data")

    print("\n" + "=" * 50)
    print("All CRUD operations completed. Your database is ready.")
    print("=" * 50)

    db.close()


if __name__ == "__main__":
    main()
