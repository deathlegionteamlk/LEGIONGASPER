import os
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image
import numpy as np

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

class OCRProcessor:
    def __init__(self, lang: str = 'en'):
        self.lang = lang
        self.easyocr_reader = None
        
        if EASYOCR_AVAILABLE:
            try:
                self.easyocr_reader = easyocr.Reader([lang])
            except:
                pass
    
    def extract_text_from_image(self, image_path: str, 
                                 confidence_threshold: float = 0.5) -> Dict[str, Any]:
        if not os.path.exists(image_path):
            return {"success": False, "error": f"Image not found: {image_path}"}
        
        results = []
        
        # Try pytesseract first
        if PYTESSERACT_AVAILABLE:
            try:
                text = pytesseract.image_to_string(image_path, lang=self.lang)
                results.append({"engine": "pytesseract", "text": text.strip()})
            except Exception as e:
                results.append({"engine": "pytesseract", "error": str(e)})
        
        # Try easyocr
        if EASYOCR_AVAILABLE and self.easyocr_reader:
            try:
                img = Image.open(image_path)
                ocr_result = self.easyocr_reader.readtext(np.array(img))
                
                text_parts = []
                for detection in ocr_result:
                    bbox, detected_text, conf = detection
                    if conf >= confidence_threshold:
                        text_parts.append({
                            "text": detected_text,
                            "confidence": conf,
                            "bbox": bbox
                        })
                
                results.append({
                    "engine": "easyocr",
                    "detections": text_parts,
                    "text": " ".join([d["text"] for d in text_parts])
                })
            except Exception as e:
                results.append({"engine": "easyocr", "error": str(e)})
        
        if not results:
            return {"success": False, "error": "No OCR engines available"}
        
        return {"success": True, "results": results}
    
    def extract_text_from_screen(self, screenshot_path: str,
                                  region: Optional[Tuple[int, int, int, int]] = None) -> Dict[str, Any]:
        if region:
            try:
                img = Image.open(screenshot_path)
                cropped = img.crop(region)
                temp_path = "/tmp/ocr_crop.png"
                cropped.save(temp_path)
                return self.extract_text_from_image(temp_path)
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        return self.extract_text_from_image(screenshot_path)
    
    def find_text_on_screen(self, screenshot_path: str, 
                            search_text: str) -> Dict[str, Any]:
        result = self.extract_text_from_image(screenshot_path)
        if not result["success"]:
            return result
        
        matches = []
        for engine_result in result["results"]:
            if "detections" in engine_result:
                for detection in engine_result["detections"]:
                    if search_text.lower() in detection["text"].lower():
                        matches.append({
                            "text": detection["text"],
                            "confidence": detection["confidence"],
                            "bbox": detection["bbox"],
                            "engine": engine_result["engine"]
                        })
            elif "text" in engine_result:
                if search_text.lower() in engine_result["text"].lower():
                    matches.append({
                        "text": engine_result["text"],
                        "engine": engine_result["engine"]
                    })
        
        return {
            "success": True,
            "found": len(matches) > 0,
            "matches": matches,
            "count": len(matches)
        }
    
    def get_text_regions(self, image_path: str) -> Dict[str, Any]:
        if not EASYOCR_AVAILABLE or not self.easyocr_reader:
            return {"success": False, "error": "EasyOCR not available for region detection"}
        
        try:
            img = Image.open(image_path)
            result = self.easyocr_reader.readtext(np.array(img))
            
            regions = []
            for detection in result:
                bbox, text, conf = detection
                regions.append({
                    "text": text,
                    "confidence": conf,
                    "bbox": {
                        "top_left": bbox[0],
                        "top_right": bbox[1],
                        "bottom_right": bbox[2],
                        "bottom_left": bbox[3]
                    },
                    "center": self._get_center(bbox)
                })
            
            return {"success": True, "regions": regions, "count": len(regions)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_center(self, bbox: List) -> Tuple[float, float]:
        x_coords = [p[0] for p in bbox]
        y_coords = [p[1] for p in bbox]
        return (sum(x_coords) / len(x_coords), sum(y_coords) / len(y_coords))
    
    def get_confidence(self, image_path: str) -> Dict[str, Any]:
        if not EASYOCR_AVAILABLE or not self.easyocr_reader:
            return {"success": False, "error": "EasyOCR not available"}
        
        try:
            img = Image.open(image_path)
            result = self.easyocr_reader.readtext(np.array(img))
            
            confidences = [detection[2] for detection in result]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                "success": True,
                "average_confidence": avg_confidence,
                "min_confidence": min(confidences) if confidences else 0,
                "max_confidence": max(confidences) if confidences else 0,
                "detections": len(confidences)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

ocr_processor = OCRProcessor()
