import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

class WorkflowEngine:
    def __init__(self):
        self.workflows = {}
        self.current_workflow = None
        self.step_results = []
        
        # Pre-built workflows
        self._register_default_workflows()
    
    def _register_default_workflows(self):
        self.workflows['instagram_post'] = {
            'name': 'Instagram Post Photo',
            'steps': [
                {'action': 'launch_app', 'package': 'com.instagram.android'},
                {'action': 'wait', 'seconds': 3},
                {'action': 'tap_text', 'text': 'Create'},
                {'action': 'tap_text', 'text': 'Post'},
                {'action': 'tap_text', 'text': 'Gallery'},
                {'action': 'tap_element', 'index': 0},
                {'action': 'tap_text', 'text': 'Next'},
                {'action': 'input_text', 'field': 'caption', 'text': '{caption}'},
                {'action': 'tap_text', 'text': 'Share'}
            ]
        }
        
        self.workflows['instagram_like'] = {
            'name': 'Instagram Like Post',
            'steps': [
                {'action': 'launch_app', 'package': 'com.instagram.android'},
                {'action': 'wait', 'seconds': 2},
                {'action': 'tap_element', 'resource_id': 'like_button'},
            ]
        }
        
        self.workflows['instagram_follow'] = {
            'name': 'Instagram Follow User',
            'steps': [
                {'action': 'launch_app', 'package': 'com.instagram.android'},
                {'action': 'tap_text', 'text': 'Search'},
                {'action': 'input_text', 'field': 'search', 'text': '{username}'},
                {'action': 'tap_text', 'text': '{username}'},
                {'action': 'tap_text', 'text': 'Follow'},
            ]
        }
        
        self.workflows['tiktok_upload'] = {
            'name': 'TikTok Upload Video',
            'steps': [
                {'action': 'launch_app', 'package': 'com.zhiliaoapp.musically'},
                {'action': 'wait', 'seconds': 3},
                {'action': 'tap_text', 'text': '+'},
                {'action': 'tap_text', 'text': 'Upload'},
                {'action': 'tap_element', 'index': 0},
                {'action': 'tap_text', 'text': 'Next'},
                {'action': 'input_text', 'field': 'caption', 'text': '{caption}'},
                {'action': 'tap_text', 'text': 'Post'}
            ]
        }
        
        self.workflows['tiktok_scroll'] = {
            'name': 'TikTok Scroll Feed',
            'steps': [
                {'action': 'launch_app', 'package': 'com.zhiliaoapp.musically'},
                {'action': 'wait', 'seconds': 2},
                {'action': 'swipe', 'direction': 'up', 'count': '{scroll_count}'},
            ]
        }
        
        self.workflows['youtube_search'] = {
            'name': 'YouTube Search',
            'steps': [
                {'action': 'launch_app', 'package': 'com.google.android.youtube'},
                {'action': 'wait', 'seconds': 2},
                {'action': 'tap_text', 'text': 'Search'},
                {'action': 'input_text', 'field': 'search', 'text': '{query}'},
                {'action': 'press_key', 'keycode': 66},
            ]
        }
        
        self.workflows['youtube_subscribe'] = {
            'name': 'YouTube Subscribe',
            'steps': [
                {'action': 'launch_app', 'package': 'com.google.android.youtube'},
                {'action': 'wait', 'seconds': 2},
                {'action': 'tap_text', 'text': 'Subscribe'},
            ]
        }
        
        self.workflows['youtube_comment'] = {
            'name': 'YouTube Comment',
            'steps': [
                {'action': 'launch_app', 'package': 'com.google.android.youtube'},
                {'action': 'wait', 'seconds': 2},
                {'action': 'tap_text', 'text': 'Comments'},
                {'action': 'tap_text', 'text': 'Add a comment'},
                {'action': 'input_text', 'field': 'comment', 'text': '{comment}'},
                {'action': 'tap_text', 'text': 'Comment'},
            ]
        }
        
        self.workflows['banking_check_balance'] = {
            'name': 'Banking Check Balance',
            'steps': [
                {'action': 'launch_app', 'package': '{bank_package}'},
                {'action': 'wait', 'seconds': 3},
                {'action': 'authenticate'},
                {'action': 'tap_text', 'text': 'Accounts'},
                {'action': 'extract_text', 'region': 'balance_area'},
            ]
        }
        
        self.workflows['game_tap_play'] = {
            'name': 'Game Tap to Play',
            'steps': [
                {'action': 'launch_app', 'package': '{game_package}'},
                {'action': 'wait', 'seconds': 5},
                {'action': 'tap_coordinates', 'x': '{tap_x}', 'y': '{tap_y}'},
            ]
        }
    
    def load_workflow(self, workflow_id: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if workflow_id not in self.workflows:
            return {"success": False, "error": f"Workflow '{workflow_id}' not found"}
        
        workflow = self.workflows[workflow_id].copy()
        workflow['id'] = workflow_id
        
        # Replace variables in steps
        if variables:
            for step in workflow['steps']:
                for key, value in step.items():
                    if isinstance(value, str) and '{' in value:
                        for var_name, var_value in variables.items():
                            value = value.replace(f'{{{var_name}}}', str(var_value))
                        step[key] = value
        
        self.current_workflow = workflow
        self.step_results = []
        
        return {"success": True, "workflow": workflow}
    
    async def execute_step(self, step: Dict[str, Any], serial: str, 
                          app_controller=None, gesture_engine=None) -> Dict[str, Any]:
        action = step.get('action')
        
        try:
            if action == 'launch_app':
                if app_controller:
                    return await app_controller.launch_app(serial, step['package'])
                return {"success": False, "error": "App controller not available"}
            
            elif action == 'wait':
                await asyncio.sleep(step.get('seconds', 1))
                return {"success": True, "action": "wait"}
            
            elif action == 'tap_text':
                if app_controller:
                    return await app_controller.tap_element(serial, text=step['text'])
                return {"success": False, "error": "App controller not available"}
            
            elif action == 'tap_element':
                if app_controller:
                    if 'resource_id' in step:
                        return await app_controller.tap_element(serial, resource_id=step['resource_id'])
                    elif 'index' in step:
                        # Get UI hierarchy and tap by index
                        hierarchy = await app_controller.get_ui_hierarchy(serial)
                        if hierarchy['success'] and len(hierarchy['elements']) > step['index']:
                            elem = hierarchy['elements'][step['index']]
                            # Parse bounds and tap center
                            bounds = app_controller._parse_bounds(elem['bounds'])
                            center = app_controller._get_center(bounds)
                            return await app_controller.tap(serial, center[0], center[1])
                return {"success": False, "error": "App controller not available"}
            
            elif action == 'tap_coordinates':
                if app_controller:
                    return await app_controller.tap(serial, step['x'], step['y'])
                return {"success": False, "error": "App controller not available"}
            
            elif action == 'input_text':
                if app_controller:
                    # First tap the field
                    if 'field' in step:
                        # Try to find by hint or resource
                        result = await app_controller.find_element_by_text(serial, step['field'])
                        if result['success']:
                            await app_controller.tap_element(serial, text=step['field'])
                    return await app_controller.input_text(serial, step['text'])
                return {"success": False, "error": "App controller not available"}
            
            elif action == 'swipe':
                if gesture_engine:
                    direction = step.get('direction', 'up')
                    count = int(step.get('count', 1))
                    for _ in range(count):
                        await gesture_engine.scroll(serial, direction)
                    return {"success": True, "action": "swipe", "count": count}
                return {"success": False, "error": "Gesture engine not available"}
            
            elif action == 'press_key':
                if app_controller:
                    return await app_controller.press_key(serial, step['keycode'])
                return {"success": False, "error": "App controller not available"}
            
            elif action == 'authenticate':
                # Placeholder for authentication
                return {"success": True, "action": "authenticate", "note": "Manual authentication required"}
            
            elif action == 'extract_text':
                # Placeholder for text extraction
                return {"success": True, "action": "extract_text", "text": "N/A"}
            
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"success": False, "error": str(e), "action": action}
    
    async def run_workflow(self, workflow_id: str, serial: str, 
                          variables: Optional[Dict[str, Any]] = None,
                          app_controller=None, gesture_engine=None) -> Dict[str, Any]:
        load_result = self.load_workflow(workflow_id, variables)
        if not load_result['success']:
            return load_result
        
        workflow = load_result['workflow']
        results = []
        
        for i, step in enumerate(workflow['steps']):
            step_result = await self.execute_step(step, serial, app_controller, gesture_engine)
            step_result['step_index'] = i
            step_result['action'] = step.get('action')
            results.append(step_result)
            
            if not step_result['success']:
                return {
                    "success": False,
                    "error": f"Step {i} failed",
                    "step_results": results,
                    "failed_at": i
                }
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "steps_executed": len(results),
            "results": results
        }
    
    def list_workflows(self) -> List[Dict[str, str]]:
        return [
            {"id": k, "name": v['name']}
            for k, v in self.workflows.items()
        ]
    
    def add_workflow(self, workflow_id: str, name: str, steps: List[Dict[str, Any]]):
        self.workflows[workflow_id] = {
            'name': name,
            'steps': steps
        }

workflow_engine = WorkflowEngine()
