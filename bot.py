import os
import sqlite3
import json
import requests
from datetime import datetime
from langdetect import detect
import config

# Endpoint for sending the POST request
post_url = 'http://localhost:8080/v2/send'
registered_number = config.registered_number
recipient_number = config.recipient_number

def get_largest_update_id(db_name):
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        query = '''
        SELECT MAX(update_id) FROM updates
        '''

        cursor.execute(query)
        result = cursor.fetchone()
        
        if result and result[0] is not None:
            return result[0]
        else:
            return 0  # Default value if no update_id is found

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return None

    finally:
        if conn:
            conn.close()

def check_and_create_db(db_name):
    if not os.path.exists(db_name):
        try:
            conn = sqlite3.connect(db_name)
            print(f"Database '{db_name}' created successfully.")
            create_table_queries = [
                '''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    is_bot BOOLEAN,
                    first_name TEXT,
                    last_name TEXT,
                    username TEXT,
                    language_code TEXT
                );
                ''',
                '''
                CREATE TABLE IF NOT EXISTS chats (
                    chat_id INTEGER PRIMARY KEY,
                    title TEXT,
                    type TEXT,
                    all_members_are_administrators BOOLEAN
                );
                ''',
                '''
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY,
                    from_user_id INTEGER,
                    chat_id INTEGER,
                    date INTEGER,
                    text TEXT,
                    message_language TEXT,
                    caption TEXT,
                    caption_entities TEXT,
                    forward_origin_type TEXT,
                    forward_from_user_id INTEGER,
                    forward_from_chat_id INTEGER,
                    forward_from_message_id INTEGER,
                    forward_signature TEXT,
                    forward_date INTEGER,
                    video_duration INTEGER,
                    video_width INTEGER,
                    video_height INTEGER,
                    video_file_name TEXT,
                    video_mime_type TEXT,
                    video_thumbnail_file_id TEXT,
                    video_file_id TEXT,
                    video_file_unique_id TEXT,
                    video_file_size INTEGER,
                    FOREIGN KEY (from_user_id) REFERENCES users(user_id),
                    FOREIGN KEY (chat_id) REFERENCES chats(chat_id),
                    FOREIGN KEY (forward_from_user_id) REFERENCES users(user_id),
                    FOREIGN KEY (forward_from_chat_id) REFERENCES chats(chat_id)
                );
                ''',
                '''
                CREATE TABLE IF NOT EXISTS updates (
                    update_id INTEGER PRIMARY KEY,
                    message_id INTEGER,
                    FOREIGN KEY (message_id) REFERENCES messages(message_id)
                );
                '''
                # '''
                # CREATE TABLE IF NOT EXISTS entities (
                #     entity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                #     message_id INTEGER,
                #     offset INTEGER,
                #     length INTEGER,
                #     type TEXT,
                #     url TEXT,
                #     FOREIGN KEY (message_id) REFERENCES messages(message_id)
                # );
                # ''',
                # '''
                # CREATE TABLE IF NOT EXISTS photos (
                #     photo_id INTEGER PRIMARY KEY AUTOINCREMENT,
                #     message_id INTEGER,
                #     file_id TEXT,
                #     file_unique_id TEXT,
                #     file_size INTEGER,
                #     width INTEGER,
                #     height INTEGER,
                #     FOREIGN KEY (message_id) REFERENCES messages(message_id)
                # );
                # '''
            ]
            
            for query in create_table_queries:
                conn.execute(query)
            print("Tables created successfully.")

        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
        
        finally:
            if conn:
                conn.close()
    else:
        print(f"Database '{db_name}' already exists.")

def extract_details(json_data):
    users = []
    chats = []
    messages = []
    # entities = []
    updates = []
    # photos = []

    for update in json_data.get("result", []):
        update_id = update.get("update_id")
        message = update.get("message")
        
        if message:
            message_id = message.get("message_id")
            from_user = message.get("from")
            chat = message.get("chat")
            date = message.get("date")
            text = message.get("text")
            message_language = detect(text) if text else 'unknown'
            caption = message.get("caption")
            caption_entities = json.dumps(message.get("caption_entities", []))
            forward_origin_type = message.get("forward_from_chat", {}).get("type")
            forward_from_user_id = message.get("forward_from", {}).get("id")
            forward_from_chat_id = message.get("forward_from_chat", {}).get("id")
            forward_from_message_id = message.get("forward_from_message_id")
            forward_signature = message.get("forward_signature")
            forward_date = message.get("forward_date")
            video_duration = message.get("video", {}).get("duration")
            video_width = message.get("video", {}).get("width")
            video_height = message.get("video", {}).get("height")
            video_file_name = message.get("video", {}).get("file_name")
            video_mime_type = message.get("video", {}).get("mime_type")
            video_thumbnail_file_id = message.get("video", {}).get("thumb", {}).get("file_id")
            video_file_id = message.get("video", {}).get("file_id")
            video_file_unique_id = message.get("video", {}).get("file_unique_id")
            video_file_size = message.get("video", {}).get("file_size")
            # entities_list = message.get("entities", [])
            # photo_list = message.get("photo", [])

            if from_user:
                users.append((
                    from_user.get("id"),
                    from_user.get("is_bot"),
                    from_user.get("first_name"),
                    from_user.get("last_name"),
                    from_user.get("username"),
                    from_user.get("language_code")
                ))
            
            if chat:
                chats.append((
                    chat.get("id"),
                    chat.get("title"),
                    chat.get("type"),
                    chat.get("all_members_are_administrators")
                ))
            
            messages.append((
                message_id,
                from_user.get("id") if from_user else None,
                chat.get("id") if chat else None,
                date,
                text,
                message_language,
                caption,
                caption_entities,
                forward_origin_type,
                forward_from_user_id,
                forward_from_chat_id,
                forward_from_message_id,
                forward_signature,
                forward_date,
                video_duration,
                video_width,
                video_height,
                video_file_name,
                video_mime_type,
                video_thumbnail_file_id,
                video_file_id,
                video_file_unique_id,
                video_file_size
            ))
            
            # for entity in entities_list:
            #     entities.append((
            #         None,
            #         message_id,
            #         entity.get("offset"),
            #         entity.get("length"),
            #         entity.get("type"),
            #         entity.get("url")
            #     ))
            
            # for photo in photo_list:
            #     photos.append((
            #         None,
            #         message_id,
            #         photo.get("file_id"),
            #         photo.get("file_unique_id"),
            #         photo.get("file_size"),
            #         photo.get("width"),
            #         photo.get("height")
            #     ))
            
            updates.append((
                update_id,
                message_id
            ))
    
    return {
        "users": users,
        "chats": chats,
        "messages": messages,
        # "entities": entities,
        "updates": updates
        # "photos": photos
    }

def insert_data_into_db(db_name, data):
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        user_query = '''
        INSERT OR IGNORE INTO users (user_id, is_bot, first_name, last_name, username, language_code) 
        VALUES (?, ?, ?, ?, ?, ?)
        '''
        chat_query = '''
        INSERT OR IGNORE INTO chats (chat_id, title, type, all_members_are_administrators) 
        VALUES (?, ?, ?, ?)
        '''
        message_query = '''
        INSERT OR IGNORE INTO messages (message_id, from_user_id, chat_id, date, text, message_language, caption, caption_entities, forward_origin_type, forward_from_user_id, forward_from_chat_id, forward_from_message_id, forward_signature, forward_date, video_duration, video_width, video_height, video_file_name, video_mime_type, video_thumbnail_file_id, video_file_id, video_file_unique_id, video_file_size) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        # entity_query = '''
        # INSERT OR IGNORE INTO entities (entity_id, message_id, offset, length, type, url) 
        # VALUES (?, ?, ?, ?, ?, ?)
        # '''
        update_query = '''
        INSERT OR IGNORE INTO updates (update_id, message_id) 
        VALUES (?, ?)
        '''
        # photo_query = '''
        # INSERT OR IGNORE INTO photos (photo_id, message_id, file_id, file_unique_id, file_size, width, height) 
        # VALUES (?, ?, ?, ?, ?, ?, ?)
        # '''
        cursor.executemany(user_query, data["users"])
        cursor.executemany(chat_query, data["chats"])
        cursor.executemany(message_query, data["messages"])
        # cursor.executemany(entity_query, data["entities"])
        cursor.executemany(update_query, data["updates"])
        # cursor.executemany(photo_query, data["photos"])
        conn.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

# Define the database file name
database_file = 'telegram.db'

# Call the function to check and create the database
check_and_create_db(database_file)

# Get the largest update_id
largest_update_id = get_largest_update_id(database_file)

# Set up the base URL for the Telegram API with the token from config
baseURL = f"https://api.telegram.org/bot{config.token_API}/getUpdates?offset={largest_update_id + 1}"

# Send the GET request to the Telegram API
resp = requests.get(baseURL)

# Parse the JSON response
data = resp.json()

# Extract details from JSON
extracted_data = extract_details(data)

# Insert data into SQLite database
insert_data_into_db(database_file, extracted_data)

# Print new updates
if extracted_data["updates"]:
    for update in extracted_data["updates"]:
        update_id = update[0]
        message_id = update[1]
        conn = sqlite3.connect(database_file)
        cursor = conn.cursor()
        cursor.execute("SELECT date, text, message_language FROM messages WHERE message_id = ?", (message_id,))
        result = cursor.fetchone()
        if result:
            # date, text = result
            date, text, message_language = result
            post_data = {
                # "message": f"Update ID: {update_id}, Date: {datetime.fromtimestamp(date)}, Text: {text}",
                "message": f"Update ID: {update_id}, Date: {datetime.fromtimestamp(date)}, Language: {message_language}, Text: {text}",
                "number": registered_number,
                "recipients": [recipient_number]
            }
            post_data_json = json.dumps(post_data, ensure_ascii=False).encode('utf-8')
            post_resp = requests.post(post_url, headers={"Content-Type": "application/json"}, data=post_data_json)
        conn.close()
else:
    print("No new updates found.")