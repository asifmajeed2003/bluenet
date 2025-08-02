import sqlite3

def populate_db():
    conn = sqlite3.connect('bluenet.db')
    cursor = conn.cursor()

    articles = [
        (
            "Fisheries Regulations in Kerala",
            "The Kerala Marine Fishing Regulation Act, 1980, governs fishing activities in the territorial waters of Kerala. It includes regulations on mesh size, fishing gear, and closed seasons to protect juvenile fish and ensure sustainable fishing.",
            "en"
        ),
        (
            "Safety at Sea",
            "Always wear a life jacket and carry a distress signaling kit. Check the weather forecast before you leave the shore. Make sure your boat is well-maintained and has all the necessary safety equipment.",
            "en"
        ),
        (
            "Cyclone Warning",
            "A cyclone warning has been issued for the coastal areas of Tamil Nadu. Fishermen are advised not to venture into the sea for the next 48 hours.",
            "en"
        )
    ]

    cursor.executemany("INSERT INTO articles (title, content, language) VALUES (?, ?, ?)", articles)
    conn.commit()
    conn.close()
    print("Database populated with sample data.")

if __name__ == '__main__':
    populate_db()
