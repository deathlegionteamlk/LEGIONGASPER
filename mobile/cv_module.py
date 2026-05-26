import cv2
import numpy as np
from PIL import Image
from typing import Dict, Any, List, Tuple, Optional
import os

class CVAnalyzer:
    def __init__(self):
        self.last_image = None
        
    def load_image(self, image_path: str) -> np.ndarray:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")
        self.last_image = img
        return img
    
    def detect_buttons(self, image_path: str, min_area: int = 1000) -> Dict[str, Any]:
        try:
            img = self.load_image(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Find contours that could be buttons
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            buttons = []
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > min_area:
                    x, y, w, h = cv2.boundingRect(cnt)
                    aspect_ratio = float(w)/h
                    # Buttons usually have aspect ratio close to 1 or wide
                    if 0.2 < aspect_ratio < 5:
                        buttons.append({
                            "x": x, "y": y, "width": w, "height": h,
                            "area": area,
                            "aspect_ratio": aspect_ratio,
                            "center": (x + w//2, y + h//2)
                        })
            
            return {"success": True, "buttons": buttons, "count": len(buttons)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def detect_text_fields(self, image_path: str) -> Dict[str, Any]:
        try:
            img = self.load_image(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Look for rectangular regions that could be text fields
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            text_fields = []
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = float(w)/h
                # Text fields are usually wide and not too tall
                if w > 100 and 20 < h < 100 and aspect_ratio > 2:
                    text_fields.append({
                        "x": x, "y": y, "width": w, "height": h,
                        "center": (x + w//2, y + h//2)
                    })
            
            return {"success": True, "text_fields": text_fields, "count": len(text_fields)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def detect_images(self, image_path: str, min_area: int = 5000) -> Dict[str, Any]:
        try:
            img = self.load_image(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect image-like regions (larger areas with texture)
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            images = []
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > min_area:
                    x, y, w, h = cv2.boundingRect(cnt)
                    images.append({
                        "x": x, "y": y, "width": w, "height": h,
                        "area": area,
                        "center": (x + w//2, y + h//2)
                    })
            
            return {"success": True, "images": images, "count": len(images)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def detect_scrollable_areas(self, image_path: str) -> Dict[str, Any]:
        try:
            img = self.load_image(image_path)
            height, width = img.shape[:2]
            
            # Assume large central areas are scrollable
            scrollable = [{
                "x": 0,
                "y": 100,  # Below potential header
                "width": width,
                "height": height - 200,  # Above potential footer
                "type": "list"
            }]
            
            return {"success": True, "scrollable_areas": scrollable}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def find_template(self, image_path: str, template_path: str, 
                      threshold: float = 0.8) -> Dict[str, Any]:
        try:
            img = self.load_image(image_path)
            template = cv2.imread(template_path)
            
            if template is None:
                return {"success": False, "error": "Template not found"}
            
            result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                h, w = template.shape[:2]
                return {
                    "success": True,
                    "found": True,
                    "confidence": max_val,
                    "location": {"x": max_loc[0], "y": max_loc[1]},
                    "center": {"x": max_loc[0] + w//2, "y": max_loc[1] + h//2},
                    "size": {"width": w, "height": h}
                }
            else:
                return {"success": True, "found": False, "confidence": max_val}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def analyze_screen_layout(self, image_path: str) -> Dict[str, Any]:
        try:
            img = self.load_image(image_path)
            height, width = img.shape[:2]
            
            # Run all detections
            buttons = self.detect_buttons(image_path)
            text_fields = self.detect_text_fields(image_path)
            images = self.detect_images(image_path)
            scrollable = self.detect_scrollable_areas(image_path)
            
            layout = {
                "screen_size": {"width": width, "height": height},
                "buttons": buttons.get("buttons", []),
                "text_fields": text_fields.get("text_fields", []),
                "images": images.get("images", []),
                "scrollable_areas": scrollable.get("scrollable_areas", [])
            }
            
            return {"success": True, "layout": layout}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_dominant_colors(self, image_path: str, k: int = 5) -> Dict[str, Any]:
        try:
            img = self.load_image(image_path)
            data = np.float32(img).reshape((-1, 3))
            
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            colors = []
            for center in centers:
                b, g, r = center
                colors.append({
                    "rgb": (int(r), int(g), int(b)),
                    "hex": f"#{int(r):02x}{int(g):02x}{int(b):02x}"
                })
            
            return {"success": True, "dominant_colors": colors}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def detect_edges(self, image_path: str) -> Dict[str, Any]:
        try:
            img = self.load_image(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            
            # Count edge pixels
            edge_pixels = np.count_nonzero(edges)
            
            return {
                "success": True,
                "edge_pixels": int(edge_pixels),
                "edge_density": float(edge_pixels) / (edges.shape[0] * edges.shape[1])
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

cv_analyzer = CVAnalyzer()
