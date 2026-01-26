import os
import json

class ChatManager:
    def __init__(self, project_path):
        self.project_path = project_path
        self.storage_path = os.path.join(project_path, ".marvelcode", "chats.json")
        self.ensure_storage()
        self.chats = self.load_chats()

    def ensure_storage(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, "w") as f:
                json.dump({"active_chat_id": "default", "chats": {"default": {"name": "Default Chat", "history": []}}}, f)

    def load_chats(self):
        try:
            with open(self.storage_path, "r") as f:
                return json.load(f)
        except:
            return {"active_chat_id": "default", "chats": {"default": {"name": "Default Chat", "history": []}}}

    def save_chats(self):
        with open(self.storage_path, "w") as f:
            json.dump(self.chats, f, indent=4)

    def add_chat(self, chat_id, name):
        self.chats["chats"][chat_id] = {"name": name, "history": []}
        self.save_chats()

    def add_message(self, chat_id, sender, message):
        if chat_id in self.chats["chats"]:
            self.chats["chats"][chat_id]["history"].append({"sender": sender, "message": message})
            self.save_chats()

    def get_history(self, chat_id):
        return self.chats["chats"].get(chat_id, {}).get("history", [])

    def rename_chat(self, chat_id, new_name):
        if chat_id in self.chats["chats"]:
            self.chats["chats"][chat_id]["name"] = new_name
            self.save_chats()

    def delete_chat(self, chat_id):
        if chat_id in self.chats["chats"] and len(self.chats["chats"]) > 1:
            del self.chats["chats"][chat_id]
            if self.chats["active_chat_id"] == chat_id:
                self.chats["active_chat_id"] = list(self.chats["chats"].keys())[0]
            self.save_chats()
