from .battle_recognizers import BattleRecognitionSuite
from .battle_command_profiles import BattleCommandProfile, BattleCommandProfileCatalog
from .battle_button_semantics import (
    BattleButtonSemanticCatalog,
    BattleButtonSemanticRule,
    SemanticVerificationResult,
)
from .button_detection import (
    BattleCommandCalibrationSuggestion,
    ButtonDetection,
    build_battle_command_calibration_suggestion,
    detect_battle_command_buttons,
)
from .interfaces import TemplateMatcher
from .observation import ObservationBuilder, ObservationSignalConfig
from .recognizer_models import RecognitionModuleResult, RecognitionModuleSpec, RecognitionSnapshot
from .regions import RegionCropper, RegionSpec
from .round_recognition import (
    RoundDigitClassifier,
    RoundDigitSegment,
    RoundDigitSegmenter,
    RoundImagePreprocessor,
    RoundNumberAssembler,
    RoundRecognitionResult,
    RoundRecognitionService,
    RoundRegionLocator,
    RoundSequenceTracker,
)
from .services import (
    NullTemplateMatcher,
    OpenCvTemplateMatcher,
    RegionRequest,
    StaticTemplateMatcher,
)
from .template_catalog import TemplateCatalog, TemplateDefinition

__all__ = [
    "ButtonDetection",
    "BattleRecognitionSuite",
    "BattleCommandProfile",
    "BattleCommandProfileCatalog",
    "BattleButtonSemanticCatalog",
    "BattleButtonSemanticRule",
    "RoundDigitClassifier",
    "RoundDigitSegment",
    "RoundDigitSegmenter",
    "RoundImagePreprocessor",
    "RoundNumberAssembler",
    "RoundRecognitionResult",
    "RoundRecognitionService",
    "RoundRegionLocator",
    "RoundSequenceTracker",
    "BattleCommandCalibrationSuggestion",
    "detect_battle_command_buttons",
    "build_battle_command_calibration_suggestion",
    "NullTemplateMatcher",
    "ObservationBuilder",
    "ObservationSignalConfig",
    "OpenCvTemplateMatcher",
    "RegionCropper",
    "RegionRequest",
    "RegionSpec",
    "StaticTemplateMatcher",
    "SemanticVerificationResult",
    "RecognitionModuleResult",
    "RecognitionModuleSpec",
    "RecognitionSnapshot",
    "TemplateCatalog",
    "TemplateDefinition",
    "TemplateMatcher",
]
