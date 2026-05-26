"""
LEGIONGASPER v2.0 - Home Assistant Integration
Smart home control and automation
Coded by DEATH LEGION Team (DEMO X HEXA)
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import os
import requests

@dataclass
class Device:
    """Smart home device"""
    entity_id: str
    name: str
    domain: str  # light, switch, sensor, climate, etc.
    state: str
    attributes: Dict[str, Any]
    last_updated: str

class HomeAssistantClient:
    """Home Assistant API client"""
    
    def __init__(self, base_url: Optional[str] = None, 
                 token: Optional[str] = None):
        self.base_url = base_url or os.getenv("HA_URL", "http://homeassistant:8123")
        self.token = token or os.getenv("HA_TOKEN", "")
        self.connected = False
        self.session = requests.Session()
        
        if self.token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            })
    
    def connect(self) -> bool:
        """Connect to Home Assistant"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/",
                timeout=10
            )
            self.connected = response.status_code == 200
            return self.connected
        except Exception as e:
            print(f"HA connection error: {e}")
            return False
    
    def get_states(self) -> List[Device]:
        """Get all entity states"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/states",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return [
                    Device(
                        entity_id=d["entity_id"],
                        name=d["attributes"].get("friendly_name", d["entity_id"]),
                        domain=d["entity_id"].split(".")[0],
                        state=d["state"],
                        attributes=d["attributes"],
                        last_updated=d.get("last_updated", datetime.now().isoformat())
                    )
                    for d in data
                ]
            return []
        except Exception as e:
            print(f"Error getting states: {e}")
            return []
    
    def call_service(self, domain: str, service: str, 
                    entity_id: str, **kwargs) -> bool:
        """Call Home Assistant service"""
        try:
            payload = {
                "entity_id": entity_id,
                **kwargs
            }
            
            response = self.session.post(
                f"{self.base_url}/api/services/{domain}/{service}",
                json=payload,
                timeout=30
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"Service call error: {e}")
            return False
    
    def turn_on(self, entity_id: str, **kwargs) -> bool:
        """Turn on entity"""
        domain = entity_id.split(".")[0]
        return self.call_service(domain, "turn_on", entity_id, **kwargs)
    
    def turn_off(self, entity_id: str) -> bool:
        """Turn off entity"""
        domain = entity_id.split(".")[0]
        return self.call_service(domain, "turn_off", entity_id)
    
    def toggle(self, entity_id: str) -> bool:
        """Toggle entity"""
        domain = entity_id.split(".")[0]
        return self.call_service(domain, "toggle", entity_id)
    
    def set_temperature(self, entity_id: str, temperature: float) -> bool:
        """Set climate temperature"""
        return self.call_service(
            "climate", "set_temperature", entity_id,
            temperature=temperature
        )
    
    def get_device_by_room(self, room: str) -> List[Device]:
        """Get devices in room"""
        devices = self.get_states()
        return [
            d for d in devices
            if room.lower() in d.attributes.get("room", "").lower() or
               room.lower() in d.name.lower()
        ]
    
    def create_automation(self, name: str, trigger: Dict, 
                         action: Dict) -> bool:
        """Create automation"""
        try:
            payload = {
                "alias": name,
                "trigger": trigger,
                "action": action
            }
            
            response = self.session.post(
                f"{self.base_url}/api/config/automation/config/{name}",
                json=payload,
                timeout=30
            )
            
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"Automation error: {e}")
            return False

# Global client
_default_client = None

def get_client(url: Optional[str] = None, token: Optional[str] = None) -> HomeAssistantClient:
    """Get Home Assistant client"""
    global _default_client
    if _default_client is None:
        _default_client = HomeAssistantClient(url, token)
    return _default_client

def turn_on(entity_id: str, **kwargs) -> bool:
    """Turn on device"""
    return get_client().turn_on(entity_id, **kwargs)

def turn_off(entity_id: str) -> bool:
    """Turn off device"""
    return get_client().turn_off(entity_id)
