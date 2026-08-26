import re
import logging
from enum import Enum, auto

logger = logging.getLogger(__name__)

class UnitMode(Enum):
    AUTO = auto()
    MM_TO_CM = auto()
    PASSTHROUGH = auto()

class PreToolUnitInterceptor:
    """
    Production-grade interceptor to convert user-friendly units (mm, degrees)
    into Fusion 360's internal API units (cm, radians).
    """
    
    def __init__(self, mode: UnitMode = UnitMode.AUTO):
        self.mode = mode

    def process(self, tool_name: str, arguments: dict) -> dict:
        if tool_name != "fusion_mcp_execute" or self.mode == UnitMode.PASSTHROUGH:
            return arguments

        if "code" not in arguments:
            return arguments
            
        code = arguments["code"]
        original_code = code
        modified_code = self._convert_units(code)
        
        if modified_code != original_code:
            logger.info("PreToolUnitInterceptor modified code to match internal units.")
            
        arguments["code"] = modified_code
        return arguments

    def _convert_units(self, code: str) -> str:
        # Avoid modifying if # mm or # degrees hint is used to skip?
        # Actually, let's use the hint to enforce conversion if in AUTO mode,
        # but here we'll just parse the geometry creations.
        
        # 1. Point3D.create(x, y, z) and Vector3D.create(x, y, z)
        # Matches numbers, ignores if already divided by 10 or 10.0
        # e.g. Point3D.create(10, 20, 30) -> Point3D.create((10)/10.0, (20)/10.0, (30)/10.0)
        def xyz_replacer(match):
            prefix = match.group(1)
            args = [match.group(2), match.group(3), match.group(4)]
            new_args = []
            for arg in args:
                arg = arg.strip()
                if '/ 10' in arg or '/10' in arg or 'cm' in arg.lower():
                    new_args.append(arg)
                else:
                    new_args.append(f"({arg})/10.0")
            return f"{prefix}({new_args[0]}, {new_args[1]}, {new_args[2]})"
            
        code = re.sub(r'(Point3D\.create|Vector3D\.create)\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^\)]+)\s*\)', xyz_replacer, code)

        # 2. ValueInput.createByReal(val)
        def real_replacer(match):
            prefix = match.group(1)
            arg = match.group(2).strip()
            if '/ 10' in arg or '/10' in arg or 'math.radians' in arg:
                return match.group(0)
            return f"{prefix}(({arg})/10.0)"
        
        code = re.sub(r'(ValueInput\.createByReal)\s*\(\s*([^\)]+)\s*\)', real_replacer, code)
        
        # 3. ValueInput.createByString('X mm')
        # Sometimes users pass string literals, we can intercept and standardize if needed, 
        # but createByString('10 mm') is natively handled correctly by Fusion 360.
        # We will leave createByString alone as it evaluates correctly in the UI context.
        
        # 4. setAngleExtent(False, angle) or setAngleExtent(True, angle)
        def angle_replacer(match):
            prefix = match.group(1)
            is_symmetric = match.group(2)
            arg = match.group(3).strip()
            if 'math.radians' in arg or 'math.pi' in arg:
                return match.group(0)
            return f"{prefix}({is_symmetric}, math.radians({arg}))"
            
        code = re.sub(r'(setAngleExtent)\s*\(\s*([^,]+)\s*,\s*([^\)]+)\s*\)', angle_replacer, code)

        # 5. setDistanceExtent(False, dist)
        def distance_replacer(match):
            prefix = match.group(1)
            is_symmetric = match.group(2)
            arg = match.group(3).strip()
            if '/ 10' in arg or '/10' in arg:
                return match.group(0)
            return f"{prefix}({is_symmetric}, adsk.core.ValueInput.createByReal(({arg.replace('adsk.core.ValueInput.createByReal(', '').replace(')', '')})/10.0))"
        
        code = re.sub(r'(setDistanceExtent)\s*\(\s*([^,]+)\s*,\s*([^\)]+)\s*\)', distance_replacer, code)
        
        return code
