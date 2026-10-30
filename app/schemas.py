# app/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional

class LoginRequest(BaseModel):
    username: str
    password: str

class ChangeAuthRequest(BaseModel):
    old_password: str
    new_username: str
    new_password: str

class ConnectionRequest(BaseModel):
    host: str
    key: str
    public_host: str = None
    user_name: str = None

class PreviewRequest(BaseModel):
    host: str
    key: str
    public_host: str = None
    user_name: str = None
    library_id: str
    config: dict
    image_data: str = None
    custom_assets: dict = None
    mode: str = "random"

class SuiteBackupRequest(BaseModel):
    host: str
    key: str
    public_host: str = None
    user_name: str = None
    suite_name: str

class SuiteRestoreRequest(BaseModel):
    host: str
    key: str
    public_host: str = None
    user_name: str = None
    suite_name: str
    target_ids: list = []

class SuiteContentRequest(BaseModel):
    suite_name: str

class EmbySearchRequest(BaseModel):
    host: str
    key: str
    public_host: str = None
    user_name: str = None
    query: str
    library_id: str = None
    type: str = "Primary"

class EmbyItemImagesRequest(BaseModel):
    host: str
    key: str
    public_host: str = None
    user_name: str = None
    item_id: str
    type: str = "Backdrop"

class EmbyRandomPoolRequest(BaseModel):
    host: str
    key: str
    public_host: str = None
    user_name: str = None
    library_id: str
    type: str = "Backdrop"
    limit: int = 50

class TaskTarget(BaseModel):
    host: str
    key: str
    public_host: str = None
    user_name: str = None
    library_id: str
    library_name: str = "Unknown"

class RunTaskRequest(BaseModel):
    preset_filename: str
    targets: list[TaskTarget]
    mode: str = "random"
    fallback_to_next_backdrop: bool = True

class CreateTaskRequest(BaseModel):
    name: str
    cron: str
    preset_filename: str
    targets: list[TaskTarget]
    mode: str = "random"
    fallback_to_next_backdrop: bool = True
    enabled: bool = True 

class UpdateTaskRequest(BaseModel):
    id: str
    name: str
    cron: str
    preset_filename: str
    targets: list[TaskTarget]
    mode: str = "random"
    fallback_to_next_backdrop: bool = True
    enabled: bool = True 

class RunSavedTaskRequest(BaseModel):
    id: str

class WebhookConfigModel(BaseModel):
    enabled: bool = False
    engine: str = "classic"
    preset: str = ""
    mode: str = "random"

class WechatNotifyConfigModel(BaseModel):
    enabled: bool = False
    name: str = "企微"
    channel_name: str = ""
    corp_id: str = ""
    app_secret: str = ""
    token: str = ""
    agent_id: str = ""
    proxy_url: str = ""
    encoding_aes_key: str = ""
    admin_whitelist: str = ""
    notify_types: dict = Field(default_factory=lambda: {
        "playback": True,
        "media_added": True,
        "task_complete": True
    })
    templates: dict = Field(default_factory=dict)

class ToggleTaskRequest(BaseModel):
    id: str
    enabled: bool
